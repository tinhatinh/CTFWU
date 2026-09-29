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
    return raw[:12], bytes((x ^ k[i % 8]) ^ 0x20 for i, x in enumerate(raw[12:]))


def s(t, p):
    n = t[p]
    return n, t[p + 1:p + 1 + n]


def walk(name):
    hdr, t = body(name)
    print("==== %s  hdr=%s  size=%d  body=%d" % (
        name, hdr.hex(" "), struct.unpack_from("<I", hdr, 8)[0], len(t)))
    p = 0
    while p < len(t):
        ty = t[p]
        if ty == 0x01:                        # character
            v = struct.unpack_from("<I", t, p + 1)[0]
            n, nm = s(t, p + 5)
            print("  %04x CHAR type=01 u32=%d name='%s'  extra=%s" %
                  (p, v, nm.decode('latin1'), t[p + 6 + n:p + 6 + n + 24].hex(" ")))
            p += 6 + n + 18
        elif ty == 0x10:                      # item
            idx, a, b = t[p + 1], t[p + 2], t[p + 3]
            nl, nm = s(t, p + 4)
            dl = struct.unpack_from("<H", t, p + 5 + nl)[0]
            ds = t[p + 7 + nl:p + 7 + nl + dl]
            print("  %04x ITEM idx=%2d a=%d b=%d name='%s' desc='%s'" %
                  (p, idx, a, b, nm.decode('latin1'), ds.decode('latin1')))
            p += 7 + nl + dl
        elif ty in (0x02, 0x03, 0x04):        # journal / location
            q = p + 1
            fields = []
            while t[q] == 0x00:
                fields.append(0)
                q += 1
            il, ident = s(t, q)
            q += 1 + il
            dl = struct.unpack_from("<H", t, q)[0]
            q += 2
            txt = t[q:q + dl]
            print("  %04x REC%02d zeros=%d id='%s'(%d) len=%d text='%s'" %
                  (p, ty, len(fields), ident.decode('latin1'), il, dl,
                   txt.decode('latin1')))
            p = q + dl
        else:
            print("  %04x ?? type=%02x  next32=%s" % (p, ty, t[p:p + 32].hex(" ")))
            break


for n in ("sample1", "sample2", "sample3", "team"):
    walk(n)
    print()
