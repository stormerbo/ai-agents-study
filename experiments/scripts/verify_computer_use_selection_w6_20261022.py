"""Verify that the historical selection harness never forwards x-api-key on redirects."""
from __future__ import annotations

import ast
import json
import threading
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/computer-use/05-when-not-to-use.mdx"
text = LESSON.read_text(encoding="utf-8")
fences = __import__("re").findall(r"^```python\s*\n([\s\S]*?)^```\s*$", text, __import__("re").MULTILINE)
full_code = next(code for code in fences if "def api_arm()" in code and "def post(body)" in code)
tree = ast.parse(full_code)
nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in {"post", "api_arm", "RejectRedirects", "open_api"}]
tool = next(node for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "TOOL" for target in node.targets))
namespace: dict[str, object] = {"__name__": "selection_lesson_test"}
exec("import json, os, urllib.request", namespace)
exec(compile(ast.Module(body=[tool, *nodes], type_ignores=[]), str(LESSON), "exec"), namespace)

captured: list[str | None] = []


class TargetHandler(BaseHTTPRequestHandler):
    def _receive(self):
        captured.append(self.headers.get("x-api-key"))
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"usage": {}, "content": []}).encode())

    do_GET = _receive
    do_POST = _receive

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
redirect_handler = type("RedirectHandler", (RedirectHandler,), {"target_url": target_url})
redirect = ThreadingHTTPServer(("127.0.0.1", 0), redirect_handler)
threads = [threading.Thread(target=server.serve_forever, daemon=True) for server in (target, redirect)]
for thread in threads:
    thread.start()

namespace["os"].environ.update({
    "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{redirect.server_port}",
    "ANTHROPIC_AUTH_TOKEN": "dummy-loopback-key",
    "VERIFY_MODEL": "local-fixture",
})
checks: dict[str, bool] = {}
for function_name, arguments in (("post", ({"model": "fixture"},)), ("api_arm", ())):
    captured.clear()
    try:
        namespace[function_name](*arguments)
    except urllib.error.HTTPError as error:
        blocked = error.code == 302
    else:
        blocked = False
    checks[f"{function_name} refuses redirect before following target"] = blocked
    checks[f"{function_name} does not send key to redirect target"] = captured == []

for server in (redirect, target):
    server.shutdown()
    server.server_close()
for thread in threads:
    thread.join(timeout=1)

metadata = (ROOT / "src/content/chapters/computer-use/meta.ts").read_text(encoding="utf-8")
resources = (ROOT / "src/content/curriculum/resources.ts").read_text(encoding="utf-8")
checkpoint = metadata.split("id: 'api-harness-redirect-boundary',", 1)[1].split("\n        },", 1)[0]
checks["redirect fact has an official source-bound checkpoint"] = (
    "basis: 'documented'" in checkpoint
    and "sourceIds: ['python-urllib-request']" in checkpoint
    and "'python-urllib-request': {" in resources
)
checks["both credentialed request paths use the rejecting opener"] = (
    text.count("with open_api(req, timeout=180)") == 2
    and "urllib.request.urlopen(req, timeout=180)" not in text
)

for name, passed in checks.items():
    print(("PASS" if passed else "FAIL") + ": " + name)
print(f"selection W6 loopback regression: {sum(checks.values())}/{len(checks)} passed; providerCalls=0; externalNetworkCalls=0")
if not all(checks.values()):
    raise SystemExit(1)
