"""Doi chieu bo code six-word S/Key voi RFC 2289 Appendix C, va sang loc checksum.

Chay:  python analysis/skey_kat.py

Phan 1: phan 27 vector trong analysis/rfc2289_test_vectors.txt (bang hex <-> sau tu,
cho MD4/MD5/SHA1 voi pass phrase + seed + count). Chung minh cach nap 64 bit, cach
lay chu thuong hoa tu bo tu dien 2048 tu va 2 bit checksum la dung RFC.
Phan 2: dung cach dong goi vua chot de kiem tung ma nghe duoc trong audio. Ma nao le
2 bit checksum cua tu cuoi thi co the dung lam mask 64 bit khi thong ke wordlist.
"""

import hashlib
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import exploit as E
from Crypto.Hash import MD4

HERE = os.path.dirname(os.path.abspath(__file__))


def digest(b, alg):
    if alg == "md4":
        return MD4.new(b).digest()
    return {"md5": hashlib.md5, "sha1": hashlib.sha1}[alg](b).digest()


def fold(d, alg):
    if alg == "sha1":
        w = struct.unpack(">5I", d)
        return struct.pack("<2I", w[0] ^ w[2] ^ w[4], w[1] ^ w[3])
    return bytes(x ^ y for x, y in zip(d[:8], d[8:16]))


def otp(alg, seed, phrase, count):
    v = fold(digest((seed.lower() + phrase).encode(), alg), alg)
    for _ in range(count):
        v = fold(digest(v, alg), alg)
    return int.from_bytes(v, "big")


def parse_vectors(path):
    txt = open(path, encoding="utf-8", errors="replace").read()
    txt = txt[txt.index("MD4 ENCODINGS"):]
    end = txt.find("Appendix D")
    if end > 0:
        txt = txt[:end]
    rows, alg, pending = [], None, None
    for line in txt.splitlines():
        m = re.match(r"^(MD4|MD5|SHA1) ENCODINGS", line)
        if m:
            alg = m.group(1).lower()
            continue
        m = re.match(r"^(.+?) (?P<seed>\S+) +(?P<cnt>\d+) +(?P<hex>[0-9A-F]{4}(?: [0-9A-F]{4}){3})\s*$", line)
        if m:
            pending = (alg, m.group(1).rstrip(), m.group("seed"), int(m.group("cnt")),
                       m.group("hex").replace(" ", ""))
            continue
        m = re.match(r"^\s*(?P<w>[A-Z]{1,4}(?: [A-Z]{1,4}){5})\s*$", line)
        if m and pending:
            rows.append(pending + (m.group("w").split(),))
            pending = None
    return rows


print("=== Phan 1: RFC 2289 Appendix C ===")
rows = parse_vectors(os.path.join(HERE, "rfc2289_test_vectors.txt"))
bad = 0
for alg, phrase, seed, cnt, hexv, ws in rows:
    v = otp(alg, seed, phrase, cnt)
    ok = ("%016X" % v == hexv) and (E.to_words(v) == ws)
    bad += not ok
    if not ok:
        print("  LECH %-18r seed=%-8r %s cnt=%2d  want %s %s | got %016X %s"
              % (phrase, seed, alg, cnt, hexv, " ".join(ws), v, " ".join(E.to_words(v))))
print("  %d/%d vector khop ca hex lan sau tu (MD4/MD5/SHA1)" % (len(rows) - bad, len(rows)))

print("\n=== Phan 2: kiem kieu dong goi 64 bit <-> sau tu ===")
for alg, phrase, seed, cnt, hexv, ws in rows[:3]:
    v = int.from_bytes(bytes.fromhex(hexv), "big")
    print("  %016X -> %s   (RFC: %s)  %s"
          % (v, " ".join(E.to_words(v)), " ".join(ws), "khop" if E.to_words(v) == ws else "LECH"))
print("  tu dien: %d tu, ngan nhat %d dai nhat %d ky tu"
      % (len(E.WORDS), min(len(w) for w in E.WORDS), max(len(w) for w in E.WORDS)))

print("\n=== Phan 3: checksum cua tung ma nghe duoc trong audio ===")
codes = E.load_codes()
for i, c in enumerate(codes, 1):
    miss = [w for w in c if w not in E.W2I]
    if miss:
        print("Code %d  %-40s  ngoai tu dien: %s" % (i, " ".join(c), " ".join(miss)))
        continue
    v = E.from_words(c)
    exp = E.to_words(v)
    print("Code %d  %-40s  checksum -> %-40s %s"
          % (i, " ".join(c), " ".join(exp), "hop le" if exp == c else ("LECH o %d" %
              [k for k in range(6) if exp[k] != c[k]][0])))
