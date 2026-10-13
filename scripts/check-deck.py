#!/usr/bin/env python3
"""Check the Comuns HTML pitch deck against its Markdown source.

Usage:
  python3 scripts/check-deck.py --html pitch/pitch-deck.html \
      --markdown pitch/pitch-deck.md --expected-slides 14 [--chrome PATH]

Checks (each prints PASS or FAIL; exit code 0 only if all pass):
  (a) the number of '<section class="slide"' elements equals --expected-slides
  (b) the '## ' headings of the Markdown equal, in order, the text of the
      first h1 or h2 of each section
  (c) no new script and no remote references (see "Deck safety" below)
  (d) the exact '@page { size: 1333px 750px; margin: 0 }' rule and
      'print-color-adjust: exact' are present
  (e) html.parser parses the file without error
  (f) headless Chrome prints the file to PDF and the PDF page count equals
      --expected-slides
  (g) headless Chrome --dump-dom shows no section with data-overflow="true"

Checks (f) and (g) run when --chrome is given or the default macOS Chrome path
exists; otherwise they are reported as SKIP. They are also reported as SKIP,
and the deck is never rendered, when (c) fails; the run still exits 1.

Deck safety. The deck is untrusted input: a pull request can change it, and
(f) and (g) render it in Chrome with JavaScript enabled. Check (c) has these
layers, all of which must pass:

  0. Encoding. Every rule below reads the deck as UTF-8, so every browser
     must read it as UTF-8 too. On the raw bytes, before decoding: no byte
     0x00-0x1F other than tab, LF, FF and CR, and no 0x7F (this excludes
     ISO-2022-JP and the other escape-driven encodings), and no leading
     byte-order mark other than the UTF-8 one (EF BB BF). On the decoded
     text: within the first 1024 bytes the document must open with an
     optional UTF-8 byte-order mark, '<!doctype html>', whitespace and
     comments, '<html>' or '<html lang="...">', '<head>' and then exactly
     '<meta charset="utf-8">' (the value compared case-insensitively), so a
     browser's encoding prescan meets that declaration first; and the
     case-folded source outside script bodies, both as written and
     entity-decoded, must contain 'charset' exactly once (that
     declaration), so no second <meta charset>, content="...; charset=..."
     or other declaration, under any encoding label, can exist.
     The deck must be served or opened as UTF-8: a web server that sends a
     different charset in its Content-Type header overrides the <meta>
     declaration (only a byte-order mark overrides that header), and the
     header is outside what this checker can see.

  1. Script pin (the primary control). Every <script> and <style> body is
     extracted from the raw source with the HTML5 rule (a start tag is
     '<script'/'<style' followed by whitespace, '/' or '>'; the body ends at
     the first case-insensitive '</script'/'</style' followed by whitespace,
     '/' or '>'; an unterminated body is a FAIL), not with html.parser, whose
     raw-text and comment handling differs between Python versions. Each
     script body's SHA-256 (UTF-8 bytes of the exact text between the start
     tag's '>' and the end tag) must be in ALLOWED_SCRIPT_SHA256, and every
     <script> and <style> start tag must be exactly '<script>' / '<style>'
     with no attributes. Changing the deck's script therefore requires
     updating ALLOWED_SCRIPT_SHA256 in the same pull request, and that hash
     change is the reviewer's signal to read the new script line by line.
     A script body must not contain '<' followed by an ASCII letter, '/',
     '!' or '?' (so no '<!--', '<script' or '</'), and a style body must not
     contain '<' at all, so no tag can hide in a body that a browser would
     tokenize differently (script-data double-escape, or foreign content
     where <style> is not raw text). A linear tokenizer walk, with the HTML5
     attribute rules, must meet every extracted <script>/<style> start tag
     at the same offset (none hidden in an attribute value or a comment).
     Each <style> body's SHA-256 (computed the same way) must be in
     ALLOWED_STYLE_SHA256, so changing the deck's CSS also requires updating
     that hash in the same pull request.
  1a. Allowlists, on the same linear tokenizer walk: every start and end tag
     name must be in ALLOWED_TAGS and every attribute name (compared
     case-insensitively) in ALLOWED_ATTRS, the names pitch/pitch-deck.html
     uses; so style=, on*, href, src, cursor, filter, mask, clip-path and
     every other attribute fail. Each attribute value, entity-decoded, must
     contain no backslash and no '(' unless the whole value is exactly
     url(#id), with id matching [A-Za-z][A-Za-z0-9_-]*.
  1b. Foreign content and raw-text elements: <textarea>, <noscript>, <xmp>,
     <noembed>, <noframes>, <plaintext>, <template> and <math> fail; one
     <title> is allowed, written exactly '<title>', with no '<' in its text.
     Between an <svg> start tag and its matching </svg>, every start and end
     tag name must be in SVG_TAGS (the names the deck's inline SVG uses), so
     <script>, <style>, <foreignObject>, <a>, <animate>, <set>, <image>,
     <use>, <feImage> and every HTML element fail there.
  2. Raw markup rules, outside the extracted bodies: every '<!--' comment
     must be terminated by '-->' and its body must not contain '<', '>' or
     '--!' (browsers also end comments at '<!-->', '<!--->' and '--!>'); any
     other '<!' except a leading '<!doctype html>' fails, and so does any
     '<?'. Event-handler attributes (a name starting with 'on'), <link>,
     <iframe>, <frame>, <object>, <embed>, <base>, <form> and <portal> fail.
  3. CSS: each complete style body (and each style attribute) is checked
     after CSS comment stripping and escape decoding, both with and without
     comment stripping, for @import, for url(), src(), image-set() targets
     and for quoted strings that start with '//' or a scheme.
  4. An html.parser attribute scan (values arrive entity-decoded, compared
     case-folded) fails on <script src>, <meta http-equiv>, any on*
     attribute, and a URL attribute (src, href, srcset, data, poster,
     action, formaction, xlink:href, background, ping) with a scheme or a
     leading '//'. An informational token scan of script text for network
     APIs (fetch, XMLHttpRequest, ...) also runs; it is a denylist and can be
     bypassed, which is why layer 1 exists.
  5. Parser-independent backstop: the whole source outside script bodies is
     entity-decoded, stripped of whitespace and control characters,
     case-folded, backslashes read as '/', and fails on any '//' (this
     covers '://', '=//', '"//', '(//' and ',//'), on 'javascript:', on
     'http-equiv', and on the network scheme names 'http:', 'https:',
     'ws:', 'wss:' and 'ftp:' (a browser reads 'http:host/x' as
     'http://host/x' when the page's own scheme differs, for example in an
     SVG <animate values=...> that no URL-attribute rule covers). A case-insensitive substring scan for 'http://',
     'https://', '<script src', '<link ' and '@import' also runs.
  Layers 0, 1, 1a, 1b, 2, 3 and 5 do not use html.parser and run first. If any of
  them fails, html.parser is never called: (b) and (e) FAIL as "not parsed",
  layer 4 is skipped, and (c) reports the raw problems.

Input files. Both paths are checked with lstat() before either is read: a
symlink, a non-regular file, or (for a relative path) a symlinked directory
component fails (a) for the deck or (b) for the Markdown, and nothing is
read, parsed or rendered. Each file is then opened without following
symlinks and read with a cap of 5 MB + 1 byte; a larger file or invalid UTF-8
is a FAIL, not a traceback (UTF-16 and UTF-32 files, with or without a
byte-order mark, fail here). Chrome is given the same, unresolved path.

Chrome runs offline as defense in depth, not as the primary control: every
request goes to a dead proxy on 127.0.0.1:9, every host name resolves to
NOTFOUND, the WebRTC IP handling policy is set to disable_non_proxied_udp,
and background, sync, component-update, extension and metrics traffic is
disabled. These flags do not stop all traffic: in a local test (headless
Chrome, these flags, a page creating an RTCPeerConnection with a STUN server
on 127.0.0.1) a STUN Binding Request datagram reached the loopback listener
both with and without the WebRTC switch when the page ran in real time
(--timeout=5000); with --virtual-time-budget=5000 no datagram arrived in
either case. Every Chrome call (both print-to-PDF calls and --dump-dom)
therefore runs with --virtual-time-budget=3000; the WebRTC switch is kept
only as defense in depth, with no demonstrated effect, and a deck is never
rendered unless (c) passes.
Each Chrome call has a CHROME_TIMEOUT (60 s) limit; after the first timeout
no further Chrome call runs and the unfinished checks of (f) and (g) FAIL.
Chrome uses a temporary profile and is never given
--allow-file-access-from-files.
Printed details are escaped so that control characters from the deck or
from Chrome stderr cannot rewrite the terminal.

The PDF page count in (f) is a heuristic: it counts object dictionaries that
match '/Type /Page' or '/Type/Page' but not '/Pages' in the raw PDF bytes. It
only sees uncompressed object dictionaries (object streams are not decoded),
so it fails if zero Page objects are found rather than guessing. The PDF is
written to a temporary directory that is deleted afterwards.
"""
import argparse
import hashlib
import html
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

