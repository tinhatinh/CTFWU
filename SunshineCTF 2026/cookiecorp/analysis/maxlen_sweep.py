#!/usr/bin/env python3
"""Sweep the middle of the size space: max-length fields, but small enough to be stamped.

The deferral search (shapes.py) used short names and short values; the jam search used
max-length ones but always went past 16 KB. Nobody looked at the region in between, and an
application-side "do not stamp this, hand it to the Chief" branch could easily key on
something that only max-length ingredients have: 48-char names, 64-char values, a
`name.length === 48` check, a total-bytes budget the mixer enforces (`tray > 4096`), or a
value that looks like a number at the edge (`1e999`, `-1`, `0.1` repeated). Each batch here
is stamped by the inspector, so the result is readable in ~10 s: `standard` means no rule
fired, `reviewed` + empty seal means the app itself declined to stamp, which is the only
honest signature of a Chief queue we can produce without breaking the transport.
"""
import re
import sys
import time

from cc import new_baker

FULL_NAME = lambda i: ("m%03d" % i) + "z" * 42      # exactly 48
FULL_VAL = "x" * 64                                  # exactly 64
EDGE = ["1e999", "-1", "0", "9" * 64, "1" + "0" * 63, " " * 0 + "x" * 64]


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


CASES = []
for n in (1, 3, 10, 30, 60, 90, 120, 130):
    CASES.append(("maxlen%03d" % n, [{"name": FULL_NAME(i), "value": FULL_VAL} for i in range(n)]))
CASES.append(("edge-values", [{"name": "e%d" % i, "value": v} for i, v in enumerate(EDGE)]))
CASES.append(("name48-value0", [{"name": FULL_NAME(i), "value": ""} for i in range(60)]))
CASES.append(("name1-value64", [{"name": "v%03d" % i, "value": FULL_VAL} for i in range(120)]))
CASES.append(("same-name-max", [{"name": "a" * 48, "value": FULL_VAL}]))

u, c, _ = new_baker("mx")
log("user", u)
made = 0
for tag, ings in CASES:
    if made >= 8:
        u, c, _ = new_baker("mx")
        made = 0
        log("new user %s" % u)
    kb = sum(len(i["name"]) + len(i["value"]) + 2 for i in ings)
    code, out, dt = c.post("/api/recipe", {"title": tag, "ingredients": ings})
    rid = out.get("id") if isinstance(out, dict) else None
    if not rid:
        log("  %-16s save -> %s %s" % (tag, code, str(out)[:70]))
        continue
    made += 1
    for k in range(12):
        sc, so, _ = c.post("/api/recipe/%s/submit" % rid, {})
        if isinstance(so, dict) and so.get("ok"):
            break
        time.sleep(8)
    st = seal = "?"
    for k in range(16):
        time.sleep(5)
        st, seal = state(c, rid)
        if st == "reviewed":
            break
    log("  %-16s %s %3d ing %6dB -> %-9s %s" % (tag, rid[:8], len(ings), kb, st, seal))
    if seal == "NONE":
        log("      !!! app declined to stamp %s (not a transport jam: %d bytes)" % (tag, kb))
        code, page, _ = c.get("/recipe/%s" % rid)
        open("../files/defer_%s.html" % tag, "w", encoding="utf-8").write(str(page))
log("done")
