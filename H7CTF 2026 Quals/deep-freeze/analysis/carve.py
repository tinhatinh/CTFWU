"""Carve the plaintext PDF around a known hit and dump heap context near the filename."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lime  # noqa: E402  (analysis/lime.py)

DUMP = sys.argv[1]
OUT = os.path.dirname(os.path.abspath(DUMP))
secs = lime.sections(DUMP)
f = open(DUMP, "rb")


def read_va(va, ln):
    fo = lime.file_off_of(secs, va)
    if fo is None:
        return b""
    f.seek(fo)
    return f.read(ln)


# 1) locate %PDF- before the token hit at 0x10b021cd7
hit = 0x10b021cd7
back = read_va(hit - 0x1200, 0x1200 + 0x1200)
i = back.rfind(b"%PDF-")
print("PDF header offset relative to hit:", i - 0x1200 if i >= 0 else "not found in window")
if i >= 0:
    body = read_va(hit - 0x1200 + i, 4096)
    end = body.find(b"%%EOF")
    pdf = body[: end + 5] if end > 0 else body
    dest = os.path.join(OUT, "memory_plain.pdf")
    open(dest, "wb").write(pdf)
    print(f"[+] wrote {dest} ({len(pdf)} bytes)")
    txt = b" ".join(re.findall(rb"\((.*?)\)\s*Tj", pdf))
    print("    text ops:", txt[:200])
    m = re.search(rb"[A-Za-z0-9_]{2,10}\{[^{}]{1,90}\}", pdf)
    print("    flag inside carved PDF:", m.group().decode() if m else "none")

# 2) heap context near the filename string
va2 = 0x10261f020
ctx = read_va(va2 - 0x40, 0x200)
print(f"\n=== heap around 0x{va2:x} (hex) ===")
for off in range(0, len(ctx), 32):
    row = ctx[off: off + 32]
    print(f"  0x{va2 - 0x40 + off:x}  {row.hex(' ')}")
    print(f"                {''.join(chr(c) if 32 <= c < 127 else '.' for c in row)}")
