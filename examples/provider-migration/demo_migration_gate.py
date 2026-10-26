"""Run the fixture-only walkthrough shown in the provider migration lesson."""
from migration_gate import Outcome, evaluate_case, migration_decision


def main() -> None:
    fixtures = [
        ("plain", "completed", Outcome("completed", text="ok")),
        ("refusal", "refusal", Outcome("refusal", text="I cannot help")),
        ("long", "truncated", Outcome("truncated", text="partial")),
        (
            "lookup",
            "tool_call",
            Outcome("tool_call", tool_name="lookup", arguments={"id": "A-1"}),
        ),
    ]
    results = [evaluate_case(*fixture) for fixture in fixtures]
    states = ", ".join(
        f"{result['case_id']} {result['actual']}" for result in results
    )
    print(f"fixture: {states}")
    print(
        "fixture decision: "
        + migration_decision(results, {result["case_id"] for result in results})
    )
    print(f"empty required suite: {migration_decision([], set())}")
    live_evidence = None
    print(
        "live-provider decision: unavailable (no live responses recorded)"
        if live_evidence is None
        else "live-provider decision: requires a separate live-evidence gate"
    )


if __name__ == "__main__":
    main()
