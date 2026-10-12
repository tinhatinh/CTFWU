---
title: "Mem-1 : When It Happened"
category: "Forensics"
tags: ["memory-forensics", "memprocfs", "filetime", "system-time"]
solve_date: "2026-10-09"
language: "en"
---

# Mem-1 : When It Happened

**Flag:** `OWASP{2026-10-08 05:07:43}`
**Artifact:** `soul.zip` 937,376,339 B (sha256 `94d15b80b78402ab027a6ab4f40d288babef7d938631766d25c1d5bcb6fd9ee0`) unpacking to the RAM image `soul.mem` 2,774,466,560 B (`0xa55f0000`, sha256 `617d69406e571bc6a80af9e4517cb2ecc3839c508e0e8374463e38f7f70014e6`).

## Challenge

"Before following the trail, determine when the machine gave up its secrets. Find the time recorded in the memory image." Flag format `OWASP{YYYY-MM-DD HH:MM:SS}`, Easy, 100 points, 3 solves at the time of work. This is the opener of a six-challenge Forensics series (mission *Echoes of Vormir*) that shares one memory image.

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

### Identifying the artifact

- The first 4 KB are zero; no `PAGE`/`PAGEDU64` (crash dump), no `Crdm` (KdCopyDataBlock), no LiME/AVML/ELF magic.
- `0x1000` holds an E820 table: eight 20-byte `(base, length, type)` records; the largest usable entry is `base=0x100000, length=0xa54f0000, type=1` and the ACPI entry is `base=0xa55f0000, length=0x10000, type=3`. Top of RAM `0xa55f0000` equals the file size (2646 MiB), so the image is linear physical memory from PA 0. The zeroed `0xA0000-0xFFFFF` range is a legitimate VGA/BIOS shadow hole.
- Boot-sector strings at `0x7C00` (`NTFS` OEM-ID, `A disk read error occurred`), SMBIOS/ACPI data of `Oracle VirtualBox BIOS`, `ntoskrnl.exe` 315 occurrences, and more than 2000 occurrences of `10.0.19041`.

The ASCII string `OWASP{` occurs **0 times**, so this challenge answers with a system time value rather than a stored flag string.

## Solution

`windows.info` (run in an environment that does have symbol tables) produces two values that must be told apart:

```text
SystemTime (UTC): 2026-10-08 05:07:43+00:00
ControlSet001\Control\TimeZoneInformation: India Standard Time (UTC+5:30)
```

The kernel stores absolute time as FILETIME (100 ns units since 1601-01-01) and **always in UTC**, while the wall clock on that machine reads `10:37:43`. The statement only says "the time recorded in the memory image", so it has to be checked which value is actually recorded in the artifact. Counting how often each candidate second appears as a 64-bit integer across the whole 2.77 GB:

```bash
python solve.py soul.mem "2026-10-08 05:07:43" "2026-10-08 10:37:43"
```

```text
== 2026-10-08 05:07:43 : 8 occurrences (FILETIME 134359096630000000)
   @0x4b27014  2026-10-08 05:07:43.793670
   @0x54d3e470  2026-10-08 05:07:43.943392
   @0x730b5058  2026-10-08 05:07:43.907888
   @0x730b5060  2026-10-08 05:07:43.907888
   @0x900f0c60  2026-10-08 05:07:43.001856
   @0x900f0cd8  2026-10-08 05:07:43.907888
   @0x900f73f8  2026-10-08 05:07:43.847620
   @0x900fd7d0  2026-10-08 05:07:43.848588
== 2026-10-08 10:37:43 : 0 occurrences (FILETIME 134359294630000000)
```

The UTC second occurs 8 times, four of them inside one kernel pool region `0x900f0000-0x900fd000` — a cluster of objects created at the capture moment. The IST second never occurs. Text forms add nothing: `2026-10-08 05:07`, `2026-10-08T05:07`, `2026-10-08 10:37`, `2026-10-08T10:37`, plus the UTF-16 forms of `2026-10-08 05:07` and `2026-10-08 05:07:43`, all return 0 hits. FILETIME UTC is therefore the only source of this value, exactly what `windows.info` prints.

Context around the capture: CodeMeter logs in the page cache contain `2026-10-08 02:50:23: Running on Microsoft Windows 10 Home 22H2, 64-Bit` and `2026-10-08 02:50:25: Server ready / Startup duration: 4 seconds` (machine-local time, hours before the capture); PowerShell history holds `Get-Item C:\Users\nightwatch\Downloads\dump\memdump.mem | Select Name,Length` and `python -m pip install volatility3`, and `FTK Imager.exe` (PID 5960) was still running.

## Result

```text
OWASP{2026-10-08 05:07:43}
```

The value is taken from the platform's solved table and cross-checked in place against FILETIME occurrence counts in the image: the UTC second `2026-10-08 05:07:43` has 8 occurrences, the local-time variant has 0.

## Reproduce

Python 3 with no third-party libraries, plus `soul.mem` extracted from `soul.zip`. Save the last `python` block as `solve.py` and run:

```bash
python solve.py soul.mem "2026-10-08 05:07:43" "2026-10-08 10:37:43"
```

The script only verifies the FILETIME part. `SystemTime` and the timezone come from `vol -f soul.mem windows.info`, which needs a matching Windows symbol table; the local environment had none for build 19041, so that part was read where symbols exist while every number in this writeup was re-measured directly on the raw dump.

```python
"""Xac dinh giay nao thuc su duoc ghi trong raw memory dump.

Kernel Windows luu thoi gian tuyet doi dang FILETIME (100 ns tu 1601-01-01,
luon la UTC). Vi vay mot giay gio local suy ra tu TimeZoneInformation se khong
xuat hien du dang FILETIME. Script dem so lan xuat hien cua tung giay ung
vien trong anh de phan biet gia tri nao co that trong artifact.

Cach nhanh: trong pham vi mot giay, ba byte thap cua FILETIME doi lien tuc
nen chi so khop 5 byte cao, sau do xac nhan lai gia tri day du.

Chay:  python solve.py <duong-dan-anh-RAM> "YYYY-MM-DD HH:MM:SS" [...]
"""
import sys
import struct
import mmap
import datetime

EPOCH = datetime.datetime(1601, 1, 1)
SECOND = 10_000_000  # so tick 100 ns trong mot giay


def to_filetime(dt):
    return int((dt - EPOCH).total_seconds() * SECOND)


def from_filetime(v):
    return EPOCH + datetime.timedelta(microseconds=v / 10)


def occurrences(path, dt):
    base = to_filetime(dt)
    keys = {struct.pack("<Q", base)[3:8], struct.pack("<Q", base + SECOND - 1)[3:8]}
    hits = []
    with open(path, "rb") as fh:
        mm = mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)
        for key in keys:
            i = mm.find(key)
            while i != -1 and i >= 3:
                v = struct.unpack_from("<Q", mm, i - 3)[0]
                if base <= v < base + SECOND:
                    hits.append((i - 3, from_filetime(v)))
                i = mm.find(key, i + 1)
        mm.close()
    hits.sort()
    return hits


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    path = sys.argv[1]
    for arg in sys.argv[2:]:
        dt = datetime.datetime.strptime(arg, "%Y-%m-%d %H:%M:%S")
        hits = occurrences(path, dt)
        print("== %s : %d occurrences (FILETIME %d)" % (arg, len(hits), to_filetime(dt)))
        for off, ts in hits[:12]:
            print("   @0x%09x  %s" % (off, ts.strftime("%Y-%m-%d %H:%M:%S.%f")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
