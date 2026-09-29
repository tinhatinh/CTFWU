import sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

NAMES = ("sample1", "sample2", "sample3", "team")


def decode(b):
    return bytes((c + 0x20 if c < 0x20 else c) for c in b)


for n in NAMES:
    p = open("analysis/%s.pt" % n, "rb").read()
    d = decode(p)
    print("=====", n)
    # a "string" in decoded space: >=4 chars of [A-Za-z ,'.\-&:]
    for m in re.finditer(rb"[A-Za-z][A-Za-z .,'\-]{6,}", d):
        s = m.start()
        L = m.end() - s
        if L < 8:
            continue
        prev = p[max(0, s - 6):s]
        print("  str@%4d len%3d prev=%s  dec=%r  b-0x20=%s b&0x1f=%s" % (
            s, L, prev.hex(" "),
            d[s:min(s + 18, m.end())],
            [(c - 0x20) for c in prev],
            [c & 0x1F for c in prev]))
