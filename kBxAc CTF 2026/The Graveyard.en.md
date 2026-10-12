---
title: "The Graveyard"
category: "Misc"
tags: ["steganography", "whitespace", "SNOW", "SpamMimic", "base64", "book-cipher"]
solve_date: "2026-10-10T19:10:00+07:00"
language: "en"
points: 916
---

# The Graveyard

**Flag:** `kBxAc{tr4c1ng_4_wh1t3sp4c3_b26_x9a8b7c6}`  
**Author:** HydraRoot  
**Provided archive:** `chall (3).zip`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `chall (3).zip` | 14,637 | `035e9a2d30fc9306e609478e05998d58455de6eec3f86be899416b9e4d849f49` |
| `archive-book.txt` | 7,141 | `cfaa8d07a76cc3375bb9f791abea8633ef0335cc4e67e556fc1c1cf59cff2756` |
| `03.txt` | 984 | `5527696da451008c7a74b88ea20ca69daf13309051bb6e71c71be2bf98092418` |
| `07.txt` | 3,642 | `7bf8c86d15e8d08e35463f18f5bf873a35906958c275847a1becfa5e01de87f8` |
| `11.txt` | 855 | `afbdd64f634785ee8e7d4a7515e02df6e87d2345087a74dc6af0b452def92bc2` |
| `14.txt` | 848 | `e61d8259e9e2a24697222783d000c852c2c4f859362caeca9355529073bd8b52` |
| `19.txt` | 755 | `963d3fde0d2c8207fad74323a9c7c65d8ecb119ed8fb3ce31ea160522ecebbcc` |

## Challenge description

> Twenty fragments were recovered from an old archive, but only some of them belong to the actual investigation. The fragments appear unrelated, and several contain misleading information. Somewhere among them is the path to reconstructing what was hidden in the archive.

The ZIP contains twenty numbered text fragments (`01.txt`–`20.txt`) and an 80-line `archive-book.txt`. The task is to identify the genuine fragments, extract their invisible payloads, and use the book to reconstruct the message.

## Initial inspection

Most fragments resemble ordinary archival inspection reports. However, `03.txt`, `07.txt`, `11.txt`, `14.txt`, and `19.txt` contain extensive **trailing tabs (`\t`) and spaces (`0x20`)**. Preserve these bytes: trimming or reformatting the text would destroy the payload.

```bash
unzip -l 'chall (3).zip'
unzip -p 'chall (3).zip' 11.txt | cat -A
```

In `cat -A`, `^I` represents a tab and `$` marks the end of a line. The whitespace pattern is consistent with **SNOW-style steganography**, where runs of spaces and tabs carry data.

## Stage 1 — SpamMimic identifies the real fragments

`07.txt` includes a long spam-like email under `Recovered Transmission:`. Its unnatural advertisement format is characteristic of **SpamMimic**, which encodes data as plausible spam text.

Extract only the email body (excluding the `Recovered Transmission:` label) and decode it using:

- <https://www.spammimic.com/decode.shtml>

The decoded string is Base64:

```text
VFJVRSBGUkFHTUVOVFM6IDAzIDA3IDExIDE0IDE5
```

```python
import base64
print(base64.b64decode('VFJVRSBGUkFHTUVOVFM6IDAzIDA3IDExIDE0IDE5').decode())
```

```text
TRUE FRAGMENTS: 03 07 11 14 19
```

This identifies **which fragments matter**, not the order in which the final flag must be assembled. The report dates are not the flag ordering either.

## Stage 2 — Recover 16-bit records from SNOW whitespace

In the SNOW encoding scheme, each run of **0–7 spaces**, separated by tabs, carries **three bits**. The bit order within each group is **least-significant bit first**. The initial tab is a start marker and is not part of the encoded payload.

For a run of `n` spaces, append `(n >> 0) & 1`, `(n >> 1) & 1`, and `(n >> 2) & 1`. Read the trailing whitespace on all encoded lines, then interpret consecutive bits as **16-bit big-endian values**. Ignore any final 1–2 padding bits.

The five files yield **67 complete 16-bit records**. These values are not ASCII; they encode locations in the book.

## Stage 3 — Interpret each record as a book-cipher coordinate

`archive-book.txt` has 80 whitespace-separated lines. Various words have deliberately altered characters, including `ketal`, `Burator`, and `sexled`. Do not spell-check or normalize them: the exact bytes are part of the cipher.

Each 16-bit value `v` contains three **zero-based** indices:

```python
line_index = v >> 8
word_index = (v >> 4) & 0x0F
char_index = v & 0x0F
character = book[line_index][word_index][char_index]
```

The first three values extracted from `11.txt` illustrate the method:

| Value | (Line, Word, Char), zero-based | Lookup | Character |
|---|---|---|---|
| `0x3B60` | `(59, 6, 0)` | `ketal[0]` | `k` |
| `0x3870` | `(56, 7, 0)` | `Burator[0]` | `B` |
| `0x3972` | `(57, 7, 2)` | `sexled[2]` | `x` |

