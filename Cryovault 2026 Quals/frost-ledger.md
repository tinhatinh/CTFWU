---
title: "frost-ledger"
category: "Forensics"
tags: ["filesystem", "copy-on-write"]
solve_date: "2026-10-10T16:43:00+07:00"
language: "vi"
---

# frost-ledger

**Flag:** `isfcr{stale_cow_67c1_root_fc8fe97f_backwards_heap}`  
**Artifact:** `frost-ledger.tar.gz` (SHA-256: `45bac57e1d504dbcbb323342ce4b7795f1ef1db024c1d52ea7edb539bce5a0ba`)

| Extracted artifact | SHA-256 |
|---|---|
| `registry.fvr` | `192685cab0fcb5a2617a472f563677879549dc071fa20e38429562613d0a1f9d` |
| `usr/sbin/fvrctl` | `6612893a19cc35206329b5c51835c313796ba4a591dbd02b5a6896e54facecbf` |
| `usr/share/doc/fvregd/ONDISK-NOTES.txt` | `b26f501f8c66ae5dfacb24939391c7e882bea5dd5b2d5875ac1c2171fec20ad5` |
| `usr/share/doc/fvregd/RELEASE-NOTES.txt` | `9d8a7b1ab4a4c499d4ac455749c054a3c0acfe125f1dac93ddab0e9d557b265d` |
| `include/fvr_format.h` | `9b77ccaa271838da7941991ba75c706a015a948e0d6d3a5b2f2649f1866db7a7` |

## Đề bài

Khôi phục `authority-token` của key `bay/07/thaw-authority` từ registry FVR offline. Artifact gồm volume, utility `fvrctl`, tài liệu format, SDK header và log cuối của controller.

## Phân tích

`fvrctl` 1.4.2 chỉ còn đọc metadata; không có `get`, `walk` hoặc thư viện reader. Cần đọc trực tiếp `registry.fvr`.

Tài liệu ONDISK mô tả v0, trong khi volume dùng v1. Descriptor v1 dài 16 byte, gồm `koff`, `ksize`, `vsize`, `voff`, `flags`. Payload nằm ngược từ cuối page 4096 byte: `page[4096-off:4096-off+size]`. Log cho biết token đã được cấp lại; record CoW cũ không phải đáp án hiện hành.

```text
$ usr/sbin/fvrctl info registry.fvr
volume            FVR, on-disk format version 1
page_size         4096
page_count        3072
file_size         12582912 bytes
root_slots        8
```

## Lời giải

1. Kiểm tra FNV-1a của tám root slot. Epoch 291 tại page 3049 bị torn; chọn epoch 290, root page 3039, slot 2.
2. Theo B+tree từ INDEX page 3039 tới DATA page 3030. Cell có đúng key cần tìm và flag `0x2`, tức giá trị nằm ngoài page. CRC-32C của hai page hợp lệ.
3. Overflow reference gồm `head_pgid = 966` và stored length 2372 byte. Đây là độ dài dữ liệu nén, không phải plaintext sau giải nén.
4. Theo `next_pgid`: 966 → 2675 → 184 → 355 → 0. Số byte dùng lần lượt 739, 662, 489, 482; tổng đúng 2372. Kiểm tra CRC-32C của từng page, sau đó ghép payload.
5. Dữ liệu có đầu zlib `78 da`, giải nén được 3961 byte. Header record ghi version 4, epoch 290 và bay 07, khớp root được chọn. Trích `authority-token` từ record này và đối chiếu SHA-256 của stored payload cùng plaintext.

   | Page | `next_pgid` | `bytes_used` |
   |---|---:|---:|
   | 966 | 2675 | 739 |
   | 2675 | 184 | 662 |
   | 184 | 355 | 489 |
   | 355 | 0 | 482 |

   ```text
   authority-token: isfcr{stale_cow_67c1_root_fc8fe97f_backwards_heap}
   ```

## Kết quả

Token nằm trong registry generation mới nhất còn commit hợp lệ. Root checksum, page CRC, overflow length và giải nén đều được kiểm tra.

`isfcr{stale_cow_67c1_root_fc8fe97f_backwards_heap}`

## Tái hiện

Giải nén archive rồi chạy Python block trong cùng thư mục với `registry.fvr`. Code chọn root qua FNV-1a, kiểm tra CRC-32C, duyệt B+tree, ghép overflow theo pointer, kiểm tra stored length, giải nén và in token. Các lệnh và output mong đợi giữ nguyên ở dưới.

