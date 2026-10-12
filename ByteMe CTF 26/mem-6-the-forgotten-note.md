---
title: "Mem-6 : The Forgotten Note"
category: "Forensics"
tags: ["memory-forensics", "memprocfs", "notepad", "open-file-buffer", "utf-16"]
solve_date: "2026-10-09"
language: "vi"
---

# Mem-6 : The Forgotten Note

**Flag:** `OWASP{soulstone_note_3c91}`
**Artifact:** `soul.zip` 937,376,339 B (sha256 `94d15b80b78402ab027a6ab4f40d288babef7d938631766d25c1d5bcb6fd9ee0`) giải nén ra ảnh RAM `soul.mem` 2,774,466,560 B (`0xa55f0000`, sha256 `617d69406e571bc6a80af9e4517cb2ecc3839c508e0e8374463e38f7f70014e6`).

## Đề bài

"The expedition ends with a record that was left open when everything stopped. If you've made it this far, you already know how to follow the traces. Find the final record." Thẻ đề lưu được 24 lời giải; điểm và độ khó không được ghi nhận nên bài này không nêu con số đó. Đây là bài cuối của chuỗi sáu bài Forensics dùng chung một ảnh.

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

### "Bản ghi còn mở" là tiến trình nào

Trong danh sách process tại thời điểm capture có `notepad.exe` vẫn đang giữ một file mở — bản ghi gốc từ `process_list()`:

```text
PID=4968|PPID=6960|NAME=notepad.exe|FULL=notepad.exe|PATH=C:\Windows\system32\notepad.exe|SES=1|STATE=0|INTEG=5|EPROC=18446703458198831232
   CMD="C:\Windows\system32\notepad.exe" C:\Users\nightwatch\Documents\Vormir\expedition.txt
```

PPID 6960 là `powershell.exe` — cùng tiến trình cha đã spawn `SoulHunt_7F31.exe` ở Mem-2. Buffer văn bản của notepad nằm trong memory của chính process, nên "bản ghi còn mở khi mọi thứ dừng lại" là nội dung file trong RAM, không phải file trên đĩa.

## Lời giải

### Đọc bản ghi

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

Dòng `Artifact reference:` chứa 52 ký tự hex, giải mã ra 26 byte `OWASP{soulstone_note_3c91}`. Bản ghi UTF-16 nằm ở vùng vật lý bắt đầu `0x24f3900`, điểm khớp chuỗi `Artifact reference` là `0x24f3afa`. Script xử lý được cả trường hợp hex bị ngắt dòng hoặc chèn byte `\x00` của UTF-16 bằng cách bỏ qua các byte phân cách khi gom.

### Xác nhận bản ghi thuộc về notepad

Tìm chuỗi hex và tiêu đề bản ghi trong address space của từng process ứng viên bằng `VmmProcess.search()` của MemProcFS (needle ≤32 byte):

```text
PID 4968 notepad.exe  note-hexpart-ascii   n=4  [0x12d19118ff7, 0x12d19119127, 0x12d19119847, 0x12d19121700]
PID 4968 notepad.exe  ExpeditionLog-utf16  n=1  [0x12d190edc18]
PID 4968 notepad.exe  VormirExped-ascii    n=4  [0x12d191190a7, 0x12d191191d7, 0x12d191198f7, 0x12d19121690]
```

Chỉ PID 4968 cho kết quả; `mspaint.exe` (1204), `Photos.exe` (4824/2820), `explorer.exe` (8900), `powershell.exe` (6960), `SoulHunt_7F31.exe` (2580) và `dwm.exe` (1076) đều không chứa bản ghi này.

### Số bản và biến thể văn bản

Chuỗi hex của bản ghi xuất hiện **43 lần** trong ảnh, gồm cả bản ASCII lẫn UTF-16, các bản giải mã được cho cùng một giá trị. Bản ASCII tại `0xd21d5ed`, `0x13251c65`, `0x16cf8075`, `0x2d2c76ce`, `0x5eb77b25`, `0x6f8ec0f5`, `0x6f8ec815`; bản ở `0x5eb77b25` bị dữ liệu khác đè lên (`...5f33633.317d`) nên không giải mã được. Có hai phần đuôi khác nhau của cùng bản ghi:

```text
The trail ends with this record. If you are reading this, you've uncovered what the others
missed. The journey is complete. Well done, traveler. -- Vormir Expedition Log

The remaining records appear to be unrelated.
\Registry\Machine\...\HKEY_USERS\S-1-5-21-3525304513-4119828853-1302462655-1000\...
```

Lệnh tạo file vẫn còn trong history: `"@ | Set-Content "$env:USERPROFILE\Documents\Vormir\expedition.txt"`, và `ActivitiesCache`/UserEngaged JSON ghi `1:{...}\notepad.exe` — bản ghi này được mở qua notepad.

## Kết quả

```text
OWASP{soulstone_note_3c91}
```

Cờ đọc trực tiếp từ ảnh bộ nhớ (buffer UTF-16 của `notepad.exe` PID 4968 đang mở `Documents\Vormir\expedition.txt`) và bảng solved của nền tảng xác nhận giá trị này đã được chấp nhận.

## Tái hiện

Chỉ cần Python 3 (`mmap`, `re`, `binascii`). Lưu block `python` cuối bài thành `solve.py`, chạy:

```bash
python solve.py soul.mem
```

Script tìm `Artifact reference` ở cả ASCII và UTF-16, gom hex (bỏ `\x00`, newline, khoảng trắng) và in toàn văn bản quanh mỗi bản. Không cần symbol table vì buffer của notepad được đọc trực tiếp trên ảnh raw; bước quy chủ process dùng `VmmProcess.search()` của MemProcFS như đã mô tả ở trên.

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
