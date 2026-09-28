"""Existence battery: one query per hypothesis, retry-on-False, spaced."""
import time
from oracle import ask

GAP = 2.5


def ask2(expr, tries=2):
    for _ in range(tries):
        if ask(expr):
            return True
        time.sleep(GAP)
    return False


def exists(tbl):
    return "(SELECT COUNT(*) FROM %s)>=0" % tbl


T = [
    ("row_to_json usable", "(SELECT row_to_json(p)::text FROM planets p LIMIT 1) LIKE '{%"),
    ("non-public tables>0", "(SELECT COUNT(*) FROM pg_tables WHERE schemaname NOT IN ('pg_catalog','information_schema'))>2"),
    ("any tbl >2", "(SELECT COUNT(*) FROM pg_tables)>2"),
    ("classif schema tbl", "(SELECT COUNT(*) FROM pg_tables WHERE schemaname NOT IN ('public','pg_catalog','information_schema'))>0"),
    ("mat view?", "(SELECT COUNT(*) FROM pg_matviews)>0"),
    ("view exists", "(SELECT COUNT(*) FROM pg_views WHERE schemaname='public')>0"),
]
for n in ["probe", "probes", "stars", "vault", "world", "worlds", "alien", "signal", "signals",
          "telemetry", "classified", "restricted", "hidden", "secret", "secrets", "flag", "flags",
          "federation", "directory", "aerial", "carrier", "needle", "broadcast", "encoded",
          "supernova", "quasar", "nebula", "blackhole", "earth", "pluto", "kepler"]:
    T.append(("table " + n, exists(n)))

for name, e in T:
    t = time.time()
    print("  %-22s %-6s (%.0fs)" % (name, ask2(e), time.time() - t), flush=True)
    time.sleep(GAP)
