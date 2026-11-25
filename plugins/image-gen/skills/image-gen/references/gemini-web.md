# Rendering in the Gemini web app (no API key)

Uses the user's own logged-in Chrome through Claude in Chrome. Free within the account's
daily image quota; slower than the API, and depends on the app's layout, so locate
controls by what they say, never by remembered coordinates or selectors.

Load the claude-in-chrome (or chrome-browser) skill first and follow it: one ToolSearch
for the tools you need (tabs_context_mcp, tabs_create_mcp, navigate, find, read_page,
computer, form_input, file_upload, javascript_tool, get_page_text), check tabs, work in a
new tab.

## What the app looked like when last checked (Nov 2026; verify, it changes)

- Prompt box: `rich-textarea .ql-editor` (contenteditable). `insertText` via
  `javascript_tool` puts a long multi-line JSON prompt in intact.
- Send: button with aria-label `Send message`. Model menu: aria-label starting
  `Open mode picker, currently ...`.
- No image tool toggle was needed: "Render this specification as a single ... image"
  produced an image directly.
- An image took ~20–30 s. The page shows it as a `blob:` `<img>` at half size
  (1376x768 for 16:9, i.e. the API's "1K"); the full size (2752x1536 JPEG, no visible
  watermark on a Plus plan) only comes through the `Download full size image` button.
- The page's CSP blocks `fetch` to localhost and to its own `blob:` URLs, but allows
  `window.open` to `http://127.0.0.1` and canvas reads of the image (see "Save").
- Same-chat follow-ups kept face, pose and framing: both a prose touch-up and a full
  JSON spec with a changed-fields list (lens, aperture, framing changed precisely).

## Steps

1. Open `https://gemini.google.com/app` in a new tab. If it shows a sign-in page, stop and
   ask the user to sign in (never type credentials).
2. **New chat** for each independent image or new style; **same chat** for follow-up edits
   of the last image (the app keeps the image in context, like `--previous`).
3. If the user asked for a specific model (Fast / Thinking / Pro), pick it in the model
   menu; otherwise leave the default. If the app has an image tool toggle ("Create image",
   a banana icon, "Tools"), turn it on.
4. **Reference images**: attach them with `file_upload` on the app's upload control
   (the "+" / "Add files" menu). Tell the user once per session that references are
   uploaded to their Google account.
5. **Prompt**: put the rendered prompt into the input box. Try `form_input`; if the box is
   a rich-text editor that ignores it, focus it with a click and insert with
   `javascript_tool`: `document.execCommand('insertText', false, <prompt>)` on the focused
   element. Check the box shows the whole prompt (JSON included), then send.
   Aspect ratio and size cannot be set by parameter here: they are in the prompt text
   ("Aspect ratio 16:9.").
6. **Wait** for the image (poll with `find` for the generated image or a download control
   every ~10 s, up to ~2 min). If Gemini replies with text only (a question or a refusal),
   capture the text with `get_page_text` and report it; do not retry blindly.
7. **Save** (default: no Chrome download, no dialogs). Start the receiver in the
   background, then hand the image over from the page:
   ```
   python3 "${CLAUDE_SKILL_DIR}/scripts/receive_image.py" --out-dir <run folder> --max 1
   ```
   ```js
   const w = window.open('http://127.0.0.1:8765/', 'imagegen_receiver');
   await new Promise(r => setTimeout(r, 1500));
   const imgs = [...document.querySelectorAll('img')].filter(i => i.naturalWidth > 400);
   const img = imgs[imgs.length - 1];                  // newest image
   const c = document.createElement('canvas');
   c.width = img.naturalWidth; c.height = img.naturalHeight;
   c.getContext('2d').drawImage(img, 0, 0);
   const blob = await new Promise(r => c.toBlob(r, 'image/png'));
   await new Promise(res => {
     addEventListener('message', function f(e) {
       if (e.data?.imageGen && (e.data.saved || e.data.error)) { removeEventListener('message', f); res(e.data); }
     });
     w.postMessage({name: 'image-1.png', blob}, 'http://127.0.0.1:8765');
   });
   ```
   Close the receiver tab afterwards. This gives the 1K preview size. When the user
   wants full size, use the `Download full size image` button (the **last** one) and
   move the newest `~/Downloads/Gemini_Generated_Image_*.jpeg` into the run folder
   (ignore dotfiles and `*.crdownload`: Chrome's temp files). That path shows a save
   dialog if Chrome's "Ask where to save each file" is on: tell the user, never change
   the setting yourself.
8. Write the run's `meta.json` with `"backend": "gemini-web"`, the model shown in the app,
   the chat URL (for follow-up edits) and the time.

## Limits to tell the user when relevant

- Daily image quota depends on the account plan; the app says when it is reached.
- Output size and model are whatever the app gives; images can carry a visible
  watermark in addition to SynthID.
- If a step fails twice (control not found, upload refused, no response), stop and ask
  rather than exploring the page.
