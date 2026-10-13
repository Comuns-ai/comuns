#!/usr/bin/env python3
"""Read-only documentation checks; usage: python3 scripts/check-docs.py [--root <dir>].

Markdown destinations are relative to their document. Bare Reference paths
starting with docs/, pitch/ or scripts/, and root filenames, are repository
relative; other bare Reference paths are relative to their document.
Hidden directories and symlink directories are not traversed. Link targets
and required files fail when their real path leaves the root or enters a
hidden directory. scripts/ is excluded from document parsing, but included
in PDF and forbidden-text checks. The checker's own source,
scripts/check-docs.py, is excluded from the forbidden-text scan because it
holds the forbidden list itself.
Mermaid validation is structural only, not a render. No network is used.
A scanned file over 5 MB fails and is not read; a document line over 20,000
characters fails and is skipped by the per-line checks. Every per-line scan
is linear in the line length: H2 headings, links and bare Reference paths
are parsed with plain string code (each documented as equivalent to the
regular expression it replaced), and every remaining regular expression was
timed on adversarial lines at the line limit.
Every printed path and message passes through escape(), so control, format
and line-separator characters from scanned files cannot rewrite the terminal;
link destinations containing such characters fail as invalid.
"""

import argparse
import json
import os
from pathlib import Path
import re
import unicodedata
from urllib.parse import unquote, urlsplit


# Add lowercase substrings here to extend the text policy. Empty by default.
FORBIDDEN_STRINGS = []
EXTENSIONS = {".md", ".html", ".json", ".py"}
# Bounds on the per-line work; every per-line scan below is linear.
MAX_LINE = 20000
MAX_FILE_BYTES = 5 * 1024 * 1024
ADR_SECTIONS = ["Context", "Decision", "Alternatives considered", "Consequences", "Links"]
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
NUMBER = re.compile(r"^(\d+)[.]?\s+(.+)$")
INLINE_CODE = re.compile(r"(?<!`)(`+)(?!`).+?(?<!`)\1(?!`)")
# A scheme is matched from the start of its run of scheme characters (the
# lookbehind), so each run is scanned once; group 1 keeps the run's leading
# non-letters, which the former pattern [A-Za-z][A-Za-z0-9+.-]*://\S* left in
# place, so URL_SCHEME.sub(r"\1", text) removes exactly what it removed.
URL_SCHEME = re.compile(r"(?<![A-Za-z0-9+.-])([0-9+.-]*)[A-Za-z][A-Za-z0-9+.-]*://\S*")
DEFINITION = re.compile(r"^ {0,3}\[[^\]]+\]:\s*(<[^>]+>|\S+)")
# Extensions a bare Reference path may end with; matched on a bounded slice.
BARE_EXTENSION = re.compile(r"\.(?:md|html|json|py)", re.I)


def unsafe(ch):
    return not ch.isprintable() or unicodedata.category(ch) in ("Cc", "Cf", "Zl", "Zp")


def escape(text):
    """Replace non-printable characters with visible escapes for printing."""
    out = []
    for ch in str(text):
        if not unsafe(ch):
            out.append(ch)
        elif ord(ch) < 0x100:
            out.append(f"\\x{ord(ch):02x}")
        elif ord(ch) < 0x10000:
            out.append(f"\\u{ord(ch):04x}")
        else:
            out.append(f"\\U{ord(ch):08x}")
    return "".join(out)


def emit(line):
    print(escape(line))


