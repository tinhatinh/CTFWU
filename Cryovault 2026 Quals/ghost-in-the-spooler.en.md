---
title: "Ghost in the Spooler"
category: "Forensics"
tags: ["print-spooler", "mic"]
solve_date: "2026-10-10T16:48:00+07:00"
language: "en"
---

# Ghost in the Spooler

**Flag:** `isfcr{e24d16be9d731cba}`  
**Artifacts:** `FP02CF4.SHD` (520 bytes), `FP02CF4.SPL` (1,872 bytes), `scan.png` (2550 × 3300 pixels)

| Artifact | SHA-256 |
|---|---|
| `FP02CF4.SHD` | `9c5ad49f547e714a90c223be955c14669c3a7725ccf5bb1b1015e743f832ada0` |
| `FP02CF4.SPL` | `afe8591220aa739d239efa86fe78e5a089b06206a599047fe248954bf235e1de` |
| `scan.png` | `4ba72a26304220be725ae5cdc98f963e65feae4d1114721832c62026a086691a` |

## Challenge

A forensic image of a workstation yielded a Windows print-job shadow file (`.SHD`) and spool file (`.SPL`), as well as a scan of the suspected printed page. Establish the relationship between the print job and the scan, then reconstruct a flag using the print-job owner's lowercase username, the printer's seven-digit serial number, and the UTC print time rounded to minute precision (seconds `00`).

The required construction is:

```text
isfcr{SHA256(username + "|" + serial + "|" + timestamp)[:16]}
```

The 16 characters in the flag are the first **16 hexadecimal characters**, not the first 16 hash bytes.

## Initial Analysis

The two spooler remnants share the job stem `FP02CF4`. The `.SHD` file contains UTF-16LE strings for the Windows user, document name, print queue, printer driver, and workstation. The `.SPL` file holds the spooled Enhanced Metafile (EMF) print content. The scan visually matches the memorandum represented in that print stream.

Relevant `.SHD` strings are:

```text
j.holbrook
Q3-Compensation-Adjustments.docx
\\PRINT01\HR-DocuColor-12
Xerox DocuColor 12 PS
NT EMF 1.008
FIN-WKS-014
```

The `.SPL` content contains the title **Q3 Compensation Adjustments** and a **MEMORANDUM** addressed to Human Resources directors, dated 17 September 2024 and signed by **J. Holbrook, VP Total Rewards**. Those identifiers and the memo text correspond to the page visible in `scan.png`. This associates the physical scan with the spooled document, rather than merely relying on a matching file name.

## Exploitation Chain

1. **Recover the print-job owner.** The shadow file stores `j.holbrook` as UTF-16LE beginning at offset `0x100` (a second occurrence follows). The already-lowercase account name is the first flag field:

   ```text
   username = j.holbrook
   ```

2. **Decode the shadow-file timestamp.** The eight bytes at `.SHD` offset `0x40` form a little-endian Windows `FILETIME` value of `133710574200000000`, counting 100-nanosecond intervals since 1601-01-01 UTC. Converting it gives 2024-09-17 14:37:00 UTC. Use the exact format specified in the challenge:

   ```text
   timestamp = 2024-09-17T14:37:00Z
   ```

3. **Reveal the printer identification pattern in the scan.** The pale yellow dots tiled across `scan.png` are a machine identification code (MIC), consistent with the Xerox DocuColor printer named in the job metadata. A single repeat is a **15-column × 8-row** matrix. Its top row holds column parity; its leftmost column holds row parity. Dots are present/absent bits. Reading the seven *data rows* of each subsequent column from top to bottom, with weights `64, 32, 16, 8, 4, 2, 1`, yields the following values in this challenge's pattern:

   | Column(s), left to right (1-based) | Decoded values | Interpretation |
   |---|---|---|
   | 2–6 | `37, 14, 17, 9, 24` | Minute, hour, day, month, two-digit year |
   | 7–13 | `8, 8, 4, 2, 0, 1, 3` | Seven serial-number digits |
   | 14–15 | `0, 0` | Unused fields in this example |

   Thus the MIC supplies:

   ```text
   serial = 8842013
   MIC time = 2024-09-17 14:37
   ```

   The MIC minute matches the `.SHD` `FILETIME` exactly. In the supplied PNG, a complete grid can be sampled at pixel centers `x = 90 + 9*c` and `y = 60 + 9*r` for zero-based column `c = 0..14` and row `r = 0..7`. The yellow-dot pixel color is `(250, 246, 160)`. All eight rows have odd parity, as do columns 2–15, providing an additional check that the grid was extracted without shifting it.

