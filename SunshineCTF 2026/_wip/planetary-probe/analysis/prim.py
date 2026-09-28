from oracle import ask

T = [
    ("LIKE works", "(SELECT 'abc') LIKE 'a%'"),
    ("LIKE upper vs lower", "(SELECT 'PostgreSQL') LIKE '%ostgre%'"),
    ("LIKE exact", "(SELECT 'PostgreSQL') LIKE 'Postgre%'"),
    ("case preserved A=A", "(SELECT 'A')='A'"),
    ("case A=a", "(SELECT 'A')='a'"),
    ("lower() fn", "(SELECT lower('ABC'))='abc'"),
    ("LOWER() fn", "(SELECT LOWER('ABC'))='abc'"),
    ("length()", "(SELECT length('abc'))=3"),
    ("unicode()", "(SELECT unicode('A'))=65"),
    ("ascii()", "(SELECT ascii('A'))=65"),
    ("substr cmp <", "(SELECT substr('abc',1,1))<'b'"),
    ("substr cmp >", "(SELECT substr('abc',3,1))>'b'"),
    ("ilike", "(SELECT 'PostgreSQL') ILIKE '%ostgre%'"),
    ("version ilike", "(SELECT version()) ILIKE '%postgre%'"),
    ("infoschema tables cnt", "(SELECT COUNT(*) FROM information_schema.tables)>0"),
    ("infoschema public", "(SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public')>0"),
    ("pgtables count", "(SELECT COUNT(*) FROM pg_tables)>0"),
    ("server_version", "(SELECT current_setting('server_version'))<>''"),
    ("cast int", "(SELECT 1::text)='1'"),
    ("md5", "(SELECT md5('a'))='0cc175b9c0f1b6a831c399e269772661'"),
]

for name, expr in T:
    try:
        print("%-22s %s" % (name, ask(expr)))
    except SystemExit as e:
        print("%-22s ERR %s" % (name, e))
