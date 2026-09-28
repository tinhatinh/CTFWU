#!/usr/bin/env python3
"""Print the Seal column for every batch we left in the DB.

Escalation, if it exists, is measured in hours, so this is the "come back and look" tool:
it logs into every recorded account and reports which batches are still `reviewed` with an
empty seal, which got stamped, and whether any of them turned `chief` (with the flag).
"""
import json
import re
import sys

from cc import Client

STATE = "../files/watch_targets.json"
EXTRA = sys.argv[1:]  # extra usernames to check, e.g. of1726 sz3576


def rows(c):
    code, dash, dt = c.get("/dashboard")
    if code != 200:
        return None
    out = {}
    for b in re.finditer(r"<tr>(.*?)</tr>", dash, re.S):
        bb = b.group(0)
        rid = re.search(r"/recipe/([0-9a-f]{24})", bb)
        if not rid:
            continue
        st = re.search(r'class="pill (\w+)">(\w+)</span>', bb)
        tail = " ".join(re.sub(r"<[^>]+>", " ", bb.split("</span>")[-1]).split())
        title = re.search(r"<td>\s*([^<]*?)\s*</td>", bb)
        out[rid.group(1)] = {"title": (title.group(1) if title else "")[:28],
                             "status": st.group(2) if st else "?",
                             "seal": ("NONE" if "&mdash;" in tail else
                                      ("standard" if "standard" in tail else tail[:24]))}
    return out, dash


data = {}
try:
    data = json.load(open(STATE, encoding="utf-8"))
except Exception as ex:
    sys.stdout.buffer.write(("no %s yet (%r)\n" % (STATE, ex)).encode())

users = list(data) + EXTRA
interesting = []
for u in users:
    pw = (data.get(u) or {}).get("password", "Passw0rd!")
    c = Client()
    code, out, dt = c.post("/login", {"username": u, "password": pw})
    if code != 200:
        sys.stdout.buffer.write(("%-10s login %s\n" % (u, code)).encode())
        continue
    st, dash = rows(c)
    if st is None:
        continue
    for rid, v in sorted(st.items(), key=lambda kv: kv[1]["title"]):
        mark = "  <<<" if v["seal"] not in ("standard", "NONE", "?") else ""
        sys.stdout.buffer.write(("%-10s %-28s %s %8s %s %s\n" % (u, v["title"], rid, v["status"],
                                                                 v["seal"], mark)).encode("utf-8", "replace"))
        if v["seal"] not in ("standard", "NONE"):
            interesting.append((u, rid, v))
    # The Seal column is the only honest oracle. A `sun{...}` string anywhere else is almost
    # certainly one of my own batch titles (shapes.py planted `sun{test}`), so a flag is
    # accepted only from the golden block: <div class="seal gold">...<div class="flag">
    for u_, rid, v in [x for x in interesting if x[0] == u]:
        code, page, _ = c.get("/recipe/%s" % rid)
        gold = re.search(r'class="seal gold"[\s\S]{0,600}?class="flag"[^>]*>\s*([^<]+)', str(page))
        sys.stdout.buffer.write(("   %s seal=%r gold=%s\n" % (rid, v["seal"],
                                 gold.group(1).strip() if gold else None)).encode("utf-8", "replace"))
        if gold:
            open("../flag.txt", "w", encoding="utf-8").write(gold.group(1).strip() + "\n")
            sys.stdout.buffer.write(("!!! GOLDEN FLAG %s\n" % gold.group(1).strip()).encode())
    if any(v["status"] == "reviewing" for v in st.values()):
        sys.stdout.buffer.write(("   (something is being reviewed in this account right now)\n").encode())
sys.stdout.buffer.write(("%d batches are neither standard nor unsealed\n" % len(interesting)).encode())
