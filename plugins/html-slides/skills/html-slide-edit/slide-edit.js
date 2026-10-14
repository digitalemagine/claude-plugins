/* slide-edit v1 — in-browser text editing for self-contained HTML decks and pages.
 *
 * Off unless the URL carries ?edit (e.g. deck.html?edit or deck.html?edit=1#4).
 * Without it this script returns immediately and changes nothing.
 *
 * Inline it in a script element at the end of body, after the page's own script,
 * with the settings as attributes on that element, e.g. data-roots=".slide".
 * (Never write a closing script tag inside this file: it ends the inline script.)
 *   data-roots     CSS selector of the editable regions (default ".slide")
 *   data-file      source file name shown in the change set (default: from the URL)
 *   data-position  top-right | top-left | bottom-right | bottom-left (default top-right)
 *                  Starting corner. Drag the grip to move the toolbar; the position is
 *                  remembered per browser, and double-clicking the grip resets it.
 *   data-download  "off" hides Download (use for reveal.js and other libraries that
 *                  rewrite the DOM at runtime, where a re-serialised page is unusable)
 *
 * Bringing edits back:
 *   Copy changes (Cmd/Ctrl+S) — puts a change set on the clipboard: one BEFORE/AFTER
 *     fragment per edited element, cumulative since page load. Paste it into Claude
 *     Code, which applies it to the source with exact replacements. The source keeps
 *     its own formatting and comments, and the git diff shows only the edits.
 *   Download — fallback. The whole page re-serialised by the browser. Formatting
 *     drifts; runtime state must be undone by the page via the hook below.
 *
 * Page integration:
 *   - While editing, keys, clicks and touches inside an editable region never reach the
 *     page's own handlers, so key, click-half and swipe navigation (deck.js) need no
 *     changes. Esc leaves edit mode.
 *   - Optional hook for Download: listen for "slide-edit:serialise" on document and
 *     undo runtime state on event.detail.root (a clone of <html>).
 *   - Never write edit UI into the page markup. This script injects its own.
 */
