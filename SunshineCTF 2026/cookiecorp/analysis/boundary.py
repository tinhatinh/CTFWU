#!/usr/bin/env python3
"""Pin the inspector's header budget exactly, to confirm whose limit we are hitting.

115 bytes per max-length ingredient, the bot's own `session`+`role` add ~85 B, and Node's
default --max-http-header-size is 16384, which predicts the first failing count at 142
(142*115+85 = 16415 > 16384 >= 16300 = 141*115+85). If the measured boundary lands on
141/142, the verdict request is dying in Node and the worker really does bypass nginx
(my own client is refused by nginx at ~8 KB). If it lands somewhere else, the model is
wrong and so is everything built on it.
"""
import re
import sys
import time

from cc import new_baker

NAME = lambda i: ("i%03d" % i) + "z" * 43
VAL = "x" * 64
PER = 115


def log(*a):
    sys.stdout.buffer.write(("[%s] " % time.strftime("%H:%M:%S") + " ".join(str(x) for x in a)
                             + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def state(c, rid):
    code, dash, dt = c.get("/dashboard")
    blk = re.search(r"<tr>(?:(?!</tr>).)*?%s(?:(?!</tr>).)*?</tr>" % rid, dash or "", re.S)
    if not blk:
        return "?", "?"
    b = blk.group(0)
    st = re.search(r'class="pill (\w+)">(\w+)</span>', b)
    tail = " ".join(re.sub(r"<[^>]+>", " ", b.split("</span>")[-1]).split())
    return (st.group(2) if st else "?", "NONE" if "&mdash;" in tail else
            ("standard" if "standard" in tail else tail[:24]))


u, c, _ = new_baker("bd")
log("user", u)
ids = {}
for n in [139, 140, 141, 142, 143]:
    code, out, dt = c.post("/api/recipe", {"title": "b%d" % n,
                                           "ingredients": [{"name": NAME(i), "value": VAL}
                                                           for i in range(n)]})
    ids[n] = out["id"]
    log("n=%d %s predict cookie bytes=%d" % (n, out["id"][:8], n * PER + 85))
    time.sleep(0.4)
for n, rid in ids.items():
    for k in range(12):
        code, out, dt = c.post("/api/recipe/%s/submit" % rid, {})
        if isinstance(out, dict) and out.get("ok"):
            break
        time.sleep(8)
    st = seal = "?"
    for k in range(16):
        time.sleep(5)
        st, seal = state(c, rid)
        if st == "reviewed":
            break
    log("n=%-4d %-8s -> %-9s %s" % (n, rid[:8], st, seal))
log("expected boundary from Node 16384 B: first jam at n=142")
