#!/usr/bin/env python3
"""Last fork in the jam model: does the verdict die on cookie BYTES or on cookie COUNT?

`collide.py` proved the trigger is a property of the jar, not of the recipe: 300 ingredients
sharing one name (34.5 KB recipe, one ~115 B cookie) seal normally, while 138 distinct
48-char names (15.9 KB of cookies) do not. But 48-char names keep count and bytes glued
together, so two causes are still indistinguishable:

  (a) the header block passes Node's 16384 B  -> transport, nothing can ever stamp that batch;
  (b) the app/worker refuses when the jar holds too many ENTRIES -> the header is tiny, so a
      second reviewer (a browser like the inspector) COULD stamp it, which is precisely the
      shape "the Chief is a very busy robot" needs.

Short distinct names separate them: 160 cookies of ~10 B is ~1.6 KB, one tenth of the header
budget, but more entries than the 138 that killed the big-named batch. Plus a 300-name batch
to sit above any count limit (a real tab showed Chrome keeps only ~170 entries per host, so
this also probes where the worker's jar actually caps), and matching byte-only controls. A
`reviewed` + empty seal here is the first evidence of an application-level escalation state.
"""
import re
import sys
import time

from cc import new_baker

VAL = "x"


def log(*a):
    sys.stdout.buffer.write(("[%s] " % time.strftime("%H:%M:%S") + " ".join(str(x) for x in a)
                             + "\n").encode("utf-8", "replace"))
    sys.stdout.buffer.flush()


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


CASES = []
for n in (160, 240, 300):
    CASES.append(("short-%d" % n, [{"name": "s%03d" % i, "value": VAL} for i in range(n)]))
for n in (160, 300):
    CASES.append(("mid-%d" % n, [{"name": "m%03d" % i + "z" * 20, "value": VAL * 8} for i in range(n)]))
CASES.append(("bytes-only-138-long", [{"name": ("b%03d" % i).ljust(48, "z"), "value": "x" * 64}
                                      for i in range(138)]))
CASES.append(("count-only-170-tiny", [{"name": "t%03d" % i, "value": "1"} for i in range(170)]))

u, c, _ = new_baker("qt")
log("user %s" % u)
ids = []
for label, ings in CASES:
    jar_bytes = sum(len(i["name"]) + len(i["value"]) + 2 for i in ings)
    code, out, dt = c.post("/api/recipe", {"title": label, "ingredients": ings})
    rid = out.get("id") if isinstance(out, dict) else None
    if not rid:
        log("  %-20s save -> %s %s" % (label, code, str(out)[:60]))
        continue
    log("  %-20s %s n=%-4d if-all-stored=%7dB" % (label, rid[:8], len(ings), jar_bytes))
    ids.append((label, rid, jar_bytes, len(ings)))
    time.sleep(0.4)

for label, rid, jb, cnt in ids:
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
    log("  %-20s n=%-4d jar<=%7dB -> %-9s %s" % (label, cnt, jb, stt, seal))
    if seal not in ("standard", "NONE"):
        code, page, _ = c.get("/recipe/%s" % rid)
        fl = re.findall(r"sun\{[^{}\r\n]{1,200}\}", str(page))
        log("      !!! %s -> %r %s" % (label, seal, fl))
        if fl:
            open("../flag.txt", "w", encoding="utf-8").write(fl[0] + "\n")
    elif seal == "NONE":
        log("      ^ unsealed: if the jar stayed under 16 KB this is an APP-side rule, and the")
        log("        batch is stampable by a lean or small-header reviewer")
log("done")
