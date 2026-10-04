"""Triage crypto-cat-3: vi sao loai moi khoa tuan hoan (Vigenere/Beaufort/variant/autokey).

Ba phep doc lap:
  A. IC theo chieu dai khoa: Vigenere that thi IC theo cot nhay len manh o dung L.
  B. khoang cach cua cac tu lap lai: cung plaintext o hai vi tri phai cach nhau boi
     boi so cua L (trong chi so dung cho khoa).
  C. crib "cdctf" o 5 chu dau: sinh kieu stream K[i]; mot L chi song neu moi cap
     crib cung cot cho cung K.
"""

import collections

S = open("files/ciphertext.txt", encoding="utf-8").read().strip().lower()
A = ord("a")
L = [c for c in S if c.isalpha()]
C = [ord(c) - A for c in L]
NL = len(L)

# --- A. IC theo period
print("== A. index of coincidence theo chieu dai khoa ==")
for p in range(1, 21):
    cols = [C[i::p] for i in range(p)]
    ics = [sum(v * (v - 1) for v in collections.Counter(col).values())
           / (len(col) * (len(col) - 1)) for col in cols if len(col) > 1]
    print(f"  L={p:2d} avgIC={sum(ics) / len(ics):.4f}")

# --- B. tu lap lai
toks = S.split()
lpos, apos, lc, ac = [], [], 0, 0
for t in toks:
    lpos.append(lc); apos.append(ac)
    lc += sum(c.isalpha() for c in t); ac += len(t) + 1
rep = [t for t in dict.fromkeys(toks) if toks.count(t) > 1]
d_l, d_a = [], []
for t in rep:
    i, j = [k for k, x in enumerate(toks) if x == t]
    d_l.append(lpos[j] - lpos[i]); d_a.append(apos[j] - apos[i])
    print(f"== B. {t!r} lap lai: {lpos[j] - lpos[i]} chu cai, {apos[j] - apos[i]} ky tu")
import math
g_l = math.gcd(*d_l); g_a = math.gcd(*d_a)
print(f"   gcd theo chu cai = {g_l} (chi L=1 thoat), gcd theo ky tu = {g_a} -> L chia {g_a}")

# --- C. crib cdctf + crib doi nhap "can't"/"we'll"
cribs = [(i, ord(p) - A) for i, p in zip(range(5), "cdctf")]
# vi tri chu cai cua "sub'stitution" va "sufficient" khi doc nhu tu co dau nhay
w2 = lpos[toks.index("nvk'npepvpehg")]
w11 = lpos[toks.index("nv'llewergp")]
contr = [(w2 + k, ord(p) - A) for k, p in zip(range(4), "cant")] + \
        [(w11 + k, ord(p) - A) for k, p in zip(range(4), "well")]
OPS = {
    "vigenere": lambda c, p: (c - p) % 26,
    "variant": lambda c, p: (p - c) % 26,
    "beaufort": lambda c, p: (c + p) % 26,
}
print("== C. crib 'cdctf' + 'cant'/'well' (chi so theo chu cai) ==")
for name, f in OPS.items():
    k = {i: f(C[i], p) for i, p in cribs + contr}
    k1 = {i: f(C[i], p) for i, p in cribs}
    ok = [p for p in range(1, 21)
          if all(k[i] == k[j] for i in k for j in k if i % p == j % p)]
    ok_crib = [p for p in range(1, 21)
               if all(k1[i] == k1[j] for i in k1 for j in k1 if i % p == j % p)]
    print(f"  {name:9s} crib cdctf thoi: {ok_crib}   cong them doi nhap: {ok}")
    print(f"    K[0..4] = {[chr(A + v) for v in (k1[i] for i, _ in cribs)]}, "
          f"K[{w2}..{w2+3}] = {[chr(A + k[w2 + i]) for i in range(4)]}")

# --- C2. same cribs but the key advances on EVERY character (spaces, braces, quotes)
pos = []           # absolute index of every letter
p = 0
for ch in S:
    if ch.isalpha():
        pos.append(p)
    p += 1
print("== C2. cung crib nhung khoa chay theo ky tu (chen ca space/ngoac/nhay) ==")
for name, f in OPS.items():
    kc = {}
    for i, (_, pl) in enumerate(cribs):
        kc[pos[i]] = f(C[i], pl)
    for j, pch in enumerate("cant"):
        kc[pos[w2 + j]] = f(C[w2 + j], ord(pch) - A)
    for j, pch in enumerate("well"):
        kc[pos[w11 + j]] = f(C[w11 + j], ord(pch) - A)
    ok = sorted(p for p in range(1, 21)
                if all(kc[i] == kc[j] for i in kc for j in kc if i % p == j % p))
    alive = [p for p in ok if 10 % p == 0]
    print(f"  {name:9s} L song (1..20): {ok}")
    print(f"    giao voi uoc cua 10 (phep thu B theo ky tu): {alive}")


# --- autokey
print("== D. autokey (primer + plaintext / + ciphertext) ==")
CRIB = [ord(c) - A for c in "cdctf"]
hits = 0
for m in range(1, 9):
    for src in ("plain", "cipher"):
        for name, f in OPS.items():
            P = list(CRIB) + [0] * (NL - len(CRIB))
            for i in range(len(CRIB), NL):
                prev = P[i - m] if src == "plain" and i - m >= 0 else (
                    C[i - m] if src == "cipher" and i - m >= 0 else 0)
                P[i] = f(C[i], prev) if name != "beaufort" else (prev - C[i]) % 26
            txt = "".join(chr(A + v) for v in P)
            good = sum(w in txt for w in (" the ", "and ", "cipher", "can", "tion"))
            if good >= 2:
                hits += 1
                print(f"  m={m} {src}/{name}: {txt[:60]}...")
print(f"  so ung vien autokey co >1 tu Anh phon: {hits}")
