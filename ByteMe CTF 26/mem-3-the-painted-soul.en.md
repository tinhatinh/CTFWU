---
title: "Mem-3 : The Painted Soul"
category: "Forensics"
tags: ["memory-forensics", "memprocfs", "hex-fragment-harvest", "utf-16", "image-carving"]
solve_date: "2026-10-09"
language: "en"
---

# Mem-3 : The Painted Soul

**Flag:** `OWASP{soulstone_paint_52af}`
**Artifact:** `soul.zip` 937,376,339 B (sha256 `94d15b80b78402ab027a6ab4f40d288babef7d938631766d25c1d5bcb6fd9ee0`) unpacking to the RAM image `soul.mem` 2,774,466,560 B (`0xa55f0000`, sha256 `617d69406e571bc6a80af9e4517cb2ecc3839c508e0e8374463e38f7f70014e6`). The statement also ships a 1152×573 RGB image with three hex lines, the last one truncated.

## Challenge

"Some things are easier to remember when they are seen. Find what was left behind." Hard, 300 points, 5 solves at the time of work. The attached statement image shows three hex lines, with the third cut off mid-line:

```text
4f574153507b736f
756c73746f6e655f
7061696e745f3
```

## Analysis

### Shared context of the series

`soul.mem` is a raw physical memory dump of a VirtualBox guest, Windows 10 build **19041**, user `nightwatch`, captured with winpmem (`C:\Users\nightwatch\Downloads\winpmem_mini_x86.exe` is still present in the image's application-name cache). MemProcFS enumerates **111 processes**.

Process, PEB, VAD and registry analysis uses the MemProcFS Python module. Volatility 3 requires symbols for `ntkrnlmp.pdb`, GUID `F57E740B088E5056E8AF0772F1CC5BEB`, age 1:

```python
import sys
sys.path.insert(0, r"C:\Tools\ctf\memprocfs")
import vmmpyc

vmm = vmmpyc.Vmm(["-device", r"C:\path\to\soul.mem"])
for pr in sorted(vmm.process_list(), key=lambda p: p.pid):
    print(pr.pid, pr.ppid, pr.fullname)
```

The image also carries seven flags planted for other missions/challenges, recoverable by harvesting hex strings: `soulstone_cmd_741f` (25 copies), `soulstone_net_4d92` (10), `pr0c3ss_hunt_7f31` (33), `v0rm1r_clip_91a7` (4), `soulstone_web_8b2d` (290), `soulstone_note_3c91` (43), `soulstone_paint_52af` (1). Three later challenges in the series had wrong submissions caused by these values.

### Two observations that set the direction

- Joining the two readable hex lines gives `OWASP{soulstone_paint_`; the remainder is in the truncated line, so it has to come from the memory image itself.
- The ASCII string `OWASP{` occurs **0 times** in the image, while the UTF-16 form occurs 7 times. Every later text search has to run on both encodings.
- No pixels survive. A full scan gives 671 PNG signatures and 393 chunk chains that validate, but they are only application icons and tiles (widest 1077 pixels; the largest by area is a 620×620 image packed into 242 bytes); of 1450 JPEG signatures, none open in PIL; the four 24/32bpp `BITMAPINFOHEADER` candidates (360×369, 1000×500, 1700×876, 1920×1033) report 38k–434k colours and render as noise, i.e. compressed data misread as bitmaps.
- The header of the statement image itself, however, is still resident: at `0x2d13d000` there is `IHDR 1152×573 bd=8 ct=2` followed by `sRGB`, `gAMA` and `pHYs`, all with correct CRCs — matching the dimensions and colour type of the attached image. Its `IDAT` chunk claims 18,632 bytes but inflates in no `wbits` mode (15/-15/31/-8), so the compressed data was paged out.

Conclusion: the flag cannot be read from a picture; the hex fragment has to be recovered from memory.

## Solution

### Harvesting hex regardless of line breaks

These artifacts are written as several 16-character lines and stored as UTF-16, so a contiguous hex regex (≥40 characters) misses them — which is exactly why the `paint` token never appeared under regex scanning. The working approach starts from the prefix `4f57415350` (hex of `OWASP{`) in both encodings, then keeps consuming hex characters while skipping `\x00`, spaces and newlines until `7d` (`}`) appears.

```bash
python solve.py soul.mem
```

```text
OWASP{soulstone_web_8b2d}                 290 copies  e.g. ['0x6ee194', '0x6ee274', '0x9e8154', '0xeda424']
OWASP{soulstone_note_3c91}                 43 copies  e.g. ['0xd21d601', '0x13251c79', '0x16cf8089', '0x2d2c76e2']
OWASP{soulstone_cmd_741f}                  25 copies  e.g. ['0xf5e8321', '0x75cf4db5', '0x88a8dcc5', '0xf5e8122']
OWASP{soulstone_net_4d92}                  10 copies  e.g. ['0x7e2370ba', '0x5e6da124', '0x6e88c1f4', '0x796ff246']
OWASP{pr0c3ss_hunt_7f31}                   33 copies  e.g. ['0x18f007c', '0x267d9120', '0x2730f7aa', '0x2730fa50']
OWASP{v0rm1r_clip_91a7}                     4 copies  e.g. ['0x1374e20c', '0x6c32544c', '0x9d2ddc88', '0x9d2ddd98']
OWASP{soulstone_paint_52af}                 1 copies  e.g. ['0x6cdc75d0']
```

Seven values, each in its own container; `soulstone_paint_52af` is the only one with a **single** copy in the whole image.

### Matching the fragment from the statement image

```bash
python solve.py soul.mem 7061696e745f
```

```text
fragment b'7061696e745f' [utf16] @0x6cdc760c -> OWASP{soulstone_paint_52af}
```

The complete UTF-16 copy sits at physical offset `0x6cdc760c` (the harvest reports the start of the hex string at `0x6cdc75d0`; the 60-byte difference is 30 hex characters × 2 bytes per UTF-16 code unit). The full 54-character hex string:

```text
4f574153507b736f 756c73746f6e655f 7061696e745f353261667d
```

decodes to 27 bytes, `OWASP{soulstone_paint_52af}`. The first two lines of this block match the statement image character for character, while the image cuts the third line at `7061696e745f3`; the copy in RAM carries the missing tail `353261667d`.

## Result

```text
OWASP{soulstone_paint_52af}
```

The flag was read directly from the memory image (the only UTF-16 copy, at `0x6cdc760c`) and the platform's solved table confirms it was accepted.

## Reproduce

Python 3 (`mmap`, `binascii`) plus `soul.mem`. Save the last `python` block as `solve.py` and run:

```bash
python solve.py soul.mem
python solve.py soul.mem 7061696e745f
```

The first command lists every flag decoded from hex fragments; the second locates the fragment visible in the statement image and prints the full string. Standard carving of PNG/JPEG/DIB leads to the same conclusion as above: the recorded carving checks did not recover the target image.

```python
"""Thu gom cac chuoi hex bi ngat dong trong raw memory dump va giai ma.

Cac artifact cua mission duoc gan duoi dang hex cua `OWASP{...}`, viet thanh
nhieu dong 16 ky tu va luu o dang ASCII hoac UTF-16. Regex hex lien mach
>=40 ky tu se bo sot, nen phuong phap o day la: tim moi occurrence cua mo dau
`4f57415350` (ASCII va UTF-16), sau do doc tiep cac ky tu hex, bo qua
\\x00 / khoang trang / xuong dong, cho toi khi gap `}`.

Chay:  python solve.py <anh-RAM> [hex-fragment-can-tim]
"""
import sys
import mmap
import binascii

HEX = set(b"0123456789abcdef")
SKIP = {0x00, 0x09, 0x0A, 0x0D, 0x20}


def harvest(mm, start, limit=400):
    out = []
    buf = ""
    i = start
    n = 0
    while i < start + 4000 and n < limit:
        c = mm[i]
        if c in HEX:
            buf += chr(c)
            if len(buf) == 2:
                b = binascii.unhexlify(buf)
                out.append(b)
                buf = ""
                n += 1
                if b == b"}":
                    break
        elif c in SKIP:
            pass
        else:
            break
        i += 1
    return b"".join(out), i


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    frag = sys.argv[2].encode() if len(sys.argv) > 2 else None
    with open(path, "rb") as fh:
        mm = mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)
        if frag:
            for enc, needle in (("a", frag), ("u", frag.decode("latin-1").encode("utf-16-le"))):
                i = mm.find(needle)
                while i != -1:
                    back = i - (i % 2)
                    txt, _ = harvest(mm, back)
                    print("fragment %s [%s] @0x%x -> %s" % (needle, enc, i, txt.decode("latin-1", "replace")))
                    i = mm.find(needle, i + 1)
            mm.close()
            return 0
        seen = {}
        for prefix in (b"4f57415350", "4f57415350".encode("utf-16-le")):
            i = mm.find(prefix)
            while i != -1:
                txt, _ = harvest(mm, i)
                s = txt.decode("latin-1", "replace")
                if s.startswith("OWASP{") and s.endswith("}"):
                    seen.setdefault(s, []).append(hex(i))
                i = mm.find(prefix, i + 1)
        for s, locs in seen.items():
            print("%-40s %3d copies  e.g. %s" % (s, len(locs), locs[:4]))
        mm.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
