"""Triage crypto-cat-2: kiem tra XOR/Vigenere byte nhieu khoa truoc khi dung 1 byte.

doi chieu (c = mat ma, k = khoa, p = ban tho):
  xor      p = c ^ k
  sub      p = (c - k) % 256
  add      p = (c + k) % 256
  beaufort p = (k - c) % 256
Mot khoa hop le o cot i khi MOI byte cua cot do cho p trong 0x20..0x7e.
"""

from pathlib import Path

data = bytes.fromhex("".join(Path("files/ciphertext.txt").read_text().split()))
N = len(data)
OPS = {
    "xor": lambda b, k: b ^ k,
    "sub": lambda b, k: (b - k) % 256,
    "add": lambda b, k: (b + k) % 256,
    "beaufort": lambda b, k: (k - b) % 256,
}


def col_keys(col, op, allow_ws):
    ok = set(range(0x20, 0x7F))
    if allow_ws:
        ok |= {0x09, 0x0A, 0x0D}
    return [k for k in range(256) if all(op(b, k) in ok for b in col)]


for allow_ws in (False, True):
    print(f"\n== phep ASCII {': kem tab/LF/CR' if allow_ws else ': tuyet doi 0x20-0x7e'} ==")
    for name, op in OPS.items():
        alive = []
        for L in range(1, 16):
            per = [len(col_keys(data[i::L], op, allow_ws)) for i in range(L)]
            if min(per) > 0:
                alive.append((L, per))
        print(f"  {name:9s} so chieu dai khoa con song: "
              + (", ".join(f"L={L}{per}" for L, per in alive) or "khong co"))
