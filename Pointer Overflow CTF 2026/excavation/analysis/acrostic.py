import sys, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

KEYS = {
    "sample1": "bff366a0192308a7",
    "sample2": "8ee28d4183df8c1b",
    "sample3": "e62903e8dcf7b038",
    "team": "1337df4e77c16cc7",
}


def body(name):
    k = bytes.fromhex(KEYS[name])
    raw = open("files/%s.sav" % name, "rb").read()
    return bytes((x ^ k[i % 8]) ^ 0x20 for i, x in enumerate(raw[12:]))


def items(t):
    """Walk item records: 10 idx a b namelen name desclen(2) desc."""
    out = []
    # locate the inventory block: scan every 0x10 that is followed by a
    # plausible (idx == previous idx + 1) chain
    best = None
    for start in range(len(t)):
        if t[start] != 0x10:
            continue
        q = start
        got = []
        ok = True
        while q < len(t) and t[q] == 0x10:
            idx, a, b, nl = t[q + 1], t[q + 2], t[q + 3], t[q + 4]
            if nl == 0 or q + 5 + nl + 3 > len(t):
                ok = False
                break
            nm = t[q + 5:q + 5 + nl]
            dl = struct.unpack_from("<H", t, q + 5 + nl)[0]
            if dl == 0 or dl > 400 or q + 7 + nl + dl > len(t):
                ok = False
                break
            ds = t[q + 7 + nl:q + 7 + nl + dl]
            if not ds.endswith(b".") or b"\x00" in nm + ds[1:]:
                ok = False
                break
            got.append((idx, a, b, nm.decode('latin1'), ds.decode('latin1')))
            q += 7 + nl + dl
            if idx >= 40:
                ok = False
                break
        if not ok and len(got) < 3:
            continue
        if best is None or len(got) > len(best):
            best = got
    return best or []


for n in ("sample1", "sample2", "sample3", "team"):
    t = body(n)
    it = items(t)
    print("==== %s  %d items" % (n, len(it)))
    for idx, a, b, nm, ds in it:
        print("   idx=%2d a=%d b=%d  %-28s  %s" % (idx, a, b, nm, ds))
    print("   first-letters:", "".join(nm[0] for _, _, _, nm, _ in it))
    print("   last-letters :", "".join(nm[-1] for _, _, _, nm, _ in it))
    print("   word-initials:", "".join(w[0] for _, _, _, nm, _ in it
                                     for w in nm.replace("-", " ").split()))
