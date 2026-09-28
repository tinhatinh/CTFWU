"""Sweep every catalog name/text column for a '{' -- row-level LIKE on the app's own tables
never covered object names, comments, settings or rules."""
import extract as E
import threading

SPECS = [
    ("pg_class.relname", "EXISTS(SELECT 1 FROM pg_class WHERE relname LIKE '%{%')"),
    ("pg_attribute.attname", "EXISTS(SELECT 1 FROM pg_attribute WHERE attname LIKE '%{%')"),
    ("pg_proc.proname", "EXISTS(SELECT 1 FROM pg_proc WHERE proname LIKE '%{%')"),
    ("pg_namespace.nspname", "EXISTS(SELECT 1 FROM pg_namespace WHERE nspname LIKE '%{%')"),
    ("pg_type.typname", "EXISTS(SELECT 1 FROM pg_type WHERE typname LIKE '%{%')"),
    ("pg_constraint.conname", "EXISTS(SELECT 1 FROM pg_constraint WHERE conname LIKE '%{%')"),
    ("pg_trigger.tgname", "EXISTS(SELECT 1 FROM pg_trigger WHERE NOT tgisinternal AND tgname LIKE '%{%')"),
    ("pg_description", "EXISTS(SELECT 1 FROM pg_description WHERE description LIKE '%{%')"),
    ("pg_database.datname", "EXISTS(SELECT 1 FROM pg_database WHERE datname LIKE '%{%')"),
    ("pg_roles.rolname", "EXISTS(SELECT 1 FROM pg_roles WHERE rolname LIKE '%{%')"),
    ("pg_settings", "EXISTS(SELECT 1 FROM pg_settings WHERE setting::text LIKE '%{%')"),
    ("pg_file_settings", "EXISTS(SELECT 1 FROM pg_file_settings WHERE coalesce(setting,'') LIKE '%{%')"),
    ("pg_indexes", "EXISTS(SELECT 1 FROM pg_indexes WHERE indexname LIKE '%{%')"),
    ("pg_views.def", "EXISTS(SELECT 1 FROM pg_views WHERE definition LIKE '%{%')"),
    ("pg_rewrite", "EXISTS(SELECT 1 FROM pg_rewrite WHERE pg_get_ruledef(oid) LIKE '%{%')"),
    ("pg_policy", "EXISTS(SELECT 1 FROM pg_policies WHERE policyname LIKE '%{%')"),
    ("zleak any brace", "EXISTS(SELECT 1 FROM zleak WHERE v::text LIKE '%{%')"),
    ("planets any brace", "EXISTS(SELECT 1 FROM planets p WHERE p::text LIKE '%{%')"),
    ("public rel names", "(SELECT string_agg(relname,',') FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public')"),
]
res = {}


def one(k, e):
    try:
        res[k] = E.cond(e)
    except Exception as ex:
        res[k] = "EXC %s" % type(ex).__name__


if __name__ == "__main__":
    th = [threading.Thread(target=one, args=(k, e), daemon=True) for k, e in SPECS[:-1]]
    for t in th:
        t.start()
    for t in th:
        t.join(90)
    for k, _ in SPECS[:-1]:
        print("  %-24s %s" % (k, res.get(k)))
    print("  public relation names:", E.read_str(SPECS[-1][1], 200, "relnames"))
