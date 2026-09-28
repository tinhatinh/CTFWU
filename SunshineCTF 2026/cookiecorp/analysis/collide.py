#!/usr/bin/env python3
"""Decouple the batch's SIZE from the inspector's COOKIE HEADER - the test I never ran.

Every "the mixer overflows the verdict request" conclusion rests on one observation: batches
from n=138 max-length ingredients upward stop being sealed. That is consistent with two very
different causes, and I conflated them:

  (a) transport: the worker's browser stores all n cookies, the header passes Node's 16384 B,
      the stamp dies and the batch is left `reviewed` with no seal;
  (b) an application rule: the batch itself is "too big for the mixer", the handler marks it
      reviewed and deliberately leaves the seal empty for the Chief.

The two are separated by duplicate ingredient names, because a cookie jar is keyed by name:
300 ingredients that all share one name are still a 34.5 KB recipe (the page, the JSON blob,
the table, the DB document) but the browser ends up holding a single ~115-byte cookie. Under
(a) those batches seal normally; under (b) they come back `reviewed` with an empty seal.

Measured in a real tab first (needed, because the whole trick depends on the browser
*replacing* same-name cookies rather than appending): 300 writes of the same name leave
`document.cookie` at one entry. Controls included: 138 distinct names (should jam under (a)),
100 distinct (should seal), and a few-collision variant to see the transition.
"""
import re
import sys
import time

from cc import new_baker

VAL = "x" * 64
PAD = lambda s: s.ljust(48, "z")[:48]


def log(*a):
    sys.stdout.buffer.write(("[%s] " % time.strftime("%H:%M:%S") + " ".join(str(x) for x in a)
                             + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def cell(c, rid):
    code, dash, dt = c.get("/dashboard")
    blk = re.search(r"<tr>(?:(?!</tr>).)*?%s(?:(?!</tr>).)*?</tr>" % rid, dash or "", re.S)
    if not blk:
        return "norow", "?"
    b = blk.group(0)
    st = re.search(r'class="pill (\w+)">(\w+)</span>', b)
    tail = " ".join(re.sub(r"<[^>]+>", " ", b.split("</span>")[-1]).split())
    return ("NONE" if "&mdash;" in tail else ("standard" if "standard" in tail else tail[:24]),
            st.group(2) if st else "?")


CASES = [
    ("all-same-name-300", [PAD("same") for _ in range(300)], 1, 34500),
    ("two-names-300", [PAD("a%d" % (i % 2)) for i in range(300)], 2, 34500),
    ("ten-names-300", [PAD("c%d" % (i % 10)) for i in range(300)], 10, 34500),
    ("fifty-names-300", [PAD("d%02d" % (i % 50)) for i in range(300)], 50, 34500),
    ("distinct-100", [PAD("e%03d" % i) for i in range(100)], 100, 11500),
    ("distinct-138-jam", [PAD("f%03d" % i) for i in range(138)], 138, 15870),
    ("same-name-138", [PAD("same2") for _ in range(138)], 1, 15870),
]

u, c, _ = new_baker("cl")
log("user %s" % u)
ids = []
for label, names, distinct, payload in CASES:
    ings = [{"name": nm, "value": VAL} for nm in names]
    code, out, dt = c.post("/api/recipe", {"title": label, "ingredients": ings})
    rid = out.get("id") if isinstance(out, dict) else None
    if not rid:
        log("  %-18s save -> %s %s" % (label, code, str(out)[:60]))
        continue
    log("  %-18s %s n=%-4d distinct=%-4d payload=%dB" % (label, rid[:8], len(ings), distinct, payload))
    ids.append((label, rid))
    time.sleep(0.4)

for label, rid in ids:
    for k in range(12):
        code, out, dt = c.post("/api/recipe/%s/submit" % rid, {})
        if isinstance(out, dict) and out.get("ok"):
            break
        time.sleep(8)
    seal = stt = "?"
    for k in range(18):
        time.sleep(5)
        seal, stt = cell(c, rid)
        if stt == "reviewed":
            break
    log("  %-18s -> %-9s %s" % (label, stt, seal))
    if seal not in ("standard", "NONE"):
        code, page, _ = c.get("/recipe/%s" % rid)
        fl = re.findall(r"sun\{[^{}\r\n]{1,200}\}", str(page))
        log("      !!! %s -> %r %s" % (label, seal, fl))
log("read: any collision case that comes back NONE while distinct-100 is standard proves an")
log("application-side size rule (b), not the transport overflow (a).")
