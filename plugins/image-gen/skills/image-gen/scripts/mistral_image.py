#!/usr/bin/env python3
"""Render one image with Mistral (Conversations API + built-in image_generation tool).

Standard library only. The prompt is always read from a file.

    python3 mistral_image.py --prompt-file run/prompt.txt --out-dir run/ \
        [--spec run/spec.json] [--model mistral-medium-latest] [--dry-run]

Key: MISTRAL_API_KEY, else the MISTRAL_API_KEY line of ~/.vibe/.env (where the Vibe CLI
stores it after login). Endpoint override for tests: MISTRAL_API_BASE.

No reference images, aspect ratio or size parameters: the API does not document any, so
aspect and size go in the prompt text and are not guaranteed. The image comes back as a
tool_file chunk that is downloaded from /v1/files/<id>/content.

Writes into --out-dir: request.json, response.json, image-N.<ext>, text.txt, meta.json.
Exit codes: 0 ok, 1 API/HTTP error, 2 bad arguments, 3 response had no image.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE = "https://api.mistral.ai/v1"
DEFAULT_MODEL = "mistral-medium-latest"


def fail(msg, code=2):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def api_key():
    key = os.environ.get("MISTRAL_API_KEY")
    if key:
        return key
    path = os.path.expanduser("~/.vibe/.env")
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                k, _, v = line.strip().partition("=")
                if k.strip() == "MISTRAL_API_KEY" and v.strip():
                    return v.strip().strip("'\"")
    except OSError:
        pass
    return None


def call(req, timeout):
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", "")


def find_outputs(resp):
    """Images, texts and the prompt the agent actually sent to the image model.

    Two shapes exist. Documented: a {"type": "tool_file", "file_id": ...} chunk, downloaded
    from /files/<id>/content with the API key. Observed (Nov 2026): the tool.execution entry
    carries info.result = '{"url": "<short-lived blob URL>"}' and message.output content is
    markdown text with the same URL. Images are returned as ("file", id, ext) or
    ("url", url, ext).
    """
    images, texts, tool_prompts = [], [], []

    def add(kind, ref, ext):
        if all(r != ref for _, r, _ in images):
            images.append((kind, ref, ext))

    def walk(n):
        if isinstance(n, dict):
            if n.get("type") == "tool_file" and n.get("file_id"):
                add("file", n["file_id"], n.get("file_type") or "png")
            elif n.get("type") == "text" and isinstance(n.get("text"), str):
                texts.append(n["text"])
            if n.get("type") == "tool.execution" and n.get("name") == "image_generation":
                try:
                    tool_prompts.append(json.loads(n.get("arguments") or "{}").get("prompt"))
                except (TypeError, ValueError):
                    pass
                res = (n.get("info") or {}).get("result")
                try:
                    res = json.loads(res) if isinstance(res, str) else res
                except ValueError:
                    res = None
                if isinstance(res, dict) and str(res.get("url", "")).startswith(("https://", "http://127.0.0.1")):
                    path = urllib.parse.urlparse(res["url"]).path
                    add("url", res["url"], os.path.splitext(path)[1].lstrip(".") or "jpg")
            if n.get("type") == "message.output" and isinstance(n.get("content"), str):
                texts.append(n["content"])
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)
    walk(resp)
    return images, texts, [p for p in tool_prompts if p]


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--prompt-file", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--spec")
    p.add_argument("--model", default=os.environ.get("MISTRAL_IMAGE_MODEL", DEFAULT_MODEL))
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--timeout", type=int, default=300)
    a = p.parse_args()

    with open(a.prompt_file, encoding="utf-8") as f:
        prompt = f.read().strip()
    if not prompt:
        fail("prompt file is empty")
    os.makedirs(a.out_dir, exist_ok=True)

    def dump(name, obj):
        with open(os.path.join(a.out_dir, name), "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)

    body = {"model": a.model, "inputs": prompt, "stream": False,
            "tools": [{"type": "image_generation"}],
            "instructions": "Use the image_generation tool to create exactly one image that "
                            "follows the user's specification as literally as possible. "
                            "Pass the full specification to the tool; do not summarise it."}
    dump("request.json", body)
    if a.spec:
        dst = os.path.join(a.out_dir, "spec" + os.path.splitext(a.spec)[1])
        if os.path.abspath(a.spec) != os.path.abspath(dst):
            with open(a.spec, encoding="utf-8") as f:
                text = f.read()
            with open(dst, "w", encoding="utf-8") as f:
                f.write(text)
    meta = {"backend": "mistral-api", "model": a.model,
            "prompt_file": os.path.abspath(a.prompt_file)}
    if a.dry_run:
        meta["dry_run"] = True
        dump("meta.json", meta)
        print(json.dumps(meta, indent=2))
        return

    key = api_key()
    if not key:
        fail("no MISTRAL_API_KEY in the environment or ~/.vibe/.env")
    base = os.environ.get("MISTRAL_API_BASE", DEFAULT_BASE).rstrip("/")
    auth = {"Authorization": f"Bearer {key}"}
    t0 = time.time()
    try:
        raw, _ = call(urllib.request.Request(
            f"{base}/conversations", data=json.dumps(body).encode("utf-8"), method="POST",
            headers={**auth, "Content-Type": "application/json", "Accept": "application/json"}),
            a.timeout)
        resp = json.loads(raw.decode("utf-8"))
        dump("response.json", resp)
        images, texts, tool_prompts = find_outputs(resp)
        paths = []
        for i, (kind, ref, ext) in enumerate(images, 1):
            if kind == "file":
                req = urllib.request.Request(
                    f"{base}/files/{ref}/content",
                    headers={**auth, "Accept": "application/octet-stream"})
            else:  # pre-signed storage URL: never send the API key there
                req = urllib.request.Request(ref)
            data, _ = call(req, a.timeout)
            path = os.path.join(a.out_dir, f"image-{i}.{ext}")
            with open(path, "wb") as f:
                f.write(data)
            paths.append(os.path.abspath(path))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        meta.update(error=f"HTTP {e.code}", detail=detail[:4000])
        dump("meta.json", meta)
        fail(f"HTTP {e.code}: {detail[:2000]}", 1)
    except (urllib.error.URLError, TimeoutError) as e:
        meta.update(error=str(e))
        dump("meta.json", meta)
        fail(str(e), 1)

    meta.update(seconds=round(time.time() - t0, 1), conversation_id=resp.get("conversation_id"),
                usage=resp.get("usage"), images=paths,
                image_model_prompt=tool_prompts[0] if tool_prompts else None)
    if texts:
        with open(os.path.join(a.out_dir, "text.txt"), "w", encoding="utf-8") as f:
            f.write("\n\n".join(texts))
        meta["text"] = "\n\n".join(texts)[:1000]
    dump("meta.json", meta)
    print(json.dumps(meta, indent=2, ensure_ascii=False))
    if not paths:
        fail("response contained no image (see response.json / text.txt)", 3)


if __name__ == "__main__":
    main()
