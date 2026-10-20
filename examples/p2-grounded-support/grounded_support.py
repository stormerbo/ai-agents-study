"""Offline lexical retrieval that returns authorized policy text as its answer."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Iterable


@dataclass(frozen=True)
class Principal:
    subject_id: str
    tenant_id: str


@dataclass(frozen=True)
class Evidence:
    doc_id: str
    version: str
    text: str
    overlap: int


@dataclass(frozen=True)
class Answer:
    status: str
    answer: str | None
    evidence: list[Evidence]


class PolicyIndex:
    MIN_OVERLAP_TERMS = 2

    def __init__(self) -> None:
        self._documents: list[dict[str, object]] = []

    def add_document(
        self,
        *,
        doc_id: str,
        version: str,
        tenant_id: str,
        text: str,
        allowed_principals: Iterable[str],
        valid_from: str = "0001-01-01",
        valid_until: str = "9999-12-31",
    ) -> None:
        self._documents.append(
            {
                "doc_id": doc_id,
                "version": version,
                "tenant_id": tenant_id,
                "text": text,
                "allowed_principals": frozenset(allowed_principals),
                "deleted": False,
                "valid_from": valid_from,
                "valid_until": valid_until,
            }
        )

    def delete_document(self, doc_id: str, version: str) -> None:
        found = False
        for doc in self._documents:
            if doc["doc_id"] == doc_id and doc["version"] == version:
                doc["deleted"] = True
                found = True
        if not found:
            raise KeyError(f"unknown policy version: {doc_id}@{version}")

    def answer(
        self, principal: Principal, query: str, top_k: int = 3, as_of: str = "9999-12-31"
    ) -> Answer:
        if top_k < 1:
            raise ValueError("top_k must be positive")
        query_terms = _tokens(query)
        if not query_terms:
            return Answer("insufficient_evidence", None, [])

        # Authorization is applied before text scoring or evidence construction.
        candidates = [
            doc
            for doc in self._documents
            if doc["tenant_id"] == principal.tenant_id
            and principal.subject_id in doc["allowed_principals"]
            and not doc["deleted"]
            and str(doc["valid_from"]) <= as_of <= str(doc["valid_until"])
        ]
        ranked: list[Evidence] = []
        for doc in candidates:
            overlap = len(query_terms & _tokens(str(doc["text"])))
            if overlap >= self.MIN_OVERLAP_TERMS:
                ranked.append(
                    Evidence(
                        doc_id=str(doc["doc_id"]),
                        version=str(doc["version"]),
                        text=str(doc["text"]),
                        overlap=overlap,
                    )
                )
        ranked.sort(key=lambda item: (-item.overlap, item.doc_id))
        selected = ranked[:top_k]
        if not selected:
            return Answer("insufficient_evidence", None, [])
        # Extractive answer: no unsupported synthesis is introduced offline.
        return Answer("evidence_found", selected[0].text, selected)


def evaluate_recall(retrieved: Iterable[str], relevant: set[str]) -> float:
    if not relevant:
        raise ValueError("relevant document set must not be empty")
    return len(set(retrieved) & relevant) / len(relevant)


def _tokens(text: str) -> set[str]:
    # Keep English words and individual CJK characters as a transparent baseline.
    return set(re.findall(r"[a-z0-9]+|[\u3400-\u9fff]", text.lower()))


def load_index(path: Path) -> PolicyIndex:
    index = PolicyIndex()
    records = json.loads(path.read_text(encoding="utf-8"))
    for record in records:
        index.add_document(
            doc_id=record["doc_id"],
            version=record["version"],
            tenant_id=record["tenant_id"],
            text=record["text"],
            allowed_principals=record["allowed_principals"],
            valid_from=record.get("valid_from", "0001-01-01"),
            valid_until=record.get("valid_until", "9999-12-31"),
        )
    return index


def evaluate_cases(index: PolicyIndex, cases: list[dict[str, object]], top_k: int = 3) -> dict[str, object]:
    answerable = 0
    recall_total = 0.0
    cited = 0
    supported_citations = 0
    correct_abstentions = 0
    exact_answer_matches = 0
    details: list[dict[str, object]] = []
    for case in cases:
        relevant = set(case["relevant_doc_ids"])
        result = index.answer(
            Principal(str(case["subject_id"]), str(case["tenant_id"])),
            str(case["query"]),
            top_k=top_k,
            as_of=str(case["as_of"]),
        )
        retrieved = [item.doc_id for item in result.evidence]
        exact_answer_matches += int(result.answer == case["expected_answer"])
        if relevant:
            answerable += 1
            recall_total += len(set(retrieved) & relevant) / len(relevant)
        else:
            correct_abstentions += int(result.status == "insufficient_evidence")
        cited += len(retrieved)
        supported_citations += sum(doc_id in relevant for doc_id in retrieved)
        details.append({
            "case_id": case["case_id"],
            "status": result.status,
            "retrieved_doc_ids": retrieved,
            "expected_doc_ids": sorted(relevant),
        })
    return {
        "case_count": len(cases),
        "answerable_cases": answerable,
        "recall_at_k": round(recall_total / answerable, 4) if answerable else None,
        "citation_precision": round(supported_citations / cited, 4) if cited else None,
        "answer_exact_match": round(exact_answer_matches / len(cases), 4) if cases else None,
        "correct_abstentions": correct_abstentions,
        "no_answer_cases": len(cases) - answerable,
        "details": details,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Offline, extractive after-sales policy retrieval")
    parser.add_argument("--tenant", default="tenant-a")
    parser.add_argument("--subject", default="member-a")
    parser.add_argument("--query", help="search a policy query")
    parser.add_argument("--as-of", default="2026-03-01", help="validity date in YYYY-MM-DD")
    parser.add_argument("--top-k", type=int, default=3, help="number of evidence candidates to return")
    parser.add_argument("--evaluate", action="store_true", help="run the fixed synthetic evaluation set")
    args = parser.parse_args()
    root = Path(__file__).parent
    index = load_index(root / "data" / "policies.json")
    if args.evaluate:
        cases = json.loads((root / "data" / "eval_cases.json").read_text(encoding="utf-8"))
        print(json.dumps(evaluate_cases(index, cases, top_k=args.top_k), ensure_ascii=False, indent=2))
    elif args.query:
        result = index.answer(Principal(args.subject, args.tenant), args.query, top_k=args.top_k, as_of=args.as_of)
        print(json.dumps({
            "status": result.status,
            "answer": result.answer,
            "citations": [item.__dict__ for item in result.evidence],
        }, ensure_ascii=False, indent=2))
    else:
        parser.error("provide --query or --evaluate")


if __name__ == "__main__":
    main()