Thus `11.txt` starts with `kBx...`, matching the expected flag prefix.

## Recovered fragments and flag

| Fragment | SNOW bits | 16-bit records | Extracted text |
|---|---:|---:|---|
| `03.txt` | 225 | 14 | `th3_sp4m_b4s36` |
| `07.txt` | 210 | 13 | `00k_c1ph3r_20` |
| `11.txt` | 225 | 14 | `kBxAc{tr4c1ng_` |
| `14.txt` | 225 | 14 | `4_wh1t3sp4c3_b` |
| `19.txt` | 192 | 12 | `26_x9a8b7c6}` |
| **Total** | **1,077** | **67** | |

Fragments `03` and `07` spell an auxiliary preface, `th3_sp4m_b4s3600k_c1ph3r_20`. The actual flag begins in `11.txt`, continues in `14.txt`, and ends in `19.txt`:

```text
11.txt: kBxAc{tr4c1ng_
14.txt: 4_wh1t3sp4c3_b
19.txt: 26_x9a8b7c6}
```

**Final flag:**

```text
kBxAc{tr4c1ng_4_wh1t3sp4c3_b26_x9a8b7c6}
```

## Reproduction (Python 3, standard library only)

Save the script as `solve.py` next to the original archive and run `python solve.py "chall (3).zip"`. It works directly on ZIP members to avoid losing trailing whitespace.

```python
#!/usr/bin/env python3
"""The Graveyard - reproducible solver. Python 3.8+, stdlib only."""
import re
import sys
import zipfile

TRUE_FRAGMENTS = ("03", "07", "11", "14", "19")


def snow_bits(data: bytes) -> str:
    """Decode the 3-bit groups from SNOW-style trailing whitespace."""
    started = False
    bits = []
    for line in data.splitlines():
        match = re.search(rb"[ \t]+$", line)
        if not match:
            continue
        ws = match.group(0)

        # SNOW starts with a delimiter tab, which is not payload.
        if not started:
            if not ws.startswith(b"\t"):
                continue
            ws = ws[1:]
            started = True

        spaces = 0
        for ch in ws:
            if ch == 0x20:  # space
                spaces += 1
            elif ch == 0x09:  # tab terminates a 3-bit group
                if spaces > 7:
                    raise ValueError("Invalid SNOW spacing")
                bits.extend(str((spaces >> i) & 1) for i in range(3))
                spaces = 0
        if spaces:  # final group at the end of a line
            if spaces > 7:
                raise ValueError("Invalid SNOW spacing")
            bits.extend(str((spaces >> i) & 1) for i in range(3))
    return "".join(bits)


def solve(archive_path: str):
    with zipfile.ZipFile(archive_path) as z:
        # Preserve line/word/character case and zero-based coordinates.
        book = [line.split() for line in
                z.read("archive-book.txt").decode("utf-8").splitlines()]
        recovered = {}
        for number in TRUE_FRAGMENTS:
            bits = snow_bits(z.read(number + ".txt"))
            # Discard the final 1-2 padding bits, if present.
            records = [int(bits[i:i + 16], 2)
                       for i in range(0, len(bits) - 15, 16)]
            chars = []
            for value in records:
                line = value >> 8
                word = (value >> 4) & 0x0F
                char = value & 0x0F
                chars.append(book[line][word][char])
            recovered[number] = "".join(chars)
            print(f"{number}.txt: {recovered[number]} "
                  f"({len(records)} records; {len(bits)} bits)")

    flag = recovered["11"] + recovered["14"] + recovered["19"]
    assert flag == "kBxAc{tr4c1ng_4_wh1t3sp4c3_b26_x9a8b7c6}"
    print("FLAG:", flag)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit('Usage: python solve.py "chall (3).zip"')
    solve(sys.argv[1])
```

Verified output:

```text
03.txt: th3_sp4m_b4s36 (14 records; 225 bits)
07.txt: 00k_c1ph3r_20 (13 records; 210 bits)
11.txt: kBxAc{tr4c1ng_ (14 records; 225 bits)
14.txt: 4_wh1t3sp4c3_b (14 records; 225 bits)
19.txt: 26_x9a8b7c6} (12 records; 192 bits)
FLAG: kBxAc{tr4c1ng_4_wh1t3sp4c3_b26_x9a8b7c6}
```

## Conclusion

The challenge chains **SpamMimic → Base64 → fragment selection → SNOW trailing-whitespace extraction → 16-bit coordinates → book cipher**. Common pitfalls are stripping whitespace, interpreting the SNOW data as raw ASCII, or ordering the fragments solely by date. The flag is reconstructed from the original files and independently reproduced by the script:

**`kBxAc{tr4c1ng_4_wh1t3sp4c3_b26_x9a8b7c6}`**
