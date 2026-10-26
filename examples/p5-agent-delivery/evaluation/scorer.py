"""Deterministic task scorer. Its bytes are pinned by release.json."""

from __future__ import annotations


def score_case(case: dict, attempts: list[dict]) -> dict:
    scored = []
    for result in attempts:
        predicted = set(result["citations"])
        required = set(case["required_citations"])
        citation_tp = len(predicted & required)
        citation_fp = len(predicted - required)
        citation_fn = len(required - predicted)
        state_ok = result["final_state"] == case["target_state"]
        refusal_ok = result["refusal"] is case["expect_refusal"]
        clarification_ok = result["clarification"] is case["expect_clarification"]
        gates_ok = all(result["hard_gate_passes"].get(gate) is True for gate in case["hard_gates"])
        scored.append({
            "attempt_id": result["attempt_id"],
            "expected_state": case["target_state"],
            "observed_state": result["final_state"],
            "expected_refusal": case["expect_refusal"],
            "observed_refusal": result["refusal"],
            "expected_clarification": case["expect_clarification"],
            "observed_clarification": result["clarification"],
            "required_citations": sorted(required),
            "observed_citations": sorted(predicted),
            "state_ok": state_ok,
            "citation_precision_counts": {"true_positive": citation_tp, "false_positive": citation_fp},
            "citation_recall_counts": {"true_positive": citation_tp, "false_negative": citation_fn},
            "refusal_ok": refusal_ok,
            "clarification_ok": clarification_ok,
            "refusal_completion_classification_correct": state_ok and refusal_ok and clarification_ok,
            "tool_correct": result["tool_correct"],
            "quality_pass": result["quality_pass"],
            "hard_gates_pass": gates_ok,
            "hard_gate_results": {gate: result["hard_gate_passes"][gate] for gate in case["hard_gates"]},
            "task_success": state_ok and refusal_ok and clarification_ok and citation_fn == 0 and gates_ok and result["quality_pass"] and (not case["requires_tool"] or result["tool_correct"] is True),
            "token_usage": result["token_usage"],
            "external_tool_cost_usd": result["external_tool_cost_usd"],
            "latency_ms": result["latency_ms"],
        })

    def mean(field: str):
        values = [item[field] for item in scored if item[field] is not None]
        return sum(values) / len(values) if values else None

    precisions = []
    recalls = []
    for item in scored:
        counts = item["citation_precision_counts"]
        precision_denominator = counts["true_positive"] + counts["false_positive"]
        recall_denominator = counts["true_positive"] + item["citation_recall_counts"]["false_negative"]
        precisions.append(counts["true_positive"] / precision_denominator if precision_denominator else None)
        recalls.append(counts["true_positive"] / recall_denominator if recall_denominator else None)

    return {
        "task_id": case["task_id"],
        "case_id": case["id"],
        "attempt_count": len(scored),
        "task_success": all(item["task_success"] for item in scored),
        "quality_pass": all(item["quality_pass"] for item in scored),
        "tool_correct": all(item["tool_correct"] for item in scored if item["tool_correct"] is not None) if any(item["tool_correct"] is not None for item in scored) else None,
        "tool_required": case["requires_tool"],
        "refusal_completion_classification_correct": all(item["refusal_completion_classification_correct"] for item in scored),
        "citation_counts": {
            "true_positive": sum(item["citation_precision_counts"]["true_positive"] for item in scored),
            "false_positive": sum(item["citation_precision_counts"]["false_positive"] for item in scored),
            "false_negative": sum(item["citation_recall_counts"]["false_negative"] for item in scored),
        },
        "citation_precision": mean_from_values(precisions),
        "citation_recall": mean_from_values(recalls),
        "hard_gate_results": {
            gate: all(item["hard_gate_results"][gate] for item in scored)
            for gate in case["hard_gates"]
        },
        "mean_token_usage": mean("token_usage"),
        "mean_external_tool_cost_usd": mean("external_tool_cost_usd"),
        "mean_latency_ms": mean("latency_ms"),
        "attempts": scored,
    }


def mean_from_values(values: list[float | None]):
    present = [value for value in values if value is not None]
    return sum(present) / len(present) if present else None
