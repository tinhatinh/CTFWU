---
title: "Hidden Patronus"
category: "Forensics"
tags: ["steganography", "png-height", "openstego", "zero-width", "stegzero"]
solve_date: "2026-10-10T18:11:00+07:00"
language: "en"
points: 916
---

# Hidden Patronus

**Flag:** `kBxAc{z3r0_w1dth_1nv1s1bl3_1nf0_3xp3ct0_p4tr0num_8f7e6d5c4b3a2f1e0d9c}`  
**Author:** HydraRoot  
**Attachments:** `flag.bmp`, `harry_potter.png`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `flag.bmp` | 1,920,054 | `de0012f017e8e15ad41229f12d4a3896541557d934ea413a6e1cf2394d3bd9f8` |
| `harry_potter.png` | 1,303,660 | `c976a144d1423312fa090d9b4142eb4d602d4a688c26272f4cc09863c251ac9d` |
| `flag.txt` (extracted) | 675 | `26bdc459890f34f2e691764f9e0bffb58e9f13798e3b641ab737061805289810` |

## Challenge

> Harry Potter is everyones favourite right? isn't it?

We are given two image files: `harry_potter.png` and `flag.bmp`. The objective is to uncover the secret passphrase hidden inside the clue image, extract the intermediate container embedded in the carrier bitmap, and decode the nested steganography layer to recover the flag in `kBxAc{...}` format.

## Analysis

### Layer 1 — Cropped PNG height in `harry_potter.png`

Inspecting `harry_potter.png`:
- Declared dimensions: 1200 × 1100 pixels, 24-bit RGB (3 bytes/pixel).
- Decompressing the concatenated `IDAT` chunks with `zlib` yields **4,321,200 bytes** of scanline data.

For a 24-bit RGB PNG of width 1200, each scanline requires:
$$\text{Scanline} = 1\text{ (filter byte)} + 1200 \times 3 = 3,601\text{ bytes}$$

If the height were genuinely 1100 pixels, the expected decompressed size would be:
$$1100 \times 3,601 = 3,961,100\text{ bytes}$$

The difference corresponds to exactly 100 extra scanlines:
$$\frac{4,321,200 - 3,961,100}{3,601} = \frac{360,100}{3,601} = 100\text{ rows}$$

The challenge author altered the height field in the `IHDR` chunk from `0x04B0` (1200) to `0x044C` (1100) and recomputed the CRC to fool standard image viewers. Restoring the height value to `1200` and updating the `IHDR` CRC reveals the bottom 100 scanlines ($y = 1100$ to $1200$). Across the newly visible strip at the bottom, white text reads:

```text
KEY:Expecto_Patronum
```

The recovered passphrase is: `Expecto_Patronum`.

### Layer 2 — Extracting `flag.txt` from `flag.bmp` with OpenStego

The image `flag.bmp` is an 800 × 800 pixel 24-bit RGB bitmap (1,920,054 bytes). Sequential LSB analysis and `steghide` fail because the carrier employs a non-linear pseudo-random embedding scheme.

Using **OpenStego** with the `RandomLSB` algorithm and passphrase `Expecto_Patronum`:

```bash
java -jar openstego.jar extract -a RandomLSB -sf flag.bmp -xd . -p Expecto_Patronum
```

This extracts `flag.txt` (675 bytes).

### Layer 3 — StegZero Unicode zero-width decoding in `flag.txt`

Opening `flag.txt` in a plain text editor shows only the cover sentence:

```text
Bruhh Your Hardwork Failed
```

Despite its short visible length (28 characters), the file size is 675 bytes. Byte inspection reveals **216 invisible Unicode characters** interleaved among the visible characters, drawn from exactly eight code points:

| Code point | Unicode Name | 3-bit Value |
|---|---|---:|
| `U+200B` | ZERO WIDTH SPACE | `000` |
| `U+200C` | ZERO WIDTH NON-JOINER | `001` |
| `U+200D` | ZERO WIDTH JOINER | `010` |
| `U+2060` | WORD JOINER | `011` |
| `U+2062` | INVISIBLE TIMES | `100` |
| `U+2063` | INVISIBLE SEPARATOR | `101` |
| `U+2064` | INVISIBLE PLUS | `110` |
| `U+FEFF` | ZERO WIDTH NO-BREAK SPACE | `111` |

This character alphabet and framing correspond to the **StegZero** protocol (an open-source zero-width steganography implementation by Clevis22):
- Each zero-width character encodes 3 bits ($216 \times 3 = 648$ bits $= 81$ bytes).
- **Header** (11 bytes / 88 bits):
  - Magic (2 bytes): `0xA55A` (42330).
  - Version (1 byte): `1` (standard, unencrypted).
  - Nonce (2 bytes): `18267` (`0x475B`).
  - Length (2 bytes): `70` (`0x0046`).
  - CRC32 (4 bytes): `0x32C22E77`.