```bash
tar -xzf frost-ledger.tar.gz
usr/sbin/fvrctl info registry.fvr
usr/sbin/fvrctl lsroot registry.fvr
```

```bash
python3 - <<'PY'
#!/usr/bin/env python3
import hashlib
import re
import struct
import zlib
from pathlib import Path

blob = Path('registry.fvr').read_bytes()
page_size, page_count, version = struct.unpack_from('<III', blob, 4)
assert page_size == 4096 and version == 1
assert len(blob) == page_size * page_count


def u32(data, offset=0):
    return struct.unpack_from('<I', data, offset)[0]


def crc32c(data):
    crc = 0xffffffff
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0x82f63b78 if crc & 1 else 0)
    return crc ^ 0xffffffff


def page(pgid):
    assert 0 < pgid < page_count
    p = blob[pgid * page_size:(pgid + 1) * page_size]
    assert u32(p) == pgid
    assert crc32c(p[24:]) == u32(p, 16), f'bad CRC32C on page {pgid}'
    return p


def cell_payload(p, off, size):
    # FVR on-disk format v1: offset is measured BACKWARD from page end.
    return p[page_size - off:page_size - off + size]


def cells(p):
    n = struct.unpack_from('<H', p, 14)[0]
    for i in range(n):
        koff, ksize, vsize, voff, flags = struct.unpack_from('<IHHII', p, 24 + i * 16)
        yield cell_payload(p, koff, ksize), cell_payload(p, voff, vsize), flags


def fnv1a64(data):
    h = 0xcbf29ce484222325
    for byte in data:
        h = ((h ^ byte) * 0x100000001b3) & 0xffffffffffffffff
    return h


roots = []
for i in range(8):
    slot = blob[16 + i * 32:16 + (i + 1) * 32]
    epoch, pgid = struct.unpack_from('<QI', slot)
    if epoch and fnv1a64(slot[:24]) == struct.unpack_from('<Q', slot, 24)[0]:
        roots.append((epoch, pgid))
epoch, pgid = max(roots)
print(f'LIVE ROOT: epoch={epoch}, page={pgid}')

target = b'bay/07/thaw-authority'
while True:
    p = page(pgid)
    kind = p[12]
    entries = list(cells(p))
    if kind == 1:
        # Separator entries address left children, final u32 is rightmost.
        choice = next((u32(value) for key, value, _ in entries if target < key), u32(p, page_size - 4))
        pgid = choice
    elif kind == 2:
        matches = [(value, flags) for key, value, flags in entries if key == target]
        assert len(matches) == 1
        value, flags = matches[0]
        print(f'DATA: page={pgid}, cell_flags=0x{flags:x}')
        break
    else:
        raise ValueError(f'unexpected kind={kind} on page {pgid}')

assert flags & 0x2 and len(value) == 12
head, total_len = struct.unpack('<QI', value)
parts, chain, seen = [], [], set()
while head:
    assert head not in seen, 'overflow loop'
    seen.add(head)
    q = page(head)
    assert q[12] == 3
    next_pgid, used = struct.unpack_from('<II', q, 24)
    assert used <= page_size - 32
    chain.append(head)
    parts.append(q[32:32 + used])
    head = next_pgid
stored = b''.join(parts)
assert len(stored) == total_len
print(f'OVERFLOW: {" -> ".join(map(str, chain))}; {len(stored)} stored bytes')

plaintext = zlib.decompress(stored)
assert b'record-version: 4\n' in plaintext
assert f'epoch: {epoch}\n'.encode() in plaintext
match = re.search(rb'^authority-token:\s*(isfcr\{[^\r\n}]+\})\s*$', plaintext, re.M)
assert match, 'authority-token missing'
print('DECODED SHA256:', hashlib.sha256(plaintext).hexdigest())
print('FLAG', match.group(1).decode())
PY
```

```text
LIVE ROOT: epoch=290, page=3039
DATA: page=3030, cell_flags=0x2
OVERFLOW: 966 -> 2675 -> 184 -> 355; 2372 stored bytes
DECODED SHA256: 49ebb0eea8c7fb3a43fc2df17a95d8cc09f25a3fc1d5b4dd6006ebc9500661d9
FLAG isfcr{stale_cow_67c1_root_fc8fe97f_backwards_heap}
```
