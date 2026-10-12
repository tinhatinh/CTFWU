---
title: "Mem-4 : A Fragment in Memory"
category: "Forensics"
tags: ["memory-forensics", "memprocfs", "clipboard", "cf-html", "ui-records"]
solve_date: "2026-10-09"
language: "en"
---

# Mem-4 : A Fragment in Memory

**Flag:** `OWASP{soulstone_memory_84c2}`
**Artifact:** `soul.zip` 937,376,339 B (sha256 `94d15b80b78402ab027a6ab4f40d288babef7d938631766d25c1d5bcb6fd9ee0`) unpacking to the RAM image `soul.mem` 2,774,466,560 B (`0xa55f0000`, sha256 `617d69406e571bc6a80af9e4517cb2ecc3839c508e0e8374463e38f7f70014e6`).

## Challenge

"Not everything that existed on the machine was meant to survive. One fragment remained where few people think to look. Dig deeper. Might be image." Hard, 250 points, 23 solves at the time of work.

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

### The token already exists as plaintext

The first three challenges of the series share one pattern: the artifact is a UTF-16 hex string split across lines, stored inside a specific OS structure. Scanning the whole image for `soulstone_` in both ASCII and UTF-16 shows that this challenge's token needs no hex decoding at all:

```text
a:soulstone_memory_84c2    x6
```

Total copies of the value: 6 ASCII + 14 UTF-16 = **20 occurrences**. "Where few people think to look" and "might be image" both point at two container types: the clipboard (temporary content that lives in no file) and UI/activation records of Paint.

## Solution

### Locating the copies and classifying their containers

```bash
python solve.py soul.mem soulstone_memory
```

```text
[ascii] @0x289980cf  CF_HTML
     | @Version:1.0..StartHTML:000000101..EndHTML:000000209..StartFragment:000000137..EndFragment:000000171
     ..<html>..<body>..<code>soulstone_memory_84c2</code>..</body>..</html>
[ascii] @0x2d444056  CF_HTML
     ..<code>soulstone_memory_84c2</code>
[utf16] @0x63184f6b  UI-record
     ...Microsoft.MSPaint_6.1907.29027.0_x64__8wekyb3d8bbwe\PaintStudio.View.exe | OWASP{soulstone_memory_84c2}
[utf16] @0x50a621b4  UI-record
     ...FrameworkViewType | 8.OWASP{soulstone_memory_84c2}
[utf16] @0x1205f91b
     ...msedge.exe | Chrome_WidgetWin_1 | soulstone_memory_84c2 | }
[utf16] @0x847e00b8
     * soulstone_memory_84c2 ... Windows.Launch
-- ascii occurrences: 6
-- utf16 occurrences: 14
```

The decisive container is the **clipboard**. The six ASCII copies sit inside `CF_HTML` blocks with the standard header `Version:1.0 / StartHTML:000000101 / EndHTML:000000209 / StartFragment:000000137 / EndFragment:000000171` and the fragment `<code>soulstone_memory_84c2</code>`, at `0x289980cf`, `0x289983cf`, `0x2d444056`, `0x4cf4b9cf`, `0x5fb480cf` and `0x5fb4828f`. This is the format Windows writes when content is copied from a browser; the header identifies clipboard HTML content but does not prove that every copy exists only in RAM.

The UTF-16 copies sit next to `PaintStudio.View.exe` (Paint 3D), the `FrameworkViewType` value name (beside GUID `{E2F669FC-1840-4ADE-9CC8-7E8A039B97FE}`), the `Windows.Launch` verb, the `Chrome_WidgetWin_1` window text of `msedge.exe`, and the shell record `WINDOWS10\nightwatch`. One value, several UI containers — consistent with "might be image", although adjacent strings do not establish the display-and-copy sequence.

### Why the other clipboard-looking flag is not the answer

The same clipboard trail holds another flag, in 4 UTF-16 copies at `0x1374e20c`, `0x6c32544c`, `0x9d2ddc88` and `0x9d2ddd98`:

```text
Set-Clipboard -Value "4f574153507b7630726d31725f636c69705f393161377d"
```

`4f574153507b7630726d31725f636c69705f393161377d` decodes to `OWASP{v0rm1r_clip_91a7}`. What separates it is location: all four copies are inside PowerShell **command history** (the `Set-Clipboard ...` lines, next to `Start-Process notepad.exe "$env:USERPROFILE\Documents\Vormir\expedition.txt"`), and none is inside a `CF_HTML` block. The token's `clip` substring pulls the analysis toward "clipboard fragment left in RAM", but this is the command that staged a different artifact, not clipboard content that survived.

## Result

```text
OWASP{soulstone_memory_84c2}
```

The flag was read directly from the memory image (the clipboard `CF_HTML` blocks and the Paint UI records) and the platform's solved table confirms it was accepted.

## Reproduce

Python 3 (`mmap`, `re`). Save the last `python` block as `solve.py` and run:

```bash
python solve.py soul.mem soulstone_memory
```

The script searches the token in both ASCII and UTF-16, prints a 640-byte window around each copy and labels the container (`CF_HTML`, `UI-record`, `raw`) from the `Version:1.0/StartFragment:` header or the presence of `View.exe`/`FrameworkViewType`. To read the decoy: `python solve.py soul.mem v0rm1r_clip`.

```python
"""Tim mot token trong raw memory dump (ASCII + UTF-16) va phan loai bo chua no.

Mission nay co hai kieu bo chua:
  - Clipboard CF_HTML: `Version:1.0` + `StartFragment:` + `<code>TOKEN</code>`
  - Ban ghi UI/activation: duong dan `...\\PaintStudio.View.exe` hoac ten gia tri
    `FrameworkViewType` nam canh chuoi `OWASP{...}`

Chay:  python solve.py <anh-RAM> <token>
       python solve.py soul.mem soulstone_memory
"""
import sys
import mmap
import re

CFHTML = re.compile(rb"Version:1\.0.{0,200}?StartFragment:(\d{9}).{0,200}?EndFragment:(\d{9})", re.S)


def readable(raw):
    s = raw.decode("latin-1", "ignore")
    return "".join(ch if 32 <= ord(ch) < 127 else "." for ch in s)


def wide(raw):
    s = raw.decode("utf-16-le", "ignore")
    return "".join(ch if 32 <= ord(ch) < 127 else "." for ch in s)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    path, token = sys.argv[1], sys.argv[2]
    needles = [("ascii", token.encode()), ("utf16", token.encode("utf-16-le"))]
    with open(path, "rb") as fh:
        mm = mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)
        for label, needle in needles:
            i = mm.find(needle)
            count = 0
            shown = 0
            while i != -1:
                count += 1
                if shown < 8:
                    lo, hi = max(0, i - 300), i + 340
                    win = mm[lo:hi]
                    ctx = readable(win) if label == "ascii" else wide(win)
                    ctx = re.sub(r"\.{3,}", " | ", ctx)
                    kind = "CF_HTML" if CFHTML.search(win) else ("UI-record" if b"View.exe" in win or b"FrameworkViewType" in win else "raw")
                    print("[%s] @0x%x  %s" % (label, i, kind))
                    print("     %s" % ctx[:420])
                    shown += 1
                i = mm.find(needle, i + 1)
            print("-- %s occurrences: %d" % (label, count))
        mm.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