- **Payload** (70 bytes / 560 bits): Obfuscated with a bit-level **xorshift32** PRNG initialized with:
  $$\text{seed} = ((\text{nonce} \ll 16) \mid \text{magic}) \ \& \ \text{0xFFFFFFFF}$$

De-obfuscating the 560 payload bits with the PRNG output yields bytes matching the expected CRC32 (`0x32C22E77`), which decode as the UTF-8 flag.

## Solution

The complete solution comprises three stages:

1. **Fix PNG dimensions:** Read `harry_potter.png`, set height $H = 1200$, update the `IHDR` CRC, and view the bottom strip to retrieve `Expecto_Patronum`.
2. **OpenStego extraction:** Run OpenStego RandomLSB with passphrase `Expecto_Patronum` on `flag.bmp` to obtain `flag.txt`.
3. **StegZero de-obfuscation:** Map zero-width characters in `flag.txt` to octal digits, parse the 11-byte header, and de-obfuscate the payload using xorshift32.

## Result

```text
kBxAc{z3r0_w1dth_1nv1s1bl3_1nf0_3xp3ct0_p4tr0num_8f7e6d5c4b3a2f1e0d9c}
```

## Reproduce

Run the self-contained Python script below to verify the PNG scanlines and decode `flag.txt`:

```python
import hashlib
import struct
import zlib
from pathlib import Path

# 1. Restore harry_potter.png height and detect excess scanlines
png_path = Path("harry_potter.png")
if png_path.exists():
    data = bytearray(png_path.read_bytes())
    # IHDR chunk is located at offset 12..29 (length=13 at offset 8)
    width = struct.unpack_from(">I", data, 16)[0]
    height = struct.unpack_from(">I", data, 20)[0]
    print(f"[*] Initial harry_potter.png: {width}x{height}")

    # Set height to 1200 and recompute IHDR CRC
    struct.pack_into(">I", data, 20, 1200)
    ihdr_crc = zlib.crc32(data[12:29])
    struct.pack_into(">I", data, 29, ihdr_crc)

    fixed_path = Path("harry_potter_fixed.png")
    fixed_path.write_bytes(data)
    print(f"[+] Restored {fixed_path} (1200x1200). Read bottom text: KEY:Expecto_Patronum")

# 2. Decode StegZero payload directly from flag.txt
flag_txt_path = Path("flag.txt")
if flag_txt_path.exists():
    text = flag_txt_path.read_text(encoding="utf-8")

    ZW_ALPHABET = [
        "\u200b", "\u200c", "\u200d", "\u2060",
        "\u2062", "\u2063", "\u2064", "\ufeff",
    ]
    ZW_MAP = {ch: f"{i:03b}" for i, ch in enumerate(ZW_ALPHABET)}

    bits = "".join(ZW_MAP[ch] for ch in text if ch in ZW_MAP)
    assert len(bits) >= 88, "Zero-width bitstream too short"

    header_bytes = bytes(int(bits[i:i + 8], 2) for i in range(0, 88, 8))
    magic = (header_bytes[0] << 8) | header_bytes[1]
    version = header_bytes[2]
    nonce = (header_bytes[3] << 8) | header_bytes[4]
    length = (header_bytes[5] << 8) | header_bytes[6]
    expected_crc = int.from_bytes(header_bytes[7:11], "big")

    assert magic == 0xA55A, f"Invalid StegZero magic: {hex(magic)}"
    print(f"[*] StegZero header: magic={hex(magic)}, ver={version}, nonce={nonce}, len={length}")

    def xorshift32(seed):
        x = seed & 0xFFFFFFFF
        while True:
            if x == 0:
                x = 0x9E3779B9
            x = (x ^ ((x << 13) & 0xFFFFFFFF)) & 0xFFFFFFFF
            x = (x ^ (x >> 17)) & 0xFFFFFFFF
            x = (x ^ ((x << 5) & 0xFFFFFFFF)) & 0xFFFFFFFF
            yield x

    seed = ((nonce << 16) | magic) & 0xFFFFFFFF
    rng = xorshift32(seed)

    payload_bits = bits[88:88 + length * 8]
    acc = 0
    remain = 0
    msg_bits = []
    for b in payload_bits:
        if remain == 0:
            acc = next(rng)
            remain = 32
        p = acc & 1
        acc >>= 1
        remain -= 1
        msg_bits.append(str((int(b) ^ p) & 1))

    msg_bytes = bytes(int("".join(msg_bits[i:i + 8]), 2) for i in range(0, len(msg_bits), 8))
    assert zlib.crc32(msg_bytes) == expected_crc, "Payload CRC mismatch"

    flag = msg_bytes.decode("utf-8")
    print(f"[+] Flag: {flag}")
```

OpenStego extraction command:

```bash
java -jar openstego.jar extract -a RandomLSB -sf flag.bmp -xd . -p Expecto_Patronum
```
