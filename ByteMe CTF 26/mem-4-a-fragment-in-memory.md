---
title: "Mem-4 : A Fragment in Memory"
category: "Forensics"
tags: ["memory-forensics", "memprocfs", "clipboard", "cf-html", "ui-records"]
solve_date: "2026-10-09"
language: "vi"
---

# Mem-4 : A Fragment in Memory

**Flag:** `OWASP{soulstone_memory_84c2}`
**Artifact:** `soul.zip` 937,376,339 B (sha256 `94d15b80b78402ab027a6ab4f40d288babef7d938631766d25c1d5bcb6fd9ee0`) giải nén ra ảnh RAM `soul.mem` 2,774,466,560 B (`0xa55f0000`, sha256 `617d69406e571bc6a80af9e4517cb2ecc3839c508e0e8374463e38f7f70014e6`).

## Đề bài

"Not everything that existed on the machine was meant to survive. One fragment remained where few people think to look. Dig deeper. Might be image." Hard, 250 điểm, 23 lời giải tại thời điểm làm.

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

### Token tồn tại sẵn dưới dạng plaintext

Ba bài đầu của chuỗi dùng chung một khuôn: artifact là chuỗi hex UTF-16 bị ngắt dòng nằm trong một cấu trúc cụ thể của hệ điều hành. Quét toàn ảnh cho `soulstone_` ở cả ASCII lẫn UTF-16 cho thấy riêng token của bài này không cần giải hex:

```text
a:soulstone_memory_84c2    x6
```

Tổng số dữ liệu gây nhiễun của giá trị này: 6 dữ liệu gây nhiễun ASCII + 14 dữ liệu gây nhiễun UTF-16 = **20 occurrence**. "Nơi ít người nghĩ tới" và "might be image" cùng chỉ về hai loại bộ chứa: clipboard (nội dung tạm, không sống trong file nào) và các dữ liệu gây nhiễun ghi UI/activation của Paint.

## Lời giải

### Định vị các dữ liệu gây nhiễun sao và phân loại bộ chứa

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

Bộ chứa quyết định là **clipboard**. Sáu dữ liệu gây nhiễun ASCII nằm trong khối `CF_HTML` có header chuẩn `Version:1.0 / StartHTML:000000101 / EndHTML:000000209 / StartFragment:000000137 / EndFragment:000000171`, phần fragment là `<code>soulstone_memory_84c2</code>`, tại `0x289980cf`, `0x289983cf`, `0x2d444056`, `0x4cf4b9cf`, `0x5fb480cf`, `0x5fb4828f`. Đây là định dạng Windows ghi khi sao chép từ trình duyệt; header này cho thấy dữ liệu được lưu dưới định dạng clipboard HTML; không đủ để kết luận mọi bản sao đều chỉ tồn tại trong RAM.

Các dữ liệu gây nhiễun UTF-16 nằm cạnh `PaintStudio.View.exe` (Paint 3D), khoá giá trị `FrameworkViewType` (cạnh GUID `{E2F669FC-1840-4ADE-9CC8-7E8A039B97FE}`), chuỗi `Windows.Launch`, văn dữ liệu gây nhiễun cửa sổ `Chrome_WidgetWin_1` của `msedge.exe` và dữ liệu gây nhiễun ghi shell `WINDOWS10\nightwatch`. Cùng một giá trị, nhiều bộ chứa UI khác nhau — khớp với gợi ý "might be image" nhưng các chuỗi nằm cạnh nhau chưa đủ xác định thứ tự hiển thị và sao chép.

### Vì sao dữ liệu gây nhiễun gây nhiễu clipboard không phải đáp án

Cũng trong vệt clipboard có một cờ khác, xuất hiện 4 dữ liệu gây nhiễun UTF-16 tại `0x1374e20c`, `0x6c32544c`, `0x9d2ddc88`, `0x9d2ddd98`:

```text
Set-Clipboard -Value "4f574153507b7630726d31725f636c69705f393161377d"
```

`4f574153507b7630726d31725f636c69705f393161377d` giải ra `OWASP{v0rm1r_clip_91a7}`. Điểm phân biệt là vị trí: cả bốn dữ liệu gây nhiễun đều nằm trong **command history** của PowerShell (dòng lệnh `Set-Clipboard ...`, cạnh các lệnh `Start-Process notepad.exe "$env:USERPROFILE\Documents\Vormir\expedition.txt"`), không có dữ liệu gây nhiễun nào nằm trong khối `CF_HTML`. Token `clip` trong tên đánh lừa theo hướng "clipboard còn lại trong RAM", nhưng đây là lệnh gán clipboard của một artifact khác, không phải nội dung clipboard còn sót.

## Kết quả

```text
OWASP{soulstone_memory_84c2}
```

Cờ đọc trực tiếp từ ảnh bộ nhớ (khối `CF_HTML` của clipboard và các dữ liệu gây nhiễun ghi UI của Paint) và dữ liệu gây nhiễung solved của nền tảng xác nhận giá trị này đã được chấp nhận.

## Tái hiện

Chỉ cần Python 3 (`mmap`, `re`). Lưu block `python` cuối bài thành `solve.py`, chạy:

```bash
python solve.py soul.mem soulstone_memory
```

Script tìm token ở cả ASCII và UTF-16, in ngữ cảnh 640 byte quanh mỗi dữ liệu gây nhiễun và gắn nhãn bộ chứa (`CF_HTML`, `UI-record`, `raw`) dựa trên header `Version:1.0/StartFragment:` hoặc sự hiện diện của `View.exe`/`FrameworkViewType`. Muốn đọc dữ liệu gây nhiễun gây nhiễu, dùng `python solve.py soul.mem v0rm1r_clip`.

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
