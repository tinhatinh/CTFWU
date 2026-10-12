---
title: "Mem-3 : The Painted Soul"
category: "Forensics"
tags: ["memory-forensics", "memprocfs", "hex-fragment-harvest", "utf-16", "image-carving"]
solve_date: "2026-10-09"
language: "vi"
---

# Mem-3 : The Painted Soul

**Flag:** `OWASP{soulstone_paint_52af}`
**Artifact:** `soul.zip` 937,376,339 B (sha256 `94d15b80b78402ab027a6ab4f40d288babef7d938631766d25c1d5bcb6fd9ee0`) giải nén ra ảnh RAM `soul.mem` 2,774,466,560 B (`0xa55f0000`, sha256 `617d69406e571bc6a80af9e4517cb2ecc3839c508e0e8374463e38f7f70014e6`). Đề kèm một ảnh 1152×573 RGB chứa ba dòng hex, dòng cuối bị cắt.

## Đề bài

"Some things are easier to remember when they are seen. Find what was left behind." Hard, 300 điểm, 5 lời giải tại thời điểm làm. Ảnh đính kèm của đề hiển thị ba dòng hex, trong đó dòng thứ ba bị cắt giữa chừng:

```text
4f574153507b736f
756c73746f6e655f
7061696e745f3
```

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

### Hai quan sát định hướng

- Ghép hai dòng hex đọc được cho `OWASP{soulstone_paint_`; phần còn lại nằm ở dòng bị cắt nên phải lấy từ chính ảnh RAM.
- Chuỗi `OWASP{` dạng ASCII xuất hiện **0 lần** trong toàn ảnh, nhưng dạng UTF-16 xuất hiện 7 lần. Mọi phép tìm văn bản về sau phải chạy trên cả hai encoding.
- Ảnh không còn giữ được pixel. Quét toàn ảnh: 671 signature PNG cho 393 chuỗi chunk hợp lệ nhưng tất cả đều là icon/tile ứng dụng (bề rộng lớn nhất 1077 pixel, ảnh có diện tích lớn nhất 620×620 gói trong 242 byte); 1450 signature JPEG không có ảnh nào mở được bằng PIL; bốn `BITMAPINFOHEADER` 24/32bpp (360×369, 1000×500, 1700×876, 1920×1033) có số màu 38k–434k và render ra nhiễu, tức dữ liệu đã nén bị diễn giải sai thành bitmap.
- Ngược lại, header PNG của chính file ảnh đề bài thì còn: tại `0x2d13d000` có `IHDR 1152×573 bd=8 ct=2` cùng `sRGB`, `gAMA`, `pHYs` đều đúng CRC — trùng kích thước và kiểu màu với ảnh đính kèm. Nhưng chunk `IDAT` khai báo 18,632 byte không inflate được ở mọi chế độ `wbits` (15/-15/31/-8), nên phần dữ liệu nén không khôi phục được bằng các phép thử này; nguyên nhân có thể là thiếu hoặc hỏng trang nhớ.

Kết luận: không đọc cờ từ ảnh được; phải đọc fragment hex còn sót trong memory.

## Lời giải

### Gom hex fragment bất kể ngắt dòng

Các artifact của mission được ghi thành nhiều dòng 16 ký tự và ở dạng UTF-16, nên regex chuỗi hex liền mạch (≥40 ký tự) bỏ sót — chính xác là lý do token `paint` không xuất hiện khi quét regex. Cách đúng là bắt đầu từ mở đầu `4f57415350` (hex của `OWASP{`) ở cả hai encoding, rồi đọc tiếp ký tự hex, bỏ qua `\x00`, khoảng trắng và newline cho tới khi gặp `7d` (`}`).

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

Bảy giá trị, mỗi cái một bộ chứa; `soulstone_paint_52af` là duy nhất chỉ có **một bản** trong toàn ảnh.

### Khớp fragment của ảnh đề bài

```bash
python solve.py soul.mem 7061696e745f
```

```text
fragment b'7061696e745f' [utf16] @0x6cdc760c -> OWASP{soulstone_paint_52af}
```

Bản UTF-16 đầy đủ nằm tại offset vật lý `0x6cdc760c` (điểm bắt đầu chuỗi hex theo harvest là `0x6cdc75d0`; hiệu 60 byte = 30 ký tự hex × 2 byte UTF-16). Chuỗi đầy đủ 54 ký tự hex:

```text
4f574153507b736f 756c73746f6e655f 7061696e745f353261667d
```

giải mã ra 27 byte `OWASP{soulstone_paint_52af}`. Hai dòng đầu của khối này khớp từng ký tự với ảnh đề bài, còn dòng thứ ba trong ảnh bị cắt ở `7061696e745f3`; bản trong RAM chứa đủ phần đuôi `353261667d`.

## Kết quả

```text
OWASP{soulstone_paint_52af}
```

Cờ đọc trực tiếp từ ảnh bộ nhớ (bản UTF-16 duy nhất tại `0x6cdc760c`) và bảng solved của nền tảng xác nhận giá trị này đã được chấp nhận.

## Tái hiện

Chỉ cần Python 3 (`mmap`, `binascii`) và `soul.mem`. Lưu block `python` cuối bài thành `solve.py`, chạy:

```bash
python solve.py soul.mem
python solve.py soul.mem 7061696e745f
```

Lệnh đầu liệt kê mọi cờ giải được từ fragment hex; lệnh sau định vị fragment nhìn thấy trong ảnh đề bài và in chuỗi đầy đủ. Phần dựng ảnh (PNG/JPEG/DIB) bằng carver chuẩn cũng cho cùng kết luận: các phép carving đã chạy không khôi phục được ảnh mục tiêu.

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
