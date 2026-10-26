"""Offline checks for the execution-policy example; no network or provider calls."""
from __future__ import annotations

import contextlib
import io
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/sandboxing/05-execution-policy.mdx"
META = ROOT / "src/content/chapters/sandboxing/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"


class ExecutionPolicyReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = LESSON.read_text()
        cls.meta = META.read_text()
        cls.resources = RESOURCES.read_text()
        section = cls.text.split("## 策略评估与唯一执行入口", 1)[1].split("## 固定攻击测试", 1)[0]
        blocks = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", section, re.M)
        if not blocks:
            raise AssertionError("the execution-policy example is missing")
        cls.source = blocks[0]
        cls.namespace = {"__name__": "policy_lesson"}
        exec(compile(cls.source, "lesson-policy-example", "exec"), cls.namespace)

    def test_code_compiles_and_keeps_model_claims_out_of_trusted_context(self):
        compile(self.source, "lesson-policy-example", "exec")
        policy = self.namespace
        admin_rule = [{"id": "admin", "tool": "delete", "allow": True,
                       "when": {"principal_role_in": ["admin"]}, "why": "admin only"}]
        forged = policy["check"]("delete", {"role": "admin"}, {"subject_id": "u1", "roles": []},
                                  {"default": "deny", "rules": admin_rule})
        trusted = policy["check"]("delete", {}, {"subject_id": "u1", "roles": ["admin"]},
                                   {"default": "deny", "rules": admin_rule})
        self.assertEqual(forged[0], "deny")
        self.assertEqual(trusted[0], "allow")

    def test_all_lesson_python_fences_compile(self):
        blocks = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", self.text, re.M)
        self.assertGreaterEqual(len(blocks), 5)
        for index, source in enumerate(blocks, 1):
            compile(source, f"lesson-python-fence-{index}", "exec")

    def test_invalid_policy_and_unknown_condition_fail_closed(self):
        check = self.namespace["check"]
        decision = check("read_file", {"path": "/workspace/a"}, {"subject_id": "u1", "roles": []},
                         {"default": "allow", "rules": []})
        self.assertEqual(decision[0], "deny")
        decision = check("read_file", {}, {"subject_id": "u1", "roles": []},
                         {"default": "deny", "rules": [{"id": "bad", "tool": "read_file",
                          "allow": True, "when": {"typo": True}, "why": "bad"}]})
        self.assertEqual(decision[0], "deny")
        conflicted = {"default": "deny", "rules": [
            {"id": "allow", "tool": "read_file", "allow": True,
             "when": {"path_under": "/workspace"}, "why": "allow"},
            {"id": "deny", "tool": "read_file", "allow": False,
             "when": {"path_prefix": "/workspace/private"}, "why": "deny"},
        ]}
        decision = check("read_file", {"path": "/workspace/private/key"},
                         {"subject_id": "u1", "roles": []}, conflicted)
        self.assertEqual(decision[0], "deny")

    def test_audit_omits_raw_arguments_and_records_handler_failure_as_unknown(self):
        ns = self.namespace
        events = []
        ns["HANDLERS"]["read_file"] = lambda path: (_ for _ in ()).throw(RuntimeError("secret detail"))
        with contextlib.redirect_stdout(io.StringIO()):
            result = ns["dispatch"]("read_file", {"path": "/workspace/a", "token": "do-not-log"},
                                    {"subject_id": "u1", "roles": []}, events.append)
        self.assertEqual(result["status"], "unknown")
        serialized = repr(events)
        self.assertNotIn("do-not-log", serialized)
        self.assertNotIn("secret detail", serialized)
        self.assertEqual(events[-1]["status"], "unknown")

    def test_unregistered_handler_is_never_audited_as_successful_allow(self):
        ns = self.namespace
        events = []
        decision = ns["dispatch"]("delete_everything", {},
                                   {"subject_id": "u1", "roles": []}, events.append)
        self.assertEqual(decision["status"], "denied")
        self.assertEqual(decision["reason"], "not_authorized")
        self.assertNotIn("rule", decision)
        self.assertEqual(events[-1]["decision"], "deny")

    def test_audit_sink_failure_blocks_handler_execution(self):
        ns = self.namespace
        calls = []
        ns["HANDLERS"]["read_file"] = lambda path: calls.append(path)

        def broken_sink(_event):
            raise OSError("synthetic sink unavailable")

        result = ns["dispatch"]("read_file", {"path": "/workspace/a"},
                                {"subject_id": "u1", "roles": []}, broken_sink)
        self.assertEqual(result["status"], "denied")
        self.assertEqual(calls, [])

    def test_lesson_and_metadata_cite_authorization_and_logging_guidance(self):
        for resource_id in ("owasp-authorization-cheat-sheet", "owasp-logging-cheat-sheet",
                            "linux-cgroup-v2", "python-subprocess"):
            self.assertIn(resource_id, self.resources)
            self.assertIn(resource_id, self.meta.split("id: 'sandboxing/execution-policy'", 1)[1].split("\n    },", 1)[0])
        self.assertIn("日志接收失败", self.text)
        self.assertIn("不是防篡改日志", self.text)
        self.assertIn("cgroup v2 文档", self.text)
        self.assertIn("Python subprocess 文档", self.text)
        self.assertIn("执行上限要落在能强制它的那一层", self.text)
        self.assertIn("Linux cgroup v2 提供 CPU、memory、pids", self.text)
        self.assertIn("该用法下子进程不会自动被杀", self.text)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(ExecutionPolicyReview)
    )
    print(f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; failures={len(result.failures) + len(result.errors)}")
    raise SystemExit(not result.wasSuccessful())