4. **Correlate the independent evidence.** The spooler queue and driver name a Xerox DocuColor 12, the EMF content matches the scanned memo, and the print time independently encoded in the yellow-dot matrix matches the `.SHD` time. The scan provides the serial number absent from the ordinary user-readable `.SHD` strings. Together these artifacts tie the physical page to the recovered workstation's print job.

5. **Build and hash the evidence string.** Concatenate the lowercase username, seven-digit serial, and UTC timestamp with **literal pipe separators** and no whitespace:

   ```text
   j.holbrook|8842013|2024-09-17T14:37:00Z
   ```

   Its SHA-256 is:

   ```text
   e24d16be9d731cba62793f93bbd3cf637d1450862c06197e37473d026b6908bd
   ```

   The first 16 hex characters are `e24d16be9d731cba`.

## Flag

`isfcr{e24d16be9d731cba}`

The flag was derived from the attached spooler artifacts and the scan, not read directly from any provided file. The calculation has been independently reproduced locally; submission/acceptance by the CTF service has not been verified here.

## Reproduce

Extract the supplied ZIP so that `FP02CF4.SHD`, `FP02CF4.SPL`, and `scan.png` are in a `ghost-spooler/` subdirectory. Install Pillow if necessary (`python3 -m pip install Pillow`), then run the following script from the directory containing that subdirectory:

```python
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from struct import unpack_from
from PIL import Image

root = Path("ghost-spooler")
shd = (root / "FP02CF4.SHD").read_bytes()
spl = (root / "FP02CF4.SPL").read_bytes()

# Print-job owner, stored as UTF-16LE in the SHD file.
username = shd[0x100:0x118].decode("utf-16le").split("\0")[0].lower()

# FILETIME: 100-ns ticks since midnight, 1601-01-01 UTC.
filetime = unpack_from("<Q", shd, 0x40)[0]
printed_at = datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(
    microseconds=filetime // 10
)
timestamp = printed_at.strftime("%Y-%m-%dT%H:%M:00Z")

# Cross-check that the spooled content is the memorandum in the scan.
assert "Q3 Compensation Adjustments".encode("utf-16le") in spl
assert "MEMORANDUM".encode("utf-16le") in spl

# One repeating 15x8 yellow-dot MIC grid in this exact supplied scan.
image = Image.open(root / "scan.png").convert("RGB")
dots = [
    [image.getpixel((90 + 9 * col, 60 + 9 * row)) == (250, 246, 160)
     for col in range(15)]
    for row in range(8)
]

# Parity: odd in each row and in columns 2..15.
assert all(sum(row) % 2 == 1 for row in dots)
assert all(sum(dots[row][col] for row in range(8)) % 2 == 1
           for col in range(1, 15))

# Ignore the top parity row; columns 2..15 each encode seven data bits.
values = [
    sum(int(dots[row][col]) << (7 - row) for row in range(1, 8))
    for col in range(15)
]
assert values[1:6] == [printed_at.minute, printed_at.hour,
                       printed_at.day, printed_at.month, printed_at.year % 100]
assert all(0 <= digit <= 9 for digit in values[6:13])
serial = "".join(str(digit) for digit in values[6:13])

message = f"{username}|{serial}|{timestamp}"
digest = sha256(message.encode("ascii")).hexdigest()
flag = f"isfcr{{{digest[:16]}}}"

print("Username:", username)
print("Serial:", serial)
print("Timestamp:", timestamp)
print("Input:", message)
print("SHA-256:", digest)
print("FLAG", flag)
```

Expected output:

```text
Username: j.holbrook
Serial: 8842013
Timestamp: 2024-09-17T14:37:00Z
Input: j.holbrook|8842013|2024-09-17T14:37:00Z
SHA-256: e24d16be9d731cba62793f93bbd3cf637d1450862c06197e37473d026b6908bd
FLAG isfcr{e24d16be9d731cba}
```
