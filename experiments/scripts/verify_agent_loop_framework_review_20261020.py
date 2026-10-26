from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-loop/05-what-frameworks-do.mdx"
TEXT = LESSON.read_text(encoding="utf-8")
FENCES = re.findall(r"```python\n(.*?)\n```", TEXT, flags=re.DOTALL)
assert len(FENCES) == 2, f"expected 2 Python fences, got {len(FENCES)}"
for index, source in enumerate(FENCES, start=1):
    compile(source, f"{LESSON}#python-{index}", "exec")

manual_source = next(source for source in FENCES if "def graph_runner" in source)
graph_source = next(source for source in FENCES if "from langgraph.graph" in source)
with tempfile.TemporaryDirectory(prefix="agent-loop-framework-review-") as temp_dir:
    manual_path = Path(temp_dir) / "manual.py"
    manual_path.write_text(manual_source, encoding="utf-8")
    manual = subprocess.run(
        [sys.executable, str(manual_path)],
        check=True,
        capture_output=True,
        text=True,
    )

    graph_path = Path(temp_dir) / "langgraph_sample.py"
    graph_path.write_text(
        graph_source
        + "\nimport json\n"
        + "\nfrom importlib.metadata import version\n"
        + "snapshot = graph.get_state(config)\n"
        + "records = list(saver.list(config))\n"
        + "terminal = next(record for record in records if record.metadata.get('step') == 4)\n"
        + "print(json.dumps({'version': version('langgraph'), 'out': out, 'next': list(snapshot.next), 'step': snapshot.metadata['step'], 'updated_channels': terminal.checkpoint['updated_channels'], 'checkpoint_values': terminal.checkpoint['channel_values']}))\n",
        encoding="utf-8",
    )
    graph_python = os.environ.get("AGENT_LOOP_FRAMEWORK_PYTHON", sys.executable)
    graph_run = subprocess.run(
        [graph_python, str(graph_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    observed = json.loads(graph_run.stdout)
    assert observed["version"] == "1.2.14"
    assert observed["out"] == {
        "pending": [],
        "trace": ["search", "fetch", "fetch", "summarize"],
    }
    assert observed["next"] == []
    assert observed["step"] == 4
    assert observed["updated_channels"] == ["trace"]
    assert observed["checkpoint_values"] == observed["out"]

expected_trace = "['search', 'fetch', 'fetch', 'summarize']"
assert expected_trace in manual.stdout
assert "两者一致：True" in manual.stdout
assert "重启后检查点丢失" in TEXT
assert "不是节点来源或并发仲裁证据" in TEXT
assert "不构成与手写系统的等价功能或性能基准" in TEXT
assert "chain、graph、agent 排成一条固定的自主性阶梯" in TEXT

print(
    json.dumps(
        {
            "pythonFencesCompiled": len(FENCES),
            "testsPassed": 13,
            "testsFailed": 0,
            "langgraphVersion": observed["version"],
            "trace": observed["out"]["trace"],
            "next": observed["next"],
            "step": observed["step"],
            "checkpointChannels": observed["updated_channels"],
            "manualDemo": manual.stdout.splitlines()[:3],
        },
        ensure_ascii=False,
        indent=2,
    )
)
