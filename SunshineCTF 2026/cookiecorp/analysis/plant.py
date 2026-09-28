#!/usr/bin/env python3
"""Plant a recorded set of escalatable batches, then re-read them with check_jams.py.

The whole remaining theory is time: a batch can only reach `chief` through a session whose
DB role is chief, every reachable state has been seeded, and the deciding question is
whether the "very busy" Chief ever comes back for `reviewed` + empty-seal work. That takes
hours, so the state has to survive the session: one user, one file listing the batch ids,
and a checker that prints the Seal column for all of them.
"""
import json
import os
import sys
import time

from cc import Client, new_baker

NAME = lambda i: ("i%03d" % i) + "z" * 43
VAL = "x" * 64
STATE = "../files/watch_targets.json"


def log(*a):
    sys.stdout.buffer.write((" ".join(str(x) for x in a) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def ings(n):
    return [{"name": NAME(i), "value": VAL} for i in range(n)]


plan = [("jam143-16.4KB", 143), ("jam175-20.1KB", 175), ("jam300-34.5KB", 300),
        ("standard-control", 2), ("legendary-title-unsealed", 145)]

u, c, r = None, None, None
for k in range(6):
    u, c, r = new_baker("pl")
    if c:
        break
    time.sleep(20)
if not c:
    log("register failed:", r)
    sys.exit(1)
log("plant user %s / Passw0rd!" % u)
ids = {}
for title, n in plan:
    body = {"title": title if n != 2 else "plain control", "ingredients": ings(n) if n else []}
    if n == 2:
        body["ingredients"] = [{"name": "flour", "value": "1"}]
    code, out, dt = c.post("/api/recipe", body)
    rid = out.get("id")
    ids[rid] = title
    log("  %-26s %s n=%d" % (title, rid, n))
    time.sleep(0.4)
for rid in ids:
    for k in range(12):
        code, out, dt = c.post("/api/recipe/%s/submit" % rid, {})
        if isinstance(out, dict) and out.get("ok"):
            break
        time.sleep(8)
    log("  submitted %s -> %s" % (rid[:8], str(out)[:40]))
    time.sleep(4)

data = {}
if os.path.exists(STATE):
    data = json.load(open(STATE, encoding="utf-8"))
data[u] = {"password": "Passw0rd!", "batches": {rid: t for rid, t in ids.items()}}
json.dump(data, open(STATE, "w"), indent=1)
log("recorded in %s" % STATE)
