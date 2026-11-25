#!/usr/bin/env python3
"""Offline checks for plugins/image-gen/.../gemini_image.py against a local mock server.

    python3 tests/image-gen/test_gemini_image.py

Covers: dry run without a key, request shape (headers, input parts, response_format,
generation_config, previous_interaction_id), image + text extraction from both documented
response shapes, thought steps skipped, prompt with quotes reaching the API intact,
HTTP error, no-image response (exit 3), argument validation. No network, no key.
"""

import base64
import json
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "plugins/image-gen/skills/image-gen/scripts/gemini_image.py")
PNG = base64.b64encode(bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082") * 4).decode()

STATE = {"mode": "steps", "last": None}


class Mock(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        STATE["last"] = {"path": self.path, "headers": dict(self.headers), "body": body}
        mode = STATE["mode"]
        if mode == "error":
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": {"message": "bad aspect"}}')
            return
        if mode == "steps":
            resp = {"id": "int-123", "steps": [
                {"type": "thought", "summary": [{"type": "text", "text": "thinking"}],
                 "content": [{"type": "image", "mime_type": "image/png", "data": PNG[::-1]}]},
                {"type": "model_output", "content": [
                    {"type": "text", "text": "Here it is."},
                    {"type": "image", "mime_type": "image/png", "data": PNG}]}]}
        elif mode == "accessor":
            resp = {"id": "int-456", "output_image": {"mime_type": "image/jpeg", "data": PNG},
                    "output_text": "done"}
        else:  # noimage
            resp = {"id": "int-789", "steps": [{"type": "model_output", "content": [
                {"type": "text", "text": "I can't make that."}]}]}
        out = json.dumps(resp).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(out)


def run(args, key=True):
    env = {k: v for k, v in os.environ.items() if k not in ("GEMINI_API_KEY", "GOOGLE_API_KEY")}
    env["GEMINI_API_BASE"] = BASE
    if key:
        env["GEMINI_API_KEY"] = "test-key"
    return subprocess.run([sys.executable, "-I", SCRIPT] + args, env=env,
                          capture_output=True, text=True)


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        global FAILED
        FAILED = True


FAILED = False
srv = HTTPServer(("127.0.0.1", 0), Mock)
BASE = f"http://127.0.0.1:{srv.server_port}/v1beta"
threading.Thread(target=srv.serve_forever, daemon=True).start()

with tempfile.TemporaryDirectory() as d:
    prompt = os.path.join(d, "prompt.txt")
    tricky = "Render this: it's a \"test\" with 'quotes' $(echo no) `nope`\n{\"a\": 1}"
    with open(prompt, "w") as f:
        f.write(tricky)
    ref = os.path.join(d, "ref.png")
    with open(ref, "wb") as f:
        f.write(base64.b64decode(PNG))
    spec = os.path.join(d, "spec.json")
    with open(spec, "w") as f:
        f.write('{"meta": {"intent": "t"}}')

    out = os.path.join(d, "dry")
    r = run(["--prompt-file", prompt, "--out-dir", out, "--ref", ref, "--aspect", "16:9",
             "--size", "2K", "--dry-run"], key=False)
    req = json.load(open(os.path.join(out, "request.json")))
    check(r.returncode == 0 and STATE["last"] is None, "dry run needs no key and sends nothing")
    check(req["input"][1]["data"].startswith("<") and "base64" in req["input"][1]["data"],
          "request.json elides base64")

    out = os.path.join(d, "v1")
    r = run(["--prompt-file", prompt, "--out-dir", out, "--spec", spec, "--ref", ref,
             "--aspect", "16:9", "--size", "2K", "--thinking", "high", "--previous", "int-0",
             "--mime", "image/png"])
    last = STATE["last"]
    b = last["body"]
    check(r.returncode == 0, f"steps response: exit 0 ({r.stderr.strip()[:200]})")
    check(last["path"] == "/v1beta/interactions", "posts to /interactions")
    hdr = {k.lower(): v for k, v in last["headers"].items()}
    check(hdr.get("x-goog-api-key") == "test-key"
          and hdr.get("api-revision") == "2026-05-20", "auth and revision headers")
    check(b["input"][0] == {"type": "text", "text": tricky}, "prompt with quotes arrives intact")
    check(b["input"][1]["type"] == "image" and b["input"][1]["mime_type"] == "image/png"
          and b["input"][1]["data"] == base64.b64encode(base64.b64decode(PNG)).decode(),
          "reference image part")
    check(b["response_format"] == {"type": "image", "mime_type": "image/png",
                                   "aspect_ratio": "16:9", "image_size": "2K"}, "response_format")
    check(b["generation_config"] == {"thinking_level": "high"}
          and b["previous_interaction_id"] == "int-0", "thinking and previous id")
    meta = json.load(open(os.path.join(out, "meta.json")))
    check(len(meta["images"]) == 1 and meta["interaction_id"] == "int-123",
          "one image (thought image skipped), interaction id")
    check(open(meta["images"][0], "rb").read() == base64.b64decode(PNG), "image bytes decoded")
    check("thinking" not in open(os.path.join(out, "text.txt")).read(), "thought text skipped")
    check(os.path.exists(os.path.join(out, "spec.json")), "spec copied into run")

    STATE["mode"] = "accessor"
    out = os.path.join(d, "v2")
    r = run(["--prompt-file", prompt, "--out-dir", out])
    meta = json.loads(r.stdout or "{}")
    check(r.returncode == 0 and meta.get("images", [""])[0].endswith(".jpg"),
          "output_image accessor shape, jpeg extension")
    check("response_format" not in STATE["last"]["body"], "no response_format when not asked")

    STATE["mode"] = "noimage"
    r = run(["--prompt-file", prompt, "--out-dir", os.path.join(d, "v3")])
    check(r.returncode == 3 and "can't" in open(os.path.join(d, "v3", "text.txt")).read(),
          "no image: exit 3, text saved")

    STATE["mode"] = "error"
    r = run(["--prompt-file", prompt, "--out-dir", os.path.join(d, "v4")])
    check(r.returncode == 1 and "bad aspect" in r.stderr, "HTTP error: exit 1 with detail")

    r = run(["--prompt-file", prompt, "--out-dir", os.path.join(d, "v5")], key=False)
    check(r.returncode == 2 and "GEMINI_API_KEY" in r.stderr, "missing key: exit 2, says so")
    r = run(["--prompt-file", prompt, "--out-dir", os.path.join(d, "v6"), "--size", "2k"])
    check(r.returncode == 2, "lowercase size rejected")
    r = run(["--prompt-file", prompt, "--out-dir", os.path.join(d, "v7"), "--aspect", "7:3"])
    check(r.returncode == 2, "unknown aspect rejected")

srv.shutdown()
sys.exit(1 if FAILED else 0)
