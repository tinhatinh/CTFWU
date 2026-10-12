---
title: "The Alphabet That Wasn't There"
category: "Forensics"
tags: ["pdf", "type3-font"]
solve_date: "2026-10-11T05:50:00+07:00"
language: "vi"
---

# The Alphabet That Wasn't There

**Flag:** `isfcr{d7ef3d5dd98bd325c3b50114}`  
**Artifact:** `damaged.pdf` (64,872 bytes), `reference.pdf` (4,011 bytes), distributed in `handout (29).zip`

| Artifact | SHA-256 |
|---|---|
| `damaged.pdf` | `52614107d762aad3ea07faf571c5d071cdd4e27b8b3f12581916074b583f4192` |
| `reference.pdf` | `cbaec694550465b9791790aac541963833fb8936bacc21c1560cce5ae2ff64af` |

## Đề bài

Giải grid 16×16 ký hiệu trong PDF có CaseID `9697624543591457a15dc6d9a4797c45`. Reference gán 16 hình ký hiệu cho chuỗi hex `8bd4e257f916c30a`. Đọc hàng theo baseline y giảm và cột theo x tăng trong default PDF user space; glyph xoay vẫn giữ danh tính.

## Phân tích

Type3 glyph name và char code không trực tiếp là digit. PDF bị hỏng/incremental, có hai EOF marker, page Rotate 90 và bốn Form XObject có transform. MuPDF thấy 358 glyph occurrence, nhiều hơn 256 cell, nên phải loại overlay/hidden drawing. Không dùng thứ tự screen-space hoặc thứ tự content stream làm grid.

```text
Reference symbols, left to right:
8 b d 4 e 2 5 7 f 9 1 6 c 3 0 a
```

## Lời giải

1. Xác nhận CaseID trong catalog và resolve Form XObject/matrix.
2. Đối chiếu hình vector với reference để dựng map glyph→hex; không phụ thuộc encoding ngẫu nhiên hoặc góc xoay.
3. Gom occurrence theo baseline cell gốc, loại drawing thừa. Sort y giảm rồi x tăng để lấy đúng 256 hex digit, giữ grid trong code block dưới đây.
4. Dựng evidence `[caseid,grid]` bằng ASCII lowercase, serialize compact JSON không thêm whitespace/newline. Prefix `b"isfcr-forensics\x00"` làm scrypt password input.
5. Dùng salt của đề, scrypt n=131072,r=8,p=1,dklen=32,maxmem=2**28. Decrypt AES-GCM với nonce và AAD `the-alphabet-that-wasnt-there`; tag hợp lệ xác nhận evidence đã dùng.

   ```text
   e7463684552dfb02
   7076afdf977a1a94
   bb89d9112b4ace4b
   c9207e7c18b3fbf5
   5526ba3a9e437c7d
   6c4a3ef3bf7e0dcd
   4694f7288fc5d4c1
   89be389bbbaadd51
   4031b50de7eba382
   0e5230915ddfa4bc
   c793d2b7aa7c880f
   1900cd60b1caedd9
   507009b6658d86d3
   ce052d46f8f4c16d
   13c9e5e6302733f3
   906ff5e24f690ab6
   ```

## Kết quả

GCM authentication kiểm tra evidence gồm CaseID, glyph và thứ tự grid.

`isfcr{d7ef3d5dd98bd325c3b50114}`

## Tái hiện

Cài cryptography. Script dưới đây dùng 16 hàng grid đã giải để kiểm tra 256 digit, serialize evidence và decrypt. Nó tái hiện bước xác thực cuối, không tự thực hiện toàn bộ việc phân loại glyph của PDF. Đổi glyph, thứ tự cell hoặc JSON serialization sẽ làm key khác và báo InvalidTag.

```python
import hashlib
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

caseid = "9697624543591457a15dc6d9a4797c45"
grid_rows = """
e7463684552dfb02
7076afdf977a1a94
bb89d9112b4ace4b
c9207e7c18b3fbf5
5526ba3a9e437c7d
6c4a3ef3bf7e0dcd
4694f7288fc5d4c1
89be389bbbaadd51
4031b50de7eba382
0e5230915ddfa4bc
c793d2b7aa7c880f
1900cd60b1caedd9
507009b6658d86d3
ce052d46f8f4c16d
13c9e5e6302733f3
906ff5e24f690ab6
""".strip().splitlines()
assert len(grid_rows) == 16 and all(len(row) == 16 for row in grid_rows)
grid = "".join(grid_rows)
assert len(grid) == 256 and all(c in "0123456789abcdef" for c in grid)

E = json.dumps([caseid, grid], ensure_ascii=True,
               separators=(",", ":")).encode("ascii")
key = hashlib.scrypt(
    b"isfcr-forensics\x00" + E,
    salt=bytes.fromhex("8a251a8101ffa67ed383a445a05e77f2"),
    n=131072, r=8, p=1, maxmem=2**28, dklen=32,
)
nonce = bytes.fromhex("cf5d90d20b821db4c5bf1b73")
ciphertext_and_tag = bytes.fromhex(
    "27b4469da3cc30f3ec487d60be3053aa2d5aa00c9f4da69fe54e7d51da8463883b4aa1b0a10a69c45c4e974171133f"
)
flag = AESGCM(key).decrypt(
    nonce, ciphertext_and_tag, b"the-alphabet-that-wasnt-there"
).decode("ascii")
print("Grid SHA-256:", hashlib.sha256(grid.encode("ascii")).hexdigest())
print("AES-GCM authentication: OK")
print("FLAG", flag)
```

```text
Grid SHA-256: 59079651bfa1efcbf31856828c304b6070b3816baea8ecaa51f2fd0633097d0d
AES-GCM authentication: OK
FLAG isfcr{d7ef3d5dd98bd325c3b50114}
```
