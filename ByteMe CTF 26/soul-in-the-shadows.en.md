---
title: "Soul in the Shadows"
category: "Steg"
tags: ["png", "lsb", "zsteg", "crib-drag", "repeating-key-xor"]
solve_date: "2026-10-09"
language: "en"
---

# Soul in the Shadows

**Flag:** `OWASP{the_soul_was_here}`
**Artifact:** `Soul_in_the_Shadows_Player - 247 TANISHK MALGE.zip` (2,109,285 B), unpacking to `archive.png` (2,108,924 B, md5 `bd736a6daca2e56f7ead89a7cbe5976e`) and `challenge.txt` (116 B). Author: Pratik Jadhav.

## Challenge

Easy, 100 points. The archive holds one PNG and one hint text file. `challenge.txt` (116 B) says nothing more than:

```text
Soul in the Shadows

There is more to this image than what you can see.

Recover the flag.

Flag format: OWASP{...}
```

The image is a dark scene with no directly readable text; the payload sits in the low bits of the pixel data and is XOR-ed with a short repeating key.

## Analysis

### Container layer

`unzip -l` shows two members, `archive.png` 2,108,924 B and `challenge.txt` 116 B, both under a top-level folder. `file` reports a 1000×1180, 8-bit RGB PNG, no palette and no alpha channel.

The chunk layout rules out any append-style carrier:

```text
IHDR, 3 x tEXt, 33 x IDAT, IEND, 0 trailing bytes
```

Nothing follows `IEND`, so searching for a second embedded file or a nested zip at the tail of the image is a dead end from the start. The three `tEXt` chunks carry these keyword/value pairs:

```text
Title   : Forgotten Record
Author  : Archives
Comment : Some things are left behind on Vormir.
```

`Comment` is the only content hint (`Vormir`); `Title` and `Author` are just labels.

### LSB scan

A self-written LSB reader over the RGB planes and a brightness-ordered scan both return `hits: 0` on this image. `zsteg -a` finds the payload under the `b1,rgb,lsb,xy` configuration — lowest bit of the three channels, walked x then y:

```text
The archive was checked twice.
GRgTHhkpIic3Ejo9IyMNOighCSc3Pywv
The records showed nothing unusual.
::END::
```

The base64 line inside that block is the payload; the two English sentences around it and the `::END::` marker are decoys carrying no data.

## Solution

Decoding the base64 line gives exactly 24 bytes:

```text
1918131e1929222737123a3d23230d3a28210927373f2c2f
```

24 is a typical length for an `OWASP{...}` flag, and the first six bytes of every flag in this event are `OWASP{`. crib-dragging that known prefix over the 24 bytes yields a repeating string:

```python
import base64
ct = base64.b64decode("GRgTHhkpIic3Ejo9IyMNOighCSc3Pywv")
known = b"OWASP{"
key = bytes(c ^ k for c, k in zip(ct, known))
print(len(ct), ct.hex())
print(key)
print(bytes(c ^ key[i % len(key)] for i, c in enumerate(ct)))
```

```text
24 1918131e1929222737123a3d23230d3a28210927373f2c2f
b'VORMIR'
b'OWASP{the_soul_was_here}'
```

The key is `VORMIR` (6 bytes, cycling 4 times over the 24-byte ciphertext). The 6-byte period is assumed from the known prefix only; what supports that assumption is that the remaining 18 bytes decrypt to printable text with a well-formed `OWASP{...}` closing brace, not the guess itself. A 6-byte crib does not prove the key is unique.

The second, independent pass over the same file recorded:

```text
derived key from OWASP{ prefix: b'VORMIR'
byte offset of message in LSB stream: 0
```

`byte offset ... : 0` means the payload starts at the very first low bit of the stream with no leading padding, and both passes land on the same flag.

## Result

```text
OWASP{the_soul_was_here}
```

The flag was extracted from the artifact itself (LSB plane `b1,rgb,lsb,xy`) and decrypted with a known-plaintext derived XOR key, then re-checked by an independent pass over the same file. No submission response recorded.

## Reproduce

Requirements: `unzip`, `file`, Python 3 (`base64`), `zsteg` (a build supporting `-a`).

```console
$ unzip "Soul_in_the_Shadows_Player - 247 TANISHK MALGE.zip"
$ file archive.png
$ md5sum archive.png
$ zsteg -a archive.png
```

Confirm the chunk layout and the byte count after `IEND` with `list_chunks.py`:

```python
import struct, collections
d = open("archive.png", "rb").read()
i, order, texts = 8, [], []
while i + 8 <= len(d):
    ln = struct.unpack(">I", d[i:i+4])[0]
    t = d[i+4:i+8].decode("latin1")
    order.append(t)
    if t == "tEXt":
        texts.append(d[i+8:i+8+ln].decode("latin1"))
    i += 12 + ln
print(collections.Counter(order), "trailing:", len(d) - i)
for x in texts:
    print(x)
```

That script only walks chunk headers of known length and never decodes pixels. The base64 line printed by `zsteg -a` is the sole input to the Python block in the Solution section, so the rest of the solve does not touch the image again.
