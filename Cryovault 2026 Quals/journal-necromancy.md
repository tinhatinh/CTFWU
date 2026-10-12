---
title: "Journal Necromancy"
category: "Forensics"
tags: ["ntfs", "aes-gcm"]
solve_date: "2026-10-10T11:36:00+07:00"
language: "vi"
---

# Journal Necromancy

**Flag:** `isfcr{mft_slack_dies_but_data_clusters_remember_1a2f}`  
**File:** `journal-necromancy.zip` (233,259 bytes), containing `evidence.img` (67,108,864 bytes; SHA-256 `CF9778B03EBE40DD10AE258B0F118576C47DED780C22B169BC73F4A6FFAFD07E`)

## Đề bài

Khôi phục key đã bị xóa khỏi NTFS image 64 MiB, giải mã archive và lấy flag.

## Phân tích

`Personal/reminders.txt` mô tả archive AES-256-GCM và cách chia key thành ba share 32 byte. Mỗi carrier có index 1–3, share và một byte XOR parity. File mã hóa gồm magic `ENC1`, nonce 12 byte, ciphertext và tag 16 byte.

## Lời giải

Đọc ba carrier 34 byte tại offset `0x28b4a61`, `0x2f65964`, `0x36187d2`. Kiểm tra parity là XOR của 33 byte trước nó và index đúng 1,2,3. XOR ba share để dựng key 32 byte. Tách nonce ngay sau magic ENC1, rồi giải mã authenticated với ciphertext/tag còn lại. Script và plaintext thu được nằm trong các block dưới đây.

| Image offset | Index | Parity check |
|---|---:|---|
| `0x28b4a61` | 1 | valid |
| `0x2f65964` | 2 | valid |
| `0x36187d2` | 3 | valid |

```python
from pathlib import Path
import sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

image_path, archive_path = map(Path, sys.argv[1:3])
image = image_path.read_bytes()

carriers = []
for offset, expected_index in [
    (0x28B4A61, 1),
    (0x2F65964, 2),
    (0x36187D2, 3),
]:
    record = image[offset:offset + 34]
    if len(record) != 34 or record[0] != expected_index:
        raise ValueError(f"Invalid carrier at {offset:#x}")
    parity = 0
    for byte in record[:33]:
        parity ^= byte
    if parity != record[33]:
        raise ValueError(f"Parity mismatch at {offset:#x}")
    carriers.append(record[1:33])

key = bytes(a ^ b ^ c for a, b, c in zip(*carriers))
archive = archive_path.read_bytes()
if archive[:4] != b"ENC1":
    raise ValueError("Unexpected archive marker")

plaintext = AESGCM(key).decrypt(archive[4:16], archive[16:], None)
print(plaintext.decode())
```

```text
isfcr{mft_slack_dies_but_data_clusters_remember_1a2f}
```

## Kết quả

Flag được đọc từ plaintext sau khi GCM tag xác thực.

```text
isfcr{mft_slack_dies_but_data_clusters_remember_1a2f}
```

## Tái hiện

Cài Python 3 và `cryptography`. Dùng 7-Zip giải nén ZIP và lấy encrypted file từ NTFS image. Lưu Python block ở phần Lời giải thành `solve.py`; truyền image cùng file mã hóa theo các lệnh dưới đây. Không cần tạo script khác.

```powershell
7z x journal-necromancy.zip -owork
7z x work\journal-necromancy\evidence.img -owork\image
python -m pip install cryptography
python solve.py work\journal-necromancy\evidence.img work\image\Personal\vault\secure_archive.enc
```
