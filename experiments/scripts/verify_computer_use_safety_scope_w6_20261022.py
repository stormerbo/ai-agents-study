"""W6 safety-scope regression checks for typed budget inputs and control ordering."""
from __future__ import annotations

import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/computer-use/04-safety-and-scope.mdx"
text = LESSON.read_text(encoding="utf-8")
fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", text, re.MULTILINE)
main = next((code for code in fences if "class Guard:" in code), None)
assert main is not None, "complete Guard example missing"
compile(main, str(LESSON), "exec")
module = types.ModuleType("lesson_guard_w6")
sys.modules[module.__name__] = module
exec(compile(main, str(LESSON), "exec"), module.__dict__)
Guard = module.Guard

checks: dict[str, bool] = {}


def invalid_configuration(**kwargs) -> bool:
    try:
        Guard(safe_zones=[], **kwargs)
    except ValueError:
        return True
    return False


checks["budgets and stagnation reject bool, float, and negative configuration"] = all(
    invalid_configuration(**{field: value})
    for field in ("step_budget", "token_budget", "no_change_limit")
    for value in (True, 1.5, -1)
)
checks["text limit rejects bool, float, and negative configuration"] = all(
    invalid_configuration(max_text_chars=value) for value in (True, 1.5, -1)
)
reservation = Guard(safe_zones=[], step_budget=2, token_budget=10)
checks["request reservation rejects bool, float, and negative values"] = all(
    reservation.begin_request(value) == (False, "invalid token reservation")
    for value in (True, 1.5, -1)
)
checks["invalid request reservations do not consume a step"] = reservation.steps_started == 0
checks["valid integer reservation still accepted"] = reservation.begin_request(0) == (True, "ok")
checks["actual usage rejects bool, float, and negative values"] = all(
    Guard(safe_zones=[], token_budget=10).finish_request(value, "frame")
    == (False, "invalid provider usage")
    for value in (True, 1.5, -1)
)

chart = re.search(r"<Mermaid[\s\S]*?chart=\{`([\s\S]*?)`\}\s*/>", text).group(1)
preflight = chart.find('A["读取当前观测并估算输入与输出预算"]')
request = chart.find('C["发送模型请求并接收动作"]')
usage_gate = chart.find('D{"实际 usage 对账通过且未触发停滞？"}')
action_gate = chart.find('E{"动作在允许范围内？"}')
execute = chart.find('H["执行动作"]')
checks["flowchart orders preflight, response accounting, policy, then side effect"] = (
    min(preflight, request, usage_gate, action_gate, execute) >= 0
    and preflight < request < usage_gate < action_gate < execute
)
expected_edges = (
    "B -->|是| C",
    "B -->|否| B0",
    "C --> D",
    "D -->|是| E",
    "D -->|否| D0",
    "E -->|是| F",
    "F -->|否| H",
    "F -->|是| G",
    "G -->|是| H",
    "H --> I",
)
checks["flowchart connects budget, reconciliation, policy and execution gates"] = all(
    edge in chart for edge in expected_edges
)
node_ids = re.findall(r"^\s*([A-Z][A-Z0-9_]*)\s*(?:\[|\{|\()", chart, re.MULTILINE)
checks["flowchart declares each node id once"] = len(node_ids) == len(set(node_ids))
metadata = (ROOT / "src/content/chapters/computer-use/meta.ts").read_text(encoding="utf-8")
resources = (ROOT / "src/content/curriculum/resources.ts").read_text(encoding="utf-8")
bool_checkpoint = metadata.split("id: 'python-bool-inheritance',", 1)[1].split(
    "sourceIds: ['python-built-in-types']", 1
)[0]
budget_checkpoint = metadata.split("id: 'budget-input-boundaries',", 1)[1].split(
    "\n        },", 1
)[0]
checks["documented Python bool claim cites its source"] = (
    "basis: 'documented'" in bool_checkpoint
)
checks["budget recommendations remain inferred"] = (
    "basis: 'inferred'" in budget_checkpoint and "sourceIds:" not in budget_checkpoint
)
checks["Python built-in types source is registered and cited in the lesson"] = (
    "'python-built-in-types': {" in resources
    and "docs.python.org/3.14/library/stdtypes.html" in text
    and "'python-built-in-types'" in metadata
)

for name, passed in checks.items():
    print(("PASS" if passed else "FAIL") + ": " + name)
print(f"safety-scope W6 regression: {sum(checks.values())}/{len(checks)} passed; providerCalls=0; externalNetworkCalls=0")
if not all(checks.values()):
    raise SystemExit(1)
