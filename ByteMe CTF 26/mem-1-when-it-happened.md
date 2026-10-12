---
title: "Mem-1 : When It Happened"
category: "Forensics"
tags: ["memory-forensics", "memprocfs", "filetime", "system-time"]
solve_date: "2026-10-09"
language: "vi"
---

# Mem-1 : When It Happened

**Flag:** `OWASP{2026-10-08 05:07:43}`
**Artifact:** `soul.zip` 937,376,339 B (sha256 `94d15b80b78402ab027a6ab4f40d288babef7d938631766d25c1d5bcb6fd9ee0`) giải nén ra ảnh RAM `soul.mem` 2,774,466,560 B (`0xa55f0000`, sha256 `617d69406e571bc6a80af9e4517cb2ecc3839c508e0e8374463e38f7f70014e6`).

## Đề bài

"Before following the trail, determine when the machine gave up its secrets. Find the time recorded in the memory image." Định dạng cờ `OWASP{YYYY-MM-DD HH:MM:SS}`, Easy, 100 điểm, 3 lời giải tại thời điểm làm. Đây là bài mở đầu của chuỗi sáu bài Forensics (mission *Echoes of Vormir*) dùng chung một ảnh bộ nhớ.

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

### Nhận dạng artifact

- Bốn KB đầu bằng 0; không có `PAGE`/`PAGEDU64` (crash dump), không có `Crdm` (KdCopyDataBlock), không có magic LiME/AVML/ELF.
- Tại `0x1000` là dữ liệu gây nhiễung E820: 8 record 20 byte dạng `(base, length, type)`; entry khả dụng lớn nhất `base=0x100000, length=0xa54f0000, type=1`, entry ACPI `base=0xa55f0000, length=0x10000, type=3`. Top of RAM `0xa55f0000` đúng bằng kích thước file (2646 MiB), nên ảnh là RAM vật lý tuyến tính từ PA 0. Vùng `0xA0000-0xFFFFF` toàn 0 là lỗ VGA/BIOS shadow hợp lệ.
- Boot sector tại `0x7C00` (`NTFS` OEM-ID, `A disk read error occurred`), SMBIOS/ACPI của `Oracle VirtualBox BIOS`, `ntoskrnl.exe` xuất hiện 315 lần, chuỗi `10.0.19041` vượt 2000 lần.

Chuỗi `OWASP{` dạng ASCII xuất hiện **0 lần**, nên đáp án của bài này là một giá trị thời gian của hệ thống chứ không phải một chuỗi cờ được ghi sẵn.

## Lời giải

`windows.info` (chạy ở môi trường có sẵn symbol table) đưa ra hai giá trị cần phân biệt:

```text
SystemTime (UTC): 2026-10-08 05:07:43+00:00
ControlSet001\Control\TimeZoneInformation: India Standard Time (UTC+5:30)
```

Kernel lưu thời gian tuyệt đối bằng FILETIME (đơn vị 100 ns từ 1601-01-01) và **luôn là UTC**, còn giờ người dùng nhìn thấy trên máy là `10:37:43`. Đề chỉ nói "the time recorded in the memory image", nên cần kiểm giá trị nào thực sự được ghi trong artifact. Đếm số lần mỗi giây ứng viên xuất hiện dưới dạng số nguyên 64 bit trên toàn bộ 2,77 GB:

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

Giây UTC xuất hiện 8 lần, trong đó bốn lần nằm trong cùng vùng kernel pool `0x900f0000-0x900fd000` — cụm object được tạo đúng nhịp lúc capture. Giây tương ứng theo giờ IST không xuất hiện lần nào. Đối chiếu thêm dạng văn dữ liệu gây nhiễun: `2026-10-08 05:07`, `2026-10-08T05:07`, `2026-10-08 10:37`, `2026-10-08T10:37` và dữ liệu gây nhiễun UTF-16 của `2026-10-08 05:07` / `2026-10-08 05:07:43` đều cho 0 kết quả. Nguồn duy nhất của giá trị này là FILETIME UTC, đúng như `windows.info` in ra.

Bối cảnh quanh thời điểm capture: log CodeMeter trong page cache ghi `2026-10-08 02:50:23: Running on Microsoft Windows 10 Home 22H2, 64-Bit` và `2026-10-08 02:50:25: Server ready / Startup duration: 4 seconds` (giờ local, trước capture nhiều giờ); PowerShell history có `Get-Item C:\Users\nightwatch\Downloads\dump\memdump.mem | Select Name,Length` và `python -m pip install volatility3`, còn `FTK Imager.exe` (PID 5960) vẫn đang chạy.

## Kết quả

```text
OWASP{2026-10-08 05:07:43}
```

Giá trị lấy từ dữ liệu gây nhiễung solved của nền tảng, đối chứng tại chỗ bằng số lần xuất hiện FILETIME trong ảnh: giây UTC `2026-10-08 05:07:43` có 8 occurrence, biến thể giờ local có 0.

## Tái hiện

Cần Python 3 (không dùng thư viện ngoài) và `soul.mem` đã giải nén từ `soul.zip`. Lưu block `python` cuối bài thành `solve.py`, chạy:

```bash
python solve.py soul.mem "2026-10-08 05:07:43" "2026-10-08 10:37:43"
```

Script chỉ kiểm chứng phần FILETIME. Giá trị `SystemTime` và timezone lấy từ `vol -f soul.mem windows.info`, đòi hỏi symbol table Windows tương ứng; môi trường local không có symbol cho build 19041 này nên phần đó được đọc ở môi trường có symbol, còn mọi con số trong bài đều đo lại trực tiếp trên raw dump.

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
