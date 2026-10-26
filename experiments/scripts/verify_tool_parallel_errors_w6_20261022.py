"""W6 whole-lesson verifier for tool-calling/parallel-and-errors."""
from __future__ import annotations

import contextlib
import io
import re
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/tool-calling/04-parallel-and-errors.mdx"
META = ROOT / "src/content/chapters/tool-calling/meta.ts"
PRIOR = ROOT / "experiments/scripts/verify_tool_parallel_errors_review_20261020.py"


class ParallelErrorsW6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = LESSON.read_text(encoding="utf-8")
        cls.fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", cls.text, re.M)
        cls.namespaces = []
        for index, source in enumerate(cls.fences):
            module_name = f"parallel_errors_w6_fixture_{index}_{uuid.uuid4().hex}"
            module = type(sys)(module_name)
            namespace = module.__dict__
            sys.modules[module_name] = module
            exec(compile(source, f"parallel-errors-w6-{index}", "exec"), namespace)
            cls.namespaces.append(namespace)

    def test_prior_issue_verifier_remains_green(self):
        result = subprocess.run([sys.executable, str(PRIOR)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("'status': 'passed'", result.stdout)

    def test_both_complete_python_fences_compile_and_execute(self):
        self.assertEqual(len(self.fences), 2)
        for namespace in self.namespaces:
            namespace["local_checks"]()
        output = io.StringIO()
        namespace = {"__name__": "__main__"}
        with contextlib.redirect_stdout(output):
            exec(compile(self.fences[1], "parallel-loop-main", "exec"), namespace)
        self.assertIn("已返回两项库存，另有一项编码不存在。", output.getvalue())

    def test_identity_scope_values_are_nonempty_strings_before_database_effects(self):
        namespace = self.namespaces[0]
        credit_once = namespace["credit_once"]
        with tempfile.TemporaryDirectory() as directory:
            database = str(Path(directory) / "test.sqlite3")
            namespace["initialize"](database)
            for field in ("tenant_id", "action_id", "account_id"):
                for invalid in (None, 7, "", "   ", "\t"):
                    args = {"tenant_id": "tenant-a", "action_id": "action-1", "account_id": "account-1", "amount_cents": 100}
                    args[field] = invalid
                    with self.subTest(field=field, invalid=invalid):
                        with self.assertRaises(ValueError):
                            credit_once(database, **args)
            with sqlite3.connect(database) as db:
                self.assertEqual(db.execute("SELECT credit_cents FROM balances").fetchone()[0], 0)
                self.assertEqual(db.execute("SELECT COUNT(*) FROM action_results").fetchone()[0], 0)

    def test_amount_contract_rejects_bool_noninteger_and_nonpositive_values(self):
        namespace = self.namespaces[0]
        with tempfile.TemporaryDirectory() as directory:
            database = str(Path(directory) / "test.sqlite3")
            namespace["initialize"](database)
            for index, invalid in enumerate((True, False, 0, -1, 1.5, "100")):
                with self.subTest(invalid=invalid):
                    with self.assertRaises(ValueError):
                        namespace["credit_once"](database, "tenant-a", f"bad-{index}", "account-1", invalid)
            with sqlite3.connect(database) as db:
                self.assertEqual(db.execute("SELECT credit_cents FROM balances").fetchone()[0], 0)
                self.assertEqual(db.execute("SELECT COUNT(*) FROM action_results").fetchone()[0], 0)

    def test_business_failure_rolls_back_and_does_not_cache_a_success(self):
        namespace = self.namespaces[0]
        with tempfile.TemporaryDirectory() as directory:
            database = str(Path(directory) / "test.sqlite3")
            namespace["initialize"](database)
            with self.assertRaisesRegex(KeyError, "account_not_found"):
                namespace["credit_once"](database, "tenant-a", "recoverable-action", "later-account", 100)
            with sqlite3.connect(database) as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM action_results").fetchone()[0], 0)
                db.execute("INSERT INTO balances VALUES (?, ?, 0)", ("tenant-a", "later-account"))
            result = namespace["credit_once"](database, "tenant-a", "recoverable-action", "later-account", 100)
            self.assertEqual(result["balance_cents"], 100)

    def test_prose_scopes_host_intent_persistence_and_denies_authz_substitution(self):
        self.assertIn("它本身不实现宿主的操作意图持久化", self.text)
        self.assertIn("同一动作的重试继续使用该 ID", self.text)
        self.assertIn("不实现身份认证或对象级授权", self.text)
        self.assertIn("幂等键不是身份凭据，也不授予访问权限", self.text)
        self.assertIn("在返回已保存结果或执行新副作用之前都做授权检查", self.text)

    def test_metadata_contains_the_new_inferred_authorization_checkpoint(self):
        meta = META.read_text(encoding="utf-8")
        start = meta.index("id: 'tool-calling/parallel-and-errors'")
        end = meta.index("id: 'tool-calling/tool-count'", start)
        chapter_lesson = meta[start:end]
        self.assertIn("idempotency-is-not-authorization", chapter_lesson)
        self.assertIn("basis: 'inferred'", chapter_lesson)
        self.assertIn("返回已缓存结果或执行新副作用之前", chapter_lesson)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(ParallelErrorsW6)
    )
    print(f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; failures={len(result.failures) + len(result.errors)}")
    raise SystemExit(not result.wasSuccessful())
