from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-security/04-exfiltration.mdx"
TEXT = LESSON.read_text(encoding="utf-8")


def python_fences() -> list[str]:
    marker = chr(96) * 3
    return [m.group(1) for m in re.finditer(rf"^{marker}python[^\n]*\n([\s\S]*?)^{marker}[ \t]*$", TEXT, re.M)]


class ExfiltrationReview(unittest.TestCase):
    def test_heuristic_and_scope_are_explicit(self) -> None:
        for phrase in (
            "威胁建模启发式",
            "不能证明现实系统的必要/充分条件",
            "不能用于估计攻击或防护的总体成功率",
            "只有请求实际发出并到达相应接收方",
            "本地模型也可能完全不经过外部模型服务",
        ):
            self.assertIn(phrase, TEXT)
        for stale in (
            "数据只要进了 URL 就已经出去了",
            "都是确定性的",
            "两道都要",
            "副本数就变成了 N",
        ):
            self.assertNotIn(stale, TEXT)

    def test_browser_csp_and_server_fetch_are_separate(self) -> None:
        self.assertIn("CSP 按浏览器资源类型生效，不是服务端网络出口防火墙", TEXT)
        self.assertIn("DNS 重绑定或检查与使用时差", TEXT)
        self.assertNotIn("def safe_image_url", TEXT)

    def test_projection_does_not_replace_authorization(self) -> None:
        self.assertIn("不能把模型提供的 user_id 当作身份", TEXT)
        self.assertIn("对象和动作的权限", TEXT)
        self.assertIn("这些信号用于复核，不替代授权与出口策略", TEXT)

    def test_local_code_compiles_and_models_only_four_boolean_branches(self) -> None:
        blocks = python_fences()
        self.assertEqual(len(blocks), 1)
        code = blocks[0]
        compile(code, str(LESSON), "exec")
        self.assertNotIn("requests.", code)
        self.assertNotIn("urlopen", code)
        ns: dict[str, object] = {"__name__": "exfiltration_review"}
        exec(compile(code, str(LESSON), "exec"), ns)
        model = ns["try_exfiltrate"]
        self.assertTrue(model(True, True, True)[0])  # type: ignore[operator]
        self.assertFalse(model(False, True, True)[0])  # type: ignore[operator]
        self.assertFalse(model(True, False, True)[0])  # type: ignore[operator]
        self.assertFalse(model(True, True, False)[0])  # type: ignore[operator]


if __name__ == "__main__":
    unittest.main()