DEFAULT_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PAGE_RULE = "@page { size: 1333px 750px; margin: 0 }"
results = []
CHROME_OFFLINE_FLAGS = [
    "--proxy-server=127.0.0.1:9",
    "--proxy-bypass-list=<-loopback>",
    "--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE localhost",
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-default-apps",
    "--disable-extensions",
    "--disable-sync",
    "--no-first-run",
    "--metrics-recording-only",
    "--disable-domain-reliability",
    "--force-webrtc-ip-handling-policy=disable_non_proxied_udp",
]
# SHA-256 of each allowed <script> body; see "Deck safety" in the docstring.
# A pinned body must also contain no '<' followed by an ASCII letter, '/', '!'
# or '?' (so no '<!--', '<script' or '</'): check (c) fails any script body
# that does, so the browser's script-data double-escape state and any
# re-tokenisation of the body as markup can never apply, whatever the script.
ALLOWED_SCRIPT_SHA256 = {
    "9fe4079961e7d861f4d834762f6fcb5f5531327b15b9392c50601ccfc8c2d7c6",
}
# SHA-256 of each allowed <style> body, extracted like the script bodies.
# Changing the deck's CSS requires updating this hash in the same pull request.
ALLOWED_STYLE_SHA256 = {
    "3ffde49053af8a9affa8b6fcf85c1f7fb60532aa194d01722c9346fe3d5ef591",
}
# Every tag and attribute name pitch/pitch-deck.html uses (layer 1a); any
# other name fails (c). Adding one to the deck requires adding it here.
ALLOWED_TAGS = {
    "aside", "body", "button", "defs", "em", "footer", "g", "h1", "h2", "head", "html",
    "li", "main", "marker", "meta", "nav", "ol", "p", "path", "rect", "script", "section",
    "span", "strong", "style", "svg", "table", "tbody", "td", "text", "th", "thead",
    "title", "tr", "ul",
}
ALLOWED_ATTRS = {
    "aria-label", "charset", "class", "content", "d", "fill", "font-size", "height", "id",
    "lang", "marker-end", "markerheight", "markerwidth", "name", "orient", "refx", "refy",
    "role", "rx", "stroke", "stroke-dasharray", "stroke-width", "text-anchor", "type",
    "viewbox", "width", "x", "y",
}
LOCAL_URL_REF = re.compile(r"url\(#[A-Za-z][A-Za-z0-9_-]*\)")
MAX_DECK_BYTES = 5 * 1024 * 1024
LEGACY_REMOTE = ("http://", "https://", "<script src", "<link ", "@import")
NETWORK_SCHEMES = ("http:", "https:", "ws:", "wss:", "ftp:")
BLOCKED_TAGS = {"link", "iframe", "frame", "object", "embed", "base", "form", "portal"}
URL_ATTRS = {"src", "href", "srcset", "data", "poster", "action", "formaction",
             "xlink:href", "background", "ping"}
