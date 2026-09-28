#!/usr/bin/env python3
"""Dump every baker-visible page and API surface, verbatim.

The archive so far only holds /, /review/:id and /recipe/:id. The two pages that
actually document the app's data model - /builder (the form the save handler reads)
and /dashboard (the seal column) - were never saved, and no GET on /api/recipe* has
ever been tried, so the raw document shape (which would reveal the seal field and who
reviewed a batch) is still unknown.
"""
import re
import sys
import time

from cc import Client

def w(s):
    sys.stdout.buffer.write((str(s) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()

def keep(path, text):
    if isinstance(text, (dict, list)):
        text = repr(text)
    with open("../files/dump_" + path.replace("/", "_").replace(":", "x"), "w",
              encoding="utf-8", errors="replace") as f:
        f.write(text)

c = Client()
code, out, dt = c.post("/register", {"username": "dump%03d" % (time.time() % 1000), "password": "Passw0rd!"})
w("register -> %s %s" % (code, str(out)[:200]))
if code not in (200, 201):
    u = "dump%03d" % (time.time() % 1000)
    c = Client()
    code, out, dt = c.post("/login", {"username": u, "password": "Passw0rd!"})
    w("login -> %s" % code)

for p in ["/", "/dashboard", "/builder", "/static/css/retro.css", "/static/js/mixer.js"]:
    code, out, dt = c.get(p)
    n = len(out) if isinstance(out, str) else 0
    w("GET %-24s -> %s %ss len=%s" % (p, code, "%.2f" % dt, n))
    keep(p, out)

# build a batch, then read every GET-able representation of it
code, out, dt = c.post("/api/recipe", {"title": "probe batch",
                                      "ingredients": [{"name": "flour", "value": "1cup"},
                                                      {"name": "sugar", "value": "2tbsp"}]})
w("save -> %s %s" % (code, str(out)[:400]))
rid = out.get("id") if isinstance(out, dict) else None
if not rid:
    sys.exit(1)
keep("/api/recipe-saved", out)

for p in ["/api/recipe", "/api/recipe/%s" % rid, "/api/recipes", "/api/dashboard",
          "/api/seal", "/api/status", "/api/status/%s" % rid, "/api/recipe/%s/status" % rid,
          "/api/recipe/%s/seal" % rid, "/recipe/%s" % rid, "/review/%s" % rid,
          "/api/user", "/api/me", "/api/session", "/api/role"]:
    code, out, dt = c.get(p)
    body = out if isinstance(out, str) else repr(out)
    w("GET %-34s -> %s %ss len=%s" % (p, code, "%.2f" % dt, len(body)))
    w("      %.300s" % body.replace("\n", " ")[:300])
    keep(p, body)

w("=== POST /api/recipe/:id (update path?) ===")
for body in [{"title": "renamed"}, {"id": rid, "title": "renamed"},
             {"_id": rid, "status": "reviewed", "seal": "chief"}]:
    code, out, dt = c.post("/api/recipe/%s" % rid, body)
    w("  %s -> %s %.2fs %s" % (str(body)[:60], code, dt, str(out)[:200]))

w("=== submit, then re-read every GET representation ===")
code, out, dt = c.post("/api/recipe/%s/submit" % rid, {})
w("submit -> %s %s" % (code, str(out)[:200]))
for _ in range(8):
    time.sleep(4)
    code, dash, dt = c.get("/dashboard")
    cells = re.findall(r"<td>\s*(.*?)\s*</td>", dash, re.S)
    pills = re.findall(r'class="pill (\w+)">(\w+)</span>', dash)
    w("  t=%s cells=%s pills=%s gold=%s" % (int(_), cells[:8], pills,
                                            bool(re.search(r"class=[\"']?flag", dash))))
code, out, dt = c.get("/api/recipe/%s" % rid)
w("  GET /api/recipe/:id after seal -> %s %.200s" % (code, str(out)[:200]))
code, dash, dt = c.get("/dashboard")
keep("/dashboard-sealed", dash)
code, out, dt = c.get("/recipe/%s" % rid)
keep("/recipe-sealed", out)
code, out, dt = c.get("/review/%s" % rid)
keep("/review-sealed", out)
w("saved dumps to ../files/")
