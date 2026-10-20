"""Small immutable after-sales fixtures; every operation is read-only."""

from __future__ import annotations

import json

FIXTURE_VERSION = "after-sales-fixtures-2026-10-18-v1"

ORDERS = {
    "A-1001": {
        "order_id": "A-1001",
        "status": "shipped",
        "carrier": "顺丰",
        "last_update": "2026-10-18",
    },
    "A-1002": {
        "order_id": "A-1002",
        "status": "processing",
        "carrier": None,
        "last_update": "2026-10-17",
    },
}

POLICIES = [
    {
        "policy_id": "returns-standard",
        "version": "2026-01",
        "text": "未使用商品可在签收后 30 天内申请退货。",
    },
    {
        "policy_id": "refund-timing",
        "version": "2026-01",
        "text": "退货申请获批后，退款通常在 5 个工作日内处理。",
    },
]


def lookup_order(order_id: str) -> str:
    order = ORDERS.get(order_id)
    if order is None:
        return json.dumps({"error": "not_found", "message": "合成订单不存在"}, ensure_ascii=False)
    return json.dumps(order, ensure_ascii=False)


def search_policy(query: str) -> str:
    normalized = query.casefold()
    terms = ("退货", "退款", "未使用", "签收", "工作日", "return", "refund")
    if not any(term in normalized for term in terms):
        return json.dumps({"results": [], "reason": "no_policy_match"}, ensure_ascii=False)
    matching = [
        policy
        for policy in POLICIES
        if any(term in normalized and term in policy["text"].casefold() for term in terms)
    ]
    return json.dumps({"results": matching}, ensure_ascii=False)
