# Tacocat - Misc

**Flag:** `cdctf{I_really_rea11y_1ik3_th3_tac0b311_classic_crunchy_taco3}` · **Points:** 500 · **Author:** alex
**Files:** `fat_tacocat.png` (578053 B, sha256 `11fe22d62e5f8a1fee9cb0d9cdc04efd6d66b20ea860aeb58351bf5b69e1f07f`)

## Challenge

The card gives one image of an orange cat holding two tacos, plus the hint "what you could ever want
that's extra or say, in addition to the classic crunchy tacobell taco". The keywords are `extra` and
`in addition to`: the data to find is appended on top of whatever the image viewer shows.

## Initial analysis

`file` reports a PNG, 1244x700 RGBA non-interlaced, 578053 bytes. Walking the chunks, the image ends at
`IEND` offset 459177 and 118876 bytes follow it. Right before that `IEND` sits a private 4-byte chunk
named `deBG` with a 16-character hex payload `0E0EE52B90EDBA88`.

Two anomalies set the direction: `deBG` is not part of the PNG spec, and the 118876-byte tail is 20% of
the file. The tail opens with `0A 00 00 00 0D 49 48 44 52`, that is a newline, then a 13-byte `IHDR`
chunk (width `0x04ED` = 1261) with the 8-byte PNG signature missing. Without the signature, tools that
scan magic bytes see nothing.

## Ruled out

1. **Stego inside the visible image**: all 56 `IDAT` chunks of the first image have valid CRC, decode to
   the cat photo, and show no LSB anomaly. Ruled out, the payload is in the second file.
2. **An archive or another container appended at the end**: scanning the tail for `PK\x03\x04`,
   `\x1f\x8b`, `7zXZ`, `Rar!`, `\xff\xd8\xff` yields 6 hits for `\x1f\x8b`, all of them inside the
   compressed `IDAT` stream, i.e. coincidence. Ruled out.
3. **`deBG` as a key or checksum**: XOR of the two payloads `0E0EE52B90EDBA88` and `2E1D19437C4E9802`
   gives `2013FC68ECA1228A`, not ASCII, and no ciphertext block exists anywhere to decrypt. Ruled out,
   it is an author label.
4. **The trailing string "Extra data is no fun!!"**: 80 bytes of plain ASCII that literally claim extra
   data is no fun, which contradicts the hint on the card. Ruled out, it is bait.

## Exploit chain

**Step 1 - Recover the second PNG.** Walk the chunks, take the offset just past the first image's `IEND`,
find the first `IHDR` in the tail and prepend the 8-byte signature. The rebuilt file has 19 chunks, all
CRCs valid, IHDR = 1261x1403 depth 8 colortype 6.

```python
appended = data[end:]                      # end = offset where the first image's IEND finishes
i = appended.find(b"\x00\x00\x00\rIHDR")
hidden = b"\x89PNG\r\n\x1a\n" + appended[i:]
```

**Step 2 - Read the alpha channel.** Decode `IDAT`, unfilter all five filter types, and every non
transparent pixel turns out to have RGB = `0,0,0`: the image is only a mask. The strokes live entirely in
the alpha byte, so inverting that channel into a grayscale image makes them readable.

```python
idat = b"".join(hidden[o + 8:o + 8 + l] for o, t, l in inner if t == "IDAT")
px = unfilter(zlib.decompress(idat), w, h)
alpha = bytes(px[i * 4 + 3] for i in range(w * h))
write_gray("analysis/alpha_read.png", w, h, bytes(255 - v for v in alpha))
```

The result is one drawn taco at the top and four handwritten lines under it, ink spanning y=28 to y=1056.

**Step 3 - Tell `l` from `1`.** The four lines form one leetspeak sentence, but this handwriting font
makes the letter `l` and the digit `1` nearly identical, while measuring stroke width in the bottom 12%
of each glyph separates them cleanly:

```text
  dong 0 're[l][l]y'       base=19   -> chu l (mong deu)
  dong 1 're[a][1][1]y'    base=39   -> so 1 (co chan ngang)
  dong 1 're[a][1][1]y'    base=41   -> so 1 (co chan ngang)
  dong 1 '[1]ik3'          base=93   -> so 1 (co chan ngang)
  dong 2 'tac0b3[1][1]'    base=56   -> so 1 (co chan ngang)
  dong 2 'tac0b3[1][1]'    base=60   -> so 1 (co chan ngang)
  dong 2 'c[l]assic'       base=19   -> chu l (mong deu)
  glyph sau '{'            top=71 stem=19 base=71  -> 'I' HOA
```

`l` is a thin bar 19-23 px wide, uniform from top to bottom. `1` has a diagonal flag at the apex and a
horizontal foot, so its lowest ink run is as wide as the whole glyph. The character after `{` carries
serifs on both ends (71 px) over a 19 px stem, which makes it a capital `I`, not `l`. The `0` in `tac0b3`
is slashed, confirming a digit.

The four lines, read left to right:

```text
cdctf{I_really_re
a11y_1ik3_th3_tac0b3
11_classic_crunchy_
taco3}
```

**Step 4 - Verify.** Joining the lines leaves no character over: `re` + `a11y` = `rea11y`, and
`tac0b3` + `11` = `tac0b311`. Every character falls inside the flag alphabet (`A-Za-z0-9_{}`), the brace
pair closes exactly once at the end, and the ink occupies two contiguous y bands with no line skipped.

## Flag

```bash
python exploit.py files/fat_tacocat.png
```

```text
== noi dung doc tu alpha_read.png ==
  dong 0: cdctf{I_really_re
  dong 1: a11y_1ik3_th3_tac0b3
  dong 2: 11_classic_crunchy_
  dong 3: taco3}

FLAG: cdctf{I_really_rea11y_1ik3_th3_tac0b311_classic_crunchy_taco3}
```

## Reproduce

```bash
python exploit.py files/fat_tacocat.png
```

The script writes `analysis/hidden.png` and `analysis/alpha_read.png`, prints the stroke measurement
table and saves `flag.txt`. The text itself still has to be read off `analysis/alpha_read.png`; the
script only pre-computes the `l`/`1` classification so nobody has to guess.
