"""Offline consistency checks for the evaluation/pass-k lesson.

This verifies the locally executable teaching example only. It makes no
provider requests and does not reproduce the unarchived historical runs.
"""

from contextlib import redirect_stdout
from hashlib import sha256
from io import StringIO
from pathlib import Path
import re
from math import isclose


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/evaluation/02-pass-k.mdx"


def check(condition, message):
    if not condition:
        raise AssertionError(message)


source = LESSON.read_text(encoding="utf-8")
fences = re.findall(r"^```[^\n]*\n([\s\S]*?)^```\s*$", source, re.MULTILINE)
check(len(fences) > 4 and "cluster_bootstrap_ci" in fences[4], "complete script fence locator changed")
python_fences = re.findall(r"^```python\n([\s\S]*?)^```\s*$", source, re.MULTILINE)
check(len(python_fences) == 4, "unexpected number of Python examples")
for index, fence in enumerate(python_fences):
    compile(fence, f"{LESSON}#python-{index}", "exec")
code = fences[4]
checkpoint_code = fences[3]

namespace = {"__name__": "__main__"}
stdout = StringIO()
with redirect_stdout(stdout):
    exec(code, namespace)
output = stdout.getvalue()
check("任务等权单次成功率 91.0%" in output, "single-run estimate changed")
check("Pass@5              100.0%" in output, "Pass@5 output changed")
check("Pass^5               60.0%" in output, "Pass^5 output changed")
check("[86.0%, 96.0%]" in output, "cluster interval output changed")
check(isclose(namespace["pass_at_k"]([True, False, False, False, False], 1), 0.2), "Pass@1 estimator mismatch")
check(namespace["pass_at_k"]([True, False, False, False, False], 5) == 1.0, "Pass@5 estimator mismatch")
check(namespace["pass_pow_k"]([True] * 5, 5) == 1.0, "all-success Pass^k mismatch")
check(namespace["pass_pow_k"]([True, True, False, True, True], 5) == 0.0, "failed-run Pass^k mismatch")
check("无法独立复核的历史记录" in source and "不是本次重新实跑的结果" in source, "historical evidence caveat missing")
check("独立、同分布且每步成功率相同" in source, "p^n assumptions missing")

checkpoint_ns = {}
exec(checkpoint_code, checkpoint_ns)
calls = []


def retry_once(*, idem_key):
    calls.append(idem_key)
    if len(calls) == 1:
        raise TimeoutError("response was lost")
    return "committed"


retry_once.replay_safe = True
check(checkpoint_ns["step_once"]("refund-1", retry_once, "refund-key-1") == "committed", "safe retry failed")
check(calls == ["refund-key-1", "refund-key-1"], "retry did not reuse the idempotency key")
check(checkpoint_ns["step_once"]("refund-1", retry_once, "refund-key-1") == "committed" and len(calls) == 2, "completed checkpoint replayed")

unknown_calls = []


def unknown_receiver(*, idem_key):
    unknown_calls.append(idem_key)
    raise TimeoutError("outcome unknown")


try:
    checkpoint_ns["step_once"]("refund-2", unknown_receiver, "refund-key-2")
except RuntimeError as error:
    check("先对账" in str(error), "unknown outcome was not stopped for reconciliation")
else:
    raise AssertionError("unknown side-effect outcome should not be retried blindly")
check(len(unknown_calls) == 1, "unknown side-effect outcome was retried")

print("pass-k review checks: 17/17")
print(f"complete-script-sha256: {sha256(code.encode('utf-8')).hexdigest()}")
print("providerCalls: 0")
