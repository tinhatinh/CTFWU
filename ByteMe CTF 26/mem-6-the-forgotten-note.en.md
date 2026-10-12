---
title: "Mem-6 : The Forgotten Note"
category: "Forensics"
tags: ["memory-forensics", "memprocfs", "notepad", "open-file-buffer", "utf-16"]
solve_date: "2026-10-09"
language: "en"
---

# Mem-6 : The Forgotten Note

**Flag:** `OWASP{soulstone_note_3c91}`
**Artifact:** `soul.zip` 937,376,339 B (sha256 `94d15b80b78402ab027a6ab4f40d288babef7d938631766d25c1d5bcb6fd9ee0`) unpacking to the RAM image `soul.mem` 2,774,466,560 B (`0xa55f0000`, sha256 `617d69406e571bc6a80af9e4517cb2ecc3839c508e0e8374463e38f7f70014e6`).

## Challenge

"The expedition ends with a record that was left open when everything stopped. If you've made it this far, you already know how to follow the traces. Find the final record." The challenge card recorded 24 solves; its points and difficulty fields were not captured, so this writeup states no number for them. This is the last of six Forensics challenges sharing one memory image.

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

### Which process holds "the record left open"

At capture time `notepad.exe` still held an open file — the raw record from `process_list()`:

```text
PID=4968|PPID=6960|NAME=notepad.exe|FULL=notepad.exe|PATH=C:\Windows\system32\notepad.exe|SES=1|STATE=0|INTEG=5|EPROC=18446703458198831232
   CMD="C:\Windows\system32\notepad.exe" C:\Users\nightwatch\Documents\Vormir\expedition.txt
```

PPID 6960 is `powershell.exe`, the same parent that spawned `SoulHunt_7F31.exe` in Mem-2. The notepad text buffer lives in that process's memory, so "a record left open when everything stopped" is the file content in RAM, not a file on disk.

## Solution

### Reading the record

```bash
python solve.py soul.mem
```

```text
=== @0x24f3afa (utf16) ===
Vormir Expedition Notes
Location: Vormir.
Status: incomplete.
Artifact reference: 4f574153507b736f756c73746f6e655f6e6f74655f336339317d
The trail ends with this record.
If you are reading this, you've uncovered what the others missed.
The journey is complete.
Well done, traveler.
-- Vormir Expedition Log
-- decoded: OWASP{soulstone_note_3c91}
```

The `Artifact reference:` line holds 52 hex characters decoding to 26 bytes, `OWASP{soulstone_note_3c91}`. The UTF-16 record sits in the physical region starting at `0x24f3900`, with the `Artifact reference` match at `0x24f3afa`. The script also handles hex split across lines or interrupted by the `\x00` bytes of UTF-16, by ignoring separator characters while collecting the run.

### Confirming the record belongs to notepad

Searching the hex string and the record headings inside each candidate process address space with MemProcFS' `VmmProcess.search()` (needle ≤32 bytes):

```text
PID 4968 notepad.exe  note-hexpart-ascii   n=4  [0x12d19118ff7, 0x12d19119127, 0x12d19119847, 0x12d19121700]
PID 4968 notepad.exe  ExpeditionLog-utf16  n=1  [0x12d190edc18]
PID 4968 notepad.exe  VormirExped-ascii    n=4  [0x12d191190a7, 0x12d191191d7, 0x12d191198f7, 0x12d19121690]
```

Only PID 4968 returns hits; `mspaint.exe` (1204), `Photos.exe` (4824/2820), `explorer.exe` (8900), `powershell.exe` (6960), `SoulHunt_7F31.exe` (2580) and `dwm.exe` (1076) contain none of this record.

### Copy count and text variants

The record's hex string appears **43 times** in the image, in both ASCII and UTF-16, and all decodable copies yield the same value. ASCII copies are at `0xd21d5ed`, `0x13251c65`, `0x16cf8075`, `0x2d2c76ce`, `0x5eb77b25`, `0x6f8ec0f5` and `0x6f8ec815`; the one at `0x5eb77b25` has other data written over it (`...5f33633.317d`) so it does not decode. Two different endings exist for the same record:

```text
The trail ends with this record. If you are reading this, you've uncovered what the others
missed. The journey is complete. Well done, traveler. -- Vormir Expedition Log

The remaining records appear to be unrelated.
\Registry\Machine\...\HKEY_USERS\S-1-5-21-3525304513-4119828853-1302462655-1000\...
```

The command that created the file is still in history: `"@ | Set-Content "$env:USERPROFILE\Documents\Vormir\expedition.txt"`, and `ActivitiesCache`/UserEngaged JSON records `1:{...}\notepad.exe`, showing the record was opened through notepad.

## Result

```text
OWASP{soulstone_note_3c91}
```

The flag was read directly from the memory image (the UTF-16 buffer of `notepad.exe` PID 4968, which still held `Documents\Vormir\expedition.txt` open) and the platform's solved table confirms it was accepted.

## Reproduce

Python 3 (`mmap`, `re`, `binascii`). Save the last `python` block as `solve.py` and run:

```bash
python solve.py soul.mem
```

The script searches for `Artifact reference` in both ASCII and UTF-16, collects the hex run (ignoring `\x00`, newlines and spaces) and prints the full text around each copy. No symbol table is needed because the notepad buffer is read directly from the raw image; the process-attribution step uses MemProcFS' `VmmProcess.search()` as described above.

```python
"""Doc "the final record": mau ghi con mo trong notepad.exe luc capture.

File `Documents\\Vormir\\expedition.txt` duoc giu trong buffer UTF-16 cua
notepad (van dang mo khi anh RAM duoc chot). Noi dung co mot dong

    Artifact reference: <hex>

Script tim dong do o ca dang ASCII lan UTF-16, in toan van ban mau ghi va giai
ma chuoi hex.

Chay:  python solve.py <anh-RAM>
"""
import sys
import mmap
import re
import binascii

KEYS = [b"Artifact reference", "Artifact reference".encode("utf-16-le")]
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
    return b"".join(out)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    with open(sys.argv[1], "rb") as fh:
        mm = mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)
        seen = set()
        for needle in KEYS:
            utf16 = needle != KEYS[0]
            i = mm.find(needle)
            while i != -1:
                raw = mm[max(0, i - 320):i + 700]
                s = raw.decode("utf-16-le" if utf16 else "latin-1", "ignore")
                s = "".join(ch if 32 <= ord(ch) < 127 or ch == "\n" else "." for ch in s)
                s = re.sub(r"\.{3,}", "\n", s).strip()
                body = harvest(mm, i + len(needle))
                txt = body.decode("latin-1", "replace")
                if txt.startswith("OWASP{") and txt.endswith("}") and txt not in seen:
                    seen.add(txt)
                    print("=== @0x%x (%s) ===" % (i, "utf16" if utf16 else "ascii"))
                    print(s[:700])
                    print("-- decoded: %s" % txt)
                i = mm.find(needle, i + 1)
        mm.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
