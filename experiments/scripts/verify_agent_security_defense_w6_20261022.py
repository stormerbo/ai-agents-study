#!/usr/bin/env python3
"""Whole-lesson reference and boundary checks for the defense-in-depth chapter lesson."""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-security/05-defense-in-depth.mdx"
META = ROOT / "src/content/chapters/agent-security/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"
EXISTING_REVIEW = ROOT / "experiments/scripts/verify_agent_security_defense_review_20261020.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    lesson = LESSON.read_text(encoding="utf-8")
    meta = META.read_text(encoding="utf-8")
    resources = RESOURCES.read_text(encoding="utf-8")

    def resource_block(source_id: str) -> str:
        start = resources.index(f"  '{source_id}': {{")
        end = resources.index("\n  },", start)
        return resources[start:end]
    checks = [
        ("第 16 节" not in lesson and "第16节" not in lesson, "stale chapter-number references remain"),
        (lesson.count("第 16 章《沙箱与权限》") == 3, "cross-references do not match the actual chapter title/order"),
        ("「执行策略与审计」一节" in lesson and "path_under" in lesson, "execution-policy subsection target is missing"),
        ("owasp-llm-prompt-injection" in meta and "sourceIds: ['owasp-llm-prompt-injection']" in meta, "documented prompt-injection checkpoint is not source-bound"),
        ("https://genai.owasp.org/llmrisk/llm01-prompt-injection/" in resources and all("verifiedAt: '2026-10-22'" in resource_block(source_id) for source_id in ("owasp-llm-prompt-injection", "owasp-authorization-cheat-sheet")), "OWASP sources are not registered and freshly reviewed"),
        ("共因失效" in lesson and "不保证统计独立" in lesson, "shared-failure boundary is missing"),
        ("审计是观测和追查控制，不会代替预防性授权" in lesson and "标签也不构成服务端权限控制" in lesson, "audit/input labels are confused with authorization"),
        ("不调用模型，也不验证注入是否成功" in lesson and "不构成生产级文件沙箱" in lesson and "TOCTOU" in lesson, "local path-policy demo scope is overstated"),
    ]
    for ok, message in checks:
        require(ok, message)

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    run = subprocess.run(
        [sys.executable, str(EXISTING_REVIEW)], cwd=ROOT, env=env, text=True, capture_output=True, check=True
    )
    require(re.search(r"Ran 3 tests[^\n]*\n\nOK", run.stderr) is not None, "existing path-policy review suite did not pass 3 tests")
    print(f"PASS: {len(checks)} whole-lesson reference and security-boundary checks")
    print("PASS: existing path-policy verifier 3/3; local code example executed")
    print("providerCalls=0 externalNetworkCalls=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
