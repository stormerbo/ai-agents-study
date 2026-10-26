"""Whole-lesson offline checks for coding-agent/error-recovery.

This validates the local teaching controller and evidence boundaries only.
It makes no provider calls and does not replay the historical model runs.
"""

from contextlib import redirect_stdout
from hashlib import sha256
from io import StringIO
from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/coding-agent/04-error-recovery.mdx"
META = ROOT / "src/content/chapters/coding-agent/meta.ts"
LEGACY_FIXTURE = ROOT / "experiments/fixtures/coding-recover-invalid-assertion.txt"


check_count = 0


def check(condition, message):
    global check_count
    check_count += 1
    if not condition:
        raise AssertionError(message)


source = LESSON.read_text(encoding="utf-8")
meta = META.read_text(encoding="utf-8")
fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", source, re.MULTILINE)
check(len(fences) == 1, "expected exactly one complete Python example")
code = fences[0]
compile(code, f"{LESSON}#python", "exec")

for phrase in (
    "不能支撑原正文的 4/5 模型成功率",
    "脚本从第一轮起就把测试全文放入 prompt",
    "API 异常被折叠成“未修好”",
    "runner_error",
    "incomplete",
    "最多 `max_repairs + 1` 次验证",
    "不会在最后一轮生成尚未验证的新代码",
    "没有逐次原始输出时，不能用事后猜测填补缺失环节",
    "这个 3 次验证、2 次提案的结果是固定 fixture 的演示",
    "真实 coding agent 需要操作系统层的 sandbox",
    "覆盖率只是其中一个诊断指标",
    "模型说已完成",
):
    check(phrase in source, f"lesson evidence boundary missing: {phrase}")

for stale in (
    "4/5 = 80%",
    "修好的四个都恰好用了 2 轮",
    "模型五轮都没改对",
):
    check(stale not in source, f"stale generalized claim returned: {stale}")

check("区分提案次数、验证次数和失败类型" in meta,
      "metadata checkpoint lost runner/API failure distinctions")
check("不能用于估计成功率" in meta,
      "metadata checkpoint lost historical evidence caveat")

broken_assertion = LEGACY_FIXTURE.read_text(encoding="utf-8").splitlines()[-1]
try:
    compile(broken_assertion, str(LEGACY_FIXTURE), "exec")
except SyntaxError:
    pass
else:
    raise AssertionError("archived legacy assertion unexpectedly compiles")

namespace = {"__name__": "__main__"}
stdout = StringIO()
with redirect_stdout(stdout):
    exec(code, namespace)
output = stdout.getvalue()
check("'status': 'passed'" in output, "published fixture did not pass")
check("'validations': 3" in output and "'proposals': 2" in output,
      "published fixture counts differ from the displayed result")
check("'requested_new_direction': True" in output,
      "published fixture did not exercise the changed-direction branch")

repair_loop = namespace["repair_loop"]
always_fails = lambda _source: [{"test_id": "stable-failure", "message": "still failing"}]
proposed = []


def proposer(*, source, failures, prior_attempts, change_direction):
    proposed.append((source, change_direction))
    return f"candidate-{len(proposed)}", f"attempt-{len(proposed)}"


exhausted = repair_loop("initial", always_fails, proposer, max_repairs=2,
                        same_failure_limit=2)
check(exhausted["status"] == "failed_unverified", "exhaustion was reported as success")
check(exhausted["validations"] == 3 and exhausted["proposals"] == 2,
      "repair cap must permit initial check plus exactly max_repairs candidate checks")
check(exhausted["source"] == "candidate-2" and exhausted["failures"],
      "exhaustion must retain the last checked candidate and its failure")
check(proposed[1][1] is True, "same stable failure did not request the alternate direction")

stalled = repair_loop("same", always_fails,
                      lambda *, source, **_kwargs: (source, "no change"),
                      max_repairs=2)
check(stalled["status"] == "stalled" and stalled["validations"] == 1,
      "no-op proposal should stop without claiming a verified result")

passed = repair_loop("already valid", lambda _source: [],
                     lambda **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected proposal")))
check(passed["status"] == "passed" and passed["validations"] == 1 and passed["proposals"] == 0,
      "already-valid source should pass without proposing a patch")

with tempfile.TemporaryDirectory(prefix="coding-agent-recovery-w6-") as temp:
    demo = Path(temp) / "demo.py"
    demo.write_text(code, encoding="utf-8")
    result = subprocess.run([sys.executable, str(demo)], check=True,
                            capture_output=True, text=True)
check(result.stdout == output, "fresh-process demo output differs from in-process output")

print(f"coding-agent recovery W6 checks: {check_count}/{check_count}")
print(f"complete-script-sha256: {sha256(code.encode('utf-8')).hexdigest()}")
print("providerCalls: 0")
print("externalNetworkCalls: 0")
