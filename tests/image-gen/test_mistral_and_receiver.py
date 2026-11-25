#!/usr/bin/env python3
"""Offline checks for mistral_image.py (against a mock API) and receive_image.py.

    python3 tests/image-gen/test_mistral_and_receiver.py

Mistral: request shape, the response shape observed in Nov 2026 (image URL inside the
tool.execution entry's info.result) and the documented tool_file shape, the API key sent
to the API but never to the storage URL, the image model's rewritten prompt logged.
Receiver: saves a POSTed body, sanitises the name, answers CORS / Private Network Access
preflight, serves the relay page, exits after --max files.
"""

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(ROOT, "plugins/image-gen/skills/image-gen/scripts")
JPEG = b"\xff\xd8\xff\xe0" + b"fake-jpeg" * 50
FAILED = False
SEEN = []
MODE = {"shape": "observed"}


def check(cond, msg):
    global FAILED
    print(("ok   " if cond else "FAIL ") + msg)
    FAILED |= not cond


class Mock(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        SEEN.append(("GET", self.path, self.headers.get("Authorization")))
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.end_headers()
        self.wfile.write(JPEG)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        SEEN.append(("POST", self.path, self.headers.get("Authorization"), body))
        if MODE["shape"] == "observed":
            resp = {"conversation_id": "conv_1", "outputs": [
                {"type": "tool.execution", "name": "image_generation",
                 "arguments": json.dumps({"prompt": "A rewritten prose prompt"}),
                 "info": {"result": json.dumps({"url": f"{BASE_ROOT}/blob/x/image.jpg?se=1&sig=2"})}},
                {"type": "message.output", "content": f"Here: ![i]({BASE_ROOT}/blob/x/image.jpg?se=1&sig=2)"}]}
        else:
            resp = {"conversation_id": "conv_2", "outputs": [
                {"type": "message.output", "content": [
                    {"type": "text", "text": "Done."},
                    {"type": "tool_file", "tool": "image_generation", "file_id": "f-9",
                     "file_name": "image_generated_0", "file_type": "png"}]}]}
        out = json.dumps(resp).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(out)


srv = HTTPServer(("127.0.0.1", 0), Mock)
BASE_ROOT = f"http://127.0.0.1:{srv.server_port}"
threading.Thread(target=srv.serve_forever, daemon=True).start()


def mistral(args):
    env = {k: v for k, v in os.environ.items() if k != "MISTRAL_API_KEY"}
    env.update(MISTRAL_API_KEY="test-key", MISTRAL_API_BASE=BASE_ROOT + "/v1",
               HOME=tempfile.gettempdir())
    return subprocess.run([sys.executable, "-I", os.path.join(SCRIPTS, "mistral_image.py")] + args,
                          env=env, capture_output=True, text=True)


with tempfile.TemporaryDirectory() as d:
    prompt = os.path.join(d, "prompt.txt")
    with open(prompt, "w") as f:
        f.write("it's a {\"json\": 'spec'}")

    out = os.path.join(d, "m1")
    r = mistral(["--prompt-file", prompt, "--out-dir", out])
    post = [s for s in SEEN if s[0] == "POST"][-1]
    gets = [s for s in SEEN if s[0] == "GET"]
    check(r.returncode == 0, f"observed shape: exit 0 ({r.stderr.strip()[:200]})")
    check(post[1] == "/v1/conversations" and post[2] == "Bearer test-key", "POST /conversations with key")
    check(post[3]["inputs"] == "it's a {\"json\": 'spec'}"
          and post[3]["tools"] == [{"type": "image_generation"}], "prompt intact, image tool requested")
    check(len(gets) == 1 and gets[0][1].startswith("/blob/") and gets[0][2] is None,
          "storage URL fetched once, without the API key")
    meta = json.load(open(os.path.join(out, "meta.json")))
    check(meta["image_model_prompt"] == "A rewritten prose prompt", "rewritten prompt logged")
    check(open(meta["images"][0], "rb").read() == JPEG and meta["images"][0].endswith(".jpg"),
          "image saved")

    MODE["shape"] = "documented"
    SEEN.clear()
    r = mistral(["--prompt-file", prompt, "--out-dir", os.path.join(d, "m2")])
    gets = [s for s in SEEN if s[0] == "GET"]
    check(r.returncode == 0 and gets and gets[0][1] == "/v1/files/f-9/content"
          and gets[0][2] == "Bearer test-key", "tool_file shape: downloaded from /files with key")

    # receiver
    import socket
    with socket.socket() as so:
        so.bind(("127.0.0.1", 0))
        port = so.getsockname()[1]
    rd = os.path.join(d, "recv")
    proc = subprocess.Popen([sys.executable, "-I", os.path.join(SCRIPTS, "receive_image.py"),
                             "--out-dir", rd, "--port", str(port), "--max", "1", "--timeout", "20"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    page = ""
    for _ in range(50):
        try:
            page = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1).read().decode()
            break
        except OSError:
            time.sleep(0.1)
    check("postMessage" in page, "relay page served")
    pre = urllib.request.urlopen(urllib.request.Request(
        f"http://127.0.0.1:{port}/save", method="OPTIONS",
        headers={"Origin": "https://gemini.google.com",
                 "Access-Control-Request-Private-Network": "true"}), timeout=2)
    check(pre.headers.get("Access-Control-Allow-Private-Network") == "true"
          and pre.headers.get("Access-Control-Allow-Origin") == "https://gemini.google.com",
          "preflight allows the page origin and private network")
    res = urllib.request.urlopen(urllib.request.Request(
        f"http://127.0.0.1:{port}/save?name=../../evil/.x.jpeg", data=JPEG, method="POST",
        headers={"Content-Type": "image/jpeg"}), timeout=2).read().decode()
    check(os.path.dirname(res) == os.path.abspath(rd) and os.path.basename(res) == "x.jpeg"
          and open(res, "rb").read() == JPEG, "body saved inside out-dir, name sanitised")
    check(proc.wait(timeout=5) == 0, "receiver exits 0 after --max files")

srv.shutdown()
sys.exit(1 if FAILED else 0)