def h2_title(line):
    """Return the title of an H2 heading line, or None; linear time.

    Equivalent to the former regex ^ {0,3}## (.+?)(?: +#+)?\\s*$ on a line
    without '\\n': at most three leading spaces, then '## ', then the shortest
    nonempty title after which only whitespace remains, or one or more spaces,
    one or more '#' and whitespace.
    """
    lead = len(line) - len(line.lstrip(" "))
    if lead > 3 or not line.startswith("## ", lead):
        return None
    start = lead + 3
    if start >= len(line):
        return None
    stripped = line.rstrip()
    end = len(stripped)
    hashes = end
    while hashes > 0 and stripped[hashes - 1] == "#":
        hashes -= 1
    spaces = hashes
    while spaces > 0 and stripped[spaces - 1] == " ":
        spaces -= 1
    # A closing '#' run preceded by at least one space: the title may end
    # anywhere in that space run, and the shortest title is wanted.
    if hashes < end and spaces < hashes and max(spaces, start + 1) <= hashes - 1:
        return line[start:max(spaces, start + 1)]
    return line[start:max(end, start + 1)]


QUOTES = "\"'"


def link_spans(text):
    """Return (start, end, destination) for each inline link, left to right.

    Linear-time equivalent of finditer with the former regex
    !?\\[(?:[^\\[\\]]|\\[[^\\]]*\\])*\\]\\(\\s*(<[^>]*>|(?:[^\\s()]|\\([^()]*\\))+)
    (?:\\s+["'][^\\n]*?["'])?\\s*\\)
    Each part of that pattern has exactly one way to match from a given
    position, so the tables below (filled right to left) give the end of
    each part in constant time and every start position costs O(1).
    """
    n = len(text)
    if "](" not in text:
        return []
    # text_end[p]: where the link-text loop starting at p stops.
    # dest_end[p]: end of the longest destination item run starting at p.
    # skip_ws[p]: first non-whitespace index at or after p.
    # title_close[p]: first quote q >= p followed by optional whitespace and ')'.
    text_end = [n] * (n + 1)
    dest_end = [n] * (n + 1)
    skip_ws = [n] * (n + 1)
    title_close = [n] * (n + 2)
    next_bracket = n
    next_paren = n
    for p in range(n - 1, -1, -1):
        c = text[p]
        if c == "]":
            text_end[p] = p
        elif c == "[":
            text_end[p] = p if next_bracket == n else text_end[next_bracket + 1]
        else:
            text_end[p] = text_end[p + 1]
        if c == "(":
            dest_end[p] = (dest_end[next_paren + 1]
                           if next_paren < n and text[next_paren] == ")" else p)
        elif c == ")" or c.isspace():
            dest_end[p] = p
        else:
            dest_end[p] = dest_end[p + 1]
        skip_ws[p] = skip_ws[p + 1] if c.isspace() else p
        if c == "]":
            next_bracket = p
        if c in "()":
            next_paren = p
    for p in range(n - 1, -1, -1):
        after = skip_ws[p + 1]
        title_close[p] = (p if text[p] in QUOTES and after < n and text[after] == ")"
                          else title_close[p + 1])

    def tail(e):
        """End of '(?:\\s+["'][^\\n]*?["'])?\\s*\\)' at e, or None."""
        w = skip_ws[e]
        if w > e and w < n and text[w] in QUOTES:
            newline = text.find("\n", w + 1)
            q = title_close[w + 1]
            if q < n and (newline < 0 or q < newline):
                return skip_ws[q + 1] + 1
        if w < n and text[w] == ")":
            return w + 1
        return None

    def match_at(i):
        t = text_end[i + 1]
        if t + 1 >= n or text[t] != "]" or text[t + 1] != "(":
            return None
        d = skip_ws[t + 2]
        if d < n and text[d] == "<":
            g = text.find(">", d + 1)
            if g >= 0:
                end = tail(g + 1)
                if end is not None:
                    return end, text[d:g + 1]
        if d < n and dest_end[d] > d:
            end = tail(dest_end[d])
            if end is not None:
                return end, text[d:dest_end[d]]
        return None

    spans = []
    pos = 0
    i = text.find("[")
    while i >= 0:
        found = match_at(i)
        if found:
            start = i - 1 if i - 1 >= pos and text[i - 1] == "!" else i
            spans.append((start, found[0], found[1]))
            pos = found[0]
            i = text.find("[", pos)
        else:
            i = text.find("[", i + 1)
    return spans


