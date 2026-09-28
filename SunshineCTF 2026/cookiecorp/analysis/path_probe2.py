#!/usr/bin/env python3
"""Path+method probe built from this app's own vocabulary, with 403 as the prize.

`routes.py` (the script in this workspace) only sent POST plus 24 GETs, so "no hidden route"
rests on a thinner list than `notes.md` claims. The interesting answer is not 404 but **401 or
403**: an unauthorized response on a path proves a handler exists behind an auth check, which
is exactly the shape a `/chief`-style staff route would have. Every candidate is built from
words the app itself uses (chief, golden, seal, inspector, review, escalate, appeal, award,
stamp, mixer, tray, queue, staff, internal, worker) crossed with the route shapes this app
already uses (`/api/<noun>`, `/api/<noun>/:id`, `/api/<noun>/:id/<verb>`, `/<noun>`, and a
trailing slash on each). Also re-sends the verbs the workspace never tried on the known
routes.
"""
import sys
import time

from cc import new_baker

NOUNS = ["chief", "golden", "gold", "seal", "seals", "inspector", "staff", "admin", "internal",
         "worker", "bot", "robot", "review", "reviews", "escalate", "escalation", "appeal",
         "appeals", "award", "awards", "stamp", "queue", "mixer", "tray", "batch", "batches",
         "recipe", "recipes", "audit", "qa", "verify", "verdict", "certificate", "certify",
         "grand", "prize", "legendary", "hall", "fame", "dashboard", "console", "reports"]
VERBS = ["approve", "approve-all", "run", "sweep", "review", "seal", "reseal", "escalate",
         "reverify", "grant", "award", "list", "pending", "unsealed"]
ID = "0" * 24

PATHS = []
for n in NOUNS:
    PATHS += ["/" + n, "/" + n + "/", "/api/" + n, "/api/" + n + "/",
              "/api/" + n + "/" + ID, "/api/" + n + "/" + ID + "/seal",
              "/api/" + n + "/" + ID + "/approve", "/api/" + n + "/sweep",
              "/staff/" + n, "/internal/" + n, "/chief/" + n]
for v in VERBS:
    PATHS += ["/api/seal/" + v, "/api/review/" + ID + "/" + v, "/api/recipe/" + ID + "/" + v,
              "/api/" + v, "/api/v1/seal", "/api/v1/recipe", "/v1/seal", "/seal/" + v]
PATHS += ["/api", "/api/", "/api/health", "/api/me", "/api/user", "/api/users", "/api/role",
          "/api/session", "/api/sessions", "/api/status", "/api/config", "/api/version",
          "/api/debug", "/debug", "/metrics", "/healthz", "/readyz", "/graphql", "/rpc",
          "/api/seal/ " + ID, "/api/seal/../seal", "/api/../api/seal"]
PATHS = sorted(set(PATHS))
METHODS = ["GET", "POST", "OPTIONS"]


def log(*a):
    sys.stdout.buffer.write(("[%s] " % time.strftime("%H:%M:%S") + " ".join(str(x) for x in a)
                             + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


u, c, _ = new_baker("pz")
log("user %s probing %d paths x %s" % (u, len(PATHS), "/".join(METHODS)))
# positive control: three paths whose non-404 answers are already known. If the harness does
# not flag these, it cannot be trusted to say "nothing else answered".
CTRL = {"/api/seal": 403, "/dashboard": 200, "/builder": 200}
for p, want in CTRL.items():
    for m in ("GET", "POST"):
        code, o, dt = c.req(m, p, body=({} if m == "POST" else None))
        log("  CONTROL %-14s %-6s got %s want %s%s" % (p, m, code, want,
            "" if code == want else "   <-- HARNESS BROKEN"))
interesting = {}
for i, p in enumerate(PATHS):
    ms = ["GET", "POST", "OPTIONS"] if p.startswith("/api") else ["GET"]
    for m in ms:
        code, o, dt = c.req(m, p, body=({} if m == "POST" else None))
        body = str(o)
        if code in (401, 403, 405, 500) or (code == 200 and m == "POST" and "Cannot" not in body):
            sig = (code, body[:60].replace("\n", " "))
            interesting.setdefault(p, []).append(sig)
            log("  %-38s %-7s %s %s" % (p, m, code, sig[1][:70]))
    if i % 40 == 0:
        log("  ... %d/%d done" % (i, len(PATHS)))
    time.sleep(0.05)
log("non-404 answers: %d paths" % len(interesting))
