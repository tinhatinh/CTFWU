"""Tim ham buoc cua chuoi OTP: trong 48 cach ket hop hash/nap/input, cai nao tai dien cac ma.

Chay:  python analysis/chain_model_scan.py

Cac ma lay ra tu transcript duoc coi la bang chung. Voi moi mo hinh buoc, kiem xem
step^k(ma A) co trung voi ma B (cho phep lech mot o tu) voi k = 1..7 hay khong.
Mo hinh RFC 1760/2289 (hash 8 byte tho) bi loai; chi co MD5 tren chuoi hex la tai
dien duoc day chuoi.
"""

import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import exploit as E
from Crypto.Hash import MD4

DIG = {"md4": lambda b: MD4.new(b).digest(),
       "md5": lambda b: hashlib.md5(b).digest(),
       "sha1": lambda b: hashlib.sha1(b).digest(),
       "sha256": lambda b: hashlib.sha256(b).digest()}
FOLD = {
    "xor-nua": lambda d: bytes(x ^ y for x, y in zip(d[:8], d[8:16])),
    "first8": lambda d: d[:8],
    "last8": lambda d: d[-8:],
    "sha1-word": lambda d: struct.pack("<2I", struct.unpack(">5I", d)[0] ^ struct.unpack(">5I", d)[2] ^ struct.unpack(">5I", d)[4],
                                       struct.unpack(">5I", d)[1] ^ struct.unpack(">5I", d)[3]),
}
INPUT = {
    "8-byte-tho": lambda v, ws: v.to_bytes(8, "big"),
    "chuoi-hex": lambda v, ws: ("%016x" % v).encode(),
    "chuoi-hex-HOA": lambda v, ws: ("%016X" % v).encode(),
    "6-tu-lien-que": lambda v, ws: " ".join(ws).encode(),
    "6-tu-khong-dau-cach": lambda v, ws: "".join(ws).encode(),
}


def regions(v):
    return [(v >> (53 - 11 * i)) & 0x7FF for i in range(5)] + [(v >> 2) & 0x1FF]


def diff(a, b):
    ra, rb = regions(a), regions(b)
    return [k for k in range(6) if ra[k] != rb[k]]


def to_words_safe(v):
    return E.to_words(v & ((1 << 64) - 1))


codes = E.load_codes()
valid = [(i + 1, E.from_words(c)) for i, c in enumerate(codes)
         if all(w in E.W2I for w in c)]
print("ma dung duoc 6 tu (lam bang chung):", [i for i, _ in valid])

hits = []
COMBOS = []
for an, dg in DIG.items():
    dl = len(dg(b"x"))
    for fn, fo in FOLD.items():
        if fn == "sha1-word":
            if dl != 20:
                continue
        elif dl < 16:
            continue
        for inn, conv in INPUT.items():
            COMBOS.append((an, fn, inn, dg, fo, conv))

for an, fn, inn, dg, fo, conv in COMBOS:
    for a, va in valid:
        for b, vb in valid:
            if a == b:
                continue
            v = va
            ws = codes[a - 1]
            for k in range(1, 8):
                v = int.from_bytes(fo(dg(conv(v, ws))), "big") & ((1 << 64) - 1)
                ws = to_words_safe(v)
                d = diff(v, vb)
                if len(d) <= 1:
                    hits.append((an, fn, inn, a, b, k, d))
print("so ket hop hash/nap/input da thu:", len(COMBOS))
for h in hits:
    print("  KHOP  step^%d(Code%d) ~ Code%d  lech=%s   [%s / %s / %s]" % (h[5], h[3], h[4], h[6], h[0], h[1], h[2]))
print("tong so kieu khop:", len(hits))
print("mo hinh RFC (8 byte tho):", [h for h in hits if h[2] == "8-byte-tho"] or "khong co")

if hits:
    an, fn, inn = hits[0][:3]
    dg, fo, conv = DIG[an], FOLD[fn], INPUT[inn]
    print("\n=== dung mo hinh %s/%s/%s, suy lai ma 1 va ma 2 tu ma 3 ===" % (an, fn, inn))
    v = dict(valid)[3]
    for target in (2, 1):
        v = int.from_bytes(fo(dg(conv(v, to_words_safe(v)))), "big")
        got = to_words_safe(v)
        print("  Code %d suy ra  %s" % (target, " ".join(got)))
        print("  Code %d nghe     %s   (o tu lech: %s)"
              % (target, " ".join(codes[target - 1]),
                 " ".join("%d:%s->%s" % (k + 1, codes[target - 1][k], got[k])
                          for k in range(6) if codes[target - 1][k] != got[k])))
