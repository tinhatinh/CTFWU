---
title: "Lossless, Not Harmless"
category: "Forensics"
tags: ["deflate", "steganography"]
solve_date: "2026-10-11T04:34:00+07:00"
language: "vi"
---

# Lossless, Not Harmless

**Flag:** `isfcr{ch0ic3s_th3_d3c0d3r_n3v3r_s33s}`  
**Artifact:** `mosaic_0417.png` (17,492 bytes; 256 × 300 pixels, indexed-color PNG)  
**Archive:** `lossless-not-harmless.zip`
| Artifact | SHA-256 |
|---|---|
| `mosaic_0417.png` | `6362e0e2d4e6eaa84ebce95850ef5100a3eeaa25f58c4faabc2e59240501736a` |

## Đề bài

Khôi phục message ẩn trong PNG đã qua lossless compressor. Dữ liệu ẩn nằm trong lựa chọn encoding DEFLATE, không phải pixel hiển thị.

## Phân tích

PNG indexed-color 256×300 có chín IDAT chunk. Nối payload IDAT thành một zlib stream trước khi phân tích. Flag trong Comment Base64 và flag từ pixel LSB là decoy. Trường Software hướng tới quyết định của compressor. Re-save PNG có thể làm mất encoding ban đầu dù ảnh không đổi.

```text
dfl-stitch 2.3 (equivalent-match mode, flush=sync)
```

## Lời giải

1. Nối IDAT theo thứ tự file: zlib stream 16415 byte, giải nén thành 77100 byte scanline/filter data.
2. Parse DEFLATE theo bit, duy trì output dictionary. Stream có 87 block, 5852 LZ77 match và 31 empty stored block dùng làm sync flush.
3. Thu bit padding khi căn byte trước LEN/NLEN ở empty stored block. Ghép theo thứ tự truyền được 128 bit secret; decoder thông thường bỏ qua các giá trị này.
4. Với mỗi LZ77 match, tìm các distance khác cho đúng cùng output và có cùng encoded bit cost dưới Huffman tree đang dùng. Có 3516 match có lựa chọn tương đương; lựa chọn distance mang bit của covert channel.
5. Đọc frame `DFL8`, dùng padding secret để dựng keystream SHA-256 và gỡ mask. Kiểm tra HMAC-SHA256 rồi lấy flag. Hai kênh ẩn không thay đổi image sau giải nén.

   ```text
   2814c69217b303ec00c6280fa2c50286
   ```

   ```text
   isfcr{ch0ic3s_th3_d3c0d3r_n3v3r_s33s}
   ```

## Kết quả

Flag đến từ compression-side payload. Lời giải nguồn ghi HMAC verification thành công; không lưu phản hồi submission.

`isfcr{ch0ic3s_th3_d3c0d3r_n3v3r_s33s}`

## Tái hiện

Giữ nguyên PNG gốc và kiểm tra SHA-256. Python block dưới đây chỉ xác minh container và stream; để lấy hidden payload phải có bit-level DEFLATE parser, thu padding và các distance choice rồi kiểm tra HMAC. `zlib.decompress()` đơn thuần không cung cấp các dữ kiện đó. Bản nguồn chưa kèm implementation đầy đủ của decoder covert channel.

```python
import hashlib
import struct
import zlib
from pathlib import Path

png = Path("mosaic_0417.png").read_bytes()
assert png[:8] == b"\x89PNG\r\n\x1a\n"
assert hashlib.sha256(png).hexdigest() == (
    "6362e0e2d4e6eaa84ebce95850ef5100a3eeaa25f58c4faabc2e59240501736a"
)

pos = 8
idat = []
while pos < len(png):
    size = struct.unpack_from(">I", png, pos)[0]
    kind = png[pos + 4:pos + 8]
    data = png[pos + 8:pos + 8 + size]
    if kind == b"IDAT":
        idat.append(data)
    pos += 12 + size  # length, type, data, CRC

compressed = b"".join(idat)
plain = zlib.decompress(compressed)
assert len(idat) == 9
assert len(compressed) == 16415
assert len(plain) == 77100
print("PNG and zlib stream verified")
```

```text
IDAT chunks:                  9
Concatenated zlib bytes:      16415
Decompressed image bytes:     77100
DEFLATE blocks:               87
Empty sync-flush blocks:      31
LZ77 match commands:          5852
Matches with cost-equivalent distances: 3516
Alignment padding bits:       128
Padding secret (hex):         2814c69217b303ec00c6280fa2c50286
FLAG isfcr{ch0ic3s_th3_d3c0d3r_n3v3r_s33s}
```

### Chuỗi đối chứng trong artifact

`isfcr{lsb_is_the_first_place_everyone_looks}`, `isfcr{nope_not_this_one}`