JS_TOKENS = ("fetch", "XMLHttpRequest", "WebSocket", "EventSource", "sendBeacon",
             "import(", "eval(", "Function(", "window.open", "location.href=",
             "location.assign", "location.replace", "document.write", "postMessage",
             "Worker(")
SCHEME = re.compile(r"^[a-z][a-z0-9+.\-]*:")
CSS_URL = re.compile(r"(?:url|src|image-set)\(\s*['\"]?\s*([^'\"()\s]*)")
CSS_STRING = re.compile(r"\"([^\"\n]*)\"|'([^'\n]*)'")
RAW_OPEN = re.compile(r"<(script|style)(?=[\t\n\f\r />])", re.I)
RAW_CLOSE = {name: re.compile(r"</%s(?=[\t\n\f\r />])" % name, re.I)
             for name in ("script", "style")}
RAW_BLOCKED = re.compile(r"<(?:%s)(?=[\t\n\f\r />])" % "|".join(sorted(BLOCKED_TAGS)), re.I)
# Event handler names are letters only; the class excludes the separators so
# the scan stays linear.
RAW_HANDLER = re.compile(r"[\t\n\f\r \"'/]on[a-z0-9_:.\-]*[\t\n\f\r ]*=", re.I)
CSS_ESCAPE = re.compile(r"\\(?:([0-9a-fA-F]{1,6})\s?|(.))", re.S)
# Raw-text and RCDATA elements whose content a browser does not tokenize as
# markup, plus <template> and <math>; the deck uses none except one <title>.
RAW_TEXTLIKE = re.compile(r"<(title|textarea|noscript|xmp|noembed|noframes|plaintext"
                          r"|template|math)(?=[\t\n\f\r />])", re.I)
TITLE_CLOSE = re.compile(r"</title(?=[\t\n\f\r />])", re.I)
# The only element names pitch/pitch-deck.html uses inside its inline <svg>.
# Inside <svg> a browser parses foreign content (no raw text, and integration
# points such as foreignObject switch back to HTML), so any other name between
# an <svg> start tag and its matching </svg> fails (c).
SVG_TAGS = {"svg", "defs", "marker", "path", "g", "rect", "text"}
SCRIPT_TAG_LIKE = re.compile(r"<[A-Za-z/!?]")
# Tokenizer helpers (HTML whitespace is tab, LF, FF, CR and space).
TOK_WS = re.compile(r"[\t\n\f\r ]*")
TOK_NAME = re.compile(r"[^\t\n\f\r />]*")
TOK_ATTR_NAME = re.compile(r"[^\t\n\f\r />][^\t\n\f\r />=]*")
TOK_UNQUOTED = re.compile(r"[^\t\n\f\r >]*")
TOK_RAW = {name: re.compile(r"</%s(?=[\t\n\f\r />])" % name, re.I)
           for name in ("script", "style", "xmp", "iframe", "noembed", "noframes",
                        "noscript", "title", "textarea")}
# Layer 0 (encoding): control bytes other than tab, LF, FF and CR, and DEL.
CONTROL_BYTE = re.compile(rb"[\x00-\x08\x0b\x0e-\x1f\x7f]")
UTF8_BOM = b"\xef\xbb\xbf"
# UTF-32 before UTF-16: FF FE 00 00 also starts with the UTF-16LE mark. Such
# files also fail UTF-8 decoding (FF, FE and NUL); this gives a clearer message.
OTHER_BOMS = ((b"\x00\x00\xfe\xff", "UTF-32BE"), (b"\xff\xfe\x00\x00", "UTF-32LE"),
              (b"\xfe\xff", "UTF-16BE"), (b"\xff\xfe", "UTF-16LE"))
CHARSET_PRESCAN_BYTES = 1024
HTML_WS = "\t\n\f\r "


def escape(text):
    """Make control, format and separator characters visible."""
    out = []
    for ch in str(text):
        if ch.isprintable() and unicodedata.category(ch) not in ("Cc", "Cf", "Zl", "Zp"):
            out.append(ch)
        elif ord(ch) < 0x100:
            out.append("\\x%02x" % ord(ch))
        elif ord(ch) < 0x10000:
            out.append("\\u%04x" % ord(ch))
        else:
            out.append("\\U%08x" % ord(ch))
    return "".join(out)


