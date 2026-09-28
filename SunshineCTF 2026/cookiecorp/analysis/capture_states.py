#!/usr/bin/env python3
"""Read the batch page in the two states we have never captured: queued and reviewing.

Every saved page is either `draft` or `reviewed`. The stylesheet defines `.pill.queued` and
`.pill.reviewing`, so those renderings exist and we have never looked at them - and a
"forwarded to the Chief" style notice would live exactly there. Submit and re-read the pages
at 1 s intervals until the batch leaves each state, dumping the HTML verbatim.
"""
import re
import sys
import time

from cc import new_baker


def log(*a):
    sys.stdout.buffer.write(("[%s] " % time.strftime("%H:%M:%S") + " ".join(str(x) for x in a)
                             + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def status_of(c, rid):
    code, dash, dt = c.get("/dashboard")
    blk = re.search(r"<tr>(?:(?!</tr>).)*?%s(?:(?!</tr>).)*?</tr>" % rid, dash or "", re.S)
    if not blk:
        return "?"
    m = re.search(r'class="pill (\w+)">(\w+)</span>', blk.group(0))
    return m.group(2) if m else "?"


u, c, _ = new_baker("cs")
log("user", u)
for ings, tag in (([{"name": "flour", "value": "1"}], "small"),
                  ([{"name": ("q%03d" % i) + "z" * 42, "value": "x" * 64} for i in range(150)], "jam")):
    code, out, dt = c.post("/api/recipe", {"title": "capture " + tag, "ingredients": ings})
    rid = out["id"]
    c.post("/api/recipe/%s/submit" % rid, {})
    log("submitted %s %s" % (tag, rid[:8]))
    last = None
    t0 = time.time()
    while time.time() - t0 < 60:
        st = status_of(c, rid)
        if st != last:
            for path in ("/recipe/%s" % rid, "/review/%s" % rid):
                code, page, _ = c.get(path)
                fn = "../files/state_%s_%s_%s.html" % (tag, st, path.split("/")[1])
                open(fn, "w", encoding="utf-8").write(str(page))
                body = re.search(r'<div class="panel">([\s\S]*?)<h2>Ingredient Sheet', str(page))
                txt = " | ".join(" ".join(re.sub(r"<[^>]+>", " ", body.group(1)).split()).split("| ")) if body else ""
                log("   %-9s %-8s %s" % (st, path.split("/")[1], txt[:150]))
            last = st
        if st == "reviewed":
            break
        time.sleep(1)
log("done - dumps in ../files/state_*.html")