def strip_links(text):
    """text with every link_spans() span removed (the former LINK.sub(""))."""
    out = []
    pos = 0
    for start, end, _ in link_spans(text):
        out.append(text[pos:start])
        pos = end
    out.append(text[pos:])
    return "".join(out)


def path_char(ch):
    return ch.isalnum() or ch in "_./%-"


def bare_paths(text):
    """Return bare repository paths in text, left to right; linear time.

    Equivalent to finditer with the former regex, case-insensitive,
    (?<![\\w:/])(?:\\.{1,2}/)?[\\w./%-]+\\.(?:md|html|json|py)
    (?:[?#][^\\s,;`<>)\\]]*)?(?=[\\s,;)\\]]|$)
    The extension must end the token, otherwise notes.markdown, trace.jsonl
    and tool.pyc are read as notes.md, trace.json and tool.py. Because no path
    character can follow the extension, the extension must end exactly where
    the run of path characters ends, so each run is examined once.
    """
    found = []
    n = len(text)
    i = 0
    while i < n:
        if not path_char(text[i]):
            i += 1
            continue
        run = i
        while i < n and path_char(text[i]):
            i += 1
        run_end = i
        start = next((p for p in range(run, run_end)
                      if p == 0 or not (path_char(text[p - 1]) and text[p - 1] not in ".%-")
                      and text[p - 1] not in ":/"), None)
        if start is None:
            continue
        if not any(run_end - size - 1 >= start + 1
                   and BARE_EXTENSION.fullmatch(text, run_end - size - 1, run_end)
                   for size in (2, 4)):
            continue
        end = run_end
        if end < n and text[end] in "?#":
            end += 1
            while end < n and not (text[end].isspace() or text[end] in ",;`<>)]"):
                end += 1
            if end < n and text[end] in "`<>":
                continue
        elif end < n and not (text[end].isspace() or text[end] in ",;)]"):
            continue
        found.append(text[start:end])
        i = end
    return found


class Report:
    def __init__(self):
        self.failed = 0
        self.checked = 0
        self.passes = []

    def check(self, name, path, line, errors):
        self.checked += 1
        if errors:
            for number, message in errors:
                self.failed += 1
                emit(f"FAIL {path}:{number} {name}: {message}")
        else:
            self.passes.append((name, line))

    def flush(self, path):
        if self.passes:
            checks = " ".join(f"{name}=PASS@{line}" for name, line in self.passes)
            emit(f"PASS {path}:1 {checks}")
            self.passes.clear()


def inventory(root):
    """Do not follow symlinks or enter hidden directories."""
    paths = []
    for directory, subdirs, files in os.walk(root, followlinks=False):
        subdirs[:] = sorted(d for d in subdirs if not d.startswith(".")
                           and not (Path(directory) / d).is_symlink())
        paths.extend(Path(directory) / name for name in sorted(files))
    return sorted(paths)


def parse_fences(lines):
    visible = list(lines)
    blocks = []
    errors = []
    opened = None
    for number, line in enumerate(lines, 1):
        match = FENCE.match(line)
        if opened:
            visible[number - 1] = ""
            if (match and match[1][0] == opened[0][0]
                    and len(match[1]) >= len(opened[0]) and not match[2].strip()):
                blocks.append((opened[1], opened[2], opened[3]))
                opened = None
            else:
                opened[3].append(line)
        elif match and not (match[1][0] == "`" and "`" in match[2]):
            tag = match[2].strip().split()
            opened = [match[1], tag[0].lower() if tag else "", number, []]
            visible[number - 1] = ""
    if opened:
        errors.append((opened[2], "unclosed fenced block"))
        blocks.append((opened[1], opened[2], opened[3]))
    return visible, blocks, errors


