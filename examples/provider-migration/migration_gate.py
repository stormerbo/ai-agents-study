"""Offline migration-contract gate; fixtures are not provider evidence."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Outcome:
    state: str  # completed, tool_call, refusal, truncated, error, unknown
    text: Optional[str] = None
    tool_name: Optional[str] = None
    arguments: Optional[dict] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


def evaluate_case(case_id: str, expected_state: str, outcome: Outcome) -> dict:
    """Keep semantically distinct terminal states distinct; never infer success."""
    passed = outcome.state == expected_state
    if outcome.state == "tool_call":
        passed = passed and bool(outcome.tool_name) and outcome.arguments is not None
    if outcome.state == "completed":
        passed = passed and outcome.text is not None
    return {
        "case_id": case_id,
        "expected": expected_state,
        "actual": outcome.state,
        "passed": passed,
        "usage": {
            "input_tokens": outcome.input_tokens,
            "output_tokens": outcome.output_tokens,
        },
    }


def migration_decision(results: list[dict], required_case_ids: set[str]) -> str:
    by_id = {item["case_id"]: item for item in results}
    if not required_case_ids or len(by_id) != len(results) or set(by_id) != required_case_ids:
        return "incomplete"
    if not all(item["passed"] for item in results):
        return "blocked"
    return "fixture-pass"