(function () {
  'use strict';
  var q = new URLSearchParams(location.search);
  if (!q.has('edit') || /^(0|false|off|no)$/i.test(q.get('edit') || '')) return;

  var ds = (document.currentScript && document.currentScript.dataset) || {};
  var ROOTS = ds.roots || '.slide';
  var FILE = ds.file || decodeURIComponent(location.pathname.split('/').pop() || 'index.html');
  var POS = /^(top|bottom)-(left|right)$/.test(ds.position || '') ? ds.position : 'top-right';
  // Block-level elements tracked for changes. The innermost changed one is reported.
  var BLOCKS = 'h1,h2,h3,h4,h5,h6,p,li,ul,ol,dl,dt,dd,table,thead,tbody,tfoot,tr,td,th,' +
               'blockquote,figcaption,pre,div,section,article,aside,header,footer';

  var roots = Array.prototype.slice.call(document.querySelectorAll(ROOTS));
  var orig = new Map();
  var editing = false;
  var exported = '';

  function rootOf(node) {
    for (var k = 0; k < roots.length; k++) if (roots[k].contains(node)) return roots[k];
    return null;
  }

  function snapshot() {
    if (orig.size) return;
    roots.forEach(function (r) {
      orig.set(r, r.innerHTML);
      r.querySelectorAll(BLOCKS).forEach(function (el) { orig.set(el, el.innerHTML); });
    });
  }

  // ── page styling while editing (removed again on Download) ─────────────
  var css = document.createElement('style');
  css.id = 'slide-edit-style';
  css.textContent =
    'body.slide-editing [data-slide-edit]{outline:2px dashed #b8892e;outline-offset:-6px}' +
    'body.slide-editing [data-slide-edit]:focus-within{outline-style:solid}' +
    'body.slide-editing [data-slide-edit] *{cursor:text}';
  document.head.appendChild(css);

  // ── toolbar, isolated in a shadow root ─────────────────────────────────
  var host = document.createElement('div');
  host.id = 'slide-edit-bar';
  var v = POS.split('-');
  host.style.cssText = 'position:fixed;z-index:2147483647;' + v[0] + ':10px;' + v[1] + ':10px';
  var sh = host.attachShadow({ mode: 'open' });
  sh.innerHTML =
    '<style>' +
    ':host{all:initial}' +
    '.grip{cursor:grab;padding:4px 2px;color:#999;user-select:none;touch-action:none;letter-spacing:-2px}' +
    '.grip:active{cursor:grabbing}' +
    '.bar{display:flex;align-items:center;gap:6px;padding:6px;border-radius:6px;' +
    'font:500 11px/1 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.04em;' +
    'background:#fbfaf7;color:#333;border:1px solid #d8d3c8;box-shadow:0 2px 10px rgba(0,0,0,.12)}' +
    'button{font:inherit;cursor:pointer;padding:6px 8px;border-radius:4px;' +
    'border:1px solid #cfc8ba;background:transparent;color:inherit}' +
    'button:hover{border-color:#b8892e;color:#8a6412}' +
    'button[aria-pressed=true]{background:#b8892e;border-color:#b8892e;color:#fff}' +
    'button:focus-visible{outline:2px solid #b8892e;outline-offset:2px}' +
    '.st{padding:0 4px;color:#777;white-space:nowrap}.st.dirty{color:#b4441f}' +
    '@media (prefers-color-scheme:dark){.bar{background:#1d1f22;color:#ddd;border-color:#3a3d42}' +
    'button{border-color:#4a4d52}button:hover{color:#e0b85c}.st{color:#999}.st.dirty{color:#f08a5d}}' +
    '</style>' +
    '<div class="bar" role="toolbar" aria-label="Edit mode">' +
    '<span class="grip" id="grip" title="Drag to move. Double-click to reset.">⋮⋮</span>' +
    '<button id="edit" aria-pressed="false" title="Type into the slides (Esc to stop)">Edit</button>' +
    '<button id="copy" title="Copy the change set for Claude Code (Cmd/Ctrl+S)">Copy changes</button>' +
    '<button id="dl" title="Download the whole page re-serialised (fallback)">Download</button>' +
    '<span class="st" id="st" aria-live="polite"></span>' +
    '</div>';
  document.body.appendChild(host);
  // Clicks on the toolbar must not reach click-to-advance page handlers.
  ['click', 'touchstart', 'touchend'].forEach(function (type) {
    host.addEventListener(type, function (e) { e.stopPropagation(); });
  });
  var $ = function (id) { return sh.getElementById(id); };
  var editBtn = $('edit'), copyBtn = $('copy'), dlBtn = $('dl'), st = $('st'), grip = $('grip');
  if (ds.download === 'off') dlBtn.hidden = true;

  // ── dragging; position remembered per browser, double-click resets ─────
  var POS_KEY = 'slide-edit-pos:' + location.pathname;
  var home = host.style.cssText;
  function place(x, y) {
    x = Math.max(0, Math.min(x, innerWidth - host.offsetWidth));
    y = Math.max(0, Math.min(y, innerHeight - host.offsetHeight));
    host.style.cssText = 'position:fixed;z-index:2147483647;left:' + x + 'px;top:' + y + 'px';
    return { x: x, y: y };
  }
  try {
    var saved = JSON.parse(localStorage.getItem(POS_KEY) || 'null');
    if (saved) place(saved.x, saved.y);
  } catch (e) {}
  grip.addEventListener('pointerdown', function (e) {
    e.preventDefault();
    try { grip.setPointerCapture(e.pointerId); } catch (err) {}
    var r = host.getBoundingClientRect(), dx = e.clientX - r.left, dy = e.clientY - r.top, at = null;
    function move(ev) { at = place(ev.clientX - dx, ev.clientY - dy); }
    function up() {
      grip.removeEventListener('pointermove', move);
      grip.removeEventListener('pointerup', up);
      grip.removeEventListener('pointercancel', up);
      if (at) try { localStorage.setItem(POS_KEY, JSON.stringify(at)); } catch (e) {}
    }
    grip.addEventListener('pointermove', move);
    grip.addEventListener('pointerup', up);
    grip.addEventListener('pointercancel', up);
  });
  grip.addEventListener('dblclick', function () {
    host.style.cssText = home;
    try { localStorage.removeItem(POS_KEY); } catch (e) {}
  });
  window.addEventListener('resize', function () {
    if (host.style.left) { var r = host.getBoundingClientRect(); place(r.left, r.top); }
  });

  if (!roots.length) {
    st.textContent = 'no "' + ROOTS + '" found';
    editBtn.disabled = copyBtn.disabled = true;
  }

  function setEditing(on) {
    editing = on;
    if (on) snapshot();
    document.body.classList.toggle('slide-editing', on);
    roots.forEach(function (r) {
      if (on) { r.setAttribute('contenteditable', 'true'); r.setAttribute('data-slide-edit', ''); }
      else { r.removeAttribute('contenteditable'); r.removeAttribute('data-slide-edit'); }
    });
    editBtn.setAttribute('aria-pressed', on ? 'true' : 'false');
    editBtn.textContent = on ? 'Stop editing' : 'Edit';
  }

  // ── change set ─────────────────────────────────────────────────────────
  function changed() {
    var all = [];
    orig.forEach(function (html, el) { if (el.isConnected && el.innerHTML !== html) all.push(el); });
    return all
      .filter(function (el) { return !all.some(function (o) { return o !== el && el.contains(o); }); })
      .sort(function (a, b) { return a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1; });
  }

  function path(el, root) {
    var parts = [];
    for (var n = el; n && n !== root; n = n.parentElement) {
      var tag = n.tagName.toLowerCase();
      var same = Array.prototype.filter.call(n.parentElement.children, function (c) { return c.tagName === n.tagName; });
      parts.unshift(same.length > 1 ? tag + ':nth-of-type(' + (same.indexOf(n) + 1) + ')' : tag);
    }
    return parts.join(' > ') || '(whole region)';
  }

  function label(root) {
    if (root.dataset.label) return root.dataset.label;
    var h = root.querySelector('h1,h2,h3');
    return h ? h.textContent.replace(/\s+/g, ' ').trim().slice(0, 60) : (root.id || '');
  }

  function report() {
    var list = changed();
    if (!list.length) return '';
    var out = [
      '# slide-edit change set for "' + FILE + '"',
      '',
      list.length + ' edit(s) made in the browser, cumulative since the page was loaded.',
      'Apply each to the source file: find BEFORE, replace it with AFTER, leave everything else untouched.',
      'Fragments are browser-serialised innerHTML: entities, attribute quoting and whitespace may differ from the source.',
      ''
    ];
    list.forEach(function (el, k) {
      var r = rootOf(el);
      var lb = label(r);
      out.push('## ' + (k + 1) + ' · region ' + (roots.indexOf(r) + 1) + (lb ? ' (' + lb + ')' : '') + ' · ' + path(el, r));
      out.push('BEFORE', '~~~html', orig.get(el).trim(), '~~~', 'AFTER', '~~~html', el.innerHTML.trim(), '~~~', '');
    });
    return out.join('\n');
  }

  function status() {
    var n = orig.size ? changed().length : 0;
    var dirty = n > 0 && report() !== exported;
    st.textContent = n ? n + ' change' + (n > 1 ? 's' : '') + (dirty ? ' · not copied' : ' · copied') : '';
    st.classList.toggle('dirty', dirty);
    return dirty;
  }

  function flash(btn, text) {
    var was = btn.textContent;
    btn.textContent = text;
    setTimeout(function () { btn.textContent = was; }, 1600);
  }

  function copyChanges() {
    var text = report();
    if (!text) { flash(copyBtn, 'No changes'); return; }
    var done = function () { exported = text; status(); flash(copyBtn, 'Copied'); };
    var fallback = function () {
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.style.cssText = 'position:fixed;opacity:0';
      document.body.appendChild(ta);
      ta.select();
      try { if (document.execCommand('copy')) done(); else flash(copyBtn, 'Copy failed'); }
      catch (e) { flash(copyBtn, 'Copy failed'); }
      ta.remove();
    };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, fallback);
    else fallback();
  }

  function serialise() {
    var clone = document.documentElement.cloneNode(true);
    ['#slide-edit-bar', '#slide-edit-style'].forEach(function (s) { var n = clone.querySelector(s); if (n) n.remove(); });
    clone.querySelectorAll('[data-slide-edit]').forEach(function (el) {
      el.removeAttribute('contenteditable');
      el.removeAttribute('data-slide-edit');
    });
    var b = clone.querySelector('body');
    b.classList.remove('slide-editing');
    if (!b.classList.length) b.removeAttribute('class');
    document.dispatchEvent(new CustomEvent('slide-edit:serialise', { detail: { root: clone } }));
    return '<!DOCTYPE html>\n' + clone.outerHTML + '\n';
  }

  function download() {
    var url = URL.createObjectURL(new Blob([serialise()], { type: 'text/html;charset=utf-8' }));
    var a = document.createElement('a');
    a.href = url;
    a.download = FILE;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  editBtn.addEventListener('click', function () { setEditing(!editing); });
  copyBtn.addEventListener('click', copyChanges);
  dlBtn.addEventListener('click', download);
  document.addEventListener('input', function (e) { if (rootOf(e.target)) status(); });

  // Paste as plain text so Word/Docs markup cannot leak into the source.
  document.addEventListener('paste', function (e) {
    if (!editing || !rootOf(e.target)) return;
    e.preventDefault();
    document.execCommand('insertText', false, e.clipboardData.getData('text/plain'));
  });

  // Capture phase on window runs before any page handler. Cmd/Ctrl+S copies the
  // change set instead of the browser's "Save page", which bakes runtime state
  // into the file. Keys typed into a region are kept from the page's own handlers.
  window.addEventListener('keydown', function (e) {
    if ((e.metaKey || e.ctrlKey) && !e.altKey && !e.shiftKey && e.key.toLowerCase() === 's') {
      e.preventDefault();
      copyChanges();
      return;
    }
    if (!editing) return;
    if (e.key === 'Escape') { e.preventDefault(); e.stopImmediatePropagation(); setEditing(false); return; }
    if (rootOf(e.target)) e.stopImmediatePropagation();
  }, true);

  // Click-to-advance and swipe navigation would fire on every click into the text.
  ['click', 'touchstart', 'touchend'].forEach(function (type) {
    window.addEventListener(type, function (e) {
      if (editing && rootOf(e.target)) e.stopImmediatePropagation();
    }, true);
  });

  window.addEventListener('beforeunload', function (e) {
    if (!status()) return;
    e.preventDefault();
    e.returnValue = '';
  });
})();
