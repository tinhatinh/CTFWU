---
title: "Mem-2 : Soul Hunt"
category: "Forensics"
tags: ["memory-forensics", "memprocfs", "process-list", "pe-comparison", "activeprocesslinks"]
solve_date: "2026-10-09"
language: "en"
---

# Mem-2 : Soul Hunt

**Flag:** `OWASP{SoulHunt_7F31}`
**Artifact:** `soul.zip` 937,376,339 B (sha256 `94d15b80b78402ab027a6ab4f40d288babef7d938631766d25c1d5bcb6fd9ee0`) unpacking to the RAM image `soul.mem` 2,774,466,560 B (`0xa55f0000`, sha256 `617d69406e571bc6a80af9e4517cb2ecc3839c508e0e8374463e38f7f70014e6`).

## Challenge

"Among everything running on the machine, something doesn't belong. Find it." Medium, 200 points, 13 solves at the time of work. The answer is the identity of one running object in the memory image, in `OWASP{...}` format.

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

### Filtering processes by image path

On build 19041 x64 the process list is recoverable by kernel signature scanning, without a symbol table. Of the 111 entries, only three have a `PATH` outside `C:\Windows`, `C:\Program Files*` and `C:\ProgramData`:

```text
PID 2024  OneDrive.exe        C:\Users\nightwatch\AppData\Local\Microsoft\OneDrive\OneDrive.exe
PID 5688  FileCoAuth.exe      C:\Users\nightwatch\AppData\Local\Microsoft\OneDrive\26.173.0906.0008\FileCoAuth.exe
PID 2580  SoulHunt_7F31.exe   C:\Users\nightwatch\Desktop\SoulHunt_7F31.exe
```

The two OneDrive entries are signed processes of that application. The remaining one has an unusual command line; the raw record from `process_list()`:

```text
PID=2580|PPID=6960|NAME=SoulHunt_7F31.|FULL=SoulHunt_7F31.exe|PATH=C:\Users\nightwatch\Desktop\SoulHunt_7F31.exe|SES=1|STATE=0|INTEG=5|EPROC=18446703458219466880
   CMD="C:\Users\nightwatch\Desktop\SoulHunt_7F31.exe" -NoLogo -NoProfile -NoExit -Command Start-Sleep -Seconds 7200
```

`EPROC=18446703458219466880` is `0xffffdb0f78242080`. The four switches `-NoLogo -NoProfile -NoExit -Command` are PowerShell switches, yet the file sits on the Desktop and is invoked by its own name. PPID 6960 is `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe` (its other child is `conhost.exe` PID 8348).

## Solution

### Ruling out a hidden process

Walking the whole `ActiveProcessLinks` chain from the EPROCESS of System, with offsets confirmed on this build: `UniqueProcessId = +0x440`, `ActiveProcessLinks = +0x448`, `ImageFileName = +0x5a8`. A list pointer is the address of the `LIST_ENTRY` field itself in the other node, so `0x448` must be subtracted to reach the EPROCESS.

```text
in MemProcFS list but not in chain: [] count 0
in chain but not in MemProcFS list: 9   (userinit.exe, explorer.exe, msedge.exe,
                                         HxTsr.exe, ScreenClipping x2, ScreenSketch x2, list head)
```

No process in the list is detached from the chain, so there is no unlink/DK4-style hiding. The nine chain-only nodes are processes whose VAD MemProcFS could not read (`ScreenClipping`/`ScreenSketch` have an EPROCESS but no valid memory region). At `EPROCESS(2580)+0x5a8` the in-image 15 characters read exactly `SoulHunt_7F31.` — a genuinely running process, not a stray string.

### Establishing the real identity of the file

Reading `ImageBaseAddress` from the PEB of the suspect and of a reference process, then comparing the in-memory PE images:

```bash
python solve.py soul.mem --compare 2580 6960
```

```text
SoulHunt_7F31.exe (pid 2580) imagebase=0x7ff616080000
powershell.exe (pid 6960) imagebase=0x7ff7a1b50000
  A: machine=0x8664 nsec=6 TimeDateStamp=3982536021 SizeOfImage=0x72000
  B: machine=0x8664 nsec=6 TimeDateStamp=3982536021 SizeOfImage=0x72000
  first 0x100 header bytes identical: True
  resident pages of A: 18, byte-identical with B: 14
```

Headers match exactly, same `TimeDateStamp` and `SizeOfImage`; 14 of 18 resident pages are byte-identical (the differences are in `.data`, overwritten at runtime). The image of PID 6960 clearly contains `powershell.pdb` and the section `.text$lp01powershell.exe!20_pri7`. Conclusion: `SoulHunt_7F31.exe` is a renamed copy of `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`, kept alive by `Start-Sleep -Seconds 7200`.

### Traces of the file creation

Console history and the HTML clipboard blob in memory store the staging sequence:

```text
Copy-Item "$env:WINDIR\System32\hh.exe"                 "$env:USERPROFILE\Desktop\SoulHunt_7F31.exe"   -> Cannot find path
Copy-Item "$env:WINDIR\System32\CalculatorApp.exe"      "$env:USERPROFILE\Desktop\SoulHunt_7F31.exe"   -> Cannot find path
Copy-Item "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" "$env:USERPROFILE\Desktop\NightWatchSvc.exe"
Copy-Item "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" "$env:USERPROFILE\Desktop\SoulStoneSvc.exe"
Start-Process "$env:USERPROFILE\Desktop\SoulHunt_7F31.exe" -ArgumentList '-NoLogo','-NoProfile','-NoExit','-Command','Start-Sleep -Seconds 7200'
```

