#!/usr/bin/env python3
"""Does /api/recipe accept a routing field, and does any error echo our input?

Two things the previous session could not have seen:

* it saved recipes with `name`, but the builder actually posts `{title, ingredients}`, so
  several of its mass-assignment conclusions were tested on a field the handler ignores.
  The brief says only "legendary bakers" reach the Chief, so a routing flag on the recipe
  document is the natural design: save with candidate fields and compare what comes back.
* both /builder and / show() do `innerHTML = ... + data.error`. If any validation message
  interpolates our own value, that is a DOM XSS sink the EJS escaping never covered.
"""
import json
import re
import sys
import time

from cc import Client, new_baker

EXTRA = ["legendary", "priority", "urgent", "escalate", "chief", "review", "level",
         "tier", "gold", "golden", "flag", "vip", "premium", "master", "admin"]

VALUES = [True, "chief", "gold", 1, "1"]


def w(s):
    sys.stdout.buffer.write((str(s) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


u, c, r = new_baker("fd")
w("user %s" % u)


def save2(body):
    return c.post("/api/recipe", body)


BASE_ING = [{"name": "flour", "value": "1 cup"}]
w("=== plain save: what does the response and the page expose? ===")
code, out, dt = save2({"title": "baseline", "ingredients": BASE_ING})
w("save -> %s %s" % (code, out))
rid = out["id"] if isinstance(out, dict) and out.get("id") else None
if rid:
    for p in ["/recipe/%s" % rid, "/api/recipe/%s" % rid, "/api/recipe"]:
        code, page, dt = c.get(p)
        txt = page if isinstance(page, str) else json.dumps(page)
        w("  GET %-26s -> %s len=%s" % (p, code, len(txt)))
        if isinstance(page, (dict, list)):
            w("     json=%s" % txt[:600])
        else:
            for m in re.finditer(r"window\.__[A-Za-z_]+\s*=\s*(.{0,300})", txt):
                w("     %s" % m.group(0)[:300])

w("=== extra top-level fields: does any survive into the doc? ===")
for k in EXTRA:
    code, out, dt = save2({"title": "probe-" + k, "ingredients": BASE_ING, k: "chief"})
    new_id = out.get("id") if isinstance(out, dict) else None
    echo = {x: out[x] for x in out if x not in ("ok", "id", "ingredients")} if isinstance(out, dict) else out
    w("  %-10s -> %s extra=%s" % (k, code, str(echo)[:120]))
    if new_id:
        code2, page, dt = c.get("/recipe/%s" % new_id)
        txt = page if isinstance(page, str) else json.dumps(page)
        hit = re.findall(r"(?i)" + re.escape(k) + r"[^,<>]{0,40}", txt)
        if hit:
            w("     field visible on page: %r" % hit[:3])
    time.sleep(0.35)

w("=== error echo hunt (innerHTML sink fed by data.error) ===")
probes = [
    {"title": "<img src=x onerror=alert(1)>", "ingredients": BASE_ING},
    {"title": "a" * 300, "ingredients": BASE_ING},
    {"title": "", "ingredients": BASE_ING},
    {"title": "x", "ingredients": []},
    {"title": "x", "ingredients": [{"name": "", "value": "y"}]},
    {"title": "x", "ingredients": [{"name": "<svg onload=1>", "value": "y"}]},
    {"title": "x", "ingredients": [{"name": "ok", "value": "<img src=x onerror=1>"}]},
    {"title": "x", "ingredients": [{"name": "a" * 200, "value": "b"}]},
    {"title": "x", "ingredients": [{"name": "ok", "value": "y", "extra": "zzQQ"}]},
    {"ingredients": BASE_ING},
    {"title": "x"},
]
for body in probes:
    code, out, dt = save2(body)
    w("  %-58s -> %s %r" % (json.dumps(body)[:58], code, str(out)[:150]))
    time.sleep(0.35)
