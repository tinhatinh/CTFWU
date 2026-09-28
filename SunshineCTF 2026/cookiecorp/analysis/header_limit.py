#!/usr/bin/env python3
"""Find the exact header budget the seal request has to live inside.

The whole "jam the inspector so the batch escalates" idea rests on one number, and the
archive only has a fuzzy 11 KB-ok / 17 KB-fail pair measured through the app. Measure it
directly instead: replay a real session against /api/seal with a Cookie header padded to
a known size and read which layer answers (nginx 400 vs Node 431 vs the app's own 403)
and at what threshold. 300 ingredients x (48-char name + 64-char value) is 34 KB, so the
app's own validation is happy with payloads far past any plausible limit.
"""
import sys
import time

from cc import Client, new_baker

def w(s):
    sys.stdout.buffer.write((str(s) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()

MAX_NAME, MAX_VAL, MAX_ING = 48, 64, 300

u, c, _ = new_baker("hl")
w("user %s" % u)
code, out, dt = c.post("/api/recipe", {"title": "limit probe",
                                      "ingredients": [{"name": "flour", "value": "1"}]})
rid = out["id"]

w("=== /api/seal with a padded Cookie header ===")
base = dict(c.jar)
for kb in [1, 2, 4, 6, 7, 8, 9, 12, 15, 16, 17, 20, 24, 32, 40]:
    jar = dict(base)
    pad = ""
    i = 0
    target = kb * 1024
    while len(pad) < target:
        name = "p%03d" % i
        jar[name] = "x" * MAX_VAL
        pad += "%s=%s; " % (name, jar[name])
        i += 1
    hdr = "; ".join("%s=%s" % kv for kv in jar.items())
    code, out, dt = c.post("/api/seal", {"recipeId": rid},
                           headers={"Cookie": hdr})
    body = str(out)[:90].replace("\n", " ")
    w("  %5sKB (%6dB) -> %s  %s" % (kb, len(hdr), code, body))
    time.sleep(0.2)

w("=== sanity: does a plain oversized request line also 400? ===")
for path_len in [100, 2000, 5000, 9000, 12000]:
    code, out, dt = c.get("/" + "a" * path_len)
    body = (str(out)[:60].replace("\n", " ") if not isinstance(out, dict) else str(out)[:60])
    w("  path %-6dB -> %s %s" % (path_len + 1, code, body))
