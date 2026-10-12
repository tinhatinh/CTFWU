---
title: "The Alphabet That Wasn't There"
category: "Forensics"
tags: ["pdf", "type3-font"]
solve_date: "2026-10-11T05:50:00+07:00"
language: "en"
---

# The Alphabet That Wasn't There

**Flag:** `isfcr{d7ef3d5dd98bd325c3b50114}`  
**Artifacts:** `damaged.pdf` (64,872 bytes), `reference.pdf` (4,011 bytes), distributed in `handout (29).zip`

| Artifact | SHA-256 |
|---|---|
| `damaged.pdf` | `52614107d762aad3ea07faf571c5d071cdd4e27b8b3f12581916074b583f4192` |
| `reference.pdf` | `cbaec694550465b9791790aac541963833fb8936bacc21c1560cce5ae2ff64af` |

## Challenge

A damaged PDF contains a 16 x 16 grid of nonstandard symbols. We must select the page whose document catalog has the 16-byte `/CaseID` `9697624543591457a15dc6d9a4797c45`. The symbols in `reference.pdf`, ordered left to right, encode the hexadecimal digits `8bd4e257f916c30a`. Decode all 256 grid cells in **default PDF user space**, reading rows from top to bottom (descending baseline `y`) and columns from left to right (ascending baseline `x`). Rotated drawings retain their symbol identities.

The final flag is not printed in the PDF: the CaseID and decoded grid form the evidence used to derive an `scrypt` key and authenticate/decrypt an AES-GCM ciphertext.

## Initial Analysis

The reference document contains 16 different vector-drawn glyphs in a Type3 font. Their byte values and glyph names are not the hexadecimal digits; the correspondence comes from their **visual shapes** and the supplied digit ordering:

```text
Reference symbols, left to right:
8 b d 4 e 2 5 7 f 9 1 6 c 3 0 a
```

`damaged.pdf` is deliberately hostile to straightforward text extraction:

- It contains two `%%EOF` markers and damaged/incremental PDF structure. PDF readers can recover different subsets of its objects, so a plain `pdftotext` dump does not reliably describe the target grid.
- The recovered catalog has `/CaseID <9697624543591457a15dc6d9a4797c45>`; this is the correct target, not a value to infer from rendered text.
- The selected page has `/Rotate 90`, and its contents call four Form XObjects (`/X0`, `/X1`, `/X2`, `/X3`) through translated coordinate systems. Screen-space left-to-right ordering is therefore **not** the ordering specified in the challenge.
- MuPDF's recovered page exposes 358 glyph occurrences, more than the 256 required cells. The content has superimposed, hidden, and misleading drawings, so simply concatenating encountered character codes or accepting the topmost glyph produces the wrong evidence.

The useful invariant is the shape of each glyph, not its font encoding, display angle, or position in the PDF content stream.

## Exploitation Chain

1. **Identify the correct page.** Inspect the recovered PDF object graph/catalog and check the exact `/CaseID` bytes. Resolve the page's Form XObjects and their transformation matrices. Work with the page's *default user-space* positions rather than rendered or `/Rotate`-adjusted image coordinates.

2. **Build the substitution alphabet.** Examine the 16 symbols in `reference.pdf`, matching each vector glyph shape to its assigned digit in `8bd4e257f916c30a`. In the damaged file, decode glyph drawings using the same shape mapping despite randomized Type3 encodings, transformations, and rotated symbols.

3. **Recover the actual 16 x 16 grid.** Group the symbol instances by their underlying cell baselines. Discard extraneous/overlaid symbol instances rather than assuming every recorded drawing belongs to the grid. Sort the recovered cells by **descending default-space `y`**, then by **ascending default-space `x`**. The resulting grid contains exactly 256 lowercase hexadecimal digits:

   ```text
   e7463684552dfb02
   7076afdf977a1a94
   bb89d9112b4ace4b
   c9207e7c18b3fbf5
   5526ba3a9e437c7d
   6c4a3ef3bf7e0dcd
   4694f7288fc5d4c1
   89be389bbbaadd51
   4031b50de7eba382
   0e5230915ddfa4bc
   c793d2b7aa7c880f
   1900cd60b1caedd9
   507009b6658d86d3
   ce052d46f8f4c16d
   13c9e5e6302733f3
   906ff5e24f690ab6
   ```

