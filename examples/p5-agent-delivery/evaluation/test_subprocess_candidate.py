from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from subprocess_candidate import SubprocessCandidateError, SubprocessCandidateRuntime


class SubprocessCandidateRuntimeTests(unittest.TestCase):
    def runtime(self, code: str, *, max_output_bytes: int = 1024) -> SubprocessCandidateRuntime:
        return SubprocessCandidateRuntime(
            argv=(sys.executable, "-c", code),
            candidate_sha256="a" * 64,
            image_digest="sha256:" + "b" * 64,
            max_output_bytes=max_output_bytes,
        )

    def execute(self, runtime: SubprocessCandidateRuntime, *, deadline_seconds: int = 5) -> dict:
        from datetime import datetime, timedelta, timezone

        deadline = (datetime.now(timezone.utc) + timedelta(seconds=deadline_seconds)).isoformat()
        return runtime.execute("task-0001", {"question": "Q"}, deadline, "1.00")

    def test_returns_one_bounded_json_result(self) -> None:
        result = self.execute(self.runtime("import json; print(json.dumps({'output': {'answer': 'A'}, 'cost_usd': '0.1', 'input_tokens': 1, 'output_tokens': 1, 'latency_ms': 2}))"))

        self.assertIsInstance(result, dict)
        self.assertEqual(result["output"], {"answer": "A"})

    def test_stops_child_when_stdout_exceeds_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pid_path = Path(temp_dir) / "child.pid"
            code = f"import os; open({str(pid_path)!r}, 'w').write(str(os.getpid())); block=b'x'*65536\nwhile True: os.write(1, block)"
            runtime = self.runtime(code, max_output_bytes=128)

            with self.assertRaisesRegex(SubprocessCandidateError, "output size"):
                self.execute(runtime)

            child_pid = int(pid_path.read_text())
            with self.assertRaises(ProcessLookupError):
                os.kill(child_pid, 0)

    def test_kills_child_when_deadline_expires(self) -> None:
        runtime = self.runtime("import time; time.sleep(10)")

        with self.assertRaisesRegex(SubprocessCandidateError, "deadline"):
            self.execute(runtime, deadline_seconds=1)

    def test_kills_descendant_that_keeps_stdout_open_after_parent_exits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            heartbeat_path = Path(temp_dir) / "grandchild.heartbeat"
            child_code = (
                f"import os,time; p={str(heartbeat_path)!r}; open(p,'w').write(str(os.getpid())+'\\n')\n"
                "with open(p,'a') as f:\n while True:\n  f.write('x'); f.flush(); time.sleep(.01)\n"
            )
            code = f"import subprocess,sys; subprocess.Popen([sys.executable, '-c', {child_code!r}]); print('parent done')"
            runtime = self.runtime(code)
            grandchild_pid = None
            try:
                with self.assertRaisesRegex(SubprocessCandidateError, "deadline"):
                    self.execute(runtime, deadline_seconds=1)
                content_after_stop = heartbeat_path.read_text()
                grandchild_pid = int(content_after_stop.splitlines()[0])
                time.sleep(0.05)
                self.assertEqual(heartbeat_path.read_text(), content_after_stop)
            finally:
                if grandchild_pid is not None:
                    try:
                        os.kill(grandchild_pid, 9)
                    except ProcessLookupError:
                        pass

    def test_rejects_nonzero_exit_without_exposing_stderr(self) -> None:
        runtime = self.runtime("import sys; sys.stderr.write('sensitive detail'); sys.exit(7)")

        with self.assertRaises(SubprocessCandidateError) as raised:
            self.execute(runtime)

        self.assertNotIn("sensitive detail", str(raised.exception))

    def test_rejects_duplicate_keys_in_candidate_json(self) -> None:
        runtime = self.runtime("print('{\\\"output\\\": {\\\"answer\\\": \\\"A\\\", \\\"answer\\\": \\\"B\\\"}}')")

        with self.assertRaisesRegex(SubprocessCandidateError, "JSON"):
            self.execute(runtime)

    def test_rejects_non_json_numeric_constants(self) -> None:
        runtime = self.runtime("print('{\\\"output\\\": {\\\"score\\\": NaN}}')")

        with self.assertRaisesRegex(SubprocessCandidateError, "JSON"):
            self.execute(runtime)

    def test_does_not_forward_parent_environment_by_default(self) -> None:
        code = "import json,os; print(json.dumps({'credential_present': 'P5_PRIVATE_CREDENTIAL' in os.environ}))"

        with patch.dict(os.environ, {"P5_PRIVATE_CREDENTIAL": "synthetic-test-value"}):
            result = self.execute(self.runtime(code))

        self.assertFalse(result["credential_present"])


if __name__ == "__main__":
    unittest.main()
