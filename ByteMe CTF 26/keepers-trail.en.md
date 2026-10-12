---
title: "The Keeper's Trail"
category: "OSINT"
tags: ["lsb-stego", "qr-decode", "encrypted-pdf", "aes-cbc", "artifact-chain"]
solve_date: "2026-10-09"
language: "en"
---

# The Keeper's Trail

**Flag:** `OWASP{YouAreTheOne}`
**Artifacts:** `Letter.png`, `key-qr.png`, `keeper.pdf`, `hidden.txt` and saved intermediate results.

## Challenge

The entire description present in the run directory is `Question.md` (356 B, CRLF line endings). Its text, verbatim:

```text
An old keeper has been waiting a long time for someone worthy. He's left something behind — a letter. Everything else is inside it.

Read it carefully. Nothing here is just decoration.

Any encryption you encounter uses AES-256 in CBC mode, with keys derived via SHA-256. The algorithm was never the puzzle.
```

The file ends with the flag-format block `OWASP{...}`.

The available record reproduces QR → password → PDF. Extraction of the QR from the original image and the AES decryption remain incomplete.

## Analysis

### Artifact inventory

```text
Question.md        356 B  challenge text
Letter.png     6,894,219 B  PNG 1245 x 2245 RGBA
lsb-0.bin        349,379 B  bit plane 0
lsb-1.bin        349,379 B  bit plane 1
lsb-2.bin        349,379 B  bit plane 2
lsb-3.bin        349,379 B  bit plane 3
lsb-012.bin    1,048,135 B  planes 0+1+2
lsb-0123.bin   1,397,513 B  planes 0+1+2+3
layer1.txt           311 B  34 x 34 palette PNG behind leading junk bytes
key-qr.png           295 B  PNG 162 x 162, mode P
pdf-password.txt      12 B  FewerReturns
keeper.pdf     2,681,960 B  %PDF-1.4, encrypted
keeper-page.png 5,313,846 B  rendered PDF page
pdf-text.txt       782 B  letter text
hidden.txt         642 B  0x + 640 hex chars
flag.txt            19 B  OWASP{YouAreTheOne}
```

The LSB dump sizes match the bit-plane arithmetic of the source image exactly:

```python
n = 1245 * 2245
print(n, [(k * n + 7) // 8 for k in (1, 3, 4)])
```

```text
2795025 [349379, 1048135, 1397513]
```

The four files `lsb-0..3.bin` are each exactly 349,379 B = one bit plane of 2,795,025 pixels; `lsb-012.bin` and `lsb-0123.bin` match 3 and 4 planes respectively. By size, they are extraction output from `Letter.png`. This is a size check, not a content check: the bytes of each plane were not regenerated from the image while writing this.

### Locked-in values

`flag.txt` is 19 B and holds `OWASP{YouAreTheOne}` with no trailing newline byte (19 characters = 19 bytes). `pdf-password.txt` likewise has no trailing byte: 12 characters = 12 bytes, value `FewerReturns`.

The string `YouAreTheOne` occurs only in `flag.txt`. Searching it in `Letter.png`, `keeper.pdf`, `keeper-page.png`, all six LSB files, `key-qr.png` and `layer1.txt` returns 0 hits — the flag is not stored in cleartext in any other artifact of the directory.

## Solution

### The QR opens the PDF

`key-qr.png` is a 162×162 image. Decoded with OpenCV:

```console
$ python - <<'PY'
> import cv2
> im = cv2.imread("key-qr.png")
> print(cv2.QRCodeDetector().detectAndDecode(im)[0])
> PY
FewerReturns
```

The decoded string is 12 characters and matches `pdf-password.txt` exactly. This link therefore has a representing file at both ends: the QR at one end, the password at the other.

Using that password on `keeper.pdf`:

```console
$ python - <<'PY'
> from pypdf import PdfReader
> r = PdfReader("keeper.pdf")
> print("encrypted:", r.is_encrypted, "| decrypt ->", r.decrypt("FewerReturns"))
> print("pages:", len(r.pages))
> PY
encrypted: True | decrypt -> 2
pages: 1
```

`decrypt()` returns a success value and text extraction works. Freshly extracted text is 757 characters, `pdf-text.txt` stores 759 characters (782 raw bytes because of CRLF endings): the same letter, differing by 2 characters of trailing whitespace, not byte-identical after normalisation.

### The Keeper's letter

`pdf-text.txt` holds the letter. The lines that point onward:

```text
Go back to where this journey
started. Not for another door, but for
what you overlooked the first time,
waiting since before you arrived.
There are three that matter. I already
signed one of them into what I gave
you. The other two are close by,
indistinguishable from everything
around them, until you know what
makes a number worth choosing.
Alone, none of them are the stone.
Only together, multiplied as one, do
they become what you came here for.
```

And the closing block, copied verbatim including the hex fragments:

```text
Regards, 
3061
0x107e61259ce9189f0674f5b9e040e69a8
8083053327714a65be2f59558614f045e666
f383b1ae60ebb2cdbaf98143f37
```

`hidden.txt` is a hex blob: `0x` then 640 characters, i.e. exactly 320 bytes, and `320 % 16 == 0` — 20 blocks of 16 bytes, a shape consistent with AES-CBC as `Question.md` describes.

Comparing it with the fragments in the letter:

- The first fragment of the letter, after dropping the `0x` prefix, is 33 hex characters long; its first 32 characters (`107e61259ce9189f0674f5b9e040e69a` = 16 bytes) are precisely the beginning of `hidden.txt`. The 33rd character in the letter is `8`, where `hidden.txt` continues with `a`. In other words the first line at the end of the letter is a cut of the ciphertext block, with one nibble too many.
- The other two fragments (`8083053327714a65be2f59558614f045e666`, `f383b1ae60ebb2cdbaf98143f37`) do not occur in `hidden.txt`, not even their leading 16 bytes.
- The number `3061` does not occur in `hidden.txt`.

The three numbers the letter refers to therefore do not assemble into the ciphertext in any way readable from the files; they belong to the key-derivation step, and that step has no artifact.

### Reproduction limits

The record does not preserve how `key-qr.png` was extracted from `Letter.png`, where `hidden.txt` came from, or the AES-256-CBC key and IV. The flag is saved in `flag.txt`, but decrypting `hidden.txt` into it has not been reproduced.

## Result

```text
OWASP{YouAreTheOne}
```

The flag comes from the saved `flag.txt`. The commands verify the QR, PDF password and letter text; they do not reproduce the final AES decryption.

## Reproduce

These steps run entirely on the artifacts in the run directory and need Python 3 with `opencv-python` (`cv2`), `pypdf` and `Pillow`:

```console
$ cd "C:/Users/Administrator/Downloads/ctf-skills-main/ctf-skills-main/work/keepers-trail/"
$ python -c "from PIL import Image; print(Image.open('Letter.png').size, Image.open('Letter.png').mode)"
(1245, 2245) RGBA
$ python -c "import cv2; print(cv2.QRCodeDetector().detectAndDecode(cv2.imread('key-qr.png'))[0])"
FewerReturns
$ python -c "
from pypdf import PdfReader
r = PdfReader('keeper.pdf')
print(r.is_encrypted, r.decrypt('FewerReturns'), len(r.pages))
print(''.join(p.extract_text() or '' for p in r.pages)[:60])
"
```

The original-image QR extraction and AES key/IV derivation cannot yet be reproduced.

`OWASP{YouAreTheOne}` is a value recorded in `flag.txt`, not the output of the commands above.
