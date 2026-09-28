#!/usr/bin/env python3
"""Keep a young unsealed batch in the database at all times.

If the Chief sweep has any age window in it (`updatedAt` newer than some cutoff, "batches the
inspector failed on in the last N minutes"), a batch left sitting for two hours is exactly the
thing that would be skipped - and silence would then look like "there is no Chief". This
plants two in-band batches (n=138 and n=140 max-length ingredients: over the browser
inspector's ~16 KB header budget, under what a lean server-side stamp could still send) every
25 minutes for six hours, rotating accounts to respect the 10-batch cap, so there is always a
fresh unsealed row for any sweep to find. Cost to the shared worker is two passes per interval.
"""
import re
import sys
import time

from cc import new_baker

INTERVAL = 25 * 60
HOURS = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
VAL = "x" * 64
NAME = lambda i: ("n%03d" % i).ljust(48, "z")


def log(*a):
    sys.stdout.buffer.write(("[%s] " % time.strftime("%m-%d %H:%M:%S")
                             + " ".join(str(x) for x in a) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def cell(c, rid):
    code, dash, dt = c.get("/dashboard")
    blk = re.search(r"<tr>(?:(?!</tr>).)*?%s(?:(?!</tr>).)*?</tr>" % rid, dash or "", re.S)
    if not blk:
        return "norow"
    tail = " ".join(re.sub(r"<[^>]+>", " ", blk.group(0).split("</span>")[-1]).split())
    return "NONE" if "&mdash;" in tail else ("standard" if "standard" in tail else tail[:24])


t0 = time.time()
n = 0
while time.time() - t0 < HOURS * 3600:
    u, c, _ = new_baker("fr")
    n += 1
    log("round %d user %s" % (n, u))
    for k, size in enumerate((138, 140)):
        code, out, dt = c.post("/api/recipe", {"title": "fresh band %d" % size,
                                               "ingredients": [{"name": NAME(i), "value": VAL}
                                                               for i in range(size)]})
        rid = out.get("id") if isinstance(out, dict) else None
        if not rid:
            log("   save -> %s %s" % (code, str(out)[:60]))
            continue
        for j in range(10):
            sc, so, _ = c.post("/api/recipe/%s/submit" % rid, {})
            if isinstance(so, dict) and so.get("ok"):
                break
            time.sleep(7)
        seal = "norow"
        for j in range(10):
            time.sleep(5)
            seal = cell(c, rid)
            if seal != "norow":
                break
        log("   n=%d %s seal=%s" % (size, rid[:8], seal))
        if seal not in ("NONE", "standard"):
            code, page, _ = c.get("/recipe/%s" % rid)
            g = re.search(r'class="seal gold"[\s\S]{0,600}?class="flag"[^>]*>\s*([^<]+)', str(page))
            log("   !!! fresh batch got %r gold=%s" % (seal, g and g.group(1)))
            if g:
                open("../flag.txt", "w", encoding="utf-8").write(g.group(1).strip() + "\n")
                sys.exit(0)
    log("   (sleeping %d s)" % (INTERVAL // 60))
    time.sleep(INTERVAL)
log("fresh-band loop over")
