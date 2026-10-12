---
title: "The Last Committed Message"
category: "Forensics"
tags: ["sqlite", "wal"]
solve_date: "2026-10-10T20:18:00+07:00"
language: "vi"
---

# The Last Committed Message

**Flag:** `isfcr{a03a410f1b87dbc115dd1ef6}`  
**Artifact:** `handout (25).zip`, containing `case.db` and `case.db-wal`

| Artifact | Size (bytes) | SHA-256 |
|---|---:|---|
| `handout (25).zip` | 153,640 | `b469c8398e94bd72df27727f9dd0e01ae132a7693ff9d59139b089885bda954d` |
| `case.db` | 109,056 | `1d64b36fb823dfd2ee85128f6ac60e6763150b4dd5a103ac86524cae81a033d5` |
| `case.db-wal` | 824,400 | `652feccb00173482e1fa2b8796e16883b74e0928330f7dc377504acc912c8d84` |

## Đề bài

Khôi phục note và attachment ngay sau operation tương ứng export `export-07abca69cd99` được acknowledged. Evidence gồm note ID, revision thập phân, destination nguyên văn và attachment SHA-256 lowercase.

## Phân tích

SQLite có notes, attachments, operations. Cùng export ID có log timed-out và acknowledged; operation đúng là `op-09e0d79b4b14`. Không lấy note revision mới nhất.

WAL có page 512 byte, frame header 24 byte, file header 32 byte; 1538 frame trải qua nhiều salt generation. Cần replay snapshot lịch sử thay vì query database hiện hành.

```json
{"export_id":"export-07abca69cd99","operation_id":"op-c46dc0e04bdd","status":"timeout"}
{"export_id":"export-07abca69cd99","operation_id":"op-09e0d79b4b14","status":"acknowledged"}
```

## Lời giải

1. Chọn log acknowledged, loại operation timed-out `op-c46dc0e04bdd`.
2. Replay page image theo thứ tự WAL lên bản copy DB. Frame có committed database size khác 0 đánh dấu commit. Snapshot cần tìm commit ở frame 455, page 197, DB size 208 page. Truncate về 208*512 byte và mở SQLite immutable để không áp dụng WAL mới.
3. Join operation replace với `note-7211098c21a6` và attachment row. Note phải trỏ lại đúng operation.
4. Destination SFTP URL dài 1097 ký tự cần lấy nguyên văn; không trim, decode hoặc tự dựng lại. Kiểm tra digest của string theo output nguồn.
5. Serialize bốn evidence string thành compact JSON dài 1192 byte. Scrypt dùng password prefix forensics/NUL, salt của đề, n=131072,r=8,p=1,dklen=32; AES-GCM AAD `the-last-committed-message` xác thực flag.

   ```text
   operation_id:      op-09e0d79b4b14
   operation_kind:    replace
   note_id:           note-7211098c21a6
   revision:          5
   attachment_id:     blob-72346f69c681
   attachment_sha256: b89d5c5695803071522614060828e31e9bb4bc25813fdbc5d516db06ac4c2d58
   ```

   ```text
   destination prefix: sftp://drop-edef61bb364d.example.invalid/inbox/
   destination suffix: .bin?ticket=a638d0e59bf0b87a8d34c22020f0555d
   SHA256(destination as ASCII): 71f49877090ba2d233c76ef472a57a6867872c4c443b5434cecc6a3b7f1c8946
   ```

   ```python
   evidence = [note_id, "5", destination, "b89d5c5695803071522614060828e31e9bb4bc25813fdbc5d516db06ac4c2d58"]
   E = json.dumps(evidence, ensure_ascii=True, separators=(",", ":")).encode("ascii")
   ```

## Kết quả

Key từ evidence của snapshot frame 455 đã vượt qua AES-GCM authentication.

`isfcr{a03a410f1b87dbc115dd1ef6}`

## Tái hiện

Cài cryptography. Lưu Python block thành solve.py cạnh `handout (25).zip`. Code replay tới frame đã xác định, lấy destination nguyên văn từ DB và dựng evidence; các checksum/output ở dưới dùng để đối chiếu.

