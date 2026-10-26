"""Small Anthropic Messages adapter for the durable P5 host.

Credential-bearing client construction stays outside durable request data. The
SDK's automatic retries are explicitly disabled so the host's request ledger is
the only place that can decide whether another provider call is allowed.
"""
from __future__ import annotations

from ipaddress import ip_address
from typing import Any
from urllib.parse import urlsplit


class AnthropicMessagesAdapter:
    """Adapt one host request to exactly one SDK Messages API call."""

    max_retries = 0

    def __init__(self, client: Any):
        messages = getattr(client, "messages", None)
        if not callable(getattr(messages, "create", None)):
            raise TypeError("Anthropic client must expose messages.create")
        if getattr(client, "max_retries", None) != 0:
            raise ValueError("Anthropic SDK client must be constructed with max_retries=0")
        self._client = client

    def __call__(self, request: dict):
        if not isinstance(request, dict):
            raise TypeError("Messages request must be an object")
        required = {"model", "max_tokens", "messages"}
        if not required.issubset(request):
            raise ValueError("Messages request is missing model, max_tokens, or messages")
        return self._client.messages.create(**request)


def build_anthropic_client(client_class, api_key: str, base_url: str | None = None,
                           *, timeout: float = 45.0):
    """Construct the SDK client with retries disabled and bounded timeout."""
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("Anthropic API key is required")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 120:
        raise ValueError("Provider timeout must be in (0, 120] seconds")
    kwargs = {"api_key": api_key, "timeout": timeout, "max_retries": 0}
    if base_url is not None:
        if not isinstance(base_url, str):
            raise ValueError("Provider base URL must use HTTPS or loopback HTTP")
        parsed = urlsplit(base_url)
        try:
            hostname = parsed.hostname
            port = parsed.port
        except ValueError as exc:
            raise ValueError("Provider base URL must use HTTPS or loopback HTTP") from exc
        loopback = hostname == "localhost"
        if hostname and not loopback:
            try:
                loopback = ip_address(hostname).is_loopback
            except ValueError:
                loopback = False
        secure = parsed.scheme == "https" and bool(hostname)
        local_http = parsed.scheme == "http" and loopback
        if (not (secure or local_http) or parsed.username is not None or parsed.password is not None
                or parsed.query or parsed.fragment or port == 0):
            raise ValueError("Provider base URL must use HTTPS or loopback HTTP")
        kwargs["base_url"] = base_url
    return client_class(**kwargs)


def create_anthropic_client(api_key: str, base_url: str | None = None, *, timeout: float = 45.0):
    """Lazy import the SDK so offline P5 contract tests need no network client."""
    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise RuntimeError("Install the P5 provider dependencies to use Anthropic") from exc
    return build_anthropic_client(Anthropic, api_key, base_url, timeout=timeout)