def containment(candidate, root):
    """Return ok, leaves, or hidden for a normalized candidate against root."""
    try:
        relative = candidate.relative_to(root)
    except ValueError:
        return "leaves"
    # Directory components only: a dotfile in a visible directory is allowed.
    if any(part.startswith(".") for part in relative.parts[:-1]):
        return "hidden"
    return "ok"


def resolve_status(candidate, root):
    """Return file, missing, leaves, hidden, or invalid.

    Real paths stop directory symlinks from counting outside the root or in a
    hidden directory. NUL and resolution errors are invalid, not fatal.
    """
    try:
        raw = os.fspath(candidate)
        root_raw = os.fspath(root)
        if "\x00" in raw or "\x00" in root_raw:
            return "invalid"
        lexical_root = Path(os.path.abspath(root_raw))
        real_root = Path(os.path.realpath(root_raw))
        lexical = Path(os.path.abspath(raw))
        real = Path(os.path.realpath(raw))
    except (OSError, ValueError):
        return "invalid"
    for status in (containment(lexical, lexical_root), containment(real, real_root)):
        if status != "ok":
            return status
    try:
        # realpath has already resolved symlinks; refuse to follow a leftover one.
        if real.is_symlink():
            return "invalid"
        return "file" if real.is_file() else "missing"
    except (OSError, ValueError):
        return "invalid"


def link_errors(path, root, visible):
    errors = []
    root_names = {p.name for p in root.iterdir() if p.is_file()}
    for number, line in enumerate(visible, 1):
        line = INLINE_CODE.sub("", line)
        targets = [(dest, False) for _, _, dest in link_spans(line)]
        definition = DEFINITION.match(line)
        if definition:
            targets.append((definition[1], False))
        if line.startswith("**Reference:**"):
            bare_line = URL_SCHEME.sub(r"\1", strip_links(line[len("**Reference:**"):]))
            targets.extend((target, True) for target in bare_paths(bare_line))
        for target, bare in dict.fromkeys(targets):
            target = target.strip("<>")
            if any(unsafe(ch) for ch in target):
                errors.append((number, f"invalid link destination: {target}"))
                continue
            try:
                parts = urlsplit(target)
            except ValueError:
                errors.append((number, f"invalid link destination: {target}"))
                continue
            if parts.scheme or parts.netloc or target.startswith(("/", "#")):
                continue
            try:
                decoded = unquote(parts.path)
            except (OSError, ValueError):
                errors.append((number, f"invalid link destination: {target}"))
                continue
            if any(unsafe(ch) for ch in decoded):
                errors.append((number, f"invalid link destination: {target}"))
                continue
            try:
                if Path(decoded).suffix.lower() not in EXTENSIONS:
                    continue
                base = path.parent
                if bare and (decoded.startswith(("docs/", "pitch/", "scripts/"))
                             or decoded in root_names):
                    base = root
                candidate = base / decoded
            except (OSError, ValueError):
                errors.append((number, f"invalid link destination: {target}"))
                continue
            # Compare real paths so '.'/'..' in --root and directory symlinks
            # cannot hide a target outside the root or in a hidden directory.
            kind = resolve_status(candidate, root)
            if kind == "leaves":
                errors.append((number, f"link leaves root: {target}"))
            elif kind == "hidden":
                errors.append((number, f"link enters an excluded directory: {target}"))
            elif kind == "invalid":
                errors.append((number, f"invalid link destination: {target}"))
            elif kind == "missing":
                errors.append((number, f"missing file: {target}"))
    return errors


