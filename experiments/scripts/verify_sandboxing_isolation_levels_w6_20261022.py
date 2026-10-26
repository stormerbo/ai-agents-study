"""Whole-lesson checks for the isolation-levels curriculum lesson."""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/sandboxing/02-isolation-levels.mdx"
META = ROOT / "src/content/chapters/sandboxing/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"


class IsolationLevelsW6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = LESSON.read_text()
        cls.meta = META.read_text()
        cls.resources = RESOURCES.read_text()
        cls.python_blocks = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", cls.text, re.M)
        cls.bash_blocks = re.findall(r"^```bash\s*\n([\s\S]*?)^```\s*$", cls.text, re.M)

    def test_all_markdown_fences_are_balanced(self):
        fences = [line for line in self.text.splitlines() if line.startswith("```")]
        self.assertEqual(len(fences) % 2, 0)

    def test_every_python_fence_compiles_and_l1_demo_only_reads_pid(self):
        self.assertEqual(len(self.python_blocks), 3)
        for index, source in enumerate(self.python_blocks, 1):
            compile(source, f"isolation-levels-python-{index}", "exec")

        source = self.python_blocks[0]
        start = source.index("def l1_blacklist():")
        end = source.index("\n\ndef l2_cpu_limit():", start)
        run_source = "import time, warnings\n" + source[start:end] + "\nprint(l1_blacklist()[2])\n"
        run = subprocess.run([sys.executable, "-c", run_source], capture_output=True, text=True, timeout=5)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertRegex(run.stdout, r"黑名单绕过成功：.*只读当前 pid=\d+")

    def test_bash_docker_continuations_use_one_backslash(self):
        self.assertGreaterEqual(len(self.bash_blocks), 2)
        for block in self.bash_blocks:
            for line in block.splitlines():
                if line.rstrip().endswith("\\"):
                    trailing = len(line.rstrip()) - len(line.rstrip().rstrip("\\"))
                    self.assertEqual(trailing, 1, f"invalid shell continuation: {line!r}")

    def test_lesson_uses_routes_instead_of_stale_chapter_ordinals(self):
        self.assertNotRegex(self.text, r"第\s*\d+\s*[章节]")
        for route in (
            "/chapters/sandboxing/least-privilege",
            "/chapters/sandboxing/execution-policy",
            "/chapters/sandboxing/why-isolate",
            "/chapters/agent-security/exfiltration",
        ):
            self.assertIn(route, self.text)

    def test_platform_claims_have_registered_documented_sources(self):
        section = self.meta.split("id: 'sandboxing/isolation-levels'", 1)[1].split("id: 'sandboxing/least-privilege'", 1)[0]
        for resource_id in (
            "docker-none-network",
            "docker-run-container",
            "python-resource-limits",
            "python-subprocess",
            "gvisor-security",
            "firecracker-microvm-design",
        ):
            self.assertIn(resource_id, self.resources)
            self.assertIn(resource_id, section)

    def test_documented_checkpoint_sources_are_bound_to_registered_claims(self):
        section = self.meta.split("id: 'sandboxing/isolation-levels'", 1)[1].split("id: 'sandboxing/least-privilege'", 1)[0]
        expected = {
            "python-resource-limit-scope": "sourceIds: ['python-resource-limits', 'python-subprocess']",
            "container-and-runtime-boundaries": "sourceIds: ['docker-run-container', 'gvisor-security', 'firecracker-microvm-design']",
        }
        for checkpoint, sources in expected.items():
            start = section.index(f"id: '{checkpoint}'")
            checkpoint_text = section[start:section.find('        },', start)]
            self.assertIn("basis: 'documented'", checkpoint_text)
            self.assertIn(sources, checkpoint_text)
            for source_id in re.findall(r"'([a-z0-9-]+)'", sources):
                self.assertIn(f"'{source_id}': {{", self.resources)

    def test_l2_vm_capability_and_lifecycle_boundaries_are_explicit(self):
        for phrase in (
            "仅适用于 Unix",
            "进程树",
            "preexec_fn 在多线程父进程中不安全",
            "共享宿主内核",
            "hypervisor",
            "Linux `CAP_*`",
            "object capability",
            "如果任务之间不该互相看见",
            "不能证明",
        ):
            self.assertIn(phrase, self.text)
        self.assertIn("输入负载不同", self.text)
        self.assertIn("不能拿来比较隔离开销", self.text)

    def test_complete_container_runner_command_executes_from_the_lesson(self):
        self.assertGreaterEqual(len(self.bash_blocks), 2)
        runner = self.python_blocks[1]
        with tempfile.TemporaryDirectory(prefix="isolation-runner-w6-") as temp:
            workspace = Path(temp)
            (workspace / "runner.py").write_text(runner)
            (workspace / "task-input").mkdir()
            (workspace / "task-input" / "fixture.txt").write_text("read-only fixture\n")
            workspace.chmod(0o755)
            (workspace / "runner.py").chmod(0o644)
            (workspace / "task-input").chmod(0o755)
            (workspace / "task-input" / "fixture.txt").chmod(0o644)
            command = self.bash_blocks[0].replace("docker run", "docker run --pull=never", 1)
            result = subprocess.run(
                ["bash", "-euc", command], cwd=workspace, capture_output=True, text=True, timeout=40
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("fixture.txt", result.stdout.splitlines())

    def test_documented_probe_matches_output_in_configured_and_weak_fixtures(self):
        probe = self.python_blocks[2]
        output_sections = re.findall(r"```text\s*\n([\s\S]*?)\n```", self.text)
        self.assertGreaterEqual(len(output_sections), 3)
        configured_expected = "\n".join(output_sections[1].splitlines()[1:])
        weak_expected = "\n".join(output_sections[2].splitlines()[1:])

        with tempfile.TemporaryDirectory(prefix="isolation-probe-w6-") as temp:
            workspace = Path(temp)
            workspace.chmod(0o755)
            (workspace / "probe.py").write_text(probe)
            (workspace / "probe.py").chmod(0o644)
            (workspace / "host-marker").write_text("harmless fixture\n")
            (workspace / "host-marker").chmod(0o644)
            secure_command = self.bash_blocks[1].replace("docker run", "docker run --pull=never", 1)
            secure = subprocess.run(
                ["bash", "-euc", secure_command], cwd=workspace, capture_output=True, text=True, timeout=40
            )
            self.assertEqual(secure.returncode, 0, secure.stderr)
            self.assertEqual(secure.stdout.rstrip("\n"), configured_expected)

            weak = subprocess.run(
                [
                    "docker", "run", "--rm", "--pull=never",
                    "--mount", f"type=bind,src={workspace},dst=/hosttmp,readonly",
                    "--mount", f"type=bind,src={workspace / 'probe.py'},dst=/app/probe.py,readonly",
                    "python:3.12-alpine", "python", "/app/probe.py",
                ],
                capture_output=True, text=True, timeout=40,
            )
            self.assertEqual(weak.returncode, 0, weak.stderr)
            self.assertEqual(weak.stdout.rstrip("\n"), weak_expected)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(IsolationLevelsW6)
    )
    print(f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; failures={len(result.failures) + len(result.errors)}")
    raise SystemExit(not result.wasSuccessful())
