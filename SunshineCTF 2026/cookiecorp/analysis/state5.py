#!/usr/bin/env python3
"""Bisect the inspector's real header budget and map the state machine.

My own client dies at nginx (400 'Request Header Or Cookie Too Large') above ~8 KB, but a
batch carrying 9.2 KB of ingredient cookies was sealed normally a minute ago. So the
inspector's stamp request does not traverse nginx - which means its ceiling is Node's
16 KB --max-http-header-size, and the exact size where a batch stops getting sealed tells
us how the worker actually reaches the app. That number is also the difference between
'the worker is a browser hitting the public nginx' and 'the worker talks to the app from
inside the container', which changes what escalation is even possible.

Second question, from leak_oracle.py: submitting an already-reviewed batch is accepted
(status -> queued). Whether the previous seal is cleared and rewritten decides if a batch
can be pushed through the inspector repeatedly, which is the only lever we have on the
'reviewed but never sealed' state.
"""
import re
import sys
import time

from cc import new_baker

NAME = lambda i: ("i%03d" % i) + "z" * 43
VAL = "x" * 64
PER = 48 + 1 + 64 + 2
SIZES = [100, 120, 135, 145, 175]


def w(*a):
    sys.stdout.buffer.write((" ".join(str(x) for x in a) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def rows(c):
    code, dash, dt = c.get("/dashboard")
    if not isinstance(dash, str):
        return {}
    out = {}
    for block in re.finditer(r"<tr>(.*?)</tr>", dash, re.S):
        b = block.group(1)
        rid = re.search(r"/recipe/([0-9a-f]{24})", b)
        if not rid:
            continue
        st = re.search(r'class="pill (\w+)">(\w+)</span>', b)
        seal = " ".join(re.sub(r"<[^>]+>", " ", b.split("</span>")[-1]).split())
        out[rid.group(1)] = (st.group(2) if st else "?",
                             "NONE" if "&mdash;" in seal else ("standard" if "standard" in seal else seal[:20]))
    return out


def settle(c, ids, limit=140):
    t0 = time.time()
    last = {}
    while time.time() - t0 < limit:
        time.sleep(8)
        st = rows(c)
        for rid in ids:
            sig = st.get(rid)
            if sig and sig != last.get(rid):
                w("   t+%3ds %s %s" % (int(time.time() - t0), rid[:8], sig))
                last[rid] = sig
        if all(st.get(r, ("?",))[0] == "reviewed" for r in ids):
            return last
    return last


u, c, _ = new_baker("sz")
w("user %s" % u)
ids = []
for n in SIZES:
    code, out, dt = c.post("/api/recipe", {"title": "n%d" % n,
                                           "ingredients": [{"name": NAME(i), "value": VAL} for i in range(n)]})
    ids.append((n, out["id"]))
    w("saved n=%-4d %s %6dB" % (n, out["id"][:8], n * PER))
    time.sleep(0.3)

w("=== submit one at a time, record settle time and seal ===")
for n, rid in ids:
    t0 = time.time()
    for i in range(20):
        code, out, dt = c.post("/api/recipe/%s/submit" % rid, {})
        if isinstance(out, dict) and out.get("ok"):
            break
        time.sleep(12)
    st = settle(c, [rid], limit=90)
    w("  n=%-4d %-8s submitted in %.0fs, settled: %s" % (n, rid[:8], time.time() - t0, st.get(rid)))

w("=== resubmit a sealed standard batch: does the seal reset? ===")
small = ids[0][1]
code, out, dt = c.post("/api/recipe", {"title": "resubmit me", "ingredients": [{"name": "flour", "value": "1"}]})
rid = out["id"]
c.post("/api/recipe/%s/submit" % rid, {})
time.sleep(25)
w("   first pass  %s" % (rows(c).get(rid),))
for i in range(3):
    code, out, dt = c.post("/api/recipe/%s/submit" % rid, {})
    w("   resubmit %d -> %s %s" % (i + 1, code, str(out)[:60]))
    time.sleep(6)
    w("      now      %s" % (rows(c).get(rid),))
    time.sleep(20)
    w("      +20s     %s" % (rows(c).get(rid),))
w("done")
