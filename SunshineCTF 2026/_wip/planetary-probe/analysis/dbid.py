from oracle import ask

T = [
    ("infoschema has rows", "(SELECT COUNT(*) FROM information_schema.tables)>0"),
    ("infoschema >1000", "(SELECT COUNT(*) FROM information_schema.tables)>1000"),
    ("infoschema cols rows", "(SELECT COUNT(*) FROM information_schema.columns)>0"),
    ("planets table", "(SELECT COUNT(*) FROM planets)>0"),
    ("pg_tables", "(SELECT COUNT(*) FROM pg_tables)>0"),
    ("pg_catalog", "(SELECT COUNT(*) FROM pg_catalog.pg_tables)>0"),
    ("mysql.user", "(SELECT COUNT(*) FROM mysql.user)>0"),
    ("sys.tables", "(SELECT COUNT(*) FROM sys.tables)>0"),
    ("sqlite_master", "(SELECT COUNT(*) FROM sqlite_master)>0"),
    ("typeof(sqlite)", "(SELECT typeof(1))='integer'"),
    ("randomblob(sqlite)", "(SELECT randomblob(1)) IS NOT NULL"),
    ("gen_random_uuid(pg)", "(SELECT gen_random_uuid()) IS NOT NULL"),
    ("version() nonempty", "(SELECT version())<>''"),
    ("pg in version", "(SELECT version()) LIKE '%ostgre%'"),
    ("mysql in version", "(SELECT version()) LIKE '%MySQL%'"),
    ("maria in version", "(SELECT version()) LIKE '%Maria%'"),
    ("concat ||", "(SELECT 'a'||'b')='ab'"),
    ("substr", "(SELECT substr('abc',2,1))='b'"),
    ("substring", "(SELECT substring('abc',2,1))='b'"),
    ("lower()", "(SELECT LOWER('A'))='a'"),
    ("ascii()", "(SELECT ascii('A'))=65"),
    ("group_concat", "(SELECT GROUP_CONCAT(x) FROM (SELECT 'a' AS x))='a'"),
    ("limit 1", "(SELECT name FROM planets LIMIT 1) IS NOT NULL"),
    ("order by 1", "(SELECT COUNT(*))=1"),
    ("sleep-free timing: case", "(SELECT CASE WHEN 1=1 THEN 1 ELSE 0 END)=1"),
    ("if() mysql", "(SELECT IF(1=1,1,0))=1"),
    ("dquote ident", '(SELECT "a") IS NULL'),
]

for name, expr in T:
    try:
        print("%-24s %s" % (name, ask(expr)))
    except SystemExit as e:
        print("%-24s ERR %s" % (name, e))
