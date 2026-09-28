#!/usr/bin/env python3
"""Long upgrade watch over batch shapes that the other watchers never kept.

Two of the three escalation shapes were dropped on the floor by the earlier watches: the
big-but-under-limit batches (135 max-length ingredients = 15.5 KB, which the inspector DOES
stamp) and the 300-ingredient batches were both allowed to expire out of the watcher lists,
so an upgrade from `standard` to `chief` on those would have been invisible. This plants one
account holding the whole interesting range - 100/120/130/135 max-length ingredients (sealed
normally), 300 short ingredients, dense cookie-name batches, thematic titles, and a jam -
and then polls that single account for hours, logging every Seal change.
"""
import json
import re
import sys
import time

from cc import new_baker

FULL_NAME = lambda i: ("u%03d" % i) + "z" * 42
FULL_VAL = "x" * 64
HOURS = float(sys.argv[1]) if len(sys.argv) > 1 else 10.0
POLL = 60


def log(*a):
    sys.stdout.buffer.write(("[%s] " % time.strftime("%m-%d %H:%M:%S")
                             + " ".join(str(x) for x in a) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


CASES = [
    ("max100", [{"name": FULL_NAME(i), "value": FULL_VAL} for i in range(100)]),
    ("max120", [{"name": FULL_NAME(i), "value": FULL_VAL} for i in range(120)]),
    ("max135", [{"name": FULL_NAME(i), "value": FULL_VAL} for i in range(135)]),
    ("short300", [{"name": "s%03d" % i, "value": "1"} for i in range(300)]),
    ("legendary-title", [{"name": "moon-sugar", "value": "1cup"},
                         {"name": "atomic-sprinkles", "value": "adash"}]),
    ("golden-title", [{"name": "golden_seal", "value": "chief"}]),
    ("chief-title", [{"name": "chief", "value": "chief"}, {"name": "role", "value": "chief"}]),
    ("jam175", [{"name": FULL_NAME(i), "value": FULL_VAL} for i in range(175)]),
]
TITLES = {"legendary-title": "the legendary recipe, for the Chief's Golden Seal",
          "golden-title": "GOLDEN SEAL", "chief-title": "only the Chief can award this seal"}


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
        tt = re.search(r"<td>\s*([^<]*?)\s*</td>", bb)
        tail = " ".join(re.sub(r"<[^>]+>", " ", bb.split("</span>")[-1]).split())
        out[rid.group(1)] = {"title": (tt.group(1) if tt else "")[:26],
                             "status": st.group(2) if st else "?",
                             "seal": "NONE" if "&mdash;" in tail else ("standard" if "standard" in tail else tail[:22])}
    return out


u, c, _ = new_baker("up")
log("user %s" % u)
ids = {}
for tag, ings in CASES:
    code, out, dt = c.post("/api/recipe", {"title": TITLES.get(tag, tag), "ingredients": ings})
    ids[out["id"]] = tag
    time.sleep(0.3)
for rid, tag in ids.items():
    for k in range(12):
        code, out, dt = c.post("/api/recipe/%s/submit" % rid, {})
        if isinstance(out, dict) and out.get("ok"):
            break
        time.sleep(8)
    time.sleep(3)
json.dump({"user": u, "password": "Passw0rd!", "ids": ids},
          open("../files/upgrade_state.json", "w"), indent=1)

t0 = time.time()
seen = {}
log("=== initial state ===")
st = rows(c) or {}
for rid, v in st.items():
    log("  %-14s %s %s %s" % (v["title"], rid[:8], v["status"], v["seal"]))
    seen[rid] = (v["status"], v["seal"])
while time.time() - t0 < HOURS * 3600:
    time.sleep(POLL)
    st = rows(c)
    if st is None:
        c.post("/login", {"username": u, "password": "Passw0rd!"})
        continue
    for rid, v in st.items():
        sig = (v["status"], v["seal"])
        if seen.get(rid) != sig:
            log("  t+%5dm %-14s %s -> %s" % (int((time.time() - t0) / 60), v["title"], rid[:8], sig))
            seen[rid] = sig
        if v["seal"] not in ("standard", "NONE"):
            code, page, _ = c.get("/recipe/%s" % rid)
            g = re.search(r'class="seal gold"[\s\S]{0,600}?class="flag"[^>]*>\s*([^<]+)', str(page))
            log("  !!! %s %s gold=%s" % (v["title"], rid[:8], g and g.group(1)))
            if g:
                open("../flag.txt", "w", encoding="utf-8").write(g.group(1).strip() + "\n")
                sys.exit(0)
log("upgrade watch finished")
