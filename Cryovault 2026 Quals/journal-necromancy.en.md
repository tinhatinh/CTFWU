---
title: "Journal Necromancy"
category: "Forensics"
tags: ["ntfs", "aes-gcm"]
solve_date: "2026-10-10T11:36:00+07:00"
language: "en"
---

# Journal Necromancy

**Flag:** `isfcr{mft_slack_dies_but_data_clusters_remember_1a2f}`  
**Files:** `journal-necromancy.zip` (233,259 bytes), containing `evidence.img` (67,108,864 bytes; SHA-256 `CF9778B03EBE40DD10AE258B0F118576C47DED780C22B169BC73F4A6FFAFD07E`)

## Challenge

A 64 MiB NTFS image contains an encrypted archive. The encryption key was deliberately destroyed before seizure. Recover the key material from the image, decrypt the archive, and report its contents as the flag.

## Initial Analysis

The image contains `Personal\reminders.txt`, which describes the archive format and key recovery scheme. The encrypted file is `Personal\vault\secure_archive.enc` (85 bytes). Its format is a four-byte marker, a 12-byte nonce, ciphertext, and a 16-byte AES-GCM tag. The key is reconstructed by XORing three 32-byte shares. Each carrier contains a share, an index from 1 to 3, and an XOR parity byte.

The note also identifies the archive as AES-256-GCM. This makes the GCM tag useful for validating the reconstructed key: successful authenticated decryption confirms that the recovered key and file layout are consistent.

## Exploitation Chain

### Recover and validate the three carriers

Inspecting raw image offsets revealed three 34-byte carrier records. Their indices identify the shares, and each record's final byte is the XOR parity of the preceding 33 bytes (index plus share):

| Image offset | Index | Parity check |
|---|---:|---|
| `0x28b4a61` | 1 | valid |
| `0x2f65964` | 2 | valid |
| `0x36187d2` | 3 | valid |

XORing the three share payloads reconstructs the 32-byte AES key. The `ENC1` marker is a format header; the GCM operation uses the following 12 bytes as the nonce and the remainder as ciphertext plus tag.

The following script reproduces parity validation, key recovery, and authenticated decryption. It expects the extracted image and encrypted file as arguments.

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

Authenticated decryption produced the flag text:

```text
isfcr{mft_slack_dies_but_data_clusters_remember_1a2f}
```

## Flag

```text
isfcr{mft_slack_dies_but_data_clusters_remember_1a2f}
```

## Reproduce

Install Python 3 and the `cryptography` package. Extract the outer ZIP and then the NTFS image with 7-Zip:

```powershell
7z x journal-necromancy.zip -owork
7z x work\journal-necromancy\evidence.img -owork\image
python -m pip install cryptography
python solve.py work\journal-necromancy\evidence.img work\image\Personal\vault\secure_archive.enc
```

Save the Python code above as `solve.py`. The final command prints the flag after AES-GCM authentication succeeds.
