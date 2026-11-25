#!/usr/bin/env python3
"""Render one image with the Gemini API (Interactions API), and log the run.

Standard library only. The prompt is always read from a file (never a shell argument), so
quotes or apostrophes in a prompt cannot break the command line.

    python3 gemini_image.py --prompt-file run/prompt.txt --out-dir run/ \
        [--spec run/spec.json] [--ref a.png --ref b.jpg] \
        [--aspect 16:9] [--size 2K] [--model gemini-nano-banana-2.1] \
        [--thinking medium] [--previous <interaction id>] [--mime image/png] [--dry-run]

Key: GEMINI_API_KEY (or GOOGLE_API_KEY). Endpoint override for tests: GEMINI_API_BASE.
--dry-run writes the request (base64 elided) to the run folder and exits without a key.

Writes into --out-dir: request.json (base64 elided), response.json (base64 elided),
image-N.<ext>, text.txt (if the model returned text), meta.json (model, params,
interaction id, timings). Prints meta.json to stdout. Exit codes: 0 ok, 1 API/HTTP error,
2 bad arguments, 3 response had no image.
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request

DEFAULT_MODEL = "gemini-nano-banana-2.1"
API_REVISION = "2026-05-20"
DEFAULT_BASE = "https://generativelanguage.googleapis.com/v1beta"
ASPECTS = {"1:1", "1:4", "1:8", "2:3", "3:2", "3:4", "4:1", "4:3", "4:5", "5:4",
           "8:1", "9:16", "16:9", "21:9"}
SIZES = {"512px", "1K", "2K", "4K"}
EXT = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}


def fail(msg, code=2):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def image_part(path):
    mime = mimetypes.guess_type(path)[0] or ""
    if not mime.startswith("image/"):
        fail(f"not an image (by extension): {path}")
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    return {"type": "image", "mime_type": mime, "data": data}


def elide(obj):
    """Copy of obj with long base64 'data' strings replaced by a length note."""
    if isinstance(obj, dict):
        return {k: (f"<{len(v)} base64 chars>" if k == "data" and isinstance(v, str)
                    and len(v) > 200 else elide(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [elide(v) for v in obj]
    return obj


def find_outputs(resp):
    """Collect (mime, base64) images and text from the response, wherever they sit.

    The documented accessors are output_image.data / output_text and steps[] with
    type "model_output" whose content[] holds {"type":"image","data":...} or
    {"type":"text","text":...}. The full raw schema is not published, so walk the whole
    tree and skip "thought" steps.
    """
    images, texts, seen = [], [], set()

    def walk(node, in_thought=False):
        if isinstance(node, dict):
            thought = in_thought or node.get("type") == "thought"
            data = node.get("data")
            mime = node.get("mime_type") or node.get("mimeType") or ""
            if isinstance(data, str) and len(data) > 100 and (
                    node.get("type") == "image" or mime.startswith("image/")):
                if not thought and data not in seen:
                    seen.add(data)
                    images.append((mime or "image/png", data))
            if node.get("type") == "text" and isinstance(node.get("text"), str) and not thought:
                texts.append(node["text"])
            for k, v in node.items():
                if k == "output_text" and isinstance(v, str) and v not in texts:
                    texts.append(v)
                walk(v, thought)
        elif isinstance(node, list):
            for v in node:
                walk(v, in_thought)

    walk(resp)
    return images, texts


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--prompt-file", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--spec", help="spec file to copy into the run log (not sent)")
    p.add_argument("--ref", action="append", default=[], help="reference image (repeatable, max 14)")
    p.add_argument("--aspect")
    p.add_argument("--size", help="1K, 2K, 4K (512px on gemini-3.1-flash-image only)")
    p.add_argument("--model", default=os.environ.get("GEMINI_IMAGE_MODEL", DEFAULT_MODEL))
    p.add_argument("--thinking", choices=["minimal", "medium", "high"])
    p.add_argument("--previous", help="previous interaction id, for a multi-turn edit")
    p.add_argument("--mime", choices=sorted(EXT), help="output image type")
    p.add_argument("--search", action="store_true", help="enable Google Search grounding")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--timeout", type=int, default=300)
    a = p.parse_args()

    if a.aspect and a.aspect not in ASPECTS:
        fail(f"--aspect must be one of {sorted(ASPECTS)}")
    if a.size and a.size not in SIZES:
        fail(f"--size must be one of {sorted(SIZES)} (uppercase K)")
    if len(a.ref) > 14:
        fail("at most 14 reference images")
    with open(a.prompt_file, encoding="utf-8") as f:
        prompt = f.read().strip()
    if not prompt:
        fail("prompt file is empty")

    os.makedirs(a.out_dir, exist_ok=True)
    body = {"model": a.model,
            "input": [{"type": "text", "text": prompt}] + [image_part(r) for r in a.ref]}
    fmt = {k: v for k, v in (("mime_type", a.mime), ("aspect_ratio", a.aspect),
                             ("image_size", a.size)) if v}
    if fmt:
        body["response_format"] = {"type": "image", **fmt}
    if a.thinking:
        body["generation_config"] = {"thinking_level": a.thinking}
    if a.previous:
        body["previous_interaction_id"] = a.previous
    if a.search:
        body["tools"] = [{"type": "google_search"}]

    def dump(name, obj):
        with open(os.path.join(a.out_dir, name), "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)

    dump("request.json", elide(body))
    if a.spec:
        dst = os.path.join(a.out_dir, "spec" + os.path.splitext(a.spec)[1])
        if os.path.abspath(a.spec) != os.path.abspath(dst):
            with open(a.spec, encoding="utf-8") as f:
                text = f.read()
            with open(dst, "w", encoding="utf-8") as f:
                f.write(text)
    meta = {"backend": "gemini-api", "model": a.model, "aspect": a.aspect, "size": a.size,
            "thinking": a.thinking, "previous": a.previous,
            "refs": [os.path.abspath(r) for r in a.ref], "prompt_file": os.path.abspath(a.prompt_file)}
    if a.dry_run:
        meta["dry_run"] = True
        dump("meta.json", meta)
        print(json.dumps(meta, indent=2))
        return

    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        fail("no GEMINI_API_KEY / GOOGLE_API_KEY in the environment (use the Chrome path, "
             "or --dry-run)")
    base = os.environ.get("GEMINI_API_BASE", DEFAULT_BASE).rstrip("/")
    req = urllib.request.Request(
        f"{base}/interactions", data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"x-goog-api-key": key, "Content-Type": "application/json",
                 "Api-Revision": API_REVISION})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=a.timeout) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        meta.update(error=f"HTTP {e.code}", detail=detail[:4000])
        dump("meta.json", meta)
        fail(f"HTTP {e.code}: {detail[:2000]}", 1)
    except (urllib.error.URLError, TimeoutError) as e:
        meta.update(error=str(e))
        dump("meta.json", meta)
        fail(str(e), 1)
    meta["seconds"] = round(time.time() - t0, 1)
    dump("response.json", elide(resp))

    images, texts = find_outputs(resp)
    meta["interaction_id"] = resp.get("id")
    meta["usage"] = resp.get("usage") or resp.get("usage_metadata")
    files = []
    for i, (mime, data) in enumerate(images, 1):
        path = os.path.join(a.out_dir, f"image-{i}.{EXT.get(mime, 'png')}")
        with open(path, "wb") as f:
            f.write(base64.b64decode(data))
        files.append(os.path.abspath(path))
    meta["images"] = files
    if texts:
        with open(os.path.join(a.out_dir, "text.txt"), "w", encoding="utf-8") as f:
            f.write("\n\n".join(texts))
        meta["text"] = "\n\n".join(texts)[:1000]
    dump("meta.json", meta)
    print(json.dumps(meta, indent=2, ensure_ascii=False))
    if not files:
        fail("response contained no image (see response.json and text.txt: often a "
             "safety refusal or a clarifying question)", 3)


if __name__ == "__main__":
    main()
