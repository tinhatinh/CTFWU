CT = "PXYWN{2.612.QNTOXCK6E7DKGMKC.WK4KK6MPPPRJGOFZZI66EISSED}"

letters = [c for c in CT if c.isalpha()]
idx = {i: n for i, n in enumerate([c for c in CT if c.isalpha()])}
L = letters
print("letters:", "".join(L), len(L))

KNOWN = "ELAPS"          # key[0..4] forced by the POCTF prefix
# Beaufort: P = K - C  ->  K = P + C
def key_from(crib, pos):
    return [(ord(crib[j]) - 65 + ord(L[pos + j]) - 65) % 26 for j in range(len(crib))]

CRIBS = ["BEAUFORT", "RECIPROCAL", "TABLEAU", "WHITMORE", "ADMIRAL", "LIMINAL",
         "SPIRIT", "MEDIUM", "FREQUENCY", "DISCRETION", "MEMBRANE", "SEALED",
         "UNSPOKEN", "ELAPSED", "ELAPSES", "ELAPSE", "NEVERSENT", "LETTERS",
         "POCTF", "SECRET", "GHOST", "DEPARTED", "NOVEMBER", "OCCULT",
         "SOCIETY", "CORRESPONDENT", "FAITHFUL", "HYDROGRAPHER", "KCB",
         "SEALEDSECOND", "TWICE", "ALDER", "LILY", "ANCHOR", "POPPY", "SWAN"]

best = []
for w in CRIBS:
    for pos in range(0, len(L) - len(w) + 1):
        ks = key_from(w, pos)
        for period in range(5, 26):
            ok = True
            for j, k in enumerate(ks):
                g = (pos + j) % period
                if g < len(KNOWN) and KNOWN[g] != chr(k + 65):
                    ok = False
                    break
            if not ok:
                continue
            # build partial key of this period and check no conflicts inside crib
            slot = {}
            conflict = False
            for j, k in enumerate(ks):
                g = (pos + j) % period
                if g in slot and slot[g] != k:
                    conflict = True
                    break
                slot[g] = k
            if conflict:
                continue
            key = "".join(chr(slot.get(i, -1) + 65) if i in slot else "?" for i in range(period))
            best.append((period, pos, w, key))

seen = set()
for period, pos, w, key in sorted(best):
    t = (period, key, w)
    if t in seen:
        continue
    seen.add(t)
    print(f"period={period:2d} crib={w:12s} at {pos:2d} key={key}")
