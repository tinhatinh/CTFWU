---
title: "Baby Misc"
category: "Misc"
tags: ["zip", "path-decoding", "long-path", "png-idat"]
solve_date: "2026-10-10"
language: "en"
---

# Baby Misc

**Flag:** `FortID{D0_or_D0_N07_Th3r3_15_n0_Tri3}`
**Artifact:** `retrieve.zip` (approximately 344 MB per the record), 7000 nested-path entries, every member image 48857 B. No instancer. Author: ipaljak.

The challenge page places this under `intro`; that label is kept as a secondary tag, while the primary category is Misc.

## Challenge

One artifact: `retrieve.zip`. No service, no script. The challenge introduces itself through the archive's own structure — and opening the archive the obvious way is already part of the solution.

## Analysis

### Paths are the data, not the plumbing

The 7000 entries use nested paths whose directory components are decimal integers. Those integers are the ASCII codes of characters, so one path segment corresponds to one character. Segment counts measured across the entries range from 99 to 273.

The longest entry has 273 segments. With 2–3 digits per segment, its full path string exceeds the Windows `MAX_PATH` limit of 260, which is exactly why Explorer and `Expand-Archive` fail on this archive: both go through the OS path API while creating the directory tree. The way out is a path-independent reader: entry names live in the ZIP central directory and can be read straight from the file without writing anything to disk.

### Every image has the same size and differs in IDAT

Every member PNG is exactly 48857 bytes. Equal sizes remove the fastest sanity check, and since the chunk layout is identical, headers say nothing either. Hashing the contents of the IDAT chunks — the pixel payload, which is the only part that actually differs — splits the 7000 images into groups of 6999 and 1. The lone image is the one to read.

Size comparisons do not distinguish the recorded images; IDAT digests identify the differing image.

### Decoding printable numeric path components

The final verification line in the record:

```text
segments: 37 all ASCII 33-126: True | FLAG: FortID{D0_or_D0_N07_Th3r3_15_n0_Tri3}
```

`decode()` keeps only numeric path components whose values are ASCII codes 33–126. Other components are skipped, so the 37 retained values can spell the flag even though full paths contain 99–273 components. The same mapping in the opposite direction:

```python
FLAG = "FortID{D0_or_D0_N07_Th3r3_15_n0_Tri3}"

segments = [str(ord(ch)) for ch in FLAG]        # one path segment per character
print("segments:", len(segments))
print("all ASCII 33-126:", all(33 <= ord(ch) <= 126 for ch in FLAG))
print(segments)
```

```text
segments: 37
all ASCII 33-126: True
['70', '111', '114', '116', '73', '68', '123', '68', '48', '95', '111', '114', '95', '68', '48', '95', '78', '48', '55', '95', '84', '104', '51', '114', '51', '95', '49', '53', '95', '110', '48', '95', '84', '114', '105', '51', '125']
```

That block checks the character mapping using the saved flag; it does not traverse the archive.

## Solution

Three operations, in order:

1. Read entry names from the central directory with a reader that does not touch the OS path API (no extraction).
2. Group the member images by digest of their IDAT contents; the group of size 1 is the target.
3. Decode the decimal segment sequence of the path into characters, assert every code lies in 33–126, print the string.

```python
import hashlib
import struct
import zipfile

zf = zipfile.ZipFile("retrieve.zip")           # central directory only, nothing is extracted
infos = zf.infolist()
print("entries:", len(infos))
print("distinct member sizes:", sorted({info.file_size for info in infos}))


def idat_digest(data):
    h = hashlib.sha1()
    pos = 8                                     # skip the 8-byte PNG signature
    while pos + 8 <= len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8])
        if typ == b"IDAT":
            h.update(data[pos + 8:pos + 8 + ln])
        pos += 12 + ln
    return h.hexdigest()


groups = {}
for info in infos:
    groups.setdefault(idat_digest(zf.read(info)), []).append(info.filename)
print("distinct IDAT digests:", len(groups))
print("group sizes:", sorted(len(v) for v in groups.values()))


def decode(name):
    out = []
    for seg in name.strip("/").split("/"):
        if seg.isdigit() and 33 <= int(seg) <= 126:
            out.append(chr(int(seg)))
    return "".join(out), len(out)
```

This block reads `retrieve.zip` directly. The saved run reports 7000 entries, 48,857 B per image and IDAT groups of 6999/1; the archive is not present here, so those measurements have not been rerun. Pass the singleton entry path to `decode()` to read its printable numeric components.

## Result

```text
FortID{D0_or_D0_N07_Th3r3_15_n0_Tri3}
```

The saved result is a 37-character flag decoded from printable numeric components of the target image path. The archive is not present here, so the path decoding and reported 6999/1 IDAT partition have not been independently rerun. The challenge has no remote service.

## Reproduce

You need `retrieve.zip`. The Python 3 standard library (`zipfile`, `hashlib`, `struct`) is sufficient; no extraction and no image library required.

```console
$ python -c "import zipfile; z=zipfile.ZipFile('retrieve.zip'); print(len(z.infolist()))"
```

That command counts entries from the central directory without extracting; the record for this challenge says 7000. Then save the python block from the Solution section as `reader.py`, run `python reader.py`, and pass the `info.filename` of the entry in the odd IDAT group to `decode()`. On Linux, names can be listed without hitting the Windows path limit using `unzip -Z1 retrieve.zip` (list only, writes nothing). On Windows, `Expand-Archive` and Explorer cannot walk this tree; keep reading the ZIP file directly.

The whole reproduction runs locally against the artifact: it costs sequential I/O over 344 MB but creates no files on disk.
