"""Whole-lesson offline checks for the credentials lesson."""
from __future__ import annotations

import ast
import contextlib
import io
import re
import unittest
from dataclasses import fields
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/sandboxing/04-secrets.mdx"
META = ROOT / "src/content/chapters/sandboxing/meta.ts"
TEXT = LESSON.read_text(encoding="utf-8")
METADATA = META.read_text(encoding="utf-8")
BLOCKS = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", TEXT, re.M)


def run_block(source: str, name: str = "__main__") -> tuple[dict[str, object], str]:
    namespace: dict[str, object] = {"__name__": name}
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        exec(compile(source, str(LESSON), "exec"), namespace)
    return namespace, output.getvalue()


class SecretsW6Review(unittest.TestCase):
    def test_every_python_fence_compiles_and_runs_offline(self) -> None:
        self.assertEqual(len(BLOCKS), 3)
        for index, source in enumerate(BLOCKS):
            compile(source, f"{LESSON}:fence-{index}", "exec")
            run_block(source)
            tree = ast.parse(source)
            imported = [
                alias.name.split(".", 1)[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            ] + [
                node.module.split(".", 1)[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module
            ]
            self.assertFalse(set(imported) & {"urllib", "requests", "httpx"})

    def test_auth_context_has_no_duplicate_field_declaration(self) -> None:
        tree = ast.parse(BLOCKS[2])
        auth_context = next(
            node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "AuthContext"
        )
        names = [node.target.id for node in auth_context.body if isinstance(node, ast.AnnAssign)]
        self.assertEqual(names, ["actor_id", "tenant_id", "scopes"])
        namespace, _ = run_block(BLOCKS[2])
        self.assertEqual([field.name for field in fields(namespace["AuthContext"])], names)

    def test_host_gate_rejects_invalid_arguments_before_credential_lookup(self) -> None:
        namespace, output = run_block(BLOCKS[2])
        broker = namespace["FakeCredentialBroker"]({"tenant-a": "synthetic-secret"})
        auth = namespace["AuthContext"]("synthetic-user", "tenant-a", frozenset({"orders:read"}))
        upstream = namespace["FakeUpstream"]("synthetic-secret")
        execute = namespace["execute_tool"]
        for raw in ('{', '{"q":"x","tenant_id":"tenant-b"}', '{"q":"  "}', '[]'):
            result = execute(raw, auth, broker, upstream)
            self.assertEqual(result.get("error_code"), "invalid_arguments")
        self.assertEqual(broker.requests, [])
        self.assertIn("PASS forged tenant rejected before credential lookup", output)
        self.assertIn("PASS failure response/log omit raw credential and exception", output)
        self.assertNotIn("synthetic-secret", output)

    def test_mcp_and_security_claims_have_documented_checkpoint_bindings(self) -> None:
        lesson = METADATA.split("id: 'sandboxing/secrets'", 1)[1].split("id: 'sandboxing/execution-policy'", 1)[0]
        for checkpoint_id, source_id in (
            ("short-lived-credentials-and-rotation", "owasp-secrets-management"),
            ("secrets-must-not-enter-logs", "owasp-logging-cheat-sheet"),
            ("authorization-is-per-request", "owasp-authorization-cheat-sheet"),
        ):
            block = lesson.split(f"id: '{checkpoint_id}'", 1)[1].split("id: '", 1)[0]
            self.assertIn("basis: 'documented'", block)
            self.assertIn(f"'{source_id}'", block)

    def test_demo_output_blocks_match_python_stdout(self) -> None:
        _, short_output = run_block(BLOCKS[0])
        self.assertEqual(short_output, '{"api_key": "sk-***（已脱敏）"}\n')
        for index in (1, 2):
            _, output = run_block(BLOCKS[index])
            python_fences = list(re.finditer(r"^```python\s*\n[\s\S]*?^```\s*$", TEXT, re.M))
            following = TEXT[python_fences[index].end():python_fences[index + 1].start() if index + 1 < len(python_fences) else len(TEXT)]
            matches = re.findall(r"^```text\s*\n([\s\S]*?)^```\s*$", following, re.M)
            self.assertTrue(matches, f"Python fence {index + 1} needs a published text output block")
            self.assertEqual(output, matches[0])
        _, leak_demo_output = run_block(BLOCKS[1])
        self.assertIn("待发送对象含测试字符串：是", leak_demo_output)
        self.assertEqual(leak_demo_output.count("仅测试值脱敏后仍含测试字符串：否"), 3)
        self.assertNotIn("sk-test-only-a1b2c3d4e5f6", leak_demo_output)

    def test_cross_references_are_routes_not_ambiguous_chapter_numbers(self) -> None:
        for stale in ("第 15 节", "第 17 节", "第 4 节讲的"):
            self.assertNotIn(stale, TEXT)
        self.assertIn("仅声明字段名 `api_key` 不会自动把值发送给模型", TEXT)
        for route in (
            "/chapters/sandboxing/isolation-levels",
            "/chapters/evaluation/traces",
            "/chapters/agent-security/exfiltration",
            "/chapters/sandboxing/execution-policy",
        ):
            self.assertIn(route, TEXT)


if __name__ == "__main__":
    unittest.main(verbosity=2)
