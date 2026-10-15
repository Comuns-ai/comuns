#!/usr/bin/env python3
"""Read-only DCO trailer check; usage: python3 scripts/check-dco.py --base <ref> [--head <ref>].

Every commit in the range base..head, merge commits included, must carry a
line matching ^Signed-off-by: .+ <[^>]+@[^>]+>$ in its message. Offending
commits are printed by short hash only; a matched trailer line or address is
never printed. Exit 0: every commit carries a trailer. Exit 1: at least one
commit lacks it. Exit 2: git failed or an argument was refused.

Scope. Commits before the base are out of range by design. The seven
pre-trailer commits are certified by CIP-0003 rather than checked here. The
merge commit the host creates when a pull request is merged lies outside
every pull request range, so it is not checked. Standard library only; git is
called with a list argv, never through a shell.
"""

import argparse
import re
import subprocess
import sys


TRAILER = re.compile(r"^Signed-off-by: .+ <[^>]+@[^>]+>$")


def git(*args):
    """Run git with a list argv; return stdout text, or None when git fails."""
    try:
        result = subprocess.run(
            ["git", *args], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", errors="replace")


def has_trailer(message):
    return any(TRAILER.match(line.rstrip("\r")) for line in message.split("\n"))


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Fail when a commit in base..head lacks a Signed-off-by trailer. Merge "
            "commits inside the range are checked too. Commits before the base are "
            "out of range by design; the seven pre-trailer commits are certified by "
            "CIP-0003. The merge commit the host creates when a pull request is "
            "merged lies outside every pull request range, so it is not checked."
        )
    )
    parser.add_argument("--base", required=True, help="exclusive start of the range")
    parser.add_argument("--head", default="HEAD", help="inclusive end of the range (default HEAD)")
    args = parser.parse_args()

    for name, value in (("--base", args.base), ("--head", args.head)):
        if not value or value.startswith("-"):
            print(f"error: {name} must be a ref and must not start with '-'", file=sys.stderr)
            return 2

    listing = git("rev-list", "--end-of-options", f"{args.base}..{args.head}")
    if listing is None:
        print("error: git rev-list failed; check the refs", file=sys.stderr)
        return 2

    bad = []
    shas = listing.split()
    for sha in shas:
        body = git("log", "-1", "--format=%B", sha)
        if body is None:
            print("error: git log failed", file=sys.stderr)
            return 2
        if not has_trailer(body):
            bad.append(sha[:7])

    if bad:
        for short in bad:
            print(f"{short}: missing Signed-off-by")
        print(f"FAIL: {len(bad)} of {len(shas)} commits missing Signed-off-by")
        return 1
    print(f"OK: {len(shas)} commits carry Signed-off-by")
    return 0


if __name__ == "__main__":
    sys.exit(main())
