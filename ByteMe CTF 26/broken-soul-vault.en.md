---
title: "Broken Soul Vault"
category: "Forensics"
tags: ["metadata", "hex-decoding", "log-analysis", "file-recovery"]
solve_date: "2026-10-09"
language: "en"
---

# Broken Soul Vault

**Flag:** `OWASP{br0k3n_s0ul_v4ult_r3c0v3r3d}`
**Artifact:** `metadata.bin.txt` (87 B) and `vault.log` (133 B). Author: Pratik Jadhav.

## Challenge

Statement (Easy, 100 points):

```text
The Soul Vault suffered metadata corruption during a recovery operation. Identify the valid recovered block and decode its contents.
```

Two input files: `vault.log` describes the recovery session, `metadata.bin.txt` holds the "recovered" metadata blocks. The task is to pick the valid block among the corrupted ones and decode it.

## Analysis

`vault.log` has seven lines and ends with a direct pointer to the metadata file:

```text
OPEN vault
AUTH keeper
READ /soul/fragment
ERROR checksum mismatch
RECOVER block=17
RECOVER block=18
NOTE corrupted metadata follows
```

The event sequence is: read fragment -> checksum mismatch -> two `RECOVER` operations (block 17 and block 18) -> a note stating that the metadata which follows is corrupted. The log carries no data beyond context, so everything that needs decoding lives in `metadata.bin.txt`.

That file contains three hex lines, one block per line, recorded verbatim:

```text
00ff11aa
4f574153507b6272306b336e5f7330756c5f7634756c745f7233633076337233647d
deadbeef
```

Block lengths (counted in hex characters, then converted to bytes):

```text
block 1 :  8 hex chars ->  4 bytes
block 2 : 68 hex chars -> 34 bytes
block 3 :  8 hex chars ->  4 bytes
```

The two outer blocks decode to non-printable byte sequences:

```text
block 1 -> 00 ff 11 aa
block 3 -> de ad be ef
```

These are the usual sentinels for corrupt/junk data (`00ff11aa` and `deadbeef`), which matches the `corrupted metadata` warning in the log. The middle block is the only one whose decoded bytes all fall in the printable ASCII range `20`-`7e`, and it starts with `4f 57 41 53 50 7b` = `OWASP{`. The block selection therefore does not rely on position but on content validity: only one of the three blocks yields a meaningful ASCII string.

## Solution

Decoding the middle block:

```console
$ python -c "h='4f574153507b6272306b336e5f7330756c5f7634756c745f7233633076337233647d'; d=bytes.fromhex(h); print(len(d), d.decode())"
```

```text
34 OWASP{br0k3n_s0ul_v4ult_r3c0v3r3d}
```

The flag is 34 bytes long, exactly the size of the block, with no trailing or padding bytes to strip.

The script below classifies all three blocks, so that rejecting the two outer ones is a measured result rather than an assertion:

```python
import pathlib

blocks = pathlib.Path("metadata.bin.txt").read_text().split()
for i, h in enumerate(blocks, 1):
    d = bytes.fromhex(h)
    printable = all(32 <= b < 127 for b in d)
    print("block %d: %2d bytes  printable=%-5s  %r" % (i, len(d), printable, d))
```

```text
block 1:  4 bytes  printable=False  b'\x00\xff\x11\xaa'
block 2: 34 bytes  printable=True   b'OWASP{br0k3n_s0ul_v4ult_r3c0v3r3d}'
block 3:  4 bytes  printable=False  b'\xde\xad\xbe\xef'
```

Only block 2 satisfies the printable condition, and it is also the only block with a flag shape.

## Result

```text
OWASP{br0k3n_s0ul_v4ult_r3c0v3r3d}
```

The flag was decoded directly from the second block of `metadata.bin.txt`; the remaining two blocks decode to sentinels and were dropped because they do not form printable ASCII. This challenge is offline, Python 3 only, with no remote service. No submission response recorded.

## Reproduce

Python 3 only (`pathlib`, `bytes.fromhex`), no external libraries. Place `metadata.bin.txt` and `vault.log` in the working directory, then run:

```console
$ python -c "import pathlib; print(pathlib.Path('vault.log').read_text())"
$ python -c "import pathlib; print(pathlib.Path('metadata.bin.txt').read_text())"
$ python -c "h='4f574153507b6272306b336e5f7330756c5f7634756c745f7233633076337233647d'; print(bytes.fromhex(h).decode())"
```

To run the block classifier, save the script from the Solution section as `solve.py` next to `metadata.bin.txt` and run `python solve.py`; the script reads the file relative to the current directory.
