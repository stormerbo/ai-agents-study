from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
lesson_path = ROOT / "src/content/chapters/computer-use/01-what-differs.mdx"
lesson = lesson_path.read_text(encoding="utf-8")
meta = (ROOT / "src/content/chapters/computer-use/meta.ts").read_text(encoding="utf-8")
resources = (ROOT / "src/content/curriculum/resources.ts").read_text(encoding="utf-8")
data = (ROOT / "docs/DATA.md").read_text(encoding="utf-8")

checks: dict[str, bool] = {
    "scope distinguishes custom screenshot-coordinate adapter from provider toolsets":
        "自建截图/坐标适配器" in lesson and "不是所有 computer-use 产品的通用定义" in lesson,
    "current computer-use, browser-use and tool-combinations sources are linked":
        all(url in lesson for url in (
            "https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool",
            "https://platform.claude.com/docs/en/agents-and-tools/tool-use/browser-use-tool",
            "https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-combinations",
        )),
    "browser structured observations are not reduced to pixels":
        "可访问性树" in lesson and "元素引用" in lesson,
    "three-action sample does not claim universality or unlimited consequences":
        "它们不能表达所有界面操作" in lesson
        and "这三个动作能表达任何界面操作" not in lesson
        and "动作空间开放，等于风险面开放" not in lesson,
    "execution result is separated from business postcondition":
        "不等于应用业务目标已经达成" in lesson and "独立的业务后置条件" in lesson,
    "two historical requests are correctly labeled as proposals, not a complete round trip":
        "两次动作提议请求" in lesson and "不会运行 click/type" in lesson
        and "不执行点击或输入" in lesson,
    "historical click coordinate is not called a hit or general accuracy":
        "动作没有被执行" in lesson and "不能称为点击命中" in lesson
        and "不能解释为准确率" in lesson,
    "three-run historical success summary is not treated as verified":
        "不据此宣称 3/3 成功" in lesson
        and "逐次 provider 响应" in lesson,
    "full-history screenshots are not claimed after every individual action":
        "不应被简化成“每个动作都重新发送整张截图”" in lesson,
    "coordinate conversion is a calibrated hypothetical, not a universal Retina rule":
        "假设的比例映射" in lesson and "不要把 Retina 的 2× 比例当成跨平台规则" in lesson,
    "historical DATA summary carries missing-trace and weak-score caveats":
        "无法独立复核成功率" in data and "不可复核历史摘要" in data,
    "meta checkpoint reflects bounded claims and registered primary sources":
        "API 封闭、GUI 开放" in meta
        and "anthropic-computer-use" in meta and "anthropic-browser-use" in meta
        and "anthropic-tool-combinations" in meta,
    "API request example is compiled and does not execute returned UI actions": False,
}

fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", lesson, flags=re.MULTILINE)
main = next((fence for fence in fences if "最小请求：把合成截图发给模型" in fence), None)
if main is not None:
    try:
        compile(main, str(lesson_path), "exec")
        checks["API request example is compiled and does not execute returned UI actions"] = (
            "pyautogui" not in main and ".click(" not in main and ".typewrite(" not in main
        )
    except SyntaxError:
        pass

for name, passed in checks.items():
    print(("PASS" if passed else "FAIL") + ": " + name)

if not all(checks.values()):
    sys.exit(1)
