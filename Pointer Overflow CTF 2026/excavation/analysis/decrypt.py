import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

KEYS = {
    "sample1": "bff366a0192308a7",
    "sample2": "8ee28d4183df8c1b",
    "sample3": "e62903e8dcf7b038",
    "team": "1337df4e77c16cc7",
}

for n, kh in KEYS.items():
    k = bytes.fromhex(kh)
    raw = open("files/%s.sav" % n, "rb").read()
    body = raw[12:]
    pt = bytes(x ^ k[i % 8] for i, x in enumerate(body))
    open("analysis/%s.pt" % n, "wb").write(pt)
    print(n, "hdr", raw[:12].hex(" "), "len", len(raw), "pt len", len(pt))
