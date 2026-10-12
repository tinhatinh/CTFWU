---
title: "Ghost in the Spooler"
category: "Forensics"
tags: ["print-spooler", "mic"]
solve_date: "2026-10-10T16:48:00+07:00"
language: "vi"
---

# Ghost in the Spooler

**Flag:** `isfcr{e24d16be9d731cba}`  
**Artifact:** `FP02CF4.SHD` (520 bytes), `FP02CF4.SPL` (1,872 bytes), `scan.png` (2550 × 3300 pixels)
| Artifact | SHA-256 |
|---|---|
| `FP02CF4.SHD` | `9c5ad49f547e714a90c223be955c14669c3a7725ccf5bb1b1015e743f832ada0` |
| `FP02CF4.SPL` | `afe8591220aa739d239efa86fe78e5a089b06206a599047fe248954bf235e1de` |
| `scan.png` | `4ba72a26304220be725ae5cdc98f963e65feae4d1114721832c62026a086691a` |

## Đề bài

Đối chiếu print job Windows với trang scan rồi dựng flag từ username chữ thường, serial máy in bảy chữ số và thời gian in UTC chính xác tới phút. SHA-256 được lấy 16 ký tự hex đầu, không phải 16 byte.

```text
isfcr{SHA256(username + "|" + serial + "|" + timestamp)[:16]}
```

## Phân tích

Hai file spooler có chung stem `FP02CF4`. SHD chứa chuỗi UTF-16LE và FILETIME; SPL chứa nội dung EMF. Trang scan tương ứng memo in bằng Xerox DocuColor 12. Yellow-dot MIC cung cấp serial cùng thời gian, độc lập với metadata SHD.

```text
j.holbrook
Q3-Compensation-Adjustments.docx
\\PRINT01\HR-DocuColor-12
Xerox DocuColor 12 PS
NT EMF 1.008
FIN-WKS-014
```

## Lời giải

1. Đọc username và thời gian FILETIME trong SHD; chuyển về UTC và đặt giây bằng 00.
2. Đối chiếu nội dung EMF với scan để xác nhận đúng print job.
3. Đọc grid MIC 15 cột × 8 hàng tại tâm pixel `x=90+9*c`, `y=60+9*r`. Pixel yellow-dot có RGB `(250,246,160)`. Kiểm tra odd parity trên tám hàng và cột 2–15 để tránh lệch grid.
4. Giải mã trường thời gian và bảy chữ số serial theo layout trong bảng. Phút MIC phải khớp FILETIME.
5. Nối `username|serial|utc_time` không thêm whitespace; băm SHA-256 rồi lấy 16 ký tự hex đầu. Kết quả là `e24d16be9d731cba`.

   | Column(s), left to right (1-based) | Decoded values | Interpretation |
   |---|---|---|
   | 2–6 | `37, 14, 17, 9, 24` | Minute, hour, day, month, two-digit year |
   | 7–13 | `8, 8, 4, 2, 0, 1, 3` | Seven serial-number digits |
   | 14–15 | `0, 0` | Unused fields in this example |

   ```text
   username = j.holbrook
   ```

   ```text
   timestamp = 2024-09-17T14:37:00Z
   ```

   ```text
   serial = 8842013
   MIC time = 2024-09-17 14:37
   ```

   ```text
   j.holbrook|8842013|2024-09-17T14:37:00Z
   ```

   ```text
   e24d16be9d731cba62793f93bbd3cf637d1450862c06197e37473d026b6908bd
   ```

## Kết quả

Flag được suy ra từ print-job metadata và MIC, không phải chuỗi có sẵn trong artifact.

`isfcr{e24d16be9d731cba}`

## Tái hiện

Giải nén để ba artifact nằm dưới `ghost-spooler/`. Cài Pillow nếu cần. Chạy Python block từ thư mục cha; script đọc SHD, kiểm tra MIC, dựng chuỗi evidence và băm. Công thức, bảng bit và output giữ nguyên trong các block dưới đây.

```python
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from struct import unpack_from
from PIL import Image

root = Path("ghost-spooler")
shd = (root / "FP02CF4.SHD").read_bytes()
spl = (root / "FP02CF4.SPL").read_bytes()

# Print-job owner, stored as UTF-16LE in the SHD file.
username = shd[0x100:0x118].decode("utf-16le").split("\0")[0].lower()

# FILETIME: 100-ns ticks since midnight, 1601-01-01 UTC.
filetime = unpack_from("<Q", shd, 0x40)[0]
printed_at = datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(
    microseconds=filetime // 10
)
timestamp = printed_at.strftime("%Y-%m-%dT%H:%M:00Z")

# Cross-check that the spooled content is the memorandum in the scan.
assert "Q3 Compensation Adjustments".encode("utf-16le") in spl
assert "MEMORANDUM".encode("utf-16le") in spl

# One repeating 15x8 yellow-dot MIC grid in this exact supplied scan.
image = Image.open(root / "scan.png").convert("RGB")
dots = [
    [image.getpixel((90 + 9 * col, 60 + 9 * row)) == (250, 246, 160)
     for col in range(15)]
    for row in range(8)
]

# Parity: odd in each row and in columns 2..15.
assert all(sum(row) % 2 == 1 for row in dots)
assert all(sum(dots[row][col] for row in range(8)) % 2 == 1
           for col in range(1, 15))

# Ignore the top parity row; columns 2..15 each encode seven data bits.
values = [
    sum(int(dots[row][col]) << (7 - row) for row in range(1, 8))
    for col in range(15)
]
assert values[1:6] == [printed_at.minute, printed_at.hour,
                       printed_at.day, printed_at.month, printed_at.year % 100]
assert all(0 <= digit <= 9 for digit in values[6:13])
serial = "".join(str(digit) for digit in values[6:13])

message = f"{username}|{serial}|{timestamp}"
digest = sha256(message.encode("ascii")).hexdigest()
flag = f"isfcr{{{digest[:16]}}}"

print("Username:", username)
print("Serial:", serial)
print("Timestamp:", timestamp)
print("Input:", message)
print("SHA-256:", digest)
print("FLAG", flag)
```

```text
Username: j.holbrook
Serial: 8842013
Timestamp: 2024-09-17T14:37:00Z
Input: j.holbrook|8842013|2024-09-17T14:37:00Z
SHA-256: e24d16be9d731cba62793f93bbd3cf637d1450862c06197e37473d026b6908bd
FLAG isfcr{e24d16be9d731cba}
```
