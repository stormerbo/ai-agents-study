#!/usr/bin/env python3
"""Offline whole-lesson checks for agent-deployment/versioning (W6)."""

from __future__ import annotations

import math
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-deployment/02-versioning.mdx"
META = ROOT / "src/content/chapters/agent-deployment/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"
DATA = ROOT / "docs/DATA.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    lesson = LESSON.read_text(encoding="utf-8")
    meta = META.read_text(encoding="utf-8")
    resources = RESOURCES.read_text(encoding="utf-8")
    data = DATA.read_text(encoding="utf-8")
    python_fences = re.findall(r"```python\n(.*?)\n```", lesson, re.DOTALL)
    require(len(python_fences) == 1, "lesson must contain exactly one complete Python fence")
    source = python_fences[0]
    compile(source, str(LESSON), "exec")

    run = subprocess.run(
        [sys.executable, "-c", source],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    published = re.search(r"\*\*实跑状态\*\*：.*?```text\n(.*?)\n```", lesson, re.DOTALL)
    require(published is not None, "complete stdout fence is missing")
    require(run.stdout.rstrip("\n") == published.group(1), "executed stdout differs from the published fence")

    z = 1.6449
    p = 0.02
    widths = (5.0, 2.0, 1.0, 0.5)
    expected = [math.ceil(4 * z**2 * p * (1 - p) / (width / 100) ** 2) for width in widths]
    require(expected == [85, 531, 2122, 8486], "independent planning arithmetic changed")
    for n, width in zip(expected, widths):
        actual_width = 2 * z * math.sqrt(p * (1 - p) / n) * 100
        require(actual_width <= width + 0.01, f"reported planning n misses width {width}pp")
    gray_data_line = next(line for line in data.splitlines() if "版本灰度与样本精度参考" in line)
    require(all(token not in lesson + gray_data_line for token in ("4,243", "16,971", "1,061")), "stale sqrt(2)-adjusted values remain")
    require("灰度 1%" not in lesson and "灰度 20%" not in lesson, "fixed rollout percentages remain prescriptive")

    manifest_fields = (
        '"app_commit"',
        '"runtime_image"',
        '"orchestrator_hash"',
        '"prompt_bundle_hash"',
        '"tool_bundle_hash"',
        '"runtime_policy_hash"',
        '"provider"',
        '"endpoint"',
        '"api_version"',
        '"requested_model_id"',
    )
    require(all(field in lesson for field in manifest_fields), "release manifest omits a behavior input")
    require("响应提供了实际 model ID / fingerprint 时也记入该次 trace" in lesson, "per-request resolved model boundary missing")
    require("latest_evaluated_release" in lesson and "latest_result" in lesson and "evaluator_version" in lesson, "regression sample omits current result provenance")
    require("不代表因果归属" in lesson and "逐版本" in lesson, "first-seen release is still framed as causality")

    source_ids = ("claude-model-deprecations", "openai-api-overview-versioning")
    require(all(source_id in resources and source_id in meta for source_id in source_ids), "model-version checkpoint source is not registered/referenced")
    require("固定流量比例、放量速度与阈值不是通用值" in meta, "metadata rollout checkpoint is stale")

    print("PASS: one Python fence compiles and executes offline")
    print("PASS: complete published stdout exactly matches the local run")
    print("PASS: independent single-proportion planning arithmetic matches 85/531/2122/8486")
    print("PASS: no stale sqrt(2)-adjusted counts or fixed rollout percentages remain")
    print("PASS: release manifest covers code, runtime, orchestration, prompts, tools, policy, and provider request")
    print("PASS: model request/response provenance is kept at per-request trace scope")
    print("PASS: regression status includes latest result and evaluator provenance")
    print("PASS: version-contract checkpoint cites registered official provider documentation")
    print("providerCalls=0 externalNetworkCalls=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
