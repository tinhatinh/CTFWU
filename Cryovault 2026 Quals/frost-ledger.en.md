---
title: "frost-ledger"
category: "Forensics"
tags: ["filesystem", "copy-on-write"]
solve_date: "2026-10-10T16:43:00+07:00"
language: "en"
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

## Challenge

Bay 07's controller cabinet failed, destroying access to the vendor's registry reader. We were given an offline Frostline Vault Registry (FVR) volume, the shipped `fvrctl` utility, documentation, an SDK header, and the last controller log. Recover the `authority-token` belonging to the registry key `bay/07/thaw-authority`.

## Initial Analysis

The provided `fvrctl` binary is usable for metadata inspection, but its version 1.4.2 no longer supports the `get` or `walk` subcommands. The release notes also say that the `libfvr` reader is missing from the controller image. Therefore, the record must be recovered by reading `registry.fvr` directly.

```text
$ usr/sbin/fvrctl info registry.fvr
volume            FVR, on-disk format version 1
page_size         4096
page_count        3072
file_size         12582912 bytes
root_slots        8
```

**The main format trap:** `ONDISK-NOTES.txt` describes format **v0**, not the actual on-disk **v1** volume. The 1.3.0 release notes and `fvr_format.h` show that v1 descriptors have a **16-byte** layout (`koff`, `ksize`, `vsize`, `voff`, `flags`) instead of v0's 12 bytes. In this volume, the v1 payload offsets are interpreted backward from the end of a 4096-byte page: a payload of length `size` at offset `off` is `page[4096 - off : 4096 - off + size]`. Using the forward offsets documented for v0 produces incorrect keys and values.

The controller log supplies a separate clue: a policy change caused `bay/07/thaw-authority` to be **re-issued**, and the superseded record was deliberately retained in copy-on-write (CoW) history. Finding just any matching historical key is therefore not sufficient.

## Exploitation Chain

1. **Select the latest valid committed root.** The superblock contains eight root slots. Each slot has an epoch, root page ID and an FNV-1a 64-bit checksum over its first 24 bytes. `fvrctl lsroot registry.fvr` shows valid epochs 284 through 290, then epoch **291** at root page **3049** with a **TORN** checksum. Epoch 291 must be discarded. The latest valid committed root is **epoch 290**, `root_pgid = 3039` (slot 2).

2. **Traverse the live B+tree using the v1 layout.** Page **3039** is an INDEX page containing separator keys such as `seg/0052`, with child references. Since `bay/07/thaw-authority` sorts before the first separator, its branch goes to child page **3030**. Page 3030 is a DATA page at epoch 290. Its first cell has exactly the requested key, and the cell's flags are `0x2`, marking the value as out-of-line. The INDEX and DATA page CRC-32C checks pass.

3. **Interpret the overflow reference.** The DATA cell's inline value is 12 bytes: an 8-byte little-endian `head_pgid` followed by a 4-byte `total_len`. These decode to `head_pgid = 966` and **stored length 2372**. Importantly, the release notes say this length refers to the *stored* data, not its subsequently decoded form.

4. **Reassemble the overflow chain.** Each OVERFLOW page provides its own `next_pgid` and `bytes_used` fields; the pages are noncontiguous and must not be read with a fixed stride. Following the pointers yields:

   | Page | `next_pgid` | `bytes_used` |
   |---|---:|---:|
   | 966 | 2675 | 739 |
   | 2675 | 184 | 662 |
   | 184 | 355 | 489 |
   | 355 | 0 | 482 |

   The payload lengths total **739 + 662 + 489 + 482 = 2372 bytes**, exactly matching the overflow reference. All four overflow page CRC-32C checks pass. The SHA-256 of the reassembled stored data is `c05e2093a0b23e8198ec916780602a9c7464dbd7550dcb8aecd07e7cfa22b5ba`.

5. **Decode the current authority record.** The stored value begins with the zlib signature `78 da` and decompresses successfully into **3961 bytes** of plaintext. Its header identifies `FROSTLINE VAULT AUTHORITY RECORD`, `record-version: 4`, `epoch: 290`, and `bay: 07`. This agrees with the latest valid root, and the decoded plaintext contains:

   ```text
   authority-token: isfcr{stale_cow_67c1_root_fc8fe97f_backwards_heap}
   ```

   The decoded plaintext's SHA-256 is `49ebb0eea8c7fb3a43fc2df17a95d8cc09f25a3fc1d5b4dd6006ebc9500661d9`.

## Flag

`isfcr{stale_cow_67c1_root_fc8fe97f_backwards_heap}`

The token was recovered from the **latest valid committed** registry generation, with the root checksum, page CRC-32C values, overflow length and decompression checked. Older CoW records and the torn epoch-291 root must not override it. Submission acceptance by the CTF service was not independently verified.

## Reproduce

Extract the archive and enter the extracted directory:

```bash
tar -xzf frost-ledger.tar.gz
usr/sbin/fvrctl info registry.fvr
usr/sbin/fvrctl lsroot registry.fvr
```

Run the following standalone Python 3 reconstruction from that same directory. It selects the root by validating the FNV-1a checksums, verifies each visited page with CRC-32C, descends through the index, reads the v1 DATA cell, walks the overflow pointers, checks the declared stored length, decompresses the record and extracts `authority-token`:

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

Expected result:

```text
LIVE ROOT: epoch=290, page=3039
DATA: page=3030, cell_flags=0x2
OVERFLOW: 966 -> 2675 -> 184 -> 355; 2372 stored bytes
DECODED SHA256: 49ebb0eea8c7fb3a43fc2df17a95d8cc09f25a3fc1d5b4dd6006ebc9500661d9
FLAG isfcr{stale_cow_67c1_root_fc8fe97f_backwards_heap}
```