def report(name, ok, detail=""):
    results.append(ok)
    detail = escape(detail)
    print("%s %s%s" % ("PASS" if ok else "FAIL", name, (": " + detail) if detail else ""))


def md_headings(text):
    return [l[3:].strip() for l in text.splitlines() if l.startswith("## ")]


def strip_md(s):
    return re.sub(r"[*_`]", "", s).strip()


class SectionHeadings(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.sections = []
        self.in_sec = False
        self.cur = None
        self.capture = False
        self.buf = []

    def handle_starttag(self, tag, attrs):
        if tag == "section":
            self.in_sec = True
            self.cur = None
        elif self.in_sec and self.cur is None and tag in ("h1", "h2"):
            self.capture = True
            self.buf = []

    def handle_endtag(self, tag):
        if tag in ("h1", "h2") and self.capture:
            self.capture = False
            self.cur = "".join(self.buf).strip()
            self.sections.append(self.cur)
        elif tag == "section":
            if self.cur is None:
                self.sections.append(None)
            self.in_sec = False

    def handle_data(self, data):
        if self.capture:
            self.buf.append(data)


def squash(value):
    """Case-fold and drop whitespace/control characters, as URL parsers do."""
    return "".join(ch for ch in value if ord(ch) > 0x20 and ch != "\x7f").casefold()


def remote_url(value):
    v = squash(value)
    # Browsers treat a backslash like a slash in http(s) URLs.
    return bool(v) and (v.replace("\\", "/").startswith("//") or bool(SCHEME.match(v)))


def strip_css_comments(css):
    """Remove /* ... */ comments in linear time; an unterminated one runs to the end."""
    out = []
    pos = 0
    while True:
        start = css.find("/*", pos)
        if start < 0:
            out.append(css[pos:])
            break
        out.append(css[pos:start])
        end = css.find("*/", start + 2)
        if end < 0:
            break
        pos = end + 2
    return "".join(out)


def css_unescape(css):
    def one(m):
        if m.group(1):
            try:
                return chr(int(m.group(1), 16))
            except (ValueError, OverflowError):
                return "\ufffd"
        return m.group(2)
    return CSS_ESCAPE.sub(one, css)


def css_decode(css):
    return css_unescape(strip_css_comments(css))


def css_problems(css):
    bad = []
    # Check with and without comment stripping: '/*' inside a CSS string is
    # not a comment, so stripping alone could hide text between two strings.
    for text in (css_decode(css), css_unescape(css)):
        folded = squash(text)
        if "@import" in folded:
            bad.append("CSS @import")
        for m in CSS_URL.finditer(text.casefold()):
            if remote_url(m.group(1)):
                bad.append("CSS url(%s)" % m.group(1))
        for m in CSS_STRING.finditer(text):
            value = m.group(1) if m.group(1) is not None else m.group(2)
            if remote_url(value):
                bad.append("CSS string %r" % value)
        if "://" in folded or "url(//" in folded:
            bad.append("CSS remote URL")
    return list(dict.fromkeys(bad))


def js_problems(code):
    flat = re.sub(r"\s+", "", code)
    return ["script uses %s" % t for t in JS_TOKENS if t in code or t in flat]


class RemoteScan(HTMLParser):
    """Collect remote-reference problems; attribute values arrive decoded."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.bad = []
        self.raw = None
        self.buf = []

    def handle_starttag(self, tag, attrs):
        self.check_tag(tag, attrs)

    def handle_startendtag(self, tag, attrs):
        self.check_tag(tag, attrs)
        self.flush_raw()

    def check_tag(self, tag, attrs):
        tag = tag.casefold()
        names = {(k or "").casefold() for k, _ in attrs}
        if tag in BLOCKED_TAGS:
            self.bad.append("<%s>" % tag)
        if tag == "script" and "src" in names:
            self.bad.append("<script src>")
        if tag == "meta" and "http-equiv" in names:
            self.bad.append("<meta http-equiv>")
        for k, v in attrs:
            k = (k or "").casefold()
            v = v or ""
            if k in URL_ATTRS:
                parts = [v] + (v.split(",") if k == "srcset" else [])
                if any(remote_url(part) for part in parts):
                    self.bad.append("%s=%s" % (k, v))
            if k == "style" or "url(" in squash(v):
                self.bad.extend(css_problems(v))
            if k.startswith("on"):
                self.bad.append("event handler attribute %s on <%s>" % (k, tag))
                self.bad.extend(js_problems(v))
        self.flush_raw()
        self.raw = tag if tag in ("script", "style") else None

    def flush_raw(self):
        text = "".join(self.buf)
        self.buf = []
        if self.raw == "style":
            self.bad.extend(css_problems(text))
        elif self.raw == "script":
            self.bad.extend(js_problems(text))
        self.raw = None

    def handle_endtag(self, tag):
        self.flush_raw()

    def handle_data(self, data):
        if self.raw:
            self.buf.append(data)

    def close(self):
        super().close()
        self.flush_raw()


def raw_text_bodies(src):
    """Split out <script>/<style> bodies with the HTML5 raw-text rule.

    Returns (bodies, problems, no_script, markup): bodies is a list of
    (name, body, complete, offset of the start tag); no_script is the source without script bodies;
    markup is the source without script and style bodies.
    """
    bodies, bad, no_script, markup = [], [], [], []
    pos = 0
    while True:
        m = RAW_OPEN.search(src, pos)
        if not m:
            no_script.append(src[pos:])
            markup.append(src[pos:])
            break
        name = m.group(1).lower()
        gt = src.find(">", m.end())
        if gt < 0:
            bad.append("unterminated <%s> start tag" % name)
            no_script.append(src[pos:])
            markup.append(src[pos:])
            break
        tag = src[m.start():gt + 1]
        if tag.lower() != "<%s>" % name:
            bad.append("<%s> start tag must have no attributes: %s" % (name, tag[:80]))
        start = gt + 1
        close = RAW_CLOSE[name].search(src, start)
        end = close.start() if close else len(src)
        if not close:
            bad.append("unterminated <%s> body" % name)
        bodies.append((name, src[start:end], bool(close), m.start()))
        markup.append(src[pos:start])
        no_script.append(src[pos:start] if name == "script" else src[pos:end])
        pos = end
    return bodies, bad, "".join(no_script), "".join(markup)


def markup_problems(markup):
    """Comments, '<!', '<?', event handlers and blocked tags in raw markup."""
    bad = []
    lead = len(markup) - len(markup.lstrip("﻿\t\n\f\r "))
    pos = 0
    while True:
        pos = markup.find("<!", pos)
        if pos < 0:
            break
        if markup.startswith("<!--", pos):
            end = markup.find("-->", pos + 4)
            if end < 0:
                bad.append("unterminated HTML comment")
                break
            body = markup[pos + 4:end]
            if "<" in body or ">" in body or "--!" in body:
                bad.append("HTML comment contains '<', '>' or '--!': %s" % body[:80])
            pos = end + 3
            continue
        if not (pos == lead and markup[pos:pos + 15].lower() == "<!doctype html>"):
            bad.append("markup declaration other than a leading <!doctype html>: %s"
                       % markup[pos:pos + 40])
        pos += 2
    if "<?" in markup:
        bad.append("processing instruction or bogus comment '<?'")
    for m in RAW_HANDLER.finditer(markup):
        bad.append("event handler attribute %s" % m.group(0).strip())
    for m in RAW_BLOCKED.finditer(markup):
        bad.append("%s>" % m.group(0).lower())
    return bad


def backstop_problems(no_script):
    """Parser-independent scan of everything outside script bodies."""
    flat = squash(html.unescape(no_script)).replace("\\", "/")
    bad = []
    if "//" in flat:
        i = flat.find("//")
        bad.append("'//' outside script: ...%s..." % flat[max(0, i - 30):i + 30])
    if "javascript:" in flat:
        bad.append("javascript: URL")
    # Browsers read 'http:host/x' (no slashes) as 'http://host/x' when the
    # page's own scheme differs, so a network scheme name alone is enough.
    for scheme in NETWORK_SCHEMES:
        if scheme in flat:
            bad.append("network scheme %s" % scheme)
    if "http-equiv" in flat:
        bad.append("http-equiv")
    return bad


def read_tag_rest(src, i, attrs=None):
    """Skip a tag's attributes the way the HTML5 tokenizer does.

    i is just after the tag name. Returns (end, self_closing), with end just
    after the closing '>', or (None, False) if the tag is unterminated. If
    attrs is a list, each (name, raw value) is appended to it.
    """
    n = len(src)
    while True:
        i = TOK_WS.match(src, i).end()
        if i >= n:
            return None, False
        c = src[i]
        if c == ">":
            return i + 1, False
        if c == "/":
            if src.startswith(">", i + 1):
                return i + 2, True
            i += 1
            continue
        m = TOK_ATTR_NAME.match(src, i)
        name, value = m.group(0), ""
        i = TOK_WS.match(src, m.end()).end()
        if i < n and src[i] == "=":
            i = TOK_WS.match(src, i + 1).end()
            if i >= n:
                return None, False
            if src[i] in "\"'":
                k = src.find(src[i], i + 1)
                if k < 0:
                    return None, False
                value = src[i + 1:k]
                i = k + 1
            else:
                j = TOK_UNQUOTED.match(src, i).end()
                value = src[i:j]
                i = j
        if attrs is not None:
            attrs.append((name, value))


def is_alpha(ch):
    return ("a" <= ch <= "z") or ("A" <= ch <= "Z")


def tag_problems(name, attrs, end_tag=False):
    """Layer 1a: tag, attribute-name and attribute-value allowlists."""
    bad = []
    label = "</%s>" % name[:40] if end_tag else "<%s>" % name[:40]
    if name not in ALLOWED_TAGS:
        bad.append("%s is not in ALLOWED_TAGS" % label)
    for key, raw in attrs:
        key = key.lower()
        if key not in ALLOWED_ATTRS:
            bad.append("attribute %s on %s is not in ALLOWED_ATTRS" % (key[:40], label))
        value = html.unescape(raw)
        if "\\" in value:
            bad.append("attribute %s on %s has a backslash in its value" % (key[:40], label))
        if "(" in value and not LOCAL_URL_REF.fullmatch(value):
            bad.append("attribute %s on %s has '(' in its value (only url(#id) is allowed)"
                       % (key[:40], label))
    return bad


def tokenizer_problems(src):
    """Walk the source the way a browser's tokenizer does, in linear time.

    Returns (problems, raw_starts): raw_starts lists the offsets of the
    <script>/<style> start tags the walk met in HTML context, whose bodies it
    skips as raw text. Inside <svg> (foreign content) every start or end tag
    name must be in SVG_TAGS. Every tag also goes through tag_problems().
    """
    bad, raw_starts = [], []
    depth = 0
    pos = 0
    while True:
        i = src.find("<", pos)
        if i < 0:
            break
        nxt = src[i + 1:i + 2]
        if is_alpha(nxt):
            m = TOK_NAME.match(src, i + 1)
            name = m.group(0).lower()
            attrs = []
            end, self_closing = read_tag_rest(src, m.end(), attrs)
            if end is None:
                bad.append("unterminated <%s> tag" % name[:40])
                break
            pos = end
            bad.extend(tag_problems(name, attrs))
            if depth or name == "svg":
                if name not in SVG_TAGS:
                    bad.append("<%s> is not allowed inside <svg>" % name[:40])
                elif name == "svg" and not self_closing:
                    depth += 1
                continue
            if name == "plaintext":
                break
            if name in TOK_RAW:
                if name in ("script", "style"):
                    raw_starts.append(i)
                close = TOK_RAW[name].search(src, end)
                if not close:
                    break
                pos = close.start()
            continue
        if nxt == "/":
            c = src[i + 2:i + 3]
            if is_alpha(c):
                m = TOK_NAME.match(src, i + 2)
                name = m.group(0).lower()
                attrs = []
                end, _ = read_tag_rest(src, m.end(), attrs)
                if end is None:
                    bad.append("unterminated </%s> tag" % name[:40])
                    break
                pos = end
                bad.extend(tag_problems(name, attrs, end_tag=True))
                if depth:
                    if name not in SVG_TAGS:
                        bad.append("</%s> is not allowed inside <svg>" % name[:40])
                    elif name == "svg":
                        depth -= 1
                continue
            if c == ">":
                pos = i + 3
                continue
            if depth:
                bad.append("bogus comment '</' inside <svg>")
            end = src.find(">", i + 2)
            if end < 0:
                break
            pos = end + 1
            continue
        if src.startswith("<!--", i):
            end = src.find("-->", i + 4)
            if end < 0:
                break
            pos = end + 3
            continue
        if nxt in ("!", "?"):
            end = src.find(">", i + 2)
            if end < 0:
                break
            pos = end + 1
            continue
        pos = i + 1
    if depth:
        bad.append("unterminated <svg> element")
    return bad, raw_starts


def textlike_problems(no_script):
    """Raw-text/RCDATA elements, <template> and <math>; one plain <title> is allowed."""
    bad = []
    titles = 0
    for m in RAW_TEXTLIKE.finditer(no_script):
        name = m.group(1).lower()
        if name != "title":
            bad.append("<%s> element is not allowed" % name)
            continue
        titles += 1
        ok = titles == 1 and no_script[m.start():m.start() + 7].lower() == "<title>"
        if ok:
            lt = no_script.find("<", m.start() + 7)
            ok = lt >= 0 and TITLE_CLOSE.match(no_script, lt) is not None
        if not ok:
            bad.append("<title> must appear once, as exactly '<title>', with no '<' in its text")
    return bad


def byte_problems(data):
    """Layer 0 on the raw bytes, before decoding."""
    bad = []
    for bom, name in OTHER_BOMS:
        if data.startswith(bom):
            bad.append("leading %s byte-order mark; only the UTF-8 one is allowed" % name)
            break
    m = CONTROL_BYTE.search(data)
    if m:
        bad.append("control byte 0x%02x at byte offset %d (only tab, LF, FF and CR are allowed)"
                   % (data[m.start()], m.start()))
    return bad


def charset_problems(src, no_script):
    """Layer 0 on the decoded text: one UTF-8 declaration, where a prescan meets it."""
    bad = []
    head = src.encode("utf-8")[:CHARSET_PRESCAN_BYTES].decode("utf-8", "ignore")
    i = 1 if head.startswith("﻿") else 0
    ok = head[i:i + 15].lower() == "<!doctype html>"
    i += 15
    while ok:
        i = len(head) - len(head[i:].lstrip(HTML_WS))
        if not head.startswith("<!--", i):
            break
        end = head.find("-->", i + 4)
        if end < 0 or "<" in head[i + 4:end] or ">" in head[i + 4:end]:
            ok = False
        i = end + 3
    if ok:
        gt = head.find(">", i)
        tag = head[i:gt + 1] if gt >= 0 else ""
        lang = tag[len('<html lang="'):-len('">')]
        ok = (tag.lower() == "<html>" or (
            tag[:len('<html lang="')].lower() == '<html lang="' and tag.endswith('">')
            and lang != "" and all(ch.isascii() and (ch.isalnum() or ch == "-") for ch in lang)))
        i = gt + 1
    if ok:
        i = len(head) - len(head[i:].lstrip(HTML_WS))
        ok = head[i:i + 6].lower() == "<head>"
        i += 6
    if ok:
        i = len(head) - len(head[i:].lstrip(HTML_WS))
        ok = (head.startswith('<meta charset="', i) and head[i + 15:i + 20].lower() == "utf-8"
              and head.startswith('">', i + 20))
    if not ok:
        bad.append("the first %d bytes must open with <!doctype html>, <html>, <head> and then"
                   ' exactly <meta charset="utf-8">' % CHARSET_PRESCAN_BYTES)
    folded = no_script.casefold()
    decoded = html.unescape(no_script).casefold()
    if folded.count("charset") != 1 or decoded.count("charset") != 1:
        bad.append("'charset' must appear exactly once outside script bodies (the one"
                   ' <meta charset="utf-8">); found %d (%d entity-decoded)'
                   % (folded.count("charset"), decoded.count("charset")))
    return bad


def cap(bad):
    bad = list(dict.fromkeys(bad))
    if len(bad) > 20:
        bad = bad[:20] + ["and %d more" % (len(bad) - 20)]
    return bad


def raw_problems(src):
    """Every (c) layer that does not use html.parser."""
    lower = src.casefold()
    bad = [s for s in LEGACY_REMOTE if s in lower]
    bodies, raw_bad, no_script, markup = raw_text_bodies(src)
    bad.extend(raw_bad)
    for name, body, complete, _ in bodies:
        if name == "script":
            digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
            if digest not in ALLOWED_SCRIPT_SHA256:
                bad.append("<script> body sha256 %s is not in ALLOWED_SCRIPT_SHA256" % digest)
            m = SCRIPT_TAG_LIKE.search(body)
            if m:
                bad.append("<script> body contains %s ('<' followed by a letter, '/', '!' or '?',"
                           " such as '<!--', '<script' or '</')" % body[m.start():m.start() + 12])
            bad.extend(js_problems(body))
        else:
            digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
            if digest not in ALLOWED_STYLE_SHA256:
                bad.append("<style> body sha256 %s is not in ALLOWED_STYLE_SHA256" % digest)
            if "<" in body:
                bad.append("<style> body contains '<'")
            if complete:
                bad.extend(css_problems(body))
                bad.extend(css_problems(html.unescape(body)))
    tok_bad, tok_starts = tokenizer_problems(src)
    bad.extend(tok_bad)
    if tok_starts != [start for _, _, _, start in bodies]:
        bad.append("a <script> or <style> start tag is not where a browser would read one"
                   " (for example inside an attribute value or a comment)")
    bad.extend(textlike_problems(no_script))
    bad.extend(charset_problems(src, no_script))
    bad.extend(markup_problems(markup))
    bad.extend(backstop_problems(no_script))
    return cap(bad)


def parser_problems(src):
    """The html.parser attribute scan; run only after raw_problems passed."""
    scan = RemoteScan()
    bad = []
    try:
        scan.feed(src)
        scan.close()
    except Exception as e:  # noqa: BLE001
        bad.append("scan failed: %s" % e)
    return cap(bad + scan.bad)


def count_overflow(dom):
    """Count matches of <section[^>]*data-overflow="true" in linear time.

    Equivalent to len(re.findall(...)) with that pattern, which rescans to
    the next '>' from every '<section' and is quadratic on many of them.
    """
    marker = 'data-overflow="true"'
    count = 0
    pos = 0
    while True:
        i = dom.find("<section", pos)
        if i < 0:
            return count
        gt = dom.find(">", i + 8)
        gt = len(dom) if gt < 0 else gt
        k = dom.rfind(marker, i + 8, gt)
        if k < 0:
            # Every later '<section' before gt sees a subset of this range.
            pos = gt
        else:
            count += 1
            pos = k + len(marker)


CHROME_TIMEOUT = 60


def run_chrome(chrome, args, timeout=CHROME_TIMEOUT):
    cmd = [chrome, "--headless", "--disable-gpu"] + CHROME_OFFLINE_FLAGS + args
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        # subprocess.run has already killed Chrome; report a FAIL, not a traceback.
        return subprocess.CompletedProcess(cmd, None, "", "Chrome timed out after %d s" % timeout)


def timed_out(r):
    """True for the result run_chrome returns when Chrome timed out."""
    return r.returncode is None


def path_problem(path, what):
    """Refuse a symlink, a non-regular file or a symlinked directory component."""
    try:
        if not stat.S_ISREG(os.lstat(path).st_mode):
            return "%s path is a symlink or not a regular file: %s" % (what, path)
        if not os.path.isabs(path):
            cur = ""
            for part in Path(path).parts[:-1]:
                cur = os.path.join(cur, part)
                if stat.S_ISLNK(os.lstat(cur).st_mode):
                    return "%s path has a symlinked directory component %s: %s" % (what, cur, path)
    except OSError as e:
        return "%s path cannot be checked (%s): %s" % (what, e.strerror, path)
    return None


def read_capped(path, what):
    """Read at most MAX_DECK_BYTES + 1 bytes without following a symlink.

    Returns (bytes, None) or (None, problem); decode_utf8() decodes them.
    """
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        fd = os.open(path, flags)
    except OSError as e:
        return None, "%s cannot be opened (%s): %s" % (what, e.strerror, path)
    chunks, left = [], MAX_DECK_BYTES + 1
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            return None, "%s path is a symlink or not a regular file: %s" % (what, path)
        while left > 0:
            chunk = os.read(fd, min(left, 1 << 20))
            if not chunk:
                break
            chunks.append(chunk)
            left -= len(chunk)
    except OSError as e:
        return None, "%s cannot be read (%s): %s" % (what, e.strerror, path)
    finally:
        os.close(fd)
    data = b"".join(chunks)
    if len(data) > MAX_DECK_BYTES:
        return None, "%s is larger than %d bytes; not scanned: %s" % (what, MAX_DECK_BYTES, path)
    return data, None


def decode_utf8(data, what, path):
    """Returns (text, None) or (None, problem)."""
    try:
        return data.decode("utf-8"), None
    except UnicodeDecodeError as e:
        return None, "%s is not valid UTF-8 (byte offset %d): %s" % (what, e.start, path)


def refuse(html_err, md_err):
    """Report an input file that was refused; nothing is parsed or rendered."""
    skipped = "not checked because an input file was refused"
    report("(a) slide count", False, html_err or skipped)
    report("(b) headings match", False, md_err or skipped)
    report("(c) no remote references", False, html_err or "not scanned because an input file was refused")
    report("(d) print rules present", False, skipped)
    report("(e) html parses", False, skipped)
    print("SKIP (f) PDF page count: not rendered because (c) failed")
    print("SKIP (g) overflow markers: not rendered because (c) failed")
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--markdown", required=True)
    ap.add_argument("--expected-slides", type=int, required=True)
    ap.add_argument("--chrome")
    a = ap.parse_args()
    # Check both paths before reading either; never follow a symlink.
    html_err = path_problem(a.html, "deck")
    md_err = path_problem(a.markdown, "markdown")
    src = md = None
    byte_bad = []
    if not (html_err or md_err):
        data, html_err = read_capped(a.html, "deck")
        md_data, md_err = read_capped(a.markdown, "markdown")
    if not (html_err or md_err):
        # Layer 0 byte rules run on the raw bytes, before decoding.
        byte_bad = byte_problems(data)
        src, html_err = decode_utf8(data, "deck", a.html)
        md, md_err = decode_utf8(md_data, "markdown", a.markdown)
        if html_err and byte_bad:
            html_err = "; ".join(byte_bad + [html_err])
    if html_err or md_err:
        return refuse(html_err, md_err)
    # Chrome gets the same path that was checked and read (no resolve()).
    html_path = Path(os.path.abspath(a.html))

    n = src.count('<section class="slide"')
    report("(a) slide count", n == a.expected_slides, "%d found, %d expected" % (n, a.expected_slides))

    # Raw, parser-independent rules run first; html.parser never sees a deck
    # that fails them (its tokenizer differs between Python versions and is
    # quadratic on some inputs).
    raw_bad = cap(byte_bad + raw_problems(src))
    not_parsed = "not parsed because the raw markup rules in (c) failed"
    if raw_bad:
        report("(b) headings match", False, not_parsed)
        bad = raw_bad
        parse_ok, parse_err = False, not_parsed
    else:
        p = SectionHeadings()
        try:
            p.feed(src)
            p.close()
            parse_ok, parse_err = True, ""
        except Exception as e:  # noqa: BLE001
            parse_ok, parse_err = False, str(e)
        want = [strip_md(h) for h in md_headings(md)]
        got = p.sections
        report("(b) headings match", want == got,
               "" if want == got else "markdown=%r html=%r" % (want, got))
        bad = parser_problems(src)
    report("(c) no remote references", not bad, ", ".join(bad))
    safe = not bad

    miss = [s for s in (PAGE_RULE, "print-color-adjust: exact") if s not in src]
    report("(d) print rules present", not miss, "missing: %s" % ", ".join(miss) if miss else "")

    report("(e) html parses", parse_ok, parse_err)

    chrome = a.chrome or (DEFAULT_CHROME if os.path.exists(DEFAULT_CHROME) else None)
    if not safe:
        print("SKIP (f) PDF page count: not rendered because (c) failed")
        print("SKIP (g) overflow markers: not rendered because (c) failed")
    elif not chrome or not os.path.exists(chrome):
        print("SKIP (f) PDF page count: Chrome not found")
        print("SKIP (g) overflow markers: Chrome not found")
    else:
        url = html_path.as_uri()
        tmp = tempfile.mkdtemp(prefix="comuns-deck-")
        try:
            pdf = os.path.join(tmp, "deck.pdf")
            base = ["--user-data-dir=" + os.path.join(tmp, "profile"), "--virtual-time-budget=3000"]
            r = run_chrome(chrome, base + ["--no-pdf-header-footer", "--print-to-pdf=" + pdf, url])
            if not os.path.exists(pdf) and not timed_out(r):
                r = run_chrome(chrome, base + ["--print-to-pdf=" + pdf, url])
            if timed_out(r):
                # Stop after the first timeout; render nothing more.
                report("(f) PDF page count", False, r.stderr)
                report("(g) no overflow markers", False, r.stderr)
                return 1
            if not os.path.exists(pdf):
                report("(f) PDF page count", False, "Chrome produced no PDF: " + r.stderr[-200:])
            else:
                data = open(pdf, "rb").read()
                count = len(re.findall(rb"/Type\s*/Page(?![s\w])", data))
                report("(f) PDF page count", count > 0 and count == a.expected_slides,
                       "%d Page objects (heuristic), %d expected" % (count, a.expected_slides))
            r = run_chrome(chrome, base + ["--dump-dom", url])
            if timed_out(r):
                report("(g) no overflow markers", False, r.stderr)
                return 1
            flagged = count_overflow(r.stdout)
            report("(g) no overflow markers", bool(r.stdout) and flagged == 0,
                   "%d section(s) flagged" % flagged)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
