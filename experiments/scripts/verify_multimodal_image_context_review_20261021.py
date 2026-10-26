"""Offline regression checks for the image-input lesson review; never calls a provider."""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/multimodal/01-how-images-enter-context.mdx"


class ImageContextReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = LESSON.read_text()
        cls.fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", cls.text, re.M)
        cls.harness = next(f for f in cls.fences if "image-usage-results.jsonl" in f)

    def test_examples_fit_readable_code_lines(self):
        json_example = re.search(r"```json\s*\n([\s\S]*?)\n```", self.text).group(1)
        self.assertLessEqual(max(map(len, json_example.splitlines())), 88)
        first_docstring = next(line for line in self.harness.splitlines() if "usage smoke test" in line)
        self.assertLessEqual(len(first_docstring), 88)
        self.assertLessEqual(max(map(len, self.harness.splitlines())), 88)

    def test_historical_measurements_are_bounded(self):
        self.assertIn("逐次请求、原始响应、完整 usage 与模型快照未归档", self.text)
        self.assertIn("不能把差值 190 解释为图像的固定 token 开销", self.text)
        for overclaim in (
            "一张 1×1 的图就加了 190 token",
            "下限以下的缩放不省钱",
            "服务端会自己缩",
            "每 1,600 像素 1 个 token",
            "把内网地址交给对方访问",
            "字节数差一倍，token 一点不变",
        ):
            self.assertNotIn(overclaim, self.text)

    def test_provider_scopes_and_url_security_are_explicit(self):
        self.assertIn("api-docs.deepseek.com/guides/vision/", self.text)
        self.assertIn("cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html", self.text)
        self.assertIn("Files API", self.text)
        self.assertNotIn("直接传字节", self.text)
        self.assertIn("stateless", self.text)

    def test_current_image_token_claim_has_documented_checkpoint(self):
        meta = (ROOT / "src/content/chapters/multimodal/meta.ts").read_text()
        checkpoint = meta.split("id: 'deepseek-vision-token-boundary'", 1)[1].split("id: ", 1)[0]
        self.assertIn("basis: 'documented'", checkpoint)
        self.assertIn("sourceIds: ['deepseek-vision', 'deepseek-image-token-usage']", checkpoint)
        self.assertIn("1024", checkpoint)
        self.assertIn("usage", checkpoint)

    def test_harness_compiles_and_uses_identical_prompt(self):
        compile(self.harness, f"{LESSON}:image-usage-harness", "exec")
        self.assertIn("PROMPT", self.harness)
        self.assertIn("finish_reason", self.harness)
        self.assertIn("prompt_tokens", self.harness)
        self.assertIn("json.dumps", self.harness)

    def test_harness_runs_offline_and_fails_closed(self):
        class FakeImage:
            def __init__(self, size):
                self.size = size

            def save(self, buffer, format):
                buffer.write(f"fake-png:{self.size[0]}x{self.size[1]}".encode())

        class FakeDraw:
            def __init__(self, _image):
                pass

            def line(self, *_args, **_kwargs):
                pass

            def rectangle(self, *_args, **_kwargs):
                pass

            def text(self, *_args, **_kwargs):
                pass

        class FakeCompletions:
            calls = []
            incomplete = False

            def create(self, **kwargs):
                type(self).calls.append(kwargs)
                usage = SimpleNamespace(prompt_tokens=225, completion_tokens=1,
                                        total_tokens=226, prompt_cache_hit_tokens=0,
                                        prompt_cache_miss_tokens=225)
                return SimpleNamespace(
                    id=f"req-{len(type(self).calls)}",
                    model="fixture-model-snapshot",
                    choices=[SimpleNamespace(
                        finish_reason="length" if type(self).incomplete else "stop",
                        message=SimpleNamespace(content="RECEIVED"),
                    )],
                    usage=usage,
                )

        fake_client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
        fake_modules = {
            "openai": types.SimpleNamespace(OpenAI=lambda **_kwargs: fake_client),
            "PIL": types.SimpleNamespace(
                Image=types.SimpleNamespace(new=lambda _mode, size, _color: FakeImage(size)),
                ImageDraw=types.SimpleNamespace(Draw=FakeDraw),
            ),
        }
        FakeCompletions.calls = []
        FakeCompletions.incomplete = False
        namespace = {"__name__": "lesson_fixture"}
        env = {
            "DEEPSEEK_API_KEY": "fixture-key",
            "RUN_LIVE_IMAGE_PROBE": "1",
            "IMAGE_PROBE_OUTPUT": "image-usage-results.jsonl",
        }
        with patch.dict(sys.modules, fake_modules), patch.dict(os.environ, env):
            exec(compile(self.harness, str(LESSON), "exec"), namespace)
            with tempfile.TemporaryDirectory() as tmp:
                previous = os.getcwd()
                os.chdir(tmp)
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        namespace["__name__"] = "__main__"
                        exec(compile(self.harness, str(LESSON), "exec"), namespace)
                    records = [json.loads(line) for line in Path("image-usage-results.jsonl").read_text().splitlines()]
                finally:
                    os.chdir(previous)
        self.assertEqual(len(records), 12)
        self.assertEqual(len(FakeCompletions.calls), 12)
        self.assertTrue(all(row["status"] == "complete" for row in records))
        prompts = []
        for call in FakeCompletions.calls:
            content = call["messages"][0]["content"]
            prompts.append(next(item["text"] for item in content if item["type"] == "text"))
        self.assertEqual(len(set(prompts)), 1)
        self.assertTrue(all(row["response_model"] == "fixture-model-snapshot" for row in records))
        incomplete = namespace["make_record"](
            "image", 64, 64, b"fixture",
            SimpleNamespace(
                id="req-incomplete", model="fixture-model-snapshot",
                choices=[SimpleNamespace(finish_reason="length", message=SimpleNamespace(content="RECEIVED"))],
                usage=SimpleNamespace(prompt_tokens=225),
            ),
        )
        self.assertEqual(incomplete["status"], "incomplete")
        self.assertFalse(incomplete["answer_correct"])
        self.assertIsNone(incomplete["usage"]["completion_tokens"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
