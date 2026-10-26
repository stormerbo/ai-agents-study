"""W6 regression: refuse API-key-bearing HTTP redirects using only loopback servers."""
from __future__ import annotations

import ast
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import re
import threading
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/computer-use/02-observe-act-loop.mdx"
text = LESSON.read_text(encoding="utf-8")
fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", text, re.MULTILINE)
full = next((fence for fence in fences if "def call_model(" in fence), None)
assert full is not None, "complete API example missing"
compile(full, str(LESSON), "exec")
parsed = ast.parse(full)
redirect_class = next((n for n in parsed.body if isinstance(n, ast.ClassDef) and n.name == "RejectRedirects"), None)
assert redirect_class is not None, "API request must define a redirect-rejecting handler"
call_model = next((n for n in parsed.body if isinstance(n, ast.FunctionDef) and n.name == "call_model"), None)
assert call_model is not None
call_source = ast.get_source_segment(full, call_model) or ""
assert "urllib.request.build_opener(RejectRedirects())" in call_source
assert ".open(req, timeout=180)" in call_source and "urlopen(req" not in call_source

# Execute only the API transport definition; never invoke the lesson's provider-backed main.
selected = [
    node for node in parsed.body
    if (isinstance(node, ast.Import) and any(alias.name in {"json", "os", "urllib.request"} for alias in node.names))
    or (isinstance(node, ast.ClassDef) and node.name == "RejectRedirects")
    or (isinstance(node, ast.FunctionDef) and node.name == "call_model")
    or (isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "SYSTEM" for target in node.targets))
]
module = ast.Module(body=selected, type_ignores=[])
ast.fix_missing_locations(module)
namespace = {"__name__": "lesson_transport_fixture"}
exec(compile(module, str(LESSON), "exec"), namespace)

forwarded_keys: list[str | None] = []
class TargetHandler(BaseHTTPRequestHandler):
    def respond(self):
        forwarded_keys.append(self.headers.get("x-api-key"))
        body = json.dumps({"content": [{"type": "text", "text": "unexpected redirect"}], "usage": {}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    do_GET = respond
    do_POST = respond
    def log_message(self, *_args):
        pass

target = ThreadingHTTPServer(("127.0.0.1", 0), TargetHandler)
target_thread = threading.Thread(target=target.serve_forever, daemon=True)
target_thread.start()
class RedirectHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        self.send_response(302)
        self.send_header("Location", f"http://127.0.0.1:{target.server_port}/collect")
        self.send_header("Content-Length", "0")
        self.end_headers()
    def log_message(self, *_args):
        pass

redirect = ThreadingHTTPServer(("127.0.0.1", 0), RedirectHandler)
redirect_thread = threading.Thread(target=redirect.serve_forever, daemon=True)
redirect_thread.start()
old_env = os.environ.copy()
try:
    os.environ["VERIFY_MODEL"] = "offline-fixture"
    os.environ["ANTHROPIC_BASE_URL"] = f"http://127.0.0.1:{redirect.server_port}"
    os.environ["ANTHROPIC_AUTH_TOKEN"] = "dummy-loopback-only-token"
    baseline_request = urllib.request.Request(
        f"http://127.0.0.1:{redirect.server_port}/v1/messages",
        data=b"{}",
        headers={"x-api-key": "dummy-loopback-only-token"},
    )
    with urllib.request.urlopen(baseline_request, timeout=3) as response:
        response.read()
    assert forwarded_keys == ["dummy-loopback-only-token"], "baseline must reproduce default-opener credential forwarding to loopback only"
    forwarded_keys.clear()
    rejected_status = None
    try:
        namespace["call_model"]([])
    except urllib.error.HTTPError as exc:
        rejected_status = exc.code
    assert rejected_status == 302, f"expected the API request to stop at 302, got {rejected_status!r}"
    assert forwarded_keys == [], f"redirect target received credential header(s): {forwarded_keys!r}"
finally:
    os.environ.clear()
    os.environ.update(old_env)
    redirect.shutdown()
    target.shutdown()
    redirect.server_close()
    target.server_close()
    redirect_thread.join(timeout=2)
    target_thread.join(timeout=2)

# Check every Python excerpt plus the source-bound curriculum checkpoint.
assert len(fences) == 4, f"expected four Python fences, found {len(fences)}"
for index, fence in enumerate(fences):
    compile(fence, f"{LESSON}#fence-{index}", "exec")
metadata = (ROOT / "src/content/chapters/computer-use/meta.ts").read_text(encoding="utf-8")
assert "id: 'credential-redirect-boundary'" in metadata
assert "sourceIds: ['python-urllib-request']" in metadata
assert "resourceIds: ['anthropic-context-engineering', 'claude-messages-api', 'anthropic-computer-use', 'deepseek-vision', 'python-urllib-request']" in metadata
assert "HTTPRedirectHandler.redirect_request" in text and "docs.python.org/3.14/library/urllib.request.html" in text
print("computer-use/observe-act-loop W6 regression: 13/13 passed; pythonFencesCompiled=4; providerCalls=0; externalNetworkCalls=0; loopbackOnly=true")
