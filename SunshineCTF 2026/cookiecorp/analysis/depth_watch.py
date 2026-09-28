#!/usr/bin/env python3
"""Passive long watch: global queue depth plus every jam batch we own.

The instance is shared, so the dashboard's `Inspector queue depth` line is a free view of
everyone's backlog. If some other team has found a batch shape the inspector never claims,
the depth will sit above zero for minutes at a time - that is the observable signature of a
"queued but untouched" state, which would be the Chief's natural inbox and something we
could not produce ourselves. Alongside it, the seal column of our own jammed batches, so a
slow Chief sweep shows up here even after the shorter watchers stop.
"""
import re
import sys
import time

from cc import Client

HOURS = float(sys.argv[1]) if len(sys.argv) > 1 else 8.0
POLL = 45
USERS = ["pl5392", "sz3576", "of1726"]


def log(*a):
    sys.stdout.buffer.write(("[%s] " % time.strftime("%m-%d %H:%M:%S")
                             + " ".join(str(x) for x in a) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def grab(c):
    code, dash, dt = c.get("/dashboard")
    if code != 200:
        return None, None
    d = re.search(r"queue depth: (\d+) batch", dash)
    rows = {}
    for b in re.finditer(r"<tr>(.*?)</tr>", dash, re.S):
        bb = b.group(0)
        rid = re.search(r"/recipe/([0-9a-f]{24})", bb)
        if not rid:
            continue
        st = re.search(r'class="pill (\w+)">(\w+)</span>', bb)
        tail = " ".join(re.sub(r"<[^>]+>", " ", bb.split("</span>")[-1]).split())
        rows[rid.group(1)] = (st.group(2) if st else "?", "NONE" if "&mdash;" in tail else
                              ("standard" if "standard" in tail else tail[:24]))
    return (int(d.group(1)) if d else -1), rows


sess = []
for u in USERS:
    c = Client()
    if c.post("/login", {"username": u, "password": "Passw0rd!"})[0] == 200:
        sess.append((u, c))
log("watching %s for %.1f h" % ([u for u, _ in sess], HOURS))

t0 = time.time()
last_depth = None
last = {}
maxdepth = 0
while time.time() - t0 < HOURS * 3600:
    time.sleep(POLL)
    for u, c in sess:
        d, rows = grab(c)
        if rows is None:
            c.post("/login", {"username": u, "password": "Passw0rd!"})
            continue
        if d is not None and d != last_depth:
            log("  depth %s -> %d" % (last_depth, d))
            maxdepth = max(maxdepth, d)
            last_depth = d
        for rid, sig in rows.items():
            if last.get(rid) != sig:
                log("  t+%5dm %-8s %s %s %s" % (int((time.time() - t0) / 60), u, rid[:8],
                                                sig[0], sig[1]))
                last[rid] = sig
                if sig[1] not in ("NONE", "standard"):
                    code, page, _ = c.get("/recipe/%s" % rid)
                    g = re.search(r'class="seal gold"[\s\S]{0,600}?class="flag"[^>]*>\s*([^<]+)',
                                  str(page))
                    log("  !!! %s %s -> gold=%s" % (u, rid[:8], g and g.group(1)))
                    if g:
                        open("../flag.txt", "w", encoding="utf-8").write(g.group(1).strip() + "\n")
                        sys.exit(0)
log("done; max queue depth observed = %d" % maxdepth)
