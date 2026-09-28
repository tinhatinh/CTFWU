#!/usr/bin/env python3
"""Sweep the content rule using the app's OWN strings, including the hyphen spellings.

If there is no second robot sweeping the DB and the level is computed at stamp time, then
`chief` must follow from the recipe, and every guess we have made so far was built from
`snake_case` inventions (`moon_sugar`, `golden_seal`). The site itself writes these as
prose with hyphens and spaces: "from moon-sugar to atomic sprinkles", "Space-Age
Confectionery", "A Better Cookie for a Brighter Tomorrow!", "Orbital City, Sector 7",
"Est. 1962", and the builder pre-fills `flour=2 cups` + `atomic_sprinkles=a dash`.
Whitespace is stripped from ingredient fields, so `atomic sprinkles` can only ever reach
the jar as `atomicsprinkles` - but `atomic-sprinkles` is a legal, different cookie name
that nothing in the previous sweeps sent.

Run both directions: minimal batches that hold EXACTLY one candidate (in case the rule
checks for an exact set) and kitchen-sink batches that hold many (in case it checks for
containment).
"""
import re
import sys
import time

from cc import new_baker


def log(*a):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), " ".join(str(x) for x in a))
    sys.stdout.buffer.write((line + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def I(n, v="1"):
    return {"name": n, "value": v}


CASES = [
    ("moon-sugar", "moon-sugar cookie", [I("moon-sugar", "1cup")]),
    ("moon-sugar-default", "moon sugar", [I("moon-sugar", "a handful")]),
    ("atomic-hyphen", "atomic sprinkles", [I("atomic-sprinkles", "a dash")]),
    ("both-exact", "space-age cookie", [I("flour", "2 cups"), I("atomic-sprinkles", "a dash"),
                                        I("moon-sugar", "1 cup")]),
    ("both-underscore", "space age cookie", [I("flour", "2 cups"), I("atomic_sprinkles", "a dash"),
                                            I("moon_sugar", "1 cup")]),
    ("golden-hyphen", "golden seal please", [I("golden-seal", "chief")]),
    ("chief-hyphen", "chief seal", [I("the-chief", "1"), I("head-chief", "1"), I("chief", "1")]),
    ("inspector-hyphen", "inspector", [I("quality-inspector", "1"), I("inspector", "1")]),
    ("tagline-title", "A Better Cookie for a Brighter Tomorrow!", [I("brighter-tomorrow", "1")]),
    ("sector7", "Orbital City, Sector 7", [I("orbital-city", "sector-7"), I("sector-7", "7"),
                                           I("est-1962", "1962")]),
    ("spaceage", "Space-Age Confectionery", [I("space-age-confectionery", "1"),
                                             I("space_age", "confectionery")]),
    ("mixer-on", "mixer", [I("fabrication-mixer", "on"), I("mixer", "full"), I("inspection", "full")]),
    ("legend-42", "legendary", [I("legendary", "legendary"), I("answer", "42"), I("golden", "golden")]),
    ("kitchen-sink", "the legendary space-age golden cookie of orbital city sector 7",
     [I("moon-sugar", "1cup"), I("moon_sugar", "1cup"), I("atomic-sprinkles", "a dash"),
      I("atomicsprinkles", "adash"), I("stardust", "2tbsp"), I("golden-seal", "1"),
      I("golden_seal", "1"), I("chief", "1"), I("the-chief", "1"), I("flour", "2 cups"),
      I("sugar", "2 cups"), I("butter", "cold"), I("eggs", "2"), I("cocoa", "1cup"),
      I("1962", "1"), I("sector7", "7"), I("orbital-city", "7"), I("brighter-tomorrow", "1"),
      I("space-age", "1"), I("legendary", "true"), I("golden", "true"), I("seal", "chief"),
      I("level", "chief"), I("approval", "chief"), I("verdict", "chief"), I("baker", "chief"),
      I("robot", "chief"), I("chief-robot", "1"), I("grand-prize", "1"), I("cookie", "cookie")]),
    ("cookiecorp-name", "CookieCorp", [I("cookie-corp", "1"), I("cookiecorp", "1"),
                                       I("company", "cookiecorp")]),
    ("badge", "Baker Badge", [I("badge", "baker"), I("passphrase", "baker")]),
]

users = []
log("=== seeding ===")
for half in (0, 1):
    u, c, r = new_baker("th")
    if not c:
        log("register failed", r)
        continue
    c.user = u
    ids = {}
    for tag, title, ings in CASES[half * 11:half * 11 + 11]:
        code, out, dt = c.post("/api/recipe", {"title": title, "ingredients": ings})
        if not (isinstance(out, dict) and out.get("id")):
            log("  %-20s save -> %s %s" % (tag, code, str(out)[:60]))
            continue
        ids[tag] = out["id"]
        time.sleep(0.3)
    users.append((u, c, ids))
    log("  user %s holds %d batches" % (u, len(ids)))

log("=== submitting, one at a time (the app serialises the worker) ===")
for u, c, ids in users:
    for tag, rid in ids.items():
        for k in range(15):
            code, out, dt = c.post("/api/recipe/%s/submit" % rid, {})
            if isinstance(out, dict) and out.get("ok"):
                break
            time.sleep(6)
        # wait for this one to settle before the next submit
        seal = ""
        for k in range(12):
            time.sleep(5)
            code, dash, dt = c.get("/dashboard")
            blk = re.search(r"<tr>(?:(?!</tr>).)*?%s(?:(?!</tr>).)*?</tr>" % rid, dash, re.S)
            if blk and 'class="pill reviewed"' in blk.group(0):
                tail = " ".join(re.sub(r"<[^>]+>", " ", blk.group(0).split("</span>")[-1]).split())
                seal = "NONE" if "&mdash;" in tail else ("standard" if "standard" in tail else tail[:30])
                break
        log("  %-20s %s" % (tag, seal))
        if seal not in ("standard", "NONE"):
            code, page, _ = c.get("/recipe/%s" % rid)
            open("../files/golden_theme_%s.html" % tag, "w", encoding="utf-8").write(str(page))
            fl = re.findall(r"sun\{[^{}\r\n]{1,200}\}", str(page))
            log("      !!! %s -> %s flag=%s" % (tag, seal, fl))
            if fl:
                open("../flag.txt", "w", encoding="utf-8").write(fl[0] + "\n")
log("=== done: any golden seal above? ===")
