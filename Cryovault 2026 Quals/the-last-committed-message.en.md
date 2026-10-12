---
title: "The Last Committed Message"
category: "Forensics"
tags: ["sqlite", "wal"]
solve_date: "2026-10-10T20:18:00+07:00"
language: "en"
---

# The Last Committed Message

**Flag:** `isfcr{a03a410f1b87dbc115dd1ef6}`  
**Artifact:** `handout (25).zip`, containing `case.db` and `case.db-wal`

| Artifact | Size (bytes) | SHA-256 |
|---|---:|---|
| `handout (25).zip` | 153,640 | `b469c8398e94bd72df27727f9dd0e01ae132a7693ff9d59139b089885bda954d` |
| `case.db` | 109,056 | `1d64b36fb823dfd2ee85128f6ac60e6763150b4dd5a103ac86524cae81a033d5` |
| `case.db-wal` | 824,400 | `652feccb00173482e1fa2b8796e16883b74e0928330f7dc377504acc912c8d84` |

## Challenge

Recover the note and its attachment record **as they stood immediately after the operation associated with export `export-07abca69cd99` was acknowledged**. A note replacement, attachment-record upsert, and operation-record insertion commit atomically. The required evidence consists of four ASCII strings, in order:

1. Note ID.
2. Revision, as a decimal string.
3. Destination, exactly as stored.
4. Attachment SHA-256, in lowercase hexadecimal.

The challenge derives an AES-256-GCM key from the JSON-serialized evidence using `hashlib.scrypt`. Successful authenticated decryption reveals the flag.

## Initial Analysis

The archive contains a SQLite database (`case.db`) and its write-ahead log (`case.db-wal`). The database has three relevant tables:

- `notes(note_id, revision, destination, attachment_id, operation_id)`
- `attachments(attachment_id, sha256)`
- `operations(operation_id, note_id, operation_kind)`

The export log gives two entries for the **same** target export ID:

```json
{"export_id":"export-07abca69cd99","operation_id":"op-c46dc0e04bdd","status":"timeout"}
{"export_id":"export-07abca69cd99","operation_id":"op-09e0d79b4b14","status":"acknowledged"}
```

The first entry is not the requested acknowledgment. The operation to locate is therefore **`op-09e0d79b4b14`**. Also, the problem asks for a historical *committed snapshot*, not the newest state of the database. A later revision of the same note cannot be used to construct the key.

The WAL uses 512-byte SQLite pages, 24-byte frame headers, and a 32-byte file header. Accordingly, each frame occupies `24 + 512 = 536` bytes. The supplied WAL contains **1,538 frames** and preserves changes across multiple WAL salt generations. Simply querying the current database or relying on a normal WAL reader does not reconstruct the requested historical state.

## Exploitation Chain

1. **Identify the acknowledged export operation.** Filter the provided export log for `export-07abca69cd99` and `status == "acknowledged"`. This selects `op-09e0d79b4b14`, not the earlier timed-out operation `op-c46dc0e04bdd`.

2. **Reconstruct the committed SQLite snapshot.** Replay the page images in WAL order onto a copy of `case.db`. Each frame starts with its page number and an optional committed database size; a nonzero database-size field marks a transaction commit. The required acknowledged operation is present in the state committed at **WAL frame 455**. This frame has `page_number = 197` and `commit_db_size = 208`, so the recovered snapshot is truncated to `208 * 512` bytes. Opening the resulting database as an immutable SQLite file prevents later WAL processing from changing the recovered state.

3. **Join the operation, note, and attachment records.** In the frame-455 snapshot, the matching operation is a `replace` operation targeting `note-7211098c21a6`. Its note row points back to the same operation ID, and its attachment ID resolves to the SHA-256 recorded in the corresponding attachment row:

   ```text
   operation_id:      op-09e0d79b4b14
   operation_kind:    replace
   note_id:           note-7211098c21a6
   revision:          5
   attachment_id:     blob-72346f69c681
   attachment_sha256: b89d5c5695803071522614060828e31e9bb4bc25813fdbc5d516db06ac4c2d58
   ```

   The destination is a **1,097-character SFTP URL**. It must be read directly from the historical note row without trimming, decoding, or reconstructing it manually. Its checksums provide a compact independent verification:

   ```text
   destination prefix: sftp://drop-edef61bb364d.example.invalid/inbox/
   destination suffix: .bin?ticket=a638d0e59bf0b87a8d34c22020f0555d
   SHA256(destination as ASCII): 71f49877090ba2d233c76ef472a57a6867872c4c443b5434cecc6a3b7f1c8946
   ```

4. **Serialize the exact evidence and derive the key.** The evidence list is:

   ```python
   evidence = [note_id, "5", destination, "b89d5c5695803071522614060828e31e9bb4bc25813fdbc5d516db06ac4c2d58"]
   E = json.dumps(evidence, ensure_ascii=True, separators=(",", ":")).encode("ascii")
   ```

   `E` is **1,192 bytes**. Use `hashlib.scrypt` with password `b"isfcr-forensics\x00" + E`, salt `a3845b1a904c5ee73abe7329b5d735d7`, `n=131072`, `r=8`, `p=1`, and `dklen=32`.

5. **Authenticate and decrypt the flag.** Pass the supplied nonce (`ca98cff993b27fd3bb352436`), ciphertext/tag, and AAD (`the-last-committed-message`) to `AESGCM(key).decrypt`. Authentication succeeds and returns the flag.

## Flag

`isfcr{a03a410f1b87dbc115dd1ef6}`

The flag was recovered from the provided SQLite artifacts. The `scrypt`-derived key successfully passed AES-GCM authentication; this confirms that the recovered historical note and attachment evidence matches the encrypted challenge material. The flag was not submitted to the CTF platform here, so platform acceptance has not been independently verified.

## Reproduce

Install the sole nonstandard Python dependency:

```bash
python -m pip install cryptography
```

Save the following as `solve.py` next to `handout (25).zip`, then run `python solve.py`. The code uses the WAL frame identified during analysis and reads the destination **verbatim** from the reconstructed database:

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

Expected output:

```text
Operation: op-09e0d79b4b14
Note: note-7211098c21a6
Revision: 5
Attachment: blob-72346f69c681
Destination length: 1097
Evidence bytes: 1192
FLAG isfcr{a03a410f1b87dbc115dd1ef6}
```
