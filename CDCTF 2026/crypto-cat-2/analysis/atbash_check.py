"""Kiem tra nhanh hai gia thuyet bi loai cho crypto-cat-2.

1. Atbash o murc ky tu: ban ma la chuoi HEX, ky tu '0'-'9' bi doi thanh
   chr(219-ord(c)) nam ngoai bang ASCII in duoc (vi du '9' -> 0xa2).
2. Atbash o murc byte = phep bit-NOT (0xff ^ b): dem so byte con trong ASCII.
"""

from pathlib import Path

text = Path("files/ciphertext.txt").read_text().strip()
data = bytes.fromhex("".join(text.split()))

bad = [(c, 219 - ord(c)) for c in sorted(set(text)) if c.isdigit()]
print("[*] atbash murc ky tu tren chuoi hex, cac chu so bi dao thanh:")
print("    " + ", ".join(f"{c!r} -> {v:#04x}" for c, v in bad))

not_bytes = bytes(0xff ^ b for b in data)
inside = sum(1 for b in not_bytes if 0x20 <= b < 0x7F)
print(f"[*] bit-NOT toan bo 45 byte: {inside}/45 byte roi vung 0x20-0x7e")
print(f"    6 byte dau: {' '.join(f'{b:#04x}' for b in not_bytes[:6])}")

# positive control: the same counter must report 45/45 for the key that works,
# otherwise "11/45" would not prove anything.
for k in (0x8F,):
    cnt = sum(1 for b in (x ^ k for x in data) if 0x20 <= b < 0x7F)
    print(f"[*] doi chieu (positive control) k={k:#04x}: {cnt}/45 byte in duoc, "
          f"chua {sum(1 for b in (x ^ k for x in data) if b == 0x0A)} ky tu xuong dong")

