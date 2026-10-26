"""Offline checks for the system-prompt altitude lesson. Never calls a provider."""
from __future__ import annotations

import ast
import json
import os
import re
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/context-engineering/02-system-prompt-altitude.mdx"
source = LESSON.read_text()
fences = [body for _lang, body in re.findall(r"^```([^\n]*)\n([\s\S]*?)^```\s*$", source, re.M)]
python_fences = [body for body in fences if body.startswith("# system_prompt_stability.py")]
if len(python_fences) != 1:
    raise SystemExit(f"expected one complete sample fence, got {len(python_fences)}")
code = python_fences[0]
compile(code, str(LESSON), "exec")
checks = 0

def check(condition: bool, label: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(label)

class Block:
    def __init__(self, kind="text", text=""):
        self.type = kind
        self.text = text

class Response:
    def __init__(self, text="", stop="end_turn", model="fixture-model"):
        self.content = [Block(text=text)] if text else []
        self.stop_reason = stop
        self.model = model
        self.usage = types.SimpleNamespace(
            input_tokens=4, output_tokens=3,
            cache_read_input_tokens=None, cache_creation_input_tokens=None,
        )

class Messages:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0
    def create(self, **kwargs):
        self.calls += 1
        if not self.responses:
            raise AssertionError("unexpected provider call")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

class FakeClient:
    def __init__(self, responses):
        self.messages = Messages(responses)

class FakeAnthropic(types.ModuleType):
    def __init__(self, responses):
        super().__init__("anthropic")
        self.responses = responses
        self.options = None
    def Anthropic(self, **kwargs):
        self.options = kwargs
        return FakeClient(self.responses)

def execute(responses, *, save_raw="0", key="fixture-key", token=None, runs="12", run_main=True):
    fake = FakeAnthropic(responses)
    old_module = sys.modules.get("anthropic")
    sys.modules["anthropic"] = fake
    env_keys = (
        "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL",
        "VERIFY_MODEL", "MAX_OUTPUT_TOKENS", "PROMPT_EVAL_RUNS",
        "PROMPT_RESULTS_PATH", "SAVE_RAW_RESPONSES",
    )
    old_env = {name: os.environ.get(name) for name in env_keys}
    with tempfile.TemporaryDirectory() as tmp:
        results_path = Path(tmp) / "runs.jsonl"
        if key is None:
            os.environ.pop("ANTHROPIC_API_KEY", None)
        else:
            os.environ["ANTHROPIC_API_KEY"] = key
        if token is None:
            os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
        else:
            os.environ["ANTHROPIC_AUTH_TOKEN"] = token
        os.environ["VERIFY_MODEL"] = "fixture-requested"
        os.environ["MAX_OUTPUT_TOKENS"] = "128"
        os.environ["PROMPT_EVAL_RUNS"] = runs
        os.environ["PROMPT_RESULTS_PATH"] = str(results_path)
        os.environ["SAVE_RAW_RESPONSES"] = save_raw
        ns = {"__name__": "__main__" if run_main else "offline_fixture"}
        try:
            exec(compile(code, str(LESSON), "exec"), ns)
        except RuntimeError as exc:
            for name, value in old_env.items():
                if value is None: os.environ.pop(name, None)
                else: os.environ[name] = value
            if old_module is None: sys.modules.pop("anthropic", None)
            else: sys.modules["anthropic"] = old_module
            return None, fake, str(exc)
        records = [json.loads(line) for line in results_path.read_text().splitlines()] if run_main else []
        result = (ns, fake, records)
    for name, value in old_env.items():
        if value is None: os.environ.pop(name, None)
        else: os.environ[name] = value
    if old_module is None: sys.modules.pop("anthropic", None)
    else: sys.modules["anthropic"] = old_module
    return result

# Import and deterministic candidate-screen fixtures.
ns = execute([], run_main=False)[0]
check(ns["classify_candidate"]("退款会在24小时内到账") == "time_mention_needs_review", "time phrase becomes manual-review candidate")
check(ns["classify_candidate"]("无法承诺具体到账时间") == "no_commitment_mention_needs_review", "no-promise phrase is only a candidate")
check(ns["classify_candidate"]("无法承诺24小时内到账") == "mixed_needs_review", "mixed language is not auto-scored")
check(ns["classify_candidate"]("我会先核实订单") == "other_needs_review", "unmatched text remains manual review")
check(ns["usage_record"](Response())["input_tokens"] == 4, "usage fields copied when present")

# API-key and bearer-token parameters stay distinct; incomplete calls stop the run.
result = execute([Response("承诺 24 小时内到账"), Response("无法承诺到账时间"), Response("", stop="max_tokens")])
ns, fake, records = result
check(fake.options["api_key"] == "fixture-key" and fake.options["auth_token"] is None, "API key uses api_key")
check(len(records) == 3 and ns["client"].messages.calls == 3, "run stops after first incomplete response")
check(records[0]["returned_model"] == "fixture-model", "response model recorded")
check(records[0]["stop_reason"] == "end_turn" and records[2]["status"] == "incomplete", "stop reasons gate scoring")
check(all("text" not in row for row in records), "raw outputs omitted by default")
check(all("text_sha256" in row for row in records), "response hashes saved")
check(records[0]["request_config"]["sampling_parameters"].endswith("not pinned"), "unpinned defaults disclosed")
check(records[0]["candidate_label"] == "time_mention_needs_review", "candidate label is not a correctness score")

# An explicit opt-in stores raw text; API failures are recorded without exception content.
_, _, raw_records = execute([Response("短文本")], save_raw="1")
check(raw_records[0]["text"] == "短文本", "raw capture requires explicit opt-in")
_, _, error_records = execute([RuntimeError("fixture failure")])
check(error_records[0]["status"] == "request_error", "request errors are recorded")
check("error_type" in error_records[0] and "error" not in error_records[0], "exception text is not persisted")

# Credential ambiguity fails before creating a client.
ns, fake, error = execute([], key="fixture-key", token="fixture-token", run_main=False)
check(ns is None and "其中一个" in error, "both credential types rejected")
ns, fake, error = execute([], key=None, run_main=False)
check(ns is None and "其中一个" in error, "missing credentials rejected")

# Editorial boundary checks: no general rule-count threshold or random/probability claim.
check("不能据此分离“规则数量”或“具体度”的因果效应" in source, "confounded output-length result qualified")
check("不能归因为“随机”" in source, "historical variation not called random")
check("不能估计部署概率" in source, "small sample not generalized")
check("它本身不能证明提示规则冲突" in source, "variance not treated as proof")
check("不证明抽象原则一定优于具体规则" in source, "no universal prompt recipe claimed")
check("高风险条件由宿主执行" in source, "hard constraints stay host-enforced")
check("原始输入/输出、模型配置与独立评分均未留存" in source, "self-audit summary limitations stated")
check("SAVE_RAW_RESPONSES=1" in source, "raw-response storage is opt-in")

print(f"offline assertions passed: {checks}")
