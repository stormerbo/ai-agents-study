"""Offline regression for typed structured-note validation in the compaction lesson."""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/context-engineering/04-compaction.mdx"
source = LESSON.read_text(encoding="utf-8")
fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", source, re.MULTILINE)
assert len(fences) == 2, f"expected two Python fences, got {len(fences)}"
for index, body in enumerate(fences, 1):
    compile(body, f"compaction-fence-{index}", "exec")

helper = next(body for body in fences if "def validate_notes" in body)
tree = ast.parse(helper)
selected = [node for node in tree.body if isinstance(node, (ast.Assign, ast.FunctionDef))]
ns: dict[str, object] = {}
exec(compile(ast.Module(body=selected, type_ignores=[]), "note-validator", "exec"), ns)
validate = ns["validate_notes"]
merge = ns["merge_notes"]

good = {
    "identifiers": [{"fact_id":"id1","value":"ORD-1","what":"订单号","source":"turn-1"}],
    "amounts": [{"fact_id":"amount1","value":4820,"unit":"CNY","what":"退款金额","source":"turn-1"}],
    "dates": [{"fact_id":"date1","value":"2026-03-15","what":"复检截止","source":"turn-2"}],
    "rejected_proposals": [{"fact_id":"rejected1","proposal":"批量接口","reason":"不支持幂等","turn":3,"source":"turn-3"}],
    "constraints": [{"fact_id":"constraint1","text":"不要动生产库","speaker":"客户","turn":8,"source":"turn-8"}],
    "error_codes": [{"fact_id":"error1","value":"ERR_POOL_EXHAUSTED","source":"turn-4"}],
    "contacts": [{"fact_id":"contact1","name":"张岚","role":"对接人","source":"turn-8"}],
}
checks: list[tuple[bool, str]] = []
def check(ok: bool, label: str) -> None:
    checks.append((ok, label))

check(validate(good) == [], "all lesson-shaped note categories pass")
check(bool(validate({})), "missing top-level categories are rejected")
check(bool(validate({**good,"amounts":[{"fact_id":"x","value":"4820","unit":"CNY","what":"amount","source":"turn-1"}]})), "amount strings are rejected instead of accepted as numbers")
check(bool(validate({**good,"amounts":[{"fact_id":"x","value":True,"unit":"CNY","what":"amount","source":"turn-1"}]})), "boolean values are rejected as monetary numbers")
check(bool(validate({**good,"dates":[{"fact_id":"x","value":"2026-03-15","source":"turn-2"}]})), "date facts require the descriptive field shown in the lesson schema")
check(bool(validate({**good,"constraints":[{"fact_id":"x","text":"不要动生产库","speaker":"客户","turn":"8","source":"turn-8"}]})), "constraint turn must be an integer")
check(bool(validate({**good,"rejected_proposals":[{"fact_id":"x","proposal":"批量接口","reason":"不支持幂等","turn":False,"source":"turn-3"}]})), "boolean is rejected for rejected-proposal turn")
check(bool(validate({**good,"contacts":["张岚"]})), "non-object list members are rejected")
check(bool(validate({**good,"identifiers":[{"fact_id":"x","value":"ORD-2","what":"订单号","source":None}]})), "source must be a nonempty string")
try:
    merge(good,[{"category":"amounts","fact_id":"new","value":"4820","unit":"CNY","what":"金额","source":"turn-9"}])
except ValueError:
    checks.append((True,"merge rejects a new fact that violates category value types"))
else:
    checks.append((False,"merge rejects a new fact that violates category value types"))
check(len(merge(good,[{"category":"amounts","fact_id":"new","value":4900,"unit":"CNY","what":"金额","source":"turn-9"}])["amounts"]) == 2, "merge accepts a well-typed new fact")

for passed, label in checks:
    print(("PASS" if passed else "FAIL") + ": " + label)
if not all(passed for passed, _ in checks):
    raise SystemExit(1)
print(f"RESULT {len(checks)}/{len(checks)} PASS; providerCalls=0; externalNetworkCalls=0")
