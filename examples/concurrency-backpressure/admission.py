"""Small deterministic model for bounded admission and retry decisions."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Admission:
    state: str
    reserved_budget: float = 0


def admit(
    *,
    now: float,
    deadline: float,
    active: int,
    queued: int,
    max_active: int,
    max_queue: int,
    remaining_budget: float,
    reserve: float,
) -> Admission:
    if now >= deadline:
        return Admission("expired")
    if reserve < 0 or reserve > remaining_budget:
        return Admission("budget_exhausted")
    if active < max_active:
        return Admission("started", reserve)
    if queued < max_queue:
        return Admission("queued", reserve)
    return Admission("queue_full")


def retry_delay(
    *,
    error_kind: str,
    attempt: int,
    max_attempts: int,
    now: float,
    deadline: float,
    retry_after: float | None,
    backoff_base: float = 1,
    backoff_cap: float = 30,
    jitter: float = 0,
) -> float | None:
    """Return a scheduled delay, or None when retry is unsafe/unhelpful.

    `retry_after` is a minimum server hint. Permanent quota/billing failures
    are intentionally distinct from transient rate limiting.
    """
    transient = {"rate_limited", "overloaded", "connection_error"}
    if error_kind not in transient or attempt >= max_attempts:
        return None
    if backoff_base <= 0 or backoff_cap < 0 or jitter < 0:
        raise ValueError("invalid retry policy")
    if retry_after is not None and retry_after < 0:
        retry_after = None
    exponential = min(backoff_cap, backoff_base * (2 ** max(0, attempt - 1)))
    delay = max(exponential, retry_after or 0) + jitter
    if now + delay >= deadline:
        return None
    return delay