The same pattern also produced `NightWatchSvc.exe` and `SoulStoneSvc.exe`; both have `LogEvents,ProcessStart` log lines but no EPROCESS at capture time. `V0RMIR_7f31.exe` (a copy of `notepad.exe` described by the clipboard HTML instructions) exists only as text, with no EPROCESS.

## Result

```text
OWASP{SoulHunt_7F31}
```

The flag was read directly from the memory image (the process name of EPROCESS PID 2580) and the platform's solved table confirms it was accepted.

## Reproduce

Requires MemProcFS for Windows (`vmm.dll`, `leechcore.dll`, `vmmpyc.pyd`) and 64-bit Python 3; point `MEMPROCFS_DIR` at the MemProcFS directory or pass `--memprocfs`. Save the last `python` block as `solve.py` and run:

```bash
python solve.py soul.mem --list
python solve.py soul.mem --compare 2580 6960
```

`--list` prints processes whose image path is outside system directories; `--compare` prints the PE headers and the count of matching pages for two pids. Both only read the file and write nothing into the image.

```python
""" Liet ke process trong anh RAM va doi chinh anh PE cua nghi pham.

Can MemProcFS (vmm.dll + vmmpyc.pyd) cho CPython 64-bit. Duong dan thu vien
MemProcFS lay tu bien moi truong MEMPROCFS_DIR hoac tham so --memprocfs.

  --list     : in cac process co duong dan anh nam ngoai thu muc he thong.
  --compare  : doc ImageBase tu PEB cua hai pid, so sanh header va dem
               page 4 KB trung khop trong phan resident cua anh.

Chay:
  python solve.py <anh-RAM> --list
  python solve.py <anh-RAM> --compare 2580 6960
"""
import sys
import os
import struct
import argparse

SYS_DIRS = ("c:\\windows", "c:\\program files", "c:\\programdata")


def connect(image, memprocfs):
    if memprocfs:
        sys.path.insert(0, memprocfs)
    import vmmpyc
    return vmmpyc.Vmm(["-device", image])


def path_of(pr):
    for attr in ("pathuser", "pathkernel"):
        try:
            v = getattr(pr, attr)
        except Exception:
            v = None
        if v:
            return v
    return None


def cmd_list(vmm):
    procs = list(vmm.process_list())
    print("processes: %d" % len(procs))
    for pr in sorted(procs, key=lambda p: p.pid):
        path = path_of(pr)
        if not path:
            continue
        low = path.lower()
        if low.startswith(SYS_DIRS):
            continue
        print("PID %-6s PPID %-6s %-22s %s" % (pr.pid, pr.ppid, pr.fullname, path))
        try:
            print("     cmd: %s" % pr.cmdline)
        except Exception:
            pass


def image_base(pr):
    peb = pr.peb
    if not peb:
        return None
    return int.from_bytes(pr.memory.read(peb + 0x10, 8, 0), "little")


def pe_info(mem, base):
    hdr = mem.read(base, 0x1000, 0)
    e = struct.unpack_from("<I", hdr, 0x3c)[0]
    machine, nsec = struct.unpack_from("<HH", hdr, e + 4)
    stamp = struct.unpack_from("<I", hdr, e + 8)[0]
    sizeimg = struct.unpack_from("<I", hdr, e + 24 + 56)[0]
    return hdr, machine, nsec, stamp, sizeimg


def cmd_compare(vmm, pid, ref):
    procs = {p.pid: p for p in vmm.process_list()}
    a, b = procs[pid], procs[ref]
    ia, ib = image_base(a), image_base(b)
    print("%s (pid %d) imagebase=%s" % (a.fullname, pid, hex(ia)))
    print("%s (pid %d) imagebase=%s" % (b.fullname, ref, hex(ib)))
    ha, ma, na, sa, za = pe_info(a.memory, ia)
    hb, mb, nb, sb, zb = pe_info(b.memory, ib)
    print("  A: machine=%s nsec=%d TimeDateStamp=%u SizeOfImage=0x%x" % (hex(ma), na, sa, za))
    print("  B: machine=%s nsec=%d TimeDateStamp=%u SizeOfImage=0x%x" % (hex(mb), nb, sb, zb))
    print("  first 0x100 header bytes identical: %s" % (ha[:0x100] == hb[:0x100]))
    total = min(za, zb)
    same = resident = 0
    for off in range(0, total, 0x1000):
        pa = a.memory.read(ia + off, 0x1000, 0)
        pb = b.memory.read(ib + off, 0x1000, 0)
        if len(pa) != 0x1000 or len(pb) != 0x1000:
            continue
        if pa.strip(b"\x00"):
            resident += 1
            if pa == pb:
                same += 1
    print("  resident pages of A: %d, byte-identical with B: %d" % (resident, same))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--memprocfs", default=os.environ.get("MEMPROCFS_DIR"))
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--compare", nargs=2, type=int, metavar=("PID", "REFPID"))
    ns = ap.parse_args()
    vmm = connect(ns.image, ns.memprocfs)
    if ns.list:
        cmd_list(vmm)
    if ns.compare:
        cmd_compare(vmm, *ns.compare)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
