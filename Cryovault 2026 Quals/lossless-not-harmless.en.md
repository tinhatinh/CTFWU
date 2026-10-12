---
title: "Lossless, Not Harmless"
category: "Forensics"
tags: ["deflate", "steganography"]
solve_date: "2026-10-11T04:34:00+07:00"
language: "en"
---

# Lossless, Not Harmless

**Flag:** `isfcr{ch0ic3s_th3_d3c0d3r_n3v3r_s33s}`  
**Artifact:** `mosaic_0417.png` (17,492 bytes; 256 × 300 pixels, indexed-color PNG)  
**Archive:** `lossless-not-harmless.zip`

| Artifact | SHA-256 |
|---|---|
| `mosaic_0417.png` | `6362e0e2d4e6eaa84ebce95850ef5100a3eeaa25f58c4faabc2e59240501736a` |

## Challenge

An archive server applies an in-house lossless compressor to every image that passes through it. One processed image contains a secret message. Recover the flag in `isfcr{...}` format from the provided `mosaic_0417.png`.

The important distinction is that *lossless* guarantees that decompression reproduces the same image data; it does **not** require the compressor to make a unique choice of compressed representation. This challenge exploits exactly that freedom.

## Initial Analysis

The supplied file is a valid 256 × 300 indexed-color PNG. Its image data is distributed over nine `IDAT` chunks, which must be concatenated into a single zlib stream before examining the underlying DEFLATE bitstream.

Two straightforward flag-shaped strings are decoys:

- The PNG `Comment` text chunk contains Base64 `aXNmY3J7bm9wZV9ub3RfdGhpc19vbmV9`, which decodes to `isfcr{nope_not_this_one}`.
- A conventional pixel-LSB extraction yields `isfcr{lsb_is_the_first_place_everyone_looks}`. This is also **not** the accepted solution.

The more useful metadata is the `Software` field:

```text
dfl-stitch 2.3 (equivalent-match mode, flush=sync)
```

It directs attention away from the visible image and toward the *encoding decisions* made by the DEFLATE compressor. A decompressed pixel array discards those decisions, so ordinary PNG viewing or re-saving can destroy the evidence.

## Exploitation Chain

1. **Recover the original compressed stream.** Parse the PNG chunk structure and concatenate the payloads of all nine `IDAT` chunks in file order. The combined zlib stream is 16,415 bytes and decompresses to 77,100 bytes of PNG scanline/filter data, consistent with a 256 × 300 indexed-color image. Work on the original compressed bytes; do not use a newly saved PNG.

2. **Parse DEFLATE at the bit level.** Decode block headers, Huffman trees, literal/length symbols, and distance symbols while maintaining the reconstructed output dictionary. This stream has 87 DEFLATE blocks and 5,852 LZ77 match commands. Thirty-one empty stored blocks act as synchronization flushes. Their byte-alignment padding bits are not uniformly zero, which is unusual for ordinary compressor output and provides a second covert channel.

3. **Extract the 128-bit padding secret.** For each empty stored/sync-flush block, read the otherwise ignored alignment bits immediately before the stored-block `LEN` and `NLEN` fields. Concatenate these bits in block order. There are exactly 128 padding bits; grouping them into bytes in transmission order gives:

   ```text
   2814c69217b303ec00c6280fa2c50286
   ```

   A DEFLATE decoder ignores the values of these alignment bits, so modifying them does not affect the decompressed image.

4. **Identify equivalent LZ77 references.** For each match, use the already reconstructed output as the dictionary and enumerate alternative backward distances that would reproduce exactly the same match bytes. DEFLATE can refer to any valid previous occurrence of a repeated sequence. Restrict the alternatives to those having the same encoded distance bit cost under that block's Huffman distance tree. Of the 5,852 actual matches, **3,516** have at least one such alternative. The selected distance therefore carries information even though all equivalent choices decode identically. Recover the compressor-choice bitstream from these selections rather than from the pixel values.

5. **Decode and authenticate the hidden message.** The choice channel contains the framed hidden data (`DFL8`). Use the recovered 128-bit padding value as the secret for the SHA-256-derived keystream and undo the payload masking. Authenticate the resulting plaintext with its HMAC-SHA256 check before accepting the flag. The recovered message gives:

   ```text
   isfcr{ch0ic3s_th3_d3c0d3r_n3v3r_s33s}
   ```

The technique relies on two details a normal image decoder never reports: the ignored flush-padding bits and which one of several equivalent LZ77 distances the encoder selected. Both survive in the original compressed file without changing its decompressed content.

## Flag

`isfcr{ch0ic3s_th3_d3c0d3r_n3v3r_s33s}`

The flag was recovered from the compression-side covert payload, not from PNG metadata or pixel LSBs. The payload's HMAC-SHA256 verification was reported as successful during recovery. Acceptance by the CTF submission service is not independently confirmed here.

## Reproduce

Extract `mosaic_0417.png` from the provided ZIP and confirm its SHA-256 matches the table above. Use a PNG chunk parser to concatenate `IDAT` data *without recompressing it*. This minimal Python check verifies the outer container and the underlying image stream:

```python
import hashlib
import struct
import zlib
from pathlib import Path

png = Path("mosaic_0417.png").read_bytes()
assert png[:8] == b"\x89PNG\r\n\x1a\n"
assert hashlib.sha256(png).hexdigest() == (
    "6362e0e2d4e6eaa84ebce95850ef5100a3eeaa25f58c4faabc2e59240501736a"
)

pos = 8
idat = []
while pos < len(png):
    size = struct.unpack_from(">I", png, pos)[0]
    kind = png[pos + 4:pos + 8]
    data = png[pos + 8:pos + 8 + size]
    if kind == b"IDAT":
        idat.append(data)
    pos += 12 + size  # length, type, data, CRC

compressed = b"".join(idat)
plain = zlib.decompress(compressed)
assert len(idat) == 9
assert len(compressed) == 16415
assert len(plain) == 77100
print("PNG and zlib stream verified")
```

For the actual hidden-channel recovery, continue with a **bit-level DEFLATE parser**, not `zlib.decompress()` alone: `zlib` exposes the output bytes but not padding values or individual distance choices. When a type-0 stored block is reached, collect the bits skipped for byte alignment; when a length/distance match is reached, record its output position, length, selected distance, and active Huffman distance code lengths. Reconstruct candidate backward references against the decompressed output, keep the candidates with the selected reference's encoded bit cost, and extract the compressor-choice channel. Finally decode the `DFL8`-framed payload using the recovered padding secret and verify its authentication tag.

Expected forensic checkpoints:

```text
IDAT chunks:                  9
Concatenated zlib bytes:      16415
Decompressed image bytes:     77100
DEFLATE blocks:               87
Empty sync-flush blocks:      31
LZ77 match commands:          5852
Matches with cost-equivalent distances: 3516
Alignment padding bits:       128
Padding secret (hex):         2814c69217b303ec00c6280fa2c50286
FLAG isfcr{ch0ic3s_th3_d3c0d3r_n3v3r_s33s}
```
