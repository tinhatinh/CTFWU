#!/usr/bin/env python3
"""Does the Chief exist as a backlog worker? Build a queue and watch who drains it.

The baker dashboard prints a live global counter (`Inspector queue depth: N batch(es)
awaiting review`), which is the only free view into the worker on a shared instance. If
the "very busy" Chief is a second sweep - the kind of loop that exists to help when the
inspector is behind - then a deep queue is the one condition that should surface it, and
the batch it takes would come back `chief` instead of `standard`. Cost to the shared
worker is a couple of minutes, and the same run validates the depth oracle.
"""
import re
import sys
import time

from cc import new_baker


def log(*a):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), " ".join(str(x) for x in a))
    sys.stdout.buffer.write((line + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def depth(c):
    code, dash, dt = c.get("/dashboard")
    m = re.search(r"queue depth: (\d+) batch", dash or "")
    return int(m.group(1)) if m else -1


def seals(c):
    code, dash, dt = c.get("/dashboard")
    out = {}
    for block in re.finditer(r"<tr>(.*?)</tr>", dash, re.S):
        b = block.group(1)
        rid = re.search(r"/recipe/([0-9a-f]{24})", b)
        if not rid:
            continue
        tail = " ".join(re.sub(r"<[^>]+>", " ", b.split("</span>")[-1]).split())
        out[rid.group(1)] = "NONE" if "&mdash;" in tail else ("standard" if "standard" in tail else tail[:26])
    return out


u1, c1, _ = new_baker("bq")
u2, c2, _ = new_baker("bq")
log("builder %s / observer %s" % (u1, u2))
ids = []
for i in range(8):
    code, out, dt = c1.post("/api/recipe", {"title": "bq%d" % i,
                                           "ingredients": [{"name": "flour", "value": "1"},
                                                           {"name": "sugar", "value": "2"}]})
    ids.append(out["id"])
    time.sleep(0.3)

log("=== firing all 8 submits without waiting for the worker ===")
t0 = time.time()
ok = 0
for rid in ids:
    for k in range(25):
        code, out, dt = c1.post("/api/recipe/%s/submit" % rid, {})
        if isinstance(out, dict) and out.get("ok"):
            ok += 1
            break
        if k % 5 == 0:
            log("   depth=%d submit %s -> %s" % (depth(c2), rid[:6], code))
    log(" submitted %d/8  depth now=%d" % (ok, depth(c2)))
log("all submitted in %.1fs, depth=%d" % (time.time() - t0, depth(c2)))

log("=== watch the drain and every seal ===")
seen = {}
for i in range(90):
    time.sleep(6)
    d = depth(c2)
    st = seals(c1)
    for rid, sig in st.items():
        if seen.get(rid) != sig:
            log("   t+%3ds depth=%d %s -> %s" % (int(time.time() - t0), d, rid[:8], sig))
            seen[rid] = sig
    if sig is not None and all(s in ("standard",) for s in seen.values()) and d == 0:
        break
log("final: depth=%d seals=%s" % (depth(c2), sorted(set(seen.values()))))
if any(s not in ("standard", "NONE") for s in seen.values()):
    log("!!! something other than standard")
