"""Offline checks for P5's trusted schema and provider adapter boundary."""
import asyncio
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
P4 = ROOT / "p4-durable-support"
P5 = ROOT / "p5-agent-delivery"
for path in (ROOT, P4, P5):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.actions import REGISTRY
from host import _usage, trusted_provider_tools
from provider import AnthropicMessagesAdapter, build_anthropic_client
from runner import (
    SYNTHETIC_PROMPT,
    SYSTEM_PROMPT,
    _live_provenance,
    _mcp_components,
    _sha256,
    _with_mcp_session,
)


class HostContractTests(unittest.TestCase):
    def test_anthropic_adapter_forwards_one_exact_messages_request(self):
        class Messages:
            def __init__(self):
                self.calls = []
                self.response = {"id": "resp_1"}

            def create(self, **kwargs):
                self.calls.append(kwargs)
                return self.response

        class Client:
            max_retries = 0

            def __init__(self):
                self.messages = Messages()

        client = Client()
        adapter = AnthropicMessagesAdapter(client)
        request = {"model": "claude-test", "max_tokens": 80,
                   "system": "synthetic only", "messages": [{"role": "user", "content": "hello"}],
                   "tools": []}

        self.assertEqual(adapter.max_retries, 0)
        self.assertIs(adapter(request), client.messages.response)
        self.assertEqual(client.messages.calls, [request])

    def test_adapter_rejects_clients_with_sdk_retries_enabled(self):
        class Messages:
            def create(self, **kwargs):
                return kwargs

        class Client:
            max_retries = 2
            messages = Messages()

        with self.assertRaisesRegex(ValueError, "max_retries=0"):
            AnthropicMessagesAdapter(Client())

    def test_anthropic_client_factory_disables_sdk_retries(self):
        class FakeAnthropicClient:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        client = build_anthropic_client(FakeAnthropicClient, "test-key", "https://api.example.test",
                                        timeout=4.5)

        self.assertEqual(client.kwargs, {"api_key": "test-key", "base_url": "https://api.example.test",
                                         "timeout": 4.5, "max_retries": 0})

    def test_anthropic_factory_rejects_non_loopback_plain_http_hosts(self):
        class FakeAnthropicClient:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        with self.assertRaisesRegex(ValueError, "HTTPS or loopback"):
            build_anthropic_client(FakeAnthropicClient, "test-key", "http://localhost.attacker.test")
        self.assertEqual(build_anthropic_client(FakeAnthropicClient, "test-key", "http://127.0.0.1:8080").kwargs,
                         {"api_key": "test-key", "timeout": 45.0, "max_retries": 0,
                          "base_url": "http://127.0.0.1:8080"})

    def test_model_schemas_come_from_registry_and_mcp_reads_must_match(self):
        peer = [
            {"name": "lookup_order", "inputSchema": REGISTRY["lookup_order"][0]},
            {"name": "search_policy", "inputSchema": REGISTRY["search_policy"][0]},
            {"name": "untrusted_write", "inputSchema": {"type": "object", "properties": {}}},
        ]
        tools = trusted_provider_tools(peer)
        self.assertEqual([item["name"] for item in tools], ["lookup_order", "search_policy", "send_notice"])
        self.assertEqual(tools[0]["input_schema"], REGISTRY["lookup_order"][0])
        self.assertEqual(tools[-1]["input_schema"], REGISTRY["send_notice"][0])
        peer[0]["inputSchema"] = {"type": "object", "properties": {"order_id": {"type": "string"}}}
        with self.assertRaisesRegex(ValueError, "schema mismatch"):
            trusted_provider_tools(peer)

    def test_actual_p3_mcp_peer_matches_registry_and_rejects_extra_arguments(self):
        async def read_and_validate(session):
            listed = await session.list_tools()
            provider_tools = trusted_provider_tools(listed.tools)
            valid = await session.call_tool("lookup_order", {"order_id": "A-1001"})
            extra = await session.call_tool("lookup_order", {"order_id": "A-1001", "tenant_id": "tenant-b"})
            return provider_tools, valid, extra

        provider_tools, valid, extra = asyncio.run(_with_mcp_session(read_and_validate, _mcp_components()))
        self.assertEqual([item["name"] for item in provider_tools], ["lookup_order", "search_policy", "send_notice"])
        self.assertEqual(valid.content[0].text, '{"order_id": "A-1001", "status": "shipped", "carrier": "顺丰", "last_update": "2026-10-18"}')
        self.assertTrue(extra.is_error)
        prompt_hash = _sha256(json.dumps(
            {"system": SYSTEM_PROMPT, "user": SYNTHETIC_PROMPT},
            sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        ))
        tools_hash = _sha256(json.dumps(
            provider_tools,
            sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        ))
        provenance = _live_provenance(prompt_hash, tools_hash, provider_tools)
        self.assertIn("examples/p3-controlled-agent/server.py", provenance["code_file_sha256"])
        self.assertIn("examples/p3-controlled-agent/fixtures.py", provenance["code_file_sha256"])

    def test_usage_preserves_unknown_dimensions_instead_of_coercing_booleans(self):
        self.assertEqual(_usage({"usage": {"input_tokens": 1, "output_tokens": 2,
            "cache_creation_input_tokens": 5, "cache_read_input_tokens": 7}, "content": []}), (15, 0))
        self.assertEqual(_usage({"usage": {"input_tokens": 1, "output_tokens": 2,
            "cache_creation_input_tokens": 5, "cache_read_input_tokens": None}, "content": []}), (None, 0))
        self.assertEqual(_usage({"usage": {"input_tokens": True, "output_tokens": 2,
            "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}, "content": []}), (None, 0))
