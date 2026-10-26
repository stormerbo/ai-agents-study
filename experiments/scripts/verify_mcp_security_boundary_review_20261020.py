"""Run deterministic checks for the MCP security-boundary lesson examples."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SECURITY_LESSON = Path("src/content/chapters/mcp/05-security-boundary.mdx")
SERVER_LESSON = Path("src/content/chapters/mcp/04-build-a-server.mdx")
security_source = SECURITY_LESSON.read_text(encoding="utf-8")
server_source = SERVER_LESSON.read_text(encoding="utf-8")
security_python = re.findall(r"^```python\n(.*?)^```\s*$", security_source, re.M | re.S)
server_python = re.findall(r"^```python\n(.*?)^```\s*$", server_source, re.M | re.S)
server_code = next(block for block in server_python if "SUPPORTED_VERSIONS" in block)
client_code = next(block for block in security_python if "class Client" in block)
for index, block in enumerate(security_python):
    compile(block, f"{SECURITY_LESSON}:python-fence-{index}", "exec")
compile(server_code, f"{SERVER_LESSON}:server", "exec")

# The executable host policy examples must reject an unregistered tool and extra arguments.
policy_code = security_python[1]
policy_ns: dict[str, object] = {}
exec(compile(policy_code, "policy-example", "exec"), policy_ns)
assert policy_ns["gate"]("tickets-prod", "close_ticket", {"id": "T-1"}, policy_ns["demo_approve"], policy_ns["demo_execute"])["status"] == "denied"
try:
    policy_ns["gate"]("unknown-server", "danger", {}, policy_ns["demo_approve"], policy_ns["demo_execute"])
except PermissionError:
    pass
else:
    raise AssertionError("unregistered tool was not denied")

projection_ns: dict[str, object] = {}
exec(compile(security_python[2], "argument-projection-example", "exec"), projection_ns)
projected = projection_ns["build_tool_arguments"](
    "code-review-prod", "review_code", {"diff": "small diff", "language": "python"}
)
assert projected == {"diff": "small diff", "language": "python"}
try:
    projection_ns["build_tool_arguments"](
        "code-review-prod", "review_code", {"diff": "small diff", "language": "python", "api_key": "example"}
    )
except ValueError:
    pass
else:
    raise AssertionError("unexpected argument was not rejected")

combo_ns: dict[str, object] = {}
exec(compile(security_python[3], "dangerous-combination-example", "exec"), combo_ns)
assert combo_ns["server_verdict"]([{"name": "read_file"}, {"name": "send_http"}]) == "deny-known-combination"
assert combo_ns["server_verdict"]([{"name": "read_file"}]) == "no-known-combination-detected"

# Exercise the complete MCP client probe against the exact server code in the previous lesson.
with tempfile.TemporaryDirectory(prefix="mcp-security-probe-") as temp_dir:
    Path(temp_dir, "mcp_server.py").write_text(server_code, encoding="utf-8")
    probe = subprocess.run(
        [sys.executable, "-c", client_code, "security"],
        cwd=temp_dir,
        text=True,
        capture_output=True,
        check=True,
        timeout=15,
    )
assert "tools/list 返回了 2 个工具" in probe.stdout
assert "演示转账确认流程；本示例不会执行真实转账。" in probe.stdout
assert probe.stdout.count("✅") == 10
assert "补上确认后重调" in probe.stdout
assert "requestState" in client_code

print(json.dumps({"pythonFencesCompiled": len(security_python) + 1, "serverRequestsChecked": 11}, ensure_ascii=False))
