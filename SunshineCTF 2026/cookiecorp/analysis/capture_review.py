#!/usr/bin/env python3
"""Run one full batch and capture everything the review page loads.

The previous run concluded the golden seal needs the Chief's own browser, but it never
saved the client-side code. mixer.js is the script that decides *what* gets POSTed to
/api/seal, so it is the cheapest authoritative answer to "where does the level come
from": if it reads a field from the recipe, that field is the target.
"""
import json
import re
import sys
import time
import urllib.parse

from cc import Client, BASE, new_baker, save, submit, gold


def w(s):
    sys.stdout.buffer.write((str(s) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


u, c, r = new_baker("mx")
if not c:
    w("register failed: %s" % (r,)); sys.exit(1)
w("user %s cookies=%s" % (u, sorted(c.jar)))

code, rec, dt = save(c, "mixer probe batch", [
    {"name": "flour", "value": "1 cup"},
    {"name": "butter", "value": "cold"},
])
rid = rec.get("id") if isinstance(rec, dict) else None
w("recipe %s -> %s" % (rid, str(rec)[:200]))
if not rid:
    sys.exit(1)

w("builder page: %s" % str(c.get("/builder")[0]))
code, body, dt = c.get("/recipe/%s" % rid)
open("../files/recipe_page.html", "w", encoding="utf-8").write(body if isinstance(body, str) else str(body))
w("/recipe/%s -> %s len=%s" % (rid, code, len(body) if isinstance(body, str) else "-"))

w(submit(c, rid)[:2])
seen = None
for i in range(18):
    time.sleep(2.5)
    code, page, dt = c.get("/review/%s" % rid)
    txt = page if isinstance(page, str) else json.dumps(page)
    st = re.findall(r"queued|reviewing|reviewed|draft", txt)
    if "reviewed" in txt or gold(txt):
        seen = txt
        break
    w("  poll %d status=%s" % (i, st[-3:] if st else "?"))
if seen is None:
    code, seen, dt = c.get("/review/%s" % rid)

open("../files/review_page.html", "w", encoding="utf-8").write(seen)
w("=== review page (%d bytes) ===" % len(seen))
w(seen[:2500])
scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)', seen) or re.findall(r'<script[^>]+src=["\']([^"\']+)', seen)
w("scripts referenced: %s" % scripts)
for s in scripts:
    path = s if s.startswith("/") else "/" + s
    code, js, dt = c.get(path)
    name = "../files" + path.replace("/", "_")
    open(name, "w", encoding="utf-8").write(js if isinstance(js, str) else str(js))
    w("---- %s (%s, %s bytes) ----" % (path, code, len(js) if isinstance(js, str) else "?"))
    w(js if isinstance(js, str) else str(js))
