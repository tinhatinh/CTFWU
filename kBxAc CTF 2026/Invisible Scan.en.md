---
title: "Invisible Scan"
category: "Misc"
tags: ["ascii-art", "qr-code", "unicode-steganography", "zero-width", "bitstream"]
solve_date: "2026-10-10T17:29:00+07:00"
language: "en"
points: 159
---

# Invisible Scan

**Flag:** `kBxAc{a5(Ii_AR7_MasTER_caNv@$_h1DdEn_In_the_piXelS_oF_THE_(ODE}`  
**Author:** HydraRoot  
**Attachment:** `invisiblescan.zip`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `invisiblescan.zip` | 1,838 | `8285314728704719d663a5b98a72a7ec44f107bdb758721607db4e19ff36c736` |
| `challenge.bin` | 15,931 | `b8d275156462e6dede12f001a049e3da14ba8b1bd5d7787c45ebc37acc30ca49` |

## Challenge

> A mysterious text file contains something hidden in plain sight. Look carefully at the patterns and uncover the secret.

The archive contains only `challenge.bin`. Despite its `.bin` extension, it is pure ASCII text made of `#`, spaces, and newlines. We must reconstruct the image represented by those characters and then unpack the hidden data embedded in its QR payload.

## Initial analysis — ASCII-art QR code

Inspect the attachment:

```bash
unzip -l invisiblescan.zip
unzip -p invisiblescan.zip challenge.bin | head -n 12
```

`challenge.bin` contains **15,931 bytes**, forming **89 lines** of **178 characters** each. Hash marks occur in `##` pairs, and two spaces `  ` represent a white cell. Consequently, each line represents 89 QR modules. The 89 × 89 grid comprises an 81 × 81 QR code surrounded by a four-module quiet zone.

Render the text according to the following mapping:

- `##` → black module.
- `  ` → white module.
- Enlarge each module to 8 × 8 pixels to make decoding reliable.

Using `Pillow` to build the image and `pyzbar` to decode it gives a payload of **560 UTF-8 bytes / 212 Unicode characters**. What appears on screen is only:

```text
Congratulations! You found the flag :)
```

That is **not the flag**. The QR payload also contains non-rendering Unicode characters interleaved with the visible text.

## Hidden layer — Three bits per invisible Unicode character

There are **38 visible ASCII characters** and **174 invisible Unicode characters**, covering exactly eight different code points. Sort the code points in ascending order and assign the values 0 through 7:

| Value | Code point | Unicode name |
|---:|---|---|
| 0 | `U+200B` | ZERO WIDTH SPACE |
| 1 | `U+200C` | ZERO WIDTH NON-JOINER |
| 2 | `U+200D` | ZERO WIDTH JOINER |
| 3 | `U+2060` | WORD JOINER |
| 4 | `U+2062` | INVISIBLE TIMES |
| 5 | `U+2063` | INVISIBLE SEPARATOR |
| 6 | `U+2064` | INVISIBLE PLUS |
| 7 | `U+FEFF` | ZERO WIDTH NO-BREAK SPACE |

Preserve the invisible characters **in their original order**, ignoring printable ASCII characters. Convert each value (0–7) into a three-bit binary representation. For example, the first five invisible characters are:

```text
U+200B U+200B U+200B U+2060 U+FEFF
   0      0      0      3      7
  000    000    000    011    111
```

174 × 3 = **522 bits**, which contain **65 complete bytes** followed by two leftover `00` bits. The decoded bytes start with `00 3f`, immediately followed by an ASCII flag:

```text
\x00?kBxAc{a5(Ii_AR7_MasTER_caNv@$_h1DdEn_In_the_piXelS_oF_THE_(ODE}
```

The two-byte prefix can be skipped, or the flag can be extracted robustly using the pattern `kBxAc\{[^}]*\}`. This is a direct decode, not a guessed candidate.

## Solution — Reproducible solver

Requires Python 3, `Pillow`, `pyzbar`, and the underlying `zbar` barcode library. Install the Python packages with:

```bash
python -m pip install pillow pyzbar
```

On Linux, if the shared `zbar` library is missing, install `libzbar0` using the system package manager.

Save the following as `solve.py` next to `invisiblescan.zip`:

```python
#!/usr/bin/env python3
from zipfile import ZipFile
from PIL import Image
from pyzbar.pyzbar import decode
import re

# 1. Convert ASCII art to an 89 x 89 QR bitmap.
with ZipFile("invisiblescan.zip") as zf:
    rows = zf.read("challenge.bin").decode("ascii").splitlines()

assert len(rows) == 89 and all(len(row) == 178 for row in rows)
qr = Image.new("L", (89, 89), color=255)
for y, row in enumerate(rows):
    for x in range(89):
        cell = row[2*x:2*x+2]
        assert cell in ("##", "  ")
        qr.putpixel((x, y), 0 if cell == "##" else 255)

qr = qr.resize((712, 712), Image.Resampling.NEAREST)
qr.save("invisible_scan_qr.png")
results = decode(qr)
assert results, "Could not decode ASCII-art QR code"
message = results[0].data.decode("utf-8")

# 2. Extract invisible Unicode code points from the QR message.
visible = "".join(ch for ch in message if ch.isascii())
hidden = [ch for ch in message if not ch.isascii()]
alphabet = sorted(set(hidden))
assert len(alphabet) == 8

# 3. Convert each Unicode symbol to a three-bit value (0..7).
bits = "".join(f"{alphabet.index(ch):03b}" for ch in hidden)
full_bits = len(bits) // 8 * 8  # ignore incomplete final byte
payload = bytes(int(bits[i:i+8], 2) for i in range(0, full_bits, 8))

# 4. Extract the flag from the decoded bytes.
match = re.search(rb"kBxAc\{[^}]*\}", payload)
assert match, "Flag not found"

print("QR visible:", visible)
print("Hidden characters:", len(hidden))
print("Hidden bitstream:", len(bits), "bits")
print("Decoded bytes:", len(payload))
print("Flag:", match.group().decode("ascii"))
```

Run:

```bash
python solve.py
```

Verified output against the original challenge attachment:

```text
QR visible: Congratulations! You found the flag :)
Hidden characters: 174
Hidden bitstream: 522 bits
Decoded bytes: 65
Flag: kBxAc{a5(Ii_AR7_MasTER_caNv@$_h1DdEn_In_the_piXelS_oF_THE_(ODE}
```

## Result

The challenge combines **ASCII-art QR encoding** with **three-bit Unicode steganography inside the QR message**. Stopping at the visually readable congratulatory message misses the real payload.

```text
kBxAc{a5(Ii_AR7_MasTER_caNv@$_h1DdEn_In_the_piXelS_oF_THE_(ODE}
```
