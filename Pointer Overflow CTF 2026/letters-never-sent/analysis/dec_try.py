CT = "PXYWN{2.612.QNTOXCK6E7DKGMKC.WK4KK6MPPPRJGOFZZI66EISSED}"
KEY = "ELAPSE"


def beaufort(c, k):          # P = K - C
    return (k - c) % 26


def vigenere(c, k):          # P = C - K
    return (c - k) % 26


def variant(c, k):           # P = C + K
    return (c + k) % 26


OPS = {"beaufort": beaufort, "vigenere": vigenere, "variant": variant}


def letters_only(ct, key, op, advance_on_all=False):
    out, ki = [], 0
    for ch in ct:
        if ch.isalpha():
            o = op(ord(ch.upper()) - 65, ord(key[ki % len(key)]) - 65)
            out.append(chr(o + 65))
            if not advance_on_all:
                ki += 1
        else:
            out.append(ch)
            if advance_on_all:
                ki += 1
    return "".join(out)


ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789."


def extended(ct, key, mode):
    out, ki = [], 0
    for ch in ct:
        if ch in ALPHA:
            c, k = ALPHA.index(ch), ALPHA.index(key[ki % len(key)])
            if mode == "beaufort":
                p = (k - c) % len(ALPHA)
            elif mode == "vigenere":
                p = (c - k) % len(ALPHA)
            else:
                p = (c + k) % len(ALPHA)
            out.append(ALPHA[p])
            ki += 1
        else:
            out.append(ch)
    return "".join(out)


for name, op in OPS.items():
    for adv in (False, True):
        print(f"{name:9s} adv_all={adv!s:5s} :", letters_only(CT, KEY, op, adv))
for name in ("beaufort", "vigenere", "variant"):
    print(f"ext36 {name:9s}   :", extended(CT, KEY, name))
