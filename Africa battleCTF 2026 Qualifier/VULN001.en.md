---
title: "VULN#001"
category: "Vuln Research"
tags: ["libexif", "exif", "jpeg", "out-of-bounds-read", "integer-underflow", "source-diff"]
solve_date: "2026-10-16T23:57:00+07:00"
language: "en"
points: 144
---

# VULN#001 — libexif APP1 length underflow to OOB read

**Flag:** `CTF{86f07cd3cbf154a2bcec7e77d8334779}` · **Files:** `libexif-src.tar.gz` (1 137 988 B, sha256 `c986b9b8b49b711ab56f85b0b06523ee85e8b45b7e597887f0fb70604628a5e6`), `base-exif.jpg` (725 B, sha256 `c261cc6bc3b4d26d9b61ee15449d96274007261fe0fa59c9d0b7449d2d24dfda`) · **Target:** `169.58.126.107:7027`

## Challenge

The card reads `VULN#001`, 144 points, description `metadata service`, hint `The exact source`,
service at `169.58.126.107 7027`, flag format `CTF{}`. The only artifact is the libexif source tree
packed as `libexif-src (1).tar.gz`; no binary is provided.

The "exact source" hint means the library version on the remote matches the tarball exactly, so the bug
to exploit lives in this snapshot rather than in some other release.

## Analysis

### Service protocol

The service reads **4-byte big-endian length + image data** and answers with a single `status: ...`
line, then closes the connection. Observed replies:

```text
status: bad length         - length 0 or too large
status: not valid          - input not accepted
status: no effect          - valid image, ordinary parse
status: insufficient       - bug triggered but the harness target was not reached
status: confirmed          - triggered correctly, prints FLAG: ...
status: rate limited, try again later   - requests sent too fast
```

`canon_makernote_variant_1.jpg` (a JPEG opening directly with APP1), a bare APP1 Exif blob and a bare
TIFF all return `status: not valid`; only a JPEG with a JFIF header (FF D8 FF E0 ...) followed by an
APP1 Exif segment is processed (`status: no effect`, `protocol.txt`). In other words the
libexif EXIF path is reachable, while `not valid` is a shape check performed by the harness.

### Provided source and the bug

Extracting the tarball and comparing it with upstream libexif: after normalising CRLF to LF, **61/61
`.c/.h` files match byte for byte** with commit `a918830` (2021-11-01, `fixed offset for EXIF Header in
App1 Header`, `0.6.23.1-dev`). This snapshot **lacks** two later oss-fuzz fixes (`source-check.txt`):

```text
54461dd  check for len < 2 to avoid it becoming negative.
4bd5cd6  actually check the length read from the data against the data size (oss-fuzz)
```

Both patches add validation to the same code in `libexif/exif-data.c` (`exif_data_load_data`). When the
buffer does not start with `Exif\0\0` (i.e. it is a JPEG), the function scans markers and, on reaching
APP1, reads the segment length and derives the EXIF data size:

```c
d++;
ds--;
len = (((unsigned int)d[0]) << 8) | d[1];
...
d += 2;
ds = len - 2;   /* we do not want the full rest size, but only the size of the tag */
```

`len` is the 16-bit JPEG segment length, fully attacker-controlled and **never validated**. `ds` is an
`unsigned int`:

- `len = 0` → `ds = len - 2 = 0xFFFFFFFE` (underflow);
- `len` larger than the real data → `ds` exceeds the buffer.

`ds` is then only capped at `0xfffe`, still far larger than the 725-byte image. Every later bound check
(`CHECKOVERFLOW` inside `exif_data_load_data_content`) relies on this wrong `ds`, so a read at
`d + 6 + offset` with an attacker-chosen `offset` leaves the buffer. This is an out-of-bounds read with a
controlled offset; the OOB bytes are interpreted as IFD entries.

Compared with a valid image whose IFD0 offset stays in bounds, the payload only changes two fields:

