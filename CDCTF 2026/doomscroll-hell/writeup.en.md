# Doomscroll Hell - Forensics

**Flag:** `cdctf{doomscrolling_is_so_much_fun!}` · **Points:** 500 · **Author:** soup
**Files:** `doomscroll.zip` (51,462,800 B, sha256 `5163b4d7...903f79`), 15 mp4 inside

## Challenge

We are given a intercepted Instagram group chat of the rival team Crimson Offense: 15 reels that
are supposedly the exfiltration channel. The flag has to be found in that pile of videos, and the
card advertises the format `cdctf{word_word_word_word_word}`.

## Initial analysis

15 mp4 files, 3.0-4.1 MB each, H.264 + AAC, 10-13 seconds long. `ffprobe` and `exiftool` turn up
nothing suspicious: the only tags are `encoder = Lavc libx264` and `creation_time` values dated
2026-10-03, so the videos were re-rendered by the author rather than downloaded intact from
Instagram. The frames are ordinary reels (a dog pulling down its owner's trousers, `@SNOPFEED`
watermark).

The real anomaly is at container level. Walking the MP4 boxes shows all 15 files share the same
sequence `ftyp, moov, free, mdat, uuid`. The first four are what ffmpeg writes; the last one is a
92-93 byte `uuid` box sitting **after** `mdat`, i.e. outside the media payload, and all 15 files use
the same UUID `5f0a6c1e-7b3d-5a8e-9c4f-2d1b6a7e3c90`. Its 68-69 byte payload mixes text and raw
bytes, and reads out `%PDF-1.4`, `1 0 obj`, `/Type /Pages`, `xref`, `trailer`, `startxref`, `%%EOF`
plus an `x\xda` opening. Each video carries one slice of the same PDF file.

## Ruled out

1. **Metadata tags**: the 53-byte `udta/meta` only holds the encoder tag, `free` is exactly 8 empty
   bytes, and the `creation_time` values differ without any pattern. Rejected.
2. **Frame and audio steganography**: not pursued. Once the 15 PDF slices closed under the `xref`
   constraint there was no reason to open that channel; only a few frames were inspected by eye, no
   LSB or spectral measurement was taken.

## Exploit chain

**Step 1 - Carving the slices.** A `uuid` box is 4 bytes size, 4 bytes type and then a **16 byte
extended_type**, so the payload starts at `o+24` (using `o+16` shifts everything by 8 bytes and no
UUID matches). The 15 payloads are 13*68 + 2*69 = 1022 bytes.

```python
size = struct.unpack(">I", buf[o:o + 4])[0]
kind = buf[o + 4:o + 8].decode("latin1")
if kind == "uuid" and buf[o + 8:o + 24] == UUID:
    chunks[name[:-4]] = buf[o + 24:o + size]
```

**Step 2 - Locating each slice with the PDF's own constraints.** The filenames give no order, but a
PDF can verify itself in two places:

- The stream region: `/Length 450`, and exactly one slice holds `stream\n` (the regex
  `(?<!end)stream\n` is needed so `endstream\n` is not mistaken for it). A DFS over the remaining
  slices keeps one `zlib.decompressobj()` over the bytes assembled so far, so any slice that breaks
  inflation is cut immediately. Once 450 bytes are reached, the closing condition is that
  `zlib.decompress` consumes the whole stream **and** the next bytes start with `\nendstream`. Only
  one run satisfies it: `Cks57_V-Hsy > CU4g7CDhW5q > CDx8NCxzTUA > CtJum68xxwr > CPZGeCCcZfB >
  Ct9t7nQO6KL > CYzUFRaPz5o > C1-sQVqsTIu`.
- The 7 remaining ASCII slices: 7! permutations x 8 insertion points, and the solution is the one
  where every offset in the `xref` table lands on its own `N 0 obj` header and `startxref` lands on
  the word `xref`.

**Step 3 - Verification.** The rebuilt file is exactly 1022 bytes, ends with `%%EOF`, and the `xref`
table matches the real positions:

```text
xref rows   15 64 121 247 317   ->  real offsets of `1 0 obj` .. `5 0 obj`: 15 64 121 247 317
startxref   839                 ->  real offset of `xref`: 839
```

Nothing is missing, so the content is the original. `fitz` renders a single page; the 946-byte
content stream holds an "internal memo" about retention metrics, and the second-to-last line is the
flag.

## Flag

```bash
python exploit.py files/chunks
```

```text
[*] 15 uuid slices, 1022 byte total
[+] order: CWBRyIGYAOd > CFH95xUXh5X > C_pn-Ww2wKg > C4cE45r8ICF > CyzAgQA4oVO > Cks57_V-Hsy > CU4g7CDhW5q > CDx8NCxzTUA > CtJum68xxwr > CPZGeCCcZfB > Ct9t7nQO6KL > CYzUFRaPz5o > C1-sQVqsTIu > CdWtouUG4Bu > C9nruRG2aNs
[+] pdf 1022 B, xref offsets verified: True, stream inflated to 946 B
BT
/F1 24 Tf 1 0 0 1 60 740 Tm (INTERNAL MEMO: Engagement Retention Initiative) Tj
/F1 11 Tf 1 0 0 1 60 704 Tm (Classification: DO NOT SCROLL PAST) Tj
/F1 11 Tf 1 0 0 1 60 681 Tm () Tj
/F1 11 Tf 1 0 0 1 60 658 Tm (Team,) Tj
/F1 11 Tf 1 0 0 1 60 635 Tm (Average session length is up 41% since we removed the end of the feed.) Tj
/F1 11 Tf 1 0 0 1 60 612 Tm (Users report they 'only meant to watch one'. This is working as intended.) Tj
/F1 11 Tf 1 0 0 1 60 589 Tm (Autoplay stays on. The refresh gesture stays satisfying. Nobody gets bored.) Tj
/F1 11 Tf 1 0 0 1 60 566 Tm () Tj
/F1 11 Tf 1 0 0 1 60 543 Tm (If you have read this far, you watched every single reel. Congratulations.) Tj
/F1 11 Tf 1 0 0 1 60 520 Tm () Tj
/F1 14 Tf 1 0 0 1 60 497 Tm (Retention key:) Tj
/F1 16 Tf 1 0 0 1 60 471 Tm (cdctf{doomscrolling_is_so_much_fun!}) Tj
/F1 11 Tf 1 0 0 1 60 443 Tm () Tj
/F1 11 Tf 1 0 0 1 60 420 Tm (Now put the phone down and go outside.) Tj
ET
[+] flag: cdctf{doomscrolling_is_so_much_fun!}
```

The card promises five words; the flag is five words with a trailing `!` attached to the last one.

## Reproduce

```bash
python exploit.py files/chunks           # carved slices, no video needed
python exploit.py /path/to/doomscroll    # carve again from the 15 mp4 files
```

Both paths produce the same `recovered.pdf` (compared byte for byte). The rebuilt PDF is stored in
`files/recovered.pdf`, the 15 slices in `files/chunks/*.bin`.