def proposal_errors(visible, headings):
    errors = []
    end = next((n - 1 for n, _ in headings), len(visible))
    header = [(n, line.strip()) for n, line in enumerate(visible[:end], 1)
              if line.strip()]
    fields = ["Author:", "Status:", "Category:", "Created:", "**Reference:**"]
    start = next((i for i, (_, line) in enumerate(header)
                  if line.startswith("Author:")), -1)
    for offset, field in enumerate(fields):
        i = start + offset
        if start < 0 or i >= len(header) or not header[i][1].startswith(field) or not header[i][1][len(field):].strip():
            errors.append((header[i][0] if start >= 0 and i < len(header) else 1,
                           f"header requires nonempty {field} in order"))
    after = start + len(fields)
    if start < 0 or after >= len(header) or header[after][1] != "---":
        errors.append((1, "header must end with --- after Reference"))
    titles = []
    for expected, (number, title) in enumerate(headings, 1):
        match = NUMBER.match(title)
        if not match or int(match[1]) != expected:
            errors.append((number, f"expected H2 section {expected}"))
        titles.append(match[2] if match else title)
    if titles[-2:] != ["Risks", "Open questions"]:
        errors.append((headings[-1][0] if headings else 1,
                       "last two H2 headings must be Risks then Open questions"))
    if not any("[RISK]" in line for line in visible):
        errors.append((1, "missing [RISK] marker"))
    return errors


def check_document(path, root, text, report):
    relative = path.relative_to(root).as_posix()
    lines = text.splitlines()
    # Over-long lines fail and are blanked so no regex runs on them.
    report.check("line-length", relative, 1,
                 [(n, f"line too long ({len(line)} characters; limit {MAX_LINE})")
                  for n, line in enumerate(lines, 1) if len(line) > MAX_LINE])
    lines = ["" if len(line) > MAX_LINE else line for line in lines]
    visible, blocks, errors = parse_fences(lines)
    report.check("fences", relative, 1, errors)
    report.check("links", relative, 1, link_errors(path, root, visible))
    mermaid_errors = []
    json_errors = []
    for tag, number, body in blocks:
        if tag == "mermaid":
            first = next((line.strip() for line in body if line.strip()), "")
            if not re.match(r"^(?:flowchart|sequenceDiagram|stateDiagram-v2|graph|classDiagram)(?:\s|$)", first):
                mermaid_errors.append((number + 1, "unsupported or missing diagram declaration"))
        if tag == "json":
            try:
                json.loads("\n".join(body), parse_constant=reject_constant)
            except json.JSONDecodeError as error:
                json_errors.append((number + error.lineno, error.msg))
            except ValueError as error:
                json_errors.append((number + 1, str(error)))
            except RecursionError:
                # Deeply nested arrays or objects exhaust the decoder's stack.
                json_errors.append((number + 1, "JSON nested too deeply to parse"))
    report.check("mermaid-structure-not-render", relative, 1, mermaid_errors)
    report.check("json", relative, 1, json_errors)
    titles = ((n, h2_title(line)) for n, line in enumerate(visible, 1))
    headings = [(n, title) for n, title in titles if title is not None]
    if path.suffix.lower() == ".md" and relative.startswith("docs/"):
        first_h2 = headings[0][0] - 1 if headings else len(visible)
        if any(line.strip() == "Category: Technical Proposal" for line in visible[:first_h2]):
            report.check("proposal", relative, 1, proposal_errors(visible, headings))
    if relative == "docs/evidence-register.md":
        errors = []
        for section in range(1, 14):
            if not any(re.search(rf"§{section}(?!\d)", title) for _, title in headings):
                errors.append((1, f"missing H2 with literal §{section}"))
        if not any(re.search(r"\bHow to cite\b", title, re.I) for _, title in headings):
            errors.append((1, "missing How to cite H2 section"))
        report.check("evidence-sections", relative, 1, errors)
    adr = re.fullmatch(r"docs/adr/(\d{4})-.+\.md", relative)
    if adr:
        errors = []
        if not lines or not lines[0].startswith(f"# ADR {adr[1]}:"):
            errors.append((1, f"must start with # ADR {adr[1]}:"))
        for field in ("**Status:**", "**Date:**", "**Deciders:**"):
            if not any(line.startswith(field) and line[len(field):].strip() for line in visible):
                errors.append((1, f"missing {field}"))
        if [title for _, title in headings] != ADR_SECTIONS:
            errors.append((1, "expected five H2 sections: " + ", ".join(ADR_SECTIONS)))
        report.check("adr", relative, 1, errors)
    if relative == "pitch/pitch-deck.md":
        errors = []
        if len(headings) != 14:
            errors.append((1, f"expected 14 slide H2 headings, found {len(headings)}"))
        for (previous, _), (current, _) in zip(headings, headings[1:]):
            if not any(line.strip() == "---" for line in visible[previous:current - 1]):
                errors.append((current, "slide needs a preceding --- separator"))
        report.check("deck-14", relative, 1, errors)


