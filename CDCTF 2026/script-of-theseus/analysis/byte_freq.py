#!/usr/bin/env python3
"""Kham pha byte: so sanh tan suat byte hai ban, kiem tra BOM va vi tri byte lech."""
from collections import Counter
from pathlib import Path

FILES = sorted((Path(__file__).resolve().parent.parent / "files").glob("*.py"))
for path in FILES:
    data = path.read_bytes()
    print(f"{path.name}: {len(data)} byte, LF(0x0A) {data.count(0x0A)}, CR(0x0D) {data.count(0x0D)}, "
          f"8 byte dau {data[:8].hex(' ')}")
    print(f"  BOM: {'co' if data[:3] in (b'\xef\xbb\xbf', b'\xff\xfe', b'\xfe\xff') else 'khong'}"
          f" | phi ASCII in duoc: {sum(1 for v in data if 32 <= v < 127)}/{len(data)}")

a, b = (p.read_bytes() for p in FILES)
print("\nThem o ban sau :", {f"0x{k:02X}": v for k, v in sorted((Counter(b) - Counter(a)).items())})
print("Mat di o ban sau:", {f"0x{k:02X}": v for k, v in sorted((Counter(a) - Counter(b)).items())})

cr = [i for i, v in enumerate(b) if v == 0x0D]
print(f"\nVi tri 0x0D: {[hex(i) for i in cr]}")
print(f"Duoc 0x0A di kem: {sum(1 for i in cr if b[i + 1:i + 2] == b'\x0a')}/{len(cr)}")
print(f"Xoa het 0x0D -> khop ban goc: {bytes(v for v in b if v != 0x0D) == a}")
print(b[:0x1a].hex(" "))
