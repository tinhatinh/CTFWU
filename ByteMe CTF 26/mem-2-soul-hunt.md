---
title: "Mem-2 : Soul Hunt"
category: "Forensics"
tags: ["memory-forensics", "memprocfs", "process-list", "pe-comparison", "activeprocesslinks"]
solve_date: "2026-10-09"
language: "vi"
---

# Mem-2 : Soul Hunt

**Flag:** `OWASP{SoulHunt_7F31}`
**Artifact:** `soul.zip` 937,376,339 B (sha256 `94d15b80b78402ab027a6ab4f40d288babef7d938631766d25c1d5bcb6fd9ee0`) giải nén ra ảnh RAM `soul.mem` 2,774,466,560 B (`0xa55f0000`, sha256 `617d69406e571bc6a80af9e4517cb2ecc3839c508e0e8374463e38f7f70014e6`).

## Đề bài

"Among everything running on the machine, something doesn't belong. Find it." Medium, 200 điểm, 13 lời giải tại thời điểm làm. Đáp án là danh tính của một đối tượng đang chạy trong ảnh bộ nhớ, theo định dạng `OWASP{...}`.

## Phân tích

### Bối cảnh chung của chuỗi bài

`soul.mem` là raw physical memory dump của một guest VirtualBox, Windows 10 build **19041**, user `nightwatch`, được chụp bằng winpmem (`C:\Users\nightwatch\Downloads\winpmem_mini_x86.exe` còn trong cache tên ứng dụng của ảnh). MemProcFS liệt kê **111 tiến trình**.

Các bước đọc process, PEB, VAD và registry dùng module Python của MemProcFS. Với Volatility 3, cần symbol table tương ứng kernel `ntkrnlmp.pdb`, GUID `F57E740B088E5056E8AF0772F1CC5BEB`, age 1:

```python
import sys
sys.path.insert(0, r"C:\Tools\ctf\memprocfs")
import vmmpyc

vmm = vmmpyc.Vmm(["-device", r"C:\path\to\soul.mem"])
for pr in sorted(vmm.process_list(), key=lambda p: p.pid):
    print(pr.pid, pr.ppid, pr.fullname)
```

Ảnh chứa nhiều giá trị `OWASP{...}` thuộc các bài khác nhau. Cần đối chiếu ngữ cảnh của từng giá trị với yêu cầu đề, không chọn chỉ theo flag format.

### Lọc tiến trình theo đường dẫn ảnh

Build 19041 x64 nên danh sách process lấy được bằng quét signature kernel, không cần symbol table. Trong 111 entry, chỉ ba cái có `PATH` nằm ngoài `C:\Windows`, `C:\Program Files*`, `C:\ProgramData`:

```text
PID 2024  OneDrive.exe        C:\Users\nightwatch\AppData\Local\Microsoft\OneDrive\OneDrive.exe
PID 5688  FileCoAuth.exe      C:\Users\nightwatch\AppData\Local\Microsoft\OneDrive\26.173.0906.0008\FileCoAuth.exe
PID 2580  SoulHunt_7F31.exe   C:\Users\nightwatch\Desktop\SoulHunt_7F31.exe
```

Hai entry OneDrive là tiến trình ký của chính ứng dụng. Entry còn lại có command line bất thường — bản ghi gốc từ `process_list()`:

```text
PID=2580|PPID=6960|NAME=SoulHunt_7F31.|FULL=SoulHunt_7F31.exe|PATH=C:\Users\nightwatch\Desktop\SoulHunt_7F31.exe|SES=1|STATE=0|INTEG=5|EPROC=18446703458219466880
   CMD="C:\Users\nightwatch\Desktop\SoulHunt_7F31.exe" -NoLogo -NoProfile -NoExit -Command Start-Sleep -Seconds 7200
```

`EPROC=18446703458219466880` tức `0xffffdb0f78242080`. Bốn tham số `-NoLogo -NoProfile -NoExit -Command` là tham số của PowerShell nhưng file nằm ở Desktop và được gọi bằng chính tên nó. PPID 6960 là `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe` (con thứ hai của nó là `conhost.exe` PID 8348).

## Lời giải

### Loại khả năng process bị ẩn

