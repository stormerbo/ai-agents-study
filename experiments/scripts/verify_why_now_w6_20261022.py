"""Offline contract checks for the capstone skeleton lesson."""

"""Whole-lesson contract checks for why-now; no live provider calls."""
from pathlib import Path
import ast
import json
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/what-is-an-agent/01-why-now.mdx"
TEXT = LESSON.read_text(encoding="utf-8")


def main() -> int:
    checks: list[tuple[str, bool]] = []

    def check(name: str, passed: bool) -> None:
        checks.append((name, bool(passed)))

    fences = re.findall(r"^\x60{3}python\s*\n(.*?)^\x60{3}\s*$", TEXT, re.M | re.S)
    check("one_appendix_python_probe", len(fences) == 1)
    code = fences[0]
    compile(code, f"{LESSON}#python-fence", "exec")

    env_names = set()
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) and node.value.attr == "environ":
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                env_names.add(node.slice.value)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get":
            if isinstance(node.func.value, ast.Attribute) and node.func.value.attr == "environ" and node.args and isinstance(node.args[0], ast.Constant):
                env_names.add(node.args[0].value)
    config_text = TEXT.split("先准备三个配置项", 1)[1].split("跑起来：", 1)[0]
    check("all_environment_variables_read_by_probe_are_documented", env_names.issubset(set(re.findall(r"ANTHROPIC_[A-Z_]+|VERIFY_MODEL", config_text))))

    check("historical_usage_is_labeled_incomplete_and_unreproducible", "原始逐次请求未归档" in TEXT and "不是完整上下文输入或账单" in TEXT and "cache_creation" in TEXT)
    check("tool_proposals_are_not_presented_as_host_commands", "不等于宿主必须执行" in TEXT and "授权校验" in TEXT)
    check("current_model_claim_has_a_date_and_official_source", "截至 2026-10-21" in TEXT and "models/overview" in TEXT)
    check("single_probe_is_not_called_a_reproduction_of_history", "当前复测数字不能替代或验证" in TEXT and "不能替代或验证日期" in TEXT)
    check("single_pair_is_not_claimed_as_causal_comparison", "这是一对接口探针，不是受控 A/B 实验" in TEXT and "重复配对并交替顺序" in TEXT)
    check("endpoint_usage_helper_requires_all_cache_dimensions", all(x in code for x in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")) and "if not required.issubset(usage)" in code)

    fake_sdk = """import json, os
class Usage:
    def model_dump(self, exclude_none=True):
        return {"input_tokens": 10, "cache_read_input_tokens": 2, "cache_creation_input_tokens": 1, "output_tokens": 3}
class Block:
    type = "tool_use"
    name = "get_weather"
    input = {"city": "北京"}
class Response:
    stop_reason = "tool_use"
    content = [Block()]
    usage = Usage()
class Messages:
    def create(self, **kwargs):
        path = os.environ["MOCK_TRACE_PATH"]
        try:
            rows = json.load(open(path, encoding="utf-8"))
        except FileNotFoundError:
            rows = []
        rows.append(kwargs)
        json.dump(rows, open(path, "w", encoding="utf-8"))
        return Response()
class Anthropic:
    def __init__(self, **kwargs):
        self.messages = Messages()
"""
    with tempfile.TemporaryDirectory(prefix="why-now-w6-") as temp_dir:
        temp = Path(temp_dir)
        (temp / "anthropic.py").write_text(fake_sdk, encoding="utf-8")
        script = temp / "probe.py"
        script.write_text(code, encoding="utf-8")
        trace = temp / "trace.json"
        env = {
            "PATH": str(Path(sys.executable).parent),
            "PYTHONPATH": temp_dir,
            "VERIFY_MODEL": "fixture-model",
            "ANTHROPIC_API_KEY": "synthetic-test-key",
            "MOCK_TRACE_PATH": str(trace),
        }
        run = subprocess.run([sys.executable, str(script)], env=env, cwd=temp, capture_output=True, text=True)
        calls = json.loads(trace.read_text(encoding="utf-8")) if trace.exists() else []
    check("fake_sdk_probe_makes_two_requests_without_network", run.returncode == 0 and len(calls) == 2)
    if len(calls) == 2:
        check("probe_compares_same_prompt_and_model_with_tool_definition_only", calls[0]["messages"] == calls[1]["messages"] and calls[0]["model"] == calls[1]["model"] and "tools" in calls[0] and "tools" not in calls[1])
    else:
        check("probe_compares_same_prompt_and_model_with_tool_definition_only", False)
    check("probe_reports_fields_without_executing_the_proposed_tool", "tool_use" in run.stdout and "记录到的上下文输入差值: 0 token" in run.stdout and all("tool_result" not in call for call in calls))

    failed = [name for name, passed in checks if not passed]
    for name, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    print(f"{len(checks) - len(failed)}/{len(checks)} W6 lesson checks")
    if run.stderr:
        print(run.stderr, file=sys.stderr)
    if failed:
        print("\n".join(failed), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
