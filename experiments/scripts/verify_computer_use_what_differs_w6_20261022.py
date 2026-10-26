"""Regression-test the computer-use lesson's credentialed HTTP redirect boundary."""
from __future__ import annotations

import ast
import base64
import json
import os
import re
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/computer-use/01-what-differs.mdx"
text = LESSON.read_text(encoding="utf-8")
fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", text, re.MULTILINE)
code = next(fence for fence in fences if "def step(prompt" in fence)
tree = ast.parse(code)
step = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "step")
nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in {"step", "RejectRedirects", "open_api"}]
namespace: dict[str, object] = {"SYSTEM": "fixture", "render": lambda *_args: b"png"}
exec("import base64, json, os, urllib.request", namespace)
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(LESSON), "exec"), namespace)

received: list[str | None] = []


class TargetHandler(BaseHTTPRequestHandler):
    def _receive(self):
        received.append(self.headers.get("x-api-key"))
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"usage": {}, "content": []}).encode())

    do_POST = _receive
    do_GET = _receive

    def log_message(self, *_args):
        pass


class RedirectHandler(BaseHTTPRequestHandler):
    target_url = ""

    def do_POST(self):
        self.send_response(302)
        self.send_header("Location", self.target_url)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, *_args):
        pass


target = ThreadingHTTPServer(("127.0.0.1", 0), TargetHandler)
target_url = f"http://127.0.0.1:{target.server_port}/v1/messages"
redirect_cls = type("RedirectHandler", (RedirectHandler,), {"target_url": target_url})
redirect = ThreadingHTTPServer(("127.0.0.1", 0), redirect_cls)
threads = [threading.Thread(target=server.serve_forever, daemon=True) for server in (target, redirect)]
for thread in threads:
    thread.start()

base_url = f"http://127.0.0.1:{redirect.server_port}"
os.environ.update({"ANTHROPIC_BASE_URL": base_url, "ANTHROPIC_AUTH_TOKEN": "dummy-loopback-key", "VERIFY_MODEL": "fixture"})
checks: dict[str, bool] = {}

# Reproduce the old default opener behavior with the same credential header.
received.clear()
old_req = urllib.request.Request(base_url + "/v1/messages", data=b"{}", headers={"x-api-key": "dummy-loopback-key"})
try:
    urllib.request.urlopen(old_req, timeout=3)
except urllib.error.HTTPError:
    pass
checks["default urllib opener reproduces credential forwarding"] = received == ["dummy-loopback-key"]

received.clear()
try:
    namespace["step"]("fixture prompt")
except urllib.error.HTTPError as error:
    checks["lesson request stops at HTTP 302"] = error.code == 302
else:
    checks["lesson request stops at HTTP 302"] = False
checks["lesson request never sends key to redirect target"] = received == []

metadata = (ROOT / "src/content/chapters/computer-use/meta.ts").read_text(encoding="utf-8")
resources = (ROOT / "src/content/curriculum/resources.ts").read_text(encoding="utf-8")
lesson_meta = metadata.split("id: 'computer-use/what-differs',", 1)[1].split("\n    },", 1)[0]
checkpoint = lesson_meta.split("id: 'api-redirect-boundary',", 1)[1].split("\n        },", 1)[0] if "id: 'api-redirect-boundary'," in lesson_meta else ""
checks["documented redirect behavior has a source-bound checkpoint"] = (
    "basis: 'documented'" in checkpoint
    and "sourceIds: ['python-urllib-request']" in checkpoint
    and "'python-urllib-request': {" in resources
)
checks["lesson uses rejecting opener"] = (
    "with open_api(req, timeout=120) as resp:" in code
    and "urllib.request.urlopen(req, timeout=120)" not in code
)

for server in (redirect, target):
    server.shutdown()
    server.server_close()
for thread in threads:
    thread.join(timeout=1)

for name, passed in checks.items():
    print(("PASS" if passed else "FAIL") + ": " + name)
print(f"what-differs W6 loopback regression: {sum(checks.values())}/{len(checks)} passed; providerCalls=0; externalNetworkCalls=0")
if not all(checks.values()):
    raise SystemExit(1)
