"""Giai ma chrono-i: Vigenere so (Gronsfeld) voi key = chu so cua moc thoi gian.

Crib CSSCTF -> ESUITO cho ra dung [2,0,2,6,0,9] = 4 chu so dau cua "20260921..."
nen key la chuoi "20260921143507" (ngay + gio cua message), lap lai.

An kiem: dem vi tri chi tren chu cai, hay tren moi ky tu.
"""

import re

KEY = "20260921143507"
CT = "ESUITO{gwfvb_xejqnf_nimgt_b_whhrlv}"


def dec(text, key, letters_only):
    out, i = [], 0
    for ch in text:
        if ch.isalpha():
            k = int(key[i % len(key)])
            i += 1
            base = 65 if ch.isupper() else 97
            out.append(chr((ord(ch) - base - k) % 26 + base))
        else:
            out.append(ch)
            if not letters_only:
                i += 1
    return "".join(out)


for lo in (True, False):
    pt = dec(CT, KEY, lo)
    body = re.sub(r"[^a-z]", " ", pt.split("{", 1)[1]).split()
    print("letters_only=%-5s -> %s" % (lo, pt))
    print("   mau tu      :", [len(w) for w in body])
