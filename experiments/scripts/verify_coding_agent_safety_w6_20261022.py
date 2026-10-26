"""Whole-lesson offline policy checks plus a pinned, harmless pytest import demo."""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/coding-agent/05-safety.mdx"
META = ROOT / "src/content/chapters/coding-agent/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"
LOCK = ROOT / "experiments/locks/pytest-8.4.2-py314-macos-arm64-20261022.txt"
checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(message)


lesson = LESSON.read_text(encoding="utf-8")
meta = META.read_text(encoding="utf-8")
resources = RESOURCES.read_text(encoding="utf-8")
for phrase in (
    "命令名白名单无法约束仓库代码的副作用",
    "Python 3.14.7、pytest 8.4.2",
    "不是对 2026-10-10 历史运行环境、原始日志或历史完整仓库的重放",
    "可能执行仓库或依赖代码",
    "威胁建模会先检查破坏、数据外泄和供应链风险；这只是便于检查的分类",
    "不能靠字符串匹配",
    "不会创建任何隔离",
    "单独使用不等同于文件系统或网络隔离",
    "根据数据敏感度、代码可信度、可触达的副作用和恢复能力逐项决定权限",
    "并在执行前再次校验",
):
    check(phrase in lesson, f"lesson boundary missing: {phrase}")

source_ids = ("pytest-plugins", "npm-scripts", "cargo-build-scripts", "docker-engine-security", "pip-secure-installs", "python-subprocess")
check(all(f"'{source_id}': {{" in resources for source_id in source_ids), "one or more official sources are not registered")
source_urls = (
    "https://docs.pytest.org/en/stable/how-to/writing_plugins.html",
    "https://docs.npmjs.com/cli/v11/using-npm/scripts/",
    "https://doc.rust-lang.org/cargo/reference/build-scripts.html",
    "https://docs.docker.com/engine/security/",
    "https://pip.pypa.io/en/stable/topics/secure-installs/",
    "https://docs.python.org/3.14/library/subprocess.html#security-considerations",
)
check(all(url in lesson and url.split("#")[0] in resources for url in source_urls), "inline official-source links and registry entries must agree")

for stale in (
    "本轮环境没有安装 pytest，未能重新执行",
    "挡不住任何东西",
    "pytest 会执行仓库里的 conftest.py",
):
    check(stale not in lesson, f"stale or overbroad claim remains: {stale}")

for phrase in (
    "pytest 8.4.2",
    "不是对 2026-10-10 历史环境或日志的重放",
    "OS/容器实施资源边界",
):
    check(phrase in meta, f"checkpoint boundary missing: {phrase}")

fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", lesson, re.MULTILINE)
check(len(fences) == 1, "one policy-model Python example expected")
compile(fences[0], f"{LESSON}#python-0", "exec")
namespace: dict[str, object] = {}
exec(compile(fences[0], "safety-policy-model", "exec"), namespace)
policy = namespace["build_policy"]
readonly = policy("readonly")
workspace = policy("workspace")
network = policy("network")
check(readonly.readable_dirs == ["."] and readonly.writable_dirs == [], "readonly policy fixture changed")
check(workspace.readable_dirs == ["."] and workspace.writable_dirs == ["."], "workspace policy fixture changed")
check(network.allow_network is True and network.allow_network_hosts == ["pypi.org", "registry.npmjs.org"], "network policy fixture changed")
try:
    policy("unknown")
except ValueError:
    check(True, "unknown policy level rejected")
else:
    raise AssertionError("unknown policy level accepted")

# Run only in a fresh temp directory, with a pinned/hash-checked pytest environment.
with TemporaryDirectory(prefix="coding-agent-safety-pytest-") as temporary:
    root = Path(temporary)
    venv = root / "venv"
    subprocess.run(["uv", "venv", "--python", sys.executable, str(venv)], check=True, capture_output=True, text=True)
    python = venv / "bin/python"
    subprocess.run(["uv", "pip", "sync", "--python", str(python), str(LOCK)], check=True, capture_output=True, text=True)
    (root / "conftest.py").write_text(
        "\n".join((
            "from pathlib import Path",
            'Path("PWNED_MARKER").write_text("conftest.py was imported")',
            "",
        )),
        encoding="utf-8",
    )
    (root / "test_demo.py").write_text(
        "\n".join(("def test_passes():", "    assert True", "")),
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    run = subprocess.run([str(python), "-m", "pytest", "-q"], cwd=root, env=env, capture_output=True, text=True, check=True)
    version = subprocess.run([str(python), "-m", "pytest", "--version"], cwd=root, env=env, capture_output=True, text=True, check=True)
    marker = (root / "PWNED_MARKER").read_text(encoding="utf-8")
    check(version.stdout.strip() == "pytest 8.4.2", "pytest dependency is not pinned to 8.4.2")
    check("1 passed" in run.stdout and marker == "conftest.py was imported", "conftest import side effect did not reproduce")

print(f"coding-agent safety W6 checks: {checks}/{checks}")
print("pytest 8.4.2 isolated fixture: 1 passed; PWNED_MARKER written by conftest.py")
print("providerCalls=0; the pinned pytest environment may use PyPI if artifacts are not cached")