def reject_constant(value):
    raise ValueError(f"invalid JSON constant: {value}")


def main():
    parser = argparse.ArgumentParser(usage="python3 scripts/check-docs.py [--root <dir>]")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    try:
        root = args.root.absolute()
    except (OSError, ValueError):
        emit(f"FAIL {args.root}:1 root: directory does not exist")
        return 1
    if not root.is_dir():
        emit(f"FAIL {root}:1 root: directory does not exist")
        return 1
    # absolute() keeps '.' and '..'; realpath normalizes them and symlinks
    # before every relative_to() comparison.
    try:
        root = Path(os.path.realpath(root))
    except (OSError, ValueError):
        emit(f"FAIL {root}:1 root: directory does not exist")
        return 1
    report = Report()
    policy_errors = [(1, "forbidden strings must be nonempty lowercase strings")
                     for item in FORBIDDEN_STRINGS
                     if not isinstance(item, str) or not item or item != item.lower()]
    report.check("forbidden-policy", "scripts/check-docs.py", 1, policy_errors)
    report.flush("scripts/check-docs.py")
    forbidden = [item for item in FORBIDDEN_STRINGS if isinstance(item, str) and item]
    paths = inventory(root)
    for path in paths:
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            report.check("read", relative, 1, [(1, "symlink file is not read")])
            continue
        report.check("no-pdf", relative, 1,
                     [(1, "PDF files are not allowed")] if path.suffix.lower() == ".pdf" else [])
        try:
            size = path.stat().st_size
            if size > MAX_FILE_BYTES:
                report.check("size", relative, 1,
                             [(1, f"file too large ({size} bytes; limit {MAX_FILE_BYTES}), not scanned")])
                report.flush(relative)
                continue
            data = path.read_bytes()
        except OSError as error:
            report.check("read", relative, 1, [(1, str(error))])
            report.flush(relative)
            continue
        # Byte matching includes non-text files and gives byte-newline positions.
        errors = []
        lower = data.lower()
        for item in ([] if relative == "scripts/check-docs.py" else forbidden):
            needle = item.encode("utf-8")
            start = 0
            while (position := lower.find(needle, start)) >= 0:
                errors.append((data.count(b"\n", 0, position) + 1,
                               f"forbidden string: {item!r}"))
                start = position + len(needle)
        report.check("forbidden", relative, 1, errors)
        if path.suffix.lower() in {".md", ".html"} and "scripts" not in path.relative_to(root).parts[:-1]:
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError as error:
                report.check("read", relative, 1, [(1, f"invalid UTF-8: {error}")])
            else:
                check_document(path, root, text, report)
        report.flush(relative)
    # Required special documents must not disappear and silently skip checks.
    for required in ("docs/evidence-register.md", "pitch/pitch-deck.md"):
        try:
            present = resolve_status(root / required, root) == "file"
        except (OSError, ValueError):
            present = False
        report.check("required", required, 1,
                     [] if present else [(1, "required document is missing")])
        report.flush(required)
    emit(f"{'FAIL' if report.failed else 'PASS'} .:1 summary: "
          f"{report.checked} checks, {report.failed} failures")
    return 1 if report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