4. **Construct the exact evidence bytes.** Let `evidence = [caseid, grid]` where both elements are lowercase ASCII strings. JSON-serialize with `ensure_ascii=True` and `separators=(",", ":")`, with no spaces or trailing newline. Prefix the serialized bytes with `b"isfcr-forensics\x00"` as the `scrypt` password input.

5. **Derive the key and decrypt.** Use the challenge-provided salt and `scrypt(n=131072, r=8, p=1, dklen=32, maxmem=2**28)`; then decrypt using the specified 12-byte nonce and AAD `the-alphabet-that-wasnt-there`. The AES-GCM authentication tag verifies and the plaintext contains the flag.

## Flag

`isfcr{d7ef3d5dd98bd325c3b50114}`

This flag is **cryptographically verified** by successful AES-GCM authenticated decryption using the specified evidence, parameters, ciphertext, nonce, and AAD. Submission to the CTF server was not checked.

## Reproduce

Install `cryptography` (`python -m pip install cryptography`), save the following code as a Python script, and run it with Python 3. The 16 rows are the decoded PDF evidence above; the script verifies the 256-digit length, constructs the exact evidence JSON, derives the key, and authenticates the decrypted flag.

```python
import hashlib
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

caseid = "9697624543591457a15dc6d9a4797c45"
grid_rows = """
e7463684552dfb02
7076afdf977a1a94
bb89d9112b4ace4b
c9207e7c18b3fbf5
5526ba3a9e437c7d
6c4a3ef3bf7e0dcd
4694f7288fc5d4c1
89be389bbbaadd51
4031b50de7eba382
0e5230915ddfa4bc
c793d2b7aa7c880f
1900cd60b1caedd9
507009b6658d86d3
ce052d46f8f4c16d
13c9e5e6302733f3
906ff5e24f690ab6
""".strip().splitlines()
assert len(grid_rows) == 16 and all(len(row) == 16 for row in grid_rows)
grid = "".join(grid_rows)
assert len(grid) == 256 and all(c in "0123456789abcdef" for c in grid)

E = json.dumps([caseid, grid], ensure_ascii=True,
               separators=(",", ":")).encode("ascii")
key = hashlib.scrypt(
    b"isfcr-forensics\x00" + E,
    salt=bytes.fromhex("8a251a8101ffa67ed383a445a05e77f2"),
    n=131072, r=8, p=1, maxmem=2**28, dklen=32,
)
nonce = bytes.fromhex("cf5d90d20b821db4c5bf1b73")
ciphertext_and_tag = bytes.fromhex(
    "27b4469da3cc30f3ec487d60be3053aa2d5aa00c9f4da69fe54e7d51da8463883b4aa1b0a10a69c45c4e974171133f"
)
flag = AESGCM(key).decrypt(
    nonce, ciphertext_and_tag, b"the-alphabet-that-wasnt-there"
).decode("ascii")
print("Grid SHA-256:", hashlib.sha256(grid.encode("ascii")).hexdigest())
print("AES-GCM authentication: OK")
print("FLAG", flag)
```

Expected output:

```text
Grid SHA-256: 59079651bfa1efcbf31856828c304b6070b3816baea8ecaa51f2fd0633097d0d
AES-GCM authentication: OK
FLAG isfcr{d7ef3d5dd98bd325c3b50114}
```

A wrong glyph choice, cell order, CaseID, or JSON serialization changes the derived key and causes `AESGCM.decrypt` to raise `InvalidTag`, making the successful decryption an independent check on the entire recovered grid.
