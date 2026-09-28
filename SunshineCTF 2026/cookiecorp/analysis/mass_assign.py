#!/usr/bin/env python3
"""Mass-assignment the Seal column, with the dashboard table as the oracle.

The dashboard renders one row per batch with an explicit `Seal` cell ("standard" /
"&mdash;"), so any recipe field that lands in the document is directly observable
without waiting for the inspector. The previous run concluded mass assignment was dead,
but two of its assumptions are now known to be wrong: it saved with `name` (the builder
posts `title`, and neither one is honoured, so the field set is not what it guessed), and
its seal/status assertions came from the /review page, whose static text contains the
word "queued" for every batch.

Also finds the real title field, because that tells us which object the handler builds.
"""
import re
import sys
import time

from cc import Client, new_baker

FIELDS = ["seal", "level", "status", "tier", "grade", "verdict", "approved",
          "certified", "golden", "gold", "chief", "legendary", "reviewed",
          "sealLevel", "seal_level", "isChief", "is_chief", "authority", "stamp"]
SEED = {"ingredients": [{"name": "flour", "value": "1"}]}


def rows(c):
    code, dash, dt = c.get("/dashboard")
    out = []
    for m in re.finditer(r"<tr>\s*<td>(.*?)</td>\s*<td>(\d+)</td>\s*<td><span class=\"pill (\w+)\">(\w+)</span></td>\s*<td>\s*(.*?)\s*</td>", dash, re.S):
        out.append({"title": m.group(1), "ings": m.group(2), "status": m.group(4),
                    "seal": re.sub(r"<[^>]+>", "", m.group(5)).strip()})
    return dash, out


def create(c, extra):
    body = dict(SEED)
    body.update(extra)
    code, out, dt = c.post("/api/recipe", body)
    return (out.get("id") if isinstance(out, dict) else None), code, out


if __name__ == "__main__":
    def w(s):
        sys.stdout.buffer.write((str(s) + "\n").encode("utf-8", "replace")); sys.stdout.flush()

    u, c, _ = new_baker("ma")
    w("user %s" % u)

    w("=== which field names the title? ===")
    for f in ["title", "name", "batch", "label", "recipe", "subject", "batchName", "batch_name"]:
        rid, code, out = create(c, {f: "SENTINEL_" + f})
        dash, rs = rows(c)
        hit = [r for r in rs if r["title"].startswith("SENTINEL")]
        w("  %-11s id=%s -> dashboard title=%r" % (f, rid and rid[:6], hit[-1]["title"] if hit else "(untitled)"))
        if hit:
            break
        time.sleep(0.3)

    w("=== mass assignment straight into the Seal column ===")
    made = []
    for f in FIELDS:
        for val in ("chief", "gold", "golden", True):
            rid, code, out = create(c, {f: val})
            if not rid:
                w("  %-11s=%-7r -> save refused %s %r" % (f, val, code, out))
                break
            dash, rs = rows(c)
            row = next((r for r in rs if True), None)
            mine = [r for r in rs if r.get("seal") not in ("", "&mdash;", "standard", None)]
            if mine:
                w("  !!! %-12s=%-7r -> seal=%r status=%r" % (f, val, mine[0]["seal"], mine[0]["status"]))
            made.append(rid)
            time.sleep(0.25)
        if len(made) >= 10:
            break
    dash, rs = rows(c)
    w("=== final table ===")
    for r in rs:
        w("   %s" % r)
    w("=== submit one of them and re-read the seal ===")
    for rid in made[:3]:
        code, out, dt = c.post("/api/recipe/%s/submit" % rid, {})
        w("  submit %s -> %s %s" % (rid[:8], code, out))
        time.sleep(1.0)
    dash, rs = rows(c)
    for r in rs:
        w("   after submit: %s" % r)
