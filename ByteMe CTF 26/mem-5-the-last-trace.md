---
title: "Mem-5 : The Last Trace"
category: "Forensics"
tags: ["memory-forensics", "memprocfs", "browser-cache", "edge-telemetry", "url-artifact"]
solve_date: "2026-10-09"
language: "vi"
---

# Mem-5 : The Last Trace

**Flag:** `OWASP{soulstone_web_8b2d}`
**Artifact:** `soul.zip` 937,376,339 B (sha256 `94d15b80b78402ab027a6ab4f40d288babef7d938631766d25c1d5bcb6fd9ee0`) giải nén ra ảnh RAM `soul.mem` 2,774,466,560 B (`0xa55f0000`, sha256 `617d69406e571bc6a80af9e4517cb2ecc3839c508e0e8374463e38f7f70014e6`).

## Đề bài

"Someone was looking for something on web shortly before the machine was captured. The trail did not end on the filesystem, Instead in the web. Follow it." Medium, 200 điểm, 23 lời giải tại thời điểm làm.

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

### Hai hướng của "vệt trên web"

Trong danh sách tiến trình có `msedge.exe` và nhiều `msedgewebview2.exe`, nên lịch sử điều hướng, log network của trình duyệt và text UIA của cửa sổ đều còn trong RAM. Hai hướng được phân biệt:

- **Filesystem**: bản ghi không khôi phục được database history/cache tương ứng; kết quả carving ảnh ở Mem-3 không đủ để loại mọi file resident.

## Lời giải

### Trích URL và tham số artifact

```bash
python solve.py soul.mem
```

```text
== URLs with artifact= ==
   49 https://example.com/vormir?artifact=4f574153507b736f756c73746f6e655f7765625f386232647d
    9 https://example.com/vormir?artifact=4f574153507b736f756c73746f6e655f7765625f386232647d......
      4f574153507b736f756c73746f6e655f7765625f386232647d -> OWASP{soulstone_web_8b2d}
== bing queries ==
   18 q=winpmen
   17 q=ftk+imager
    6 q=dump+it
   11 q=Download+Free+FTK+Imager
```

Chuỗi hex 54 ký tự trong tham số `artifact=` giải mã thành 27 byte `OWASP{soulstone_web_8b2d}`. Bản UTF-16 đầy đủ của URL xuất hiện **49 lần**, các bản ASCII xuất hiện khoảng **29 lần** và thường bị cắt; toàn bộ trùng nhau ở phần `artifact=`.

Cùng URL còn nằm trong log telemetry của Edge:

```text
TopTrafficMiss.uri: https://example.com/vormir?artifact=4f574153507b736f756c73746f6e655f7765625f386232647d  browser_remotedata.cpp.150
CacheFilterHit.uri: https://example.com/vormir?artifact=4f574153507b736f756c73746f6e655f7765625f386232647d  browser_remotedata.cpp.188
```

`TopTrafficMiss` và `CacheFilterHit` là hai nhánh của bộ lọc cache, tức URL này đã được trình duyệt xử lý thật chứ không phải một chuỗi tình cờ. `example.com` là domain giữ chỗ; không có request nào tới nó trong log DNS, dấu vết chỉ tồn tại trong cache/telemetry của trình duyệt — đúng ý "vệt không kết thúc ở filesystem".

### Trình tự hành vi khớp với đề

Các truy vấn Bing còn trong RAM mô tả đúng "tìm trên web ngay trước khi capture": `winpmem` (công cụ lấy RAM, chuỗi bị cắt ở `winpmen`), `ftk imager` / `Download Free FTK Imager` (công cụ đọc ảnh), `dump it`. Song song, PowerShell history có `Get-Item C:\Users\nightwatch\Downloads\dump\memdump.mem | Select Name,Length` và `python -m pip install volatility3`, còn `FTK Imager.exe` (PID 5960, `C:\Program Files\AccessData\FTK Imager\FTK Imager.exe`) vẫn đang chạy tại thời điểm capture.

## Kết quả

```text
OWASP{soulstone_web_8b2d}
```

Cờ đọc trực tiếp từ ảnh bộ nhớ (tham số `artifact=` của URL trong cache/telemetry Edge) và bảng solved của nền tảng xác nhận giá trị này đã được chấp nhận.

## Tái hiện

Chỉ cần Python 3 (`mmap`, `re`, `binascii`). Lưu block `python` cuối bài thành `solve.py`, chạy:

```bash
python solve.py soul.mem
```

Script quét toàn ảnh theo chunk 16 MiB, bắt mọi URL có `artifact=` (ASCII và UTF-16), giải tham số hex và gom các truy vấn `q=` của Bing.

```python
"""Trich vet web trong raw memory dump: URL co tham so artifact + tu khoa tim kiem.

Lich su/cache cua Edge (va UIA text) nam trong RAM duoi dang ASCII va UTF-16.
Script gom moi URL kieu

    https://example.com/vormir?artifact=<hex>

doi chieu ASCII/UTF-16, giai ma tham so hex, va liet ke cac truy van Bing
(`q=...`) de cho thay thuat toan da tim giuoc truc luc capture.

Chay:  python solve.py <anh-RAM>
"""
import sys
import mmap
import re
import binascii
import collections

PU = re.compile(rb"https?://[^\s\"'<>|]{10,300}")
PW = re.compile(rb"(?:[ -~]\x00){12,300}")
ART = re.compile(r"artifact=([0-9a-fA-F]{20,})")
QUERY = re.compile(r"[?&]q=([^&]{2,60})")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    with open(sys.argv[1], "rb") as fh:
        mm = mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)
        total = len(mm)
        urls = collections.Counter()
        queries = collections.Counter()
        chunk = 1 << 24
        off = 0
        while off < total:
            blob = mm[off:min(off + chunk + 320, total)]
            for g in PU.finditer(blob):
                u = g.group().decode("latin-1", "ignore")
                if "artifact=" in u:
                    urls[re.sub(r"[^ -~]", ".", u)[:200]] += 1
                elif "bing.com/search" in u:
                    for q in QUERY.findall(u):
                        queries[q] += 1
            for g in PW.finditer(blob):
                s = g.group().decode("utf-16-le", "ignore")
                if s.startswith(("http://", "https://")):
                    if "artifact=" in s:
                        urls[re.sub(r"[^ -~]", ".", s)[:200]] += 1
                    elif "bing.com/search" in s:
                        for q in QUERY.findall(s):
                            queries[q] += 1
            off += chunk
        mm.close()

    print("== URLs with artifact= ==")
    seen = set()
    for u, n in urls.most_common(40):
        print("%5d %s" % (n, u[:150]))
        for m in ART.finditer(u):
            h = m.group(1)
            h = h[:len(h) // 2 * 2]
            try:
                d = binascii.unhexlify(h).decode("latin-1")
            except Exception:
                continue
            if d.startswith("OWASP{") and d not in seen:
                seen.add(d)
                print("      %s -> %s" % (h, d))
    print("== bing queries ==")
    for q, n in queries.most_common(25):
        print("%5d %s" % (n, q))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
