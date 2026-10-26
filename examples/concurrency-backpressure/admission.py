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
    queue_wait: float,
    max_queue_wait: float,
) -> Admission:
    capacities = (active, queued, max_active, max_queue)
    if any(type(value) is not int for value in capacities):
        raise ValueError("invalid admission capacity")
    finite_values = (now, deadline, remaining_budget, reserve, queue_wait, max_queue_wait)
    if not all(math.isfinite(value) for value in finite_values):
        raise ValueError("invalid admission values")
    if max_active <= 0 or max_queue < 0 or active < 0 or queued < 0:
        raise ValueError("invalid admission capacity")
    if remaining_budget < 0 or reserve < 0 or queue_wait < 0 or max_queue_wait < 0:
        raise ValueError("invalid admission values")
    if now >= deadline:
        return Admission("expired")
    if reserve < 0 or reserve > remaining_budget:
        return Admission("budget_exhausted")
    if active < max_active:
        return Admission("started", reserve)
    if queued < max_queue:
        if queue_wait > max_queue_wait:
            return Admission("queue_wait_exceeded")
        if now + queue_wait >= deadline:
            return Admission("expired")
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
    request_replay_safe: bool = False,
    backoff_base: float = 1,
    backoff_cap: float = 30,
    jitter_seconds: float = 0,
) -> float | None:
    """Return a scheduled delay, or None when retry is unsafe/unhelpful.

    `retry_after` is a minimum server hint. Permanent quota/billing failures
    are intentionally distinct from transient rate limiting.
    """
    if type(attempt) is not int or type(max_attempts) is not int:
        raise ValueError("invalid retry policy")
    transient = {"rate_limited", "overloaded"}
    if error_kind == "connection_error" and request_replay_safe:
        transient.add("connection_error")
    if error_kind not in transient or attempt >= max_attempts:
        return None
    if not all(math.isfinite(value) for value in (now, deadline, backoff_base, backoff_cap, jitter_seconds)):
        raise ValueError("invalid retry policy")
    if attempt < 1 or max_attempts < 1 or backoff_base <= 0 or backoff_cap < 0 or jitter_seconds < 0:
        raise ValueError("invalid retry policy")
    if retry_after is not None and (not math.isfinite(retry_after) or retry_after < 0):
        raise ValueError("retry_after must be a parsed non-negative delay")
    exponential = min(backoff_cap, backoff_base * (2 ** max(0, attempt - 1)))
    delay = max(exponential, retry_after or 0) + jitter_seconds
    if now + delay >= deadline:
        return None
    return delay
