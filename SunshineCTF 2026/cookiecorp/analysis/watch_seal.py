#!/usr/bin/env python3
"""Watcher: submit a batch and poll until something seals it.

Right now nothing seals at all - two batches sat `queued` for 10+ minutes, while the
previous session measured a worker sealing in 6.5-20s. Either the shared queue is
backed up or the inspector changed. This script keeps a batch of its own under watch and
records the exact moment a seal appears and at which level, so the routing question
(does the Chief ever come?) is answered with a timestamp instead of a guess.
"""
import json
import re
import sys
import time

from cc import Client, new_baker, save, submit

BUDGET_S = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
POLL_S = 45


def w(s):
    line = "[%s] %s\n" % (time.strftime("%H:%M:%S"), s)
    sys.stdout.buffer.write(line.encode("utf-8", "replace"))
    sys.stdout.flush()


u, c, r = new_baker("wt")
w("watcher user %s" % u)
code, rec, dt = save(c, "watched batch", [{"name": "moon_sugar", "value": "1"}])
rid = rec["id"]
w("recipe %s submit=%s" % (rid, submit(c, rid)[1]))

t0 = time.time()
last = None
while time.time() - t0 < BUDGET_S:
    time.sleep(POLL_S)
    code, page, dt = c.get("/review/%s" % rid)
    txt = page if isinstance(page, str) else json.dumps(page)
    status = re.findall(r"queued|reviewing|reviewed|draft", txt)
    seal = re.findall(r"(?i)golden|chief|standard|sealed", txt)
    flag = re.findall(r"sun\{[^{}\r\n]{1,160}\}", txt)
    sig = (tuple(status[-2:]), tuple(seal), bool(flag))
    if sig != last:
        w("t=%4.0fs status=%s seal=%s flag=%s" % (time.time() - t0, status[-2:], seal, flag))
        last = sig
    if flag:
        open("../flag.txt", "w", encoding="utf-8").write(flag[0] + "\n")
        w("FLAG FOUND: %s" % flag[0])
        break
    if re.search(r"seal[\"']?\s*[:=]\s*[\"']?(chief|gold)", txt, re.I):
        w("seal appeared: %r" % txt[max(0, txt.lower().find("seal") - 80):txt.lower().find("seal") + 200])
w("done, elapsed %.0fs" % (time.time() - t0))