Đi hết chuỗi `ActiveProcessLinks` từ EPROCESS của System, với offset đã xác định trên build này: `UniqueProcessId = +0x440`, `ActiveProcessLinks = +0x448`, `ImageFileName = +0x5a8`. Con trỏ trong danh sách là địa chỉ của chính trường `LIST_ENTRY` ở node kia, nên phải trừ `0x448` mới ra EPROCESS.

```text
in MemProcFS list but not in chain: [] count 0
in chain but not in MemProcFS list: 9   (userinit.exe, explorer.exe, msedge.exe,
                                         HxTsr.exe, ScreenClipping x2, ScreenSketch x2, list head)
```

Không có tiến trình nào trong danh sách bị tách khỏi chuỗi liên kết, đối với các entry đã đối chiếu; kết quả này không loại trừ mọi kỹ thuật ẩn process. Chín node chỉ có trong chuỗi là do MemProcFS đọc không được VAD của chúng (`ScreenClipping`/`ScreenSketch` có EPROCESS nhưng không có vùng nhớ hợp lệ). Tại `EPROCESS(2580)+0x5a8`, ảnh nội 15 ký tự cho đúng `SoulHunt_7F31.` — đây là tiến trình thật đang chạy, không phải chuỗi rơi tự do.

### Xác định danh tính thật của file

Đọc `ImageBaseAddress` từ PEB của nghi phạm và của tiến trình chuẩn, rồi so sánh ảnh PE trong memory:

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

Header trùng khít, cùng `TimeDateStamp` và `SizeOfImage`; 14/18 page đang resident giống nhau từng byte (phần khác nằm ở vùng `.data` bị ghi đè lúc chạy). Ảnh của PID 6960 chứa rõ `powershell.pdb` và section `.text$lp01powershell.exe!20_pri7`. Kết luận: `SoulHunt_7F31.exe` là bản sao đã đổi tên của `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`, được giữ sống bằng `Start-Sleep -Seconds 7200`.

### Dấu vết tạo file

Console history và clipboard HTML trong memory lưu lại đúng sequence dựng hiện trường:

```text
Copy-Item "$env:WINDIR\System32\hh.exe"                 "$env:USERPROFILE\Desktop\SoulHunt_7F31.exe"   -> Cannot find path
Copy-Item "$env:WINDIR\System32\CalculatorApp.exe"      "$env:USERPROFILE\Desktop\SoulHunt_7F31.exe"   -> Cannot find path
Copy-Item "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" "$env:USERPROFILE\Desktop\NightWatchSvc.exe"
Copy-Item "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" "$env:USERPROFILE\Desktop\SoulStoneSvc.exe"
Start-Process "$env:USERPROFILE\Desktop\SoulHunt_7F31.exe" -ArgumentList '-NoLogo','-NoProfile','-NoExit','-Command','Start-Sleep -Seconds 7200'
```

Cùng khuôn mẫu này còn tạo `NightWatchSvc.exe` và `SoulStoneSvc.exe`; hai file đó có dòng log `LogEvents,ProcessStart` nhưng không còn EPROCESS tại thời điểm capture. `V0RMIR_7f31.exe` (bản sao `notepad.exe` theo đoạn HTML hướng dẫn trong clipboard) chỉ tồn tại dưới dạng văn bản, không có EPROCESS.

## Kết quả

```text
OWASP{SoulHunt_7F31}
```

Cờ đọc trực tiếp từ ảnh bộ nhớ (tên tiến trình của EPROCESS PID 2580) và bảng solved của nền tảng xác nhận giá trị này đã được chấp nhận.

## Tái hiện

Cần MemProcFS cho Windows (`vmm.dll`, `leechcore.dll`, `vmmpyc.pyd`) và Python 3 64-bit; đặt `MEMPROCFS_DIR` trỏ tới thư mục MemProcFS hoặc dùng `--memprocfs`. Lưu block `python` cuối bài thành `solve.py`, chạy:

```bash
python solve.py soul.mem --list
python solve.py soul.mem --compare 2580 6960
```

`--list` in các tiến trình có đường dẫn ảnh ngoài thư mục hệ thống; `--compare` in header PE và số page trùng khớp giữa hai pid. Cả hai chỉ đọc file, không ghi gì vào ảnh.

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
