"""Offline W6 regression for the just-in-time lesson's SDK credential routing."""
from __future__ import annotations

import os
import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/context-engineering/03-just-in-time.mdx"
source = LESSON.read_text(encoding="utf-8")
meta = (ROOT / "src/content/chapters/context-engineering/meta.ts").read_text(encoding="utf-8")
fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", source, re.MULTILINE)
samples = [body for body in fences if body.startswith("# preload_vs_jit.py")]
assert len(samples) == 1, f"expected one sample, found {len(samples)}"
sample = samples[0]
compile(sample, str(LESSON), "exec")
checks: list[tuple[bool, str]] = []


def check(ok: bool, label: str) -> None:
    checks.append((ok, label))


def client_options(*, api_key: str | None, auth_token: str | None) -> dict[str, object]:
    captured: list[dict[str, object]] = []

    class FakeAnthropic(types.ModuleType):
        def __init__(self) -> None:
            super().__init__("anthropic")

        def Anthropic(self, **kwargs: object) -> object:
            captured.append(kwargs)
            return object()

    old_module = sys.modules.get("anthropic")
    keys = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "VERIFY_MODEL")
    previous = {key: os.environ.get(key) for key in keys}
    try:
        if api_key is None:
            os.environ.pop("ANTHROPIC_API_KEY", None)
        else:
            os.environ["ANTHROPIC_API_KEY"] = api_key
        if auth_token is None:
            os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
        else:
            os.environ["ANTHROPIC_AUTH_TOKEN"] = auth_token
        os.environ["ANTHROPIC_BASE_URL"] = "https://fixture.invalid/anthropic"
        os.environ["VERIFY_MODEL"] = "fixture-model"
        sys.modules["anthropic"] = FakeAnthropic()
        exec(compile(sample, "preload_vs_jit.py", "exec"), {"__name__": "offline_audit"})
        assert len(captured) == 1
        return captured[0]
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        if old_module is None:
            sys.modules.pop("anthropic", None)
        else:
            sys.modules["anthropic"] = old_module


api_options = client_options(api_key="fixture-api-key", auth_token=None)
token_options = client_options(api_key=None, auth_token="fixture-bearer-token")
check(api_options.get("api_key") == "fixture-api-key" and api_options.get("auth_token") is None,
      "API key is passed through the SDK api_key parameter")
check(token_options.get("auth_token") == "fixture-bearer-token" and token_options.get("api_key") is None,
      "bearer auth token is passed through auth_token, never relabeled as api_key")
check(api_options.get("base_url") == "https://fixture.invalid/anthropic"
      and token_options.get("base_url") == "https://fixture.invalid/anthropic",
      "both credential modes retain the explicitly configured compatible base URL")
check("ANTHROPIC_AUTH_TOKEN" in source and "auth_token=" in source,
      "sample exposes the SDK's separate bearer-token configuration")
check("id: 'sdk-credential-routing'" in meta and "basis: 'documented'" in meta
      and "anthropic-python-sdk'" in meta and "deepseek-anthropic-api'" in meta,
      "metadata checkpoint ties credential guidance to official SDK and endpoint sources")
check("不能把两类值合并到 `api_key`" in source,
      "lesson explains the credential-routing boundary in prose")
check("预加载" in source and "按需取" in source,
      "the audited lesson still compares both context-loading strategies")

for passed, label in checks:
    print(("PASS" if passed else "FAIL") + ": " + label)
if not all(passed for passed, _ in checks):
    raise SystemExit(1)
print(f"RESULT {len(checks)}/{len(checks)} PASS; providerCalls=0; externalNetworkCalls=0")
