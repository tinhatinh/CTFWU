#!/usr/bin/env python3
"""Measure the app's own ingredient length clamp before trusting any overflow claim.

escalate.py built "21 KB of cookies" from 100 ingredients with 200-char values, then
concluded the 16 KB header overflow no longer reproduces. /builder says name <= 48 and
value <= 64, so if the server clamps instead of rejecting, that batch really carried
~11 KB - under the limit - and the "did not reproduce" result measured nothing.
Read the stored document back through window.__recipe on /review/<id>, because that is
the exact byte string mixer.js will write into the browser's cookie jar.
"""
import json
import re
import sys
import time

from cc import new_baker

def w(s):
    sys.stdout.buffer.write((str(s) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def recipe_json(c, rid):
    code, page, dt = c.get("/review/%s" % rid)
    m = re.search(r"window\.__recipe = (\{.*?\});\n</script>", page, re.S)
    if not m:
        return None
    return json.loads(m.group(1))


def cookie_bytes(ings):
    return sum(len(i["name"]) + len(i["value"]) + 2 for i in ings)


u, c, _ = new_baker("cl")
w("user %s" % u)

w("=== does the server clamp, truncate or reject? ===")
cases = [
    ("name60", [{"name": "n" * 60, "value": "v"}]),
    ("name200", [{"name": "n" * 200, "value": "v"}]),
    ("val200", [{"name": "a", "value": "v" * 200}]),
    ("val400", [{"name": "a", "value": "v" * 400}]),
    ("max48_64", [{"name": "m" * 48, "value": "x" * 64}]),
    ("n301", [{"name": "z%03d" % i, "value": "y" * 64} for i in range(301)]),
    ("n300", [{"name": "y%03d" % i, "value": "x" * 64} for i in range(300)]),
    ("n250", [{"name": "q%03d" % i, "value": "p" * 64} for i in range(250)]),
]
ids = {}
for tag, ings in cases:
    code, out, dt = c.post("/api/recipe", {"title": tag, "ingredients": ings})
    claimed = cookie_bytes(ings)
    if isinstance(out, dict) and out.get("id"):
        ids[tag] = out["id"]
        got = recipe_json(c, out["id"])
        stored = cookie_bytes(got["ingredients"]) if got else -1
        w("  %-8s -> %s sent=%dB stored=%dB n=%s" % (tag, code, claimed, stored,
                                                     len(got["ingredients"]) if got else "?"))
    else:
        w("  %-8s -> %s %s" % (tag, code, str(out)[:160]))
    time.sleep(0.4)

w("=== the biggest batch the app itself allows ===")
big = ids.get("n300")
if big:
    got = recipe_json(c, big)
    w("  n300 stores %d ingredients -> %d bytes of cookies" % (len(got["ingredients"]),
                                                               cookie_bytes(got["ingredients"])))
    names = set(i["name"] for i in got["ingredients"])
    w("  distinct names: %d (duplicate names collapse in a cookie jar)" % len(names))
    w("  sample name %r (%d) value %r (%d)" % (got["ingredients"][0]["name"],
        len(got["ingredients"][0]["name"]), got["ingredients"][0]["value"][:20],
        len(got["ingredients"][0]["value"])))