| Field | Position | Value | Purpose |
| --- | --- | --- | --- |
| APP1 length | `[22:24]` | `0x0000` | underflow `ds`, disabling the bound |
| TIFF IFD0 offset | `[34:38]` | `0x00000800` | landing point of the OOB read |

## Approaches tried

1. **Sending a JPEG opening directly with APP1 / a bare EXIF blob / a bare TIFF:** all return
   `not valid`. The JFIF header must stay before APP1 (`protocol.txt`).
2. **Continuous variant sweep:** firing ~350 requests drove the service into `rate limited` and
   contaminated the middle results. Requests had to be spaced out and re-run.
3. **Arbitrary IFD0 offsets:** `0xf000` gives `status: insufficient`, `0xfff0` (with `len = 1`) gives
   `not valid`, and only `0x0800` gives `status: confirmed`. The success condition belongs to the
   harness, so the offset is a parameter to tune rather than something derivable from the source.

## Solution

### Step 1 - Recover the framing and the input condition

The first four bytes are a big-endian length. A PIL-generated JFIF+EXIF JPEG (`base-exif.jpg`)
passes the shape check and returns `status: no effect`, making it the base image to patch.

### Step 2 - Compare the source to locate the bug

Normalise line endings and compare each file with upstream at `a918830`: **0 differences across 61
files**, and both `len` checks are absent. The bug is in `exif_data_load_data` as described above.

### Step 3 - Build the OOB payload

`base-exif.jpg` is a Motorola JPEG (`MM`) with the APP1 Exif segment at offset 20. The APP0/JFIF
header is already in front of APP1, so only the APP1 length field and the IFD0 offset need patching:

```python
img = bytearray(base)                       # JFIF + APP1 Exif JPEG, 725 B
img[22:24] = struct.pack(">H", 0x0000)      # APP1 length = 0  -> ds = len - 2 underflows
img[34:38] = struct.pack(">I", 0x0800)      # IFD0 offset     -> OOB landing point
```

The full script is `exploit.py`. The generated payload has sha256
`bb362e31eeec05523da535ce06bee08164657a04d162755b097fc13a00c18ed1`, exactly the payload used for the
successful run (`payload-confirmed.jpg`).

With `len = 0`, `ds` becomes `0xFFFFFFFE` and is capped at `0xfffe`; `offset = 0x0800` passes the
`offset > ds` check and forces `exif_data_load_data_content` to read IFD0 at `TIFF + 0x800`, roughly
1 353 bytes past the 725-byte buffer. That OOB region is read as IFD entries, the harness recognises its
target condition, and it prints the flag.

### Step 4 - Verification

- The offline-rebuilt payload matches the sha256 of the payload that succeeded.
- The flag is printed by the service itself (`status: confirmed` + `FLAG:`), not an inferred value.
- It uses the `CTF{...}` wrapper stated on the card.

## Result

```bash
python exploit.py
```

```text
host 169.58.126.107:7027  payload 725 byte
RAW RESPONSE b'status: confirmed\nFLAG: CTF{86f07cd3cbf154a2bcec7e77d8334779}\n'
CTF{86f07cd3cbf154a2bcec7e77d8334779}
```

```text
CTF{86f07cd3cbf154a2bcec7e77d8334779}
```

This flag was printed by the service (`exploit-output.txt`), not built from an artifact.

## Reproduce

Requires: the service at `169.58.126.107:7027` still running, Python 3 (no external libraries). The base
image `base-exif.jpg` and `exploit.py` are sufficient; the script builds the payload, sends it and
extracts the flag.

```bash
cd vuln001
python exploit.py
```

Because the service rate-limits, the script backs off on `status: rate limited` and retries. The payload
has no random component, so results are stable across sends:

```bash
python -c "import hashlib, exploit; print(hashlib.sha256(exploit.build_payload()).hexdigest())"
# bb362e31eeec05523da535ce06bee08164657a04d162755b097fc13a00c18ed1
```
