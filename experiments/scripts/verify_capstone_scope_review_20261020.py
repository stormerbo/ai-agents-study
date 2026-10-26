"""Offline checks for the capstone scope lesson and its executable example."""

from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/capstone/01-scope.mdx"
REGISTRY = ROOT / "examples/p4-durable-support/app/actions.py"
TEXT = LESSON.read_text(encoding="utf-8")


def main() -> int:
    checks = []
    fences = re.findall(r"```python\s*\n(.*?)\n```", TEXT, flags=re.DOTALL)
    assert len(fences) == 1, f"expected one Python fence, found {len(fences)}"
    code = fences[0]
    compile(code, str(LESSON), "exec")
    checks.append("single Python fence compiles")

    with tempfile.TemporaryDirectory(prefix="capstone-scope-") as temp_dir:
        script = Path(temp_dir) / "scope.py"
        script.write_text(code, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(script)], capture_output=True, text=True, check=True
        )
    assert "'active_tools': ['lookup_order', 'search_policy', 'send_notice']" in result.stdout
    assert "新增未审批工具被检出" in result.stdout and "refund_order" in result.stdout
    checks.append("scope example executes and catches an added tool")

    registry = REGISTRY.read_text(encoding="utf-8")
    for name in ("lookup_order", "search_policy", "send_notice"):
        assert f"'{name}'" in registry, f"tool absent from project registry: {name}"
        assert f'"{name}"' in TEXT, f"tool absent from lesson: {name}"
    assert re.search(r"'send_notice': \(schema\(\('resource_id','message'\)\),True\)", registry)
    assert '"send_notice": "approval-required"' in code
    assert "真实注册表" in TEXT
    checks.append("lesson tool names and approval mode match the current registry source")

    assert "一个预先固定的在线 smoke 用例" in TEXT
    assert "每个 smoke 任务受最大模型轮数和单轮输出 token 上限约束" in TEXT
    checks.append("scope limits the fixed smoke case without claiming a global one-run quota")

    outdated = (
        "功能是一天，配套是两周",
        "成本是功能本身的好几倍",
        "问\"这个功能要不要自己的评测集\"",
        "不做持久化      → 不需要管状态迁移",
    )
    assert not [phrase for phrase in outdated if phrase in TEXT]
    for phrase in (
        "不能推断其他模型/任务的准确率",
        "一次 smoke 或公开 fixture 宣称通用准确率",
        "真实客户数据、真实外部通知与生产写入",
        "业务目标、数据边界、操作权限和证据强度",
    ):
        assert phrase in TEXT, f"missing bounded scope statement: {phrase}"
    checks.append("unsupported estimates and universal evaluation rule are removed")

    print(f"{len(checks)}/{len(checks)} checks passed")
    for check in checks:
        print(f"- {check}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
