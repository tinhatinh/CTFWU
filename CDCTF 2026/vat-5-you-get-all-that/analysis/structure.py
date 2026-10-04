"""Phan tich cau truc 17 word: vi tri nao mang thong tin, bang chu cai nao duoc dung.
Chay: python analysis/structure.py
"""
from pathlib import Path

TXT = Path("files/cred_call_transcript.txt")
LETTERS = set("abcdefghijklmnopqrstuvwxyz")

raw = TXT.read_text()
payload = raw.split(":")[-1]                      # moi word nam sau dau ':' cuoi
words = [w.strip(".").lower() for w in payload.split()]
words = [w for w in words if len(w) == 5 and w.isalpha()]
print(f"word      : {len(words)} x {sorted(set(len(w) for w in words))} chu cai")
print(f"first word: {words[0]}   last word: {words[-1]}")
print(f"anchors   : [0][0]='{words[0][0]}' [-1][-1]='{words[-1][-1]}'")

pos = list(zip(*words))
for i, p in enumerate(pos):
    s = sorted(set(p))
    pat = "".join("V" if c in "aeiouy" else "C" for c in p[0])
    print(f"pos {i}: {''.join(s):26s} distinct={len(s):2d}  pattern={pat}")

used = set("".join(words))
print(f"used      : {''.join(sorted(used))}")
print(f"missing   : {''.join(sorted(LETTERS - used))}")
print(f"vowels    : {''.join(sorted(used & set('aeiouy')))}  -> radix 6")
print(f"consonants: {''.join(sorted(used & (LETTERS - set('aeiouy'))))} -> radix 17 (16 + 'x')")
print(f"letters   : {len(used)} (6 vow + 15 cons dung thuc te)")
print(f"bytes     : (rounds-1)*2 + 1 = {(len(words)-1)*2+1}   [rounds = len/2+1]")
