#!/usr/bin/env python3
"""Receive images POSTed from a browser page and save them, so web-app backends never
go through Chrome's download (and its save dialogs).

    python3 receive_image.py --out-dir image-gen/<slug>/vN [--port 8765] [--max 1] [--timeout 300]

Listens on 127.0.0.1 only. Each POST /save?name=<file> writes the raw body to
<out-dir>/<file> (name sanitised; default image-N.<ext> from Content-Type) and prints the
saved path. Exits after --max files or --timeout seconds. The page side (run with
javascript_tool):

    const blob = await (await fetch(img.src)).blob();
    await fetch('http://127.0.0.1:8765/save?name=image-1.jpeg',
                {method: 'POST', body: blob, headers: {'Content-Type': blob.type}});

Sends CORS and Private Network Access headers so an https page may post to it.
"""

import argparse
import os
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

EXT = {"image/png": "png", "image/jpeg": "jpeg", "image/webp": "webp", "image/gif": "gif"}
RELAY = """<!doctype html><meta charset="utf-8"><title>image-gen receiver</title>
<p>image-gen receiver: waiting for images. This tab can be closed afterwards.</p>
<script>
window.addEventListener('message', async (e) => {
  const d = e.data || {};
  if (!(d.blob instanceof Blob)) return;
  try {
    const r = await fetch('/save?name=' + encodeURIComponent(d.name || ''),
      {method: 'POST', body: d.blob, headers: {'Content-Type': d.blob.type}});
    e.source.postMessage({imageGen: true, saved: await r.text(), ok: r.ok}, e.origin);
  } catch (err) {
    e.source.postMessage({imageGen: true, error: String(err)}, e.origin);
  }
});
if (window.opener) window.opener.postMessage({imageGen: true, ready: true}, '*');
</script>"""


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--out-dir", required=True)
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--max", type=int, default=1)
    p.add_argument("--timeout", type=int, default=300)
    a = p.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    saved = []

    class H(BaseHTTPRequestHandler):
        def log_message(self, *x):
            pass

        def cors(self):
            self.send_header("Access-Control-Allow-Origin", self.headers.get("Origin") or "*")
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Private-Network", "true")

        def do_GET(self):
            # Relay page for sites whose CSP blocks fetch to localhost: the site opens
            # this page with window.open and postMessages {name, blob}; this page (same
            # origin as the server) uploads it and replies {saved} or {error}.
            if urlparse(self.path).path != "/":
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(RELAY.encode())

        def do_OPTIONS(self):
            self.send_response(204)
            self.cors()
            self.end_headers()

        def do_POST(self):
            u = urlparse(self.path)
            if u.path != "/save":
                self.send_response(404)
                self.cors()
                self.end_headers()
                return
            n = int(self.headers.get("Content-Length") or 0)
            if n <= 0 or n > 64 * 1024 * 1024:
                self.send_response(400)
                self.cors()
                self.end_headers()
                return
            body = self.rfile.read(n)
            ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip()
            name = (parse_qs(u.query).get("name") or [""])[0]
            name = re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(name)).lstrip(".")
            if not name:
                name = f"image-{len(saved) + 1}.{EXT.get(ctype, 'bin')}"
            path = os.path.abspath(os.path.join(a.out_dir, name))
            with open(path, "wb") as f:
                f.write(body)
            saved.append(path)
            print(path, flush=True)
            self.send_response(200)
            self.cors()
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(path.encode())
            if len(saved) >= a.max:
                threading.Thread(target=srv.shutdown, daemon=True).start()

    srv = HTTPServer(("127.0.0.1", a.port), H)
    timer = threading.Timer(a.timeout, srv.shutdown)
    timer.daemon = True  # must not keep the process alive after --max files
    timer.start()
    print(f"listening on http://127.0.0.1:{a.port}/save -> {os.path.abspath(a.out_dir)}",
          file=sys.stderr, flush=True)
    srv.serve_forever()
    sys.exit(0 if saved else 3)


if __name__ == "__main__":
    main()
