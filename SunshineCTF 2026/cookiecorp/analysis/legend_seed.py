#!/usr/bin/env python3
"""Seed standard-sealed batches with every flavour of "legendary" and wait for an upgrade.

The jam ladder tests the other half of the same sentence, but "the Chief is a very busy
robot" supports two different sweep conditions and they are mutually exclusive signals:

  * the Chief looks for batches nobody could stamp   (seal = null)   -> ladder_watch.py
  * the Chief *upgrades* batches that deserve it     (seal = reviewed) -> this script

The second one matters because the ladder batches can never be upgraded by a Chief that
would load the same page: its own verdict request would overflow on the same cookies. A
Chief that promotes already-sealed batches works over normal-sized batches and is the only
version of escalation that survives the author's own mechanic. Since we cannot read the
rule, seed the plausible ones - the builder's default recipe verbatim, the complete
space-age pantry from the site copy, the tagline as a title, numeric edge values, and
"legendary"/"golden"/42 - let the inspector seal them standard, then watch for hours.
"""
import json
import re
import sys
import time

from cc import new_baker, Client

HOURS = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
POLL = 90

SPACE = [{"name": n, "value": v} for n, v in [
    ("moon_sugar", "1cup"), ("atomic_sprinkles", "a dash"), ("stardust", "2tbsp"),
    ("nebula_flour", "3cups"), ("solar_butter", "cold"), ("cosmic_cocoa", "1cup"),
    ("quantum_vanilla", "1tsp"), ("gravity_eggs", "2"), ("comet_sprinkles", "top"),
    ("plasma_honey", "3tbsp")]]
CLASSIC = [{"name": n, "value": v} for n, v in [
    ("flour", "2+1/4 cups"), ("baking_soda", "1 tsp"), ("salt", "1 tsp"),
    ("butter", "1 cup"), ("sugar", "3/4 cup"), ("brown_sugar", "3/4 cup"),
    ("eggs", "2"), ("vanilla", "2 tsp"), ("chocolate_chips", "2 cups")]]
SEEDS = [
    ("defaults", "Untitled Batch", [{"name": "flour", "value": "2 cups"},
                                     {"name": "atomic_sprinkles", "value": "a dash"}]),
    ("space-pantry", "The Legendary Space-Age Cookie", SPACE),
    ("classic", "A Better Cookie for a Brighter Tomorrow", CLASSIC),
    ("golden-title", "GOLDEN", [{"name": "golden_seal", "value": "1"}]),
    ("legendary-title", "legendary", [{"name": "legendary", "value": "true"}]),
    ("answer42", "42", [{"name": "answer", "value": "42"}]),
    ("inf-value", "overflow sugar", [{"name": "moon_sugar", "value": "1e999"},
                                     {"name": "stardust", "value": "Infinity"},
                                     {"name": "nan", "value": "NaN"},
                                     {"name": "neg", "value": "-0"}]),
    ("chief-ing", "for the chief", [{"name": "chief", "value": "1"},
                                    {"name": "the_chief", "value": "1"},
                                    {"name": "head_chief", "value": "1"}]),
]


def log(*a):
    line = "[%s] %s" % (time.strftime("%m-%d %H:%M:%S"), " ".join(str(x) for x in a))
    sys.stdout.buffer.write((line + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def table(c):
    code, dash, dt = c.get("/dashboard")
    if code != 200:
        return None
    out = {}
    for block in re.finditer(r"<tr>(.*?)</tr>", dash, re.S):
        b = block.group(1)
        rid = re.search(r"/recipe/([0-9a-f]{24})", b)
        if not rid:
            continue
        st = re.search(r'class="pill (\w+)">(\w+)</span>', b)
        tail = " ".join(re.sub(r"<[^>]+>", " ", b.split("</span>")[-1]).split())
        out[rid.group(1)] = (st.group(2) if st else "?",
                             "NONE" if "&mdash;" in tail else ("standard" if "standard" in tail else tail[:26]))
    return {"_dash": dash, **out}


users = []
for half in (0, 1):
    u, c, r = new_baker("lg")
    if not c:
        log("register failed", r)
        continue
    c.user = u
    items = SEEDS[half * 4:half * 4 + 4]
    ids = {}
    for tag, title, ings in items:
        code, out, dt = c.post("/api/recipe", {"title": title, "ingredients": ings})
        if not (isinstance(out, dict) and out.get("id")):
            log("  %-14s save -> %s %s" % (tag, code, str(out)[:60]))
            continue
        ids[tag] = out["id"]
        time.sleep(0.3)
    for tag, rid in ids.items():
        for k in range(10):
            code, out, dt = c.post("/api/recipe/%s/submit" % rid, {})
            if isinstance(out, dict) and out.get("ok"):
                break
            time.sleep(8)
        log("  seeded+submitted %-14s %s" % (tag, rid[:8]))
        time.sleep(3)
    users.append((u, c, ids))

state = {u: ids for u, c, ids in users}
json.dump(state, open("../files/legend_seed_state.json", "w"), indent=1)
log("=== watching %.1f h for an upgrade to chief ===" % HOURS)

t0 = time.time()
seen = {}
while time.time() - t0 < HOURS * 3600:
    time.sleep(POLL)
    for u, c, ids in users:
        st = table(c)
        if st is None:
            c.post("/login", {"username": u, "password": "Passw0rd!"})
            continue
        dash = st.pop("_dash")
        fl = re.findall(r"sun\{[^{}\r\n]{1,200}\}", dash)
        if fl or 'class="flag"' in dash:
            open("../flag.txt", "w", encoding="utf-8").write((fl[0] if fl else "") + "\n")
            open("../files/golden_legend_dashboard.html", "w", encoding="utf-8").write(dash)
            log("!!! FLAG on %s: %s" % (u, fl))
            break
        for tag, rid in ids.items():
            sig = st.get(rid)
            if sig and seen.get(rid) != sig:
                log("  t+%5dm %-14s %s %s" % (int((time.time() - t0) / 60), tag, rid[:8], sig))
                seen[rid] = sig
            if sig and sig[1] not in ("NONE", "standard"):
                code, page, _ = c.get("/recipe/%s" % rid)
                open("../files/golden_legend_%s.html" % tag, "w", encoding="utf-8").write(str(page))
                f2 = re.findall(r"sun\{[^{}\r\n]{1,200}\}", str(page))
                if f2:
                    open("../flag.txt", "w", encoding="utf-8").write(f2[0] + "\n")
                log("!!! %s became %s (flag=%s)" % (tag, sig, f2))
log("legend watch over")
