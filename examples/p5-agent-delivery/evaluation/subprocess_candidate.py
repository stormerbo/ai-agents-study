from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import selectors
import signal
import subprocess
import tempfile
import time
from typing import Any


class SubprocessCandidateError(RuntimeError):
    pass


class SubprocessCandidateRuntime:
    """Bound one POSIX child process; this does not provide a security sandbox."""

    def __init__(
        self,
        *,
        argv: tuple[str, ...],
        candidate_sha256: str,
        image_digest: str,
        max_output_bytes: int,
        env: dict[str, str] | None = None,
    ):
        if not argv or any(not isinstance(arg, str) or not arg for arg in argv):
            raise ValueError("argv must contain non-empty argument strings")
        if isinstance(max_output_bytes, bool) or not isinstance(max_output_bytes, int) or max_output_bytes < 1:
            raise ValueError("max_output_bytes must be a positive integer")
        if os.name != "posix":
            raise RuntimeError("subprocess candidate runtime currently requires POSIX process groups")
        self.argv = tuple(argv)
        self.candidate_sha256 = candidate_sha256
        self.image_digest = image_digest
        self.max_output_bytes = max_output_bytes
        self.env = dict(env or {})

    def execute(
        self,
        attempt_id: str,
        public_input: dict[str, Any],
        deadline_utc: str,
        remaining_budget_usd: str,
    ) -> dict[str, Any]:
        try:
            deadline = datetime.fromisoformat(deadline_utc.replace("Z", "+00:00"))
        except (AttributeError, ValueError) as exc:
            raise SubprocessCandidateError("candidate deadline is invalid") from exc
        if deadline.tzinfo is None or deadline.utcoffset() != timezone.utc.utcoffset(deadline):
            raise SubprocessCandidateError("candidate deadline must be UTC")
        timeout_seconds = (deadline.astimezone(timezone.utc) - datetime.now(timezone.utc)).total_seconds()
        if timeout_seconds <= 0:
            raise SubprocessCandidateError("candidate deadline already expired")

        try:
            request = json.dumps(
                {
                    "attempt_id": attempt_id,
                    "public_input": public_input,
                    "deadline_utc": deadline_utc,
                    "remaining_budget_usd": remaining_budget_usd,
                },
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise SubprocessCandidateError("candidate request is not finite JSON") from exc

        started = time.monotonic()
        with tempfile.TemporaryFile() as request_file:
            request_file.write(request)
            request_file.seek(0)
            try:
                process = subprocess.Popen(
                    self.argv,
                    stdin=request_file,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    env=self.env,
                    close_fds=True,
                    start_new_session=True,
                )
            except OSError as exc:
                raise SubprocessCandidateError("candidate process could not be started") from exc

        assert process.stdout is not None
        output = bytearray()
        deadline_monotonic = started + timeout_seconds
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while True:
                    remaining = deadline_monotonic - time.monotonic()
                    if remaining <= 0:
                        raise SubprocessCandidateError("candidate deadline exceeded")
                    ready = selector.select(min(remaining, 1.0))
                    if not ready:
                        if deadline_monotonic - time.monotonic() <= 0:
                            raise SubprocessCandidateError("candidate deadline exceeded")
                        continue
                    chunk = os.read(process.stdout.fileno(), min(65_536, self.max_output_bytes + 1 - len(output)))
                    if not chunk:
                        selector.unregister(process.stdout)
                        break
                    output.extend(chunk)
                    if len(output) > self.max_output_bytes:
                        raise SubprocessCandidateError("candidate output size exceeded the configured limit")

            remaining = deadline_monotonic - time.monotonic()
            if remaining <= 0:
                raise SubprocessCandidateError("candidate deadline exceeded")
            try:
                exit_code = process.wait(timeout=remaining)
            except subprocess.TimeoutExpired as exc:
                raise SubprocessCandidateError("candidate deadline exceeded") from exc
            if exit_code != 0:
                raise SubprocessCandidateError("candidate process exited unsuccessfully")
        except BaseException:
            self._kill_process_group(process)
            raise
        finally:
            process.stdout.close()

        try:
            result = json.loads(
                output.decode("utf-8"),
                object_pairs_hook=self._reject_duplicate_keys,
                parse_constant=self._reject_non_json_constant,
            )
        except (UnicodeDecodeError, ValueError) as exc:
            raise SubprocessCandidateError("candidate output is not one valid strict JSON document") from exc
        if not isinstance(result, dict):
            raise SubprocessCandidateError("candidate output must be a JSON object")
        return result

    @staticmethod
    def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON object key")
            result[key] = value
        return result

    @staticmethod
    def _reject_non_json_constant(value: str) -> None:
        raise ValueError(f"non-JSON numeric constant: {value}")

    @staticmethod
    def _kill_process_group(process: subprocess.Popen[bytes]) -> None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except OSError:
            if process.poll() is None:
                process.kill()
        if process.poll() is None:
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