```bash
python -m pip install cryptography
```

```python
import hashlib
import json
import sqlite3
import struct
import tempfile
import zipfile
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ZIP = Path("handout (25).zip")
TARGET_OP = "op-09e0d79b4b14"
TARGET_COMMIT = 455

with zipfile.ZipFile(ZIP) as archive:
    db_name = next(n for n in archive.namelist() if n.endswith("/case.db"))
    wal_name = next(n for n in archive.namelist() if n.endswith("/case.db-wal"))
    db = bytearray(archive.read(db_name))
    wal = archive.read(wal_name)

assert struct.unpack_from(">I", wal, 0)[0] in (0x377F0682, 0x377F0683)
page_size = struct.unpack_from(">I", wal, 8)[0] or 65536
assert page_size == 512
frame_size = 24 + page_size
assert len(wal) >= 32 + TARGET_COMMIT * frame_size

last_committed_db_pages = None
for frame in range(1, TARGET_COMMIT + 1):
    off = 32 + (frame - 1) * frame_size
    page_number, commit_pages = struct.unpack_from(">II", wal, off)
    assert page_number > 0
    end = page_number * page_size
    if len(db) < end:
        db.extend(b"\x00" * (end - len(db)))
    db[end - page_size:end] = wal[off + 24:off + frame_size]
    if commit_pages:
        last_committed_db_pages = commit_pages

assert last_committed_db_pages == 208
snapshot = db[:last_committed_db_pages * page_size]

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "snapshot.db"
    path.write_bytes(snapshot)
    con = sqlite3.connect(path.as_uri() + "?immutable=1", uri=True)
    try:
        op = con.execute(
            "SELECT note_id, operation_kind FROM operations WHERE operation_id = ?",
            (TARGET_OP,),
        ).fetchone()
        assert op and op[1] == "replace"

        note = con.execute(
            "SELECT note_id, revision, destination, attachment_id, operation_id "
            "FROM notes WHERE note_id = ?",
            (op[0],),
        ).fetchone()
        assert note and note[4] == TARGET_OP

        (attachment_sha256,) = con.execute(
            "SELECT sha256 FROM attachments WHERE attachment_id = ?",
            (note[3],),
        ).fetchone()
    finally:
        con.close()

note_id, revision, destination, attachment_id, operation_id = note
evidence = [note_id, str(revision), destination, attachment_sha256]
E = json.dumps(evidence, ensure_ascii=True, separators=(",", ":")).encode("ascii")

assert note_id == "note-7211098c21a6" and revision == 5
assert len(destination) == 1097 and len(E) == 1192
assert hashlib.sha256(destination.encode("ascii")).hexdigest() == (
    "71f49877090ba2d233c76ef472a57a6867872c4c443b5434cecc6a3b7f1c8946"
)

key = hashlib.scrypt(
    b"isfcr-forensics\x00" + E,
    salt=bytes.fromhex("a3845b1a904c5ee73abe7329b5d735d7"),
    n=131072, r=8, p=1, maxmem=2**28, dklen=32,
)
flag = AESGCM(key).decrypt(
    bytes.fromhex("ca98cff993b27fd3bb352436"),
    bytes.fromhex(
        "3fa8b9049b01fb8d12df130b404352f9c678c272cccb7e6c034554c902f1ca4d574fc04db8892fead1ad394735e021"
    ),
    b"the-last-committed-message",
).decode("ascii")

print("Operation:", operation_id)
print("Note:", note_id)
print("Revision:", revision)
print("Attachment:", attachment_id)
print("Destination length:", len(destination))
print("Evidence bytes:", len(E))
print("FLAG", flag)
```

```text
Operation: op-09e0d79b4b14
Note: note-7211098c21a6
Revision: 5
Attachment: blob-72346f69c681
Destination length: 1097
Evidence bytes: 1192
FLAG isfcr{a03a410f1b87dbc115dd1ef6}
```
