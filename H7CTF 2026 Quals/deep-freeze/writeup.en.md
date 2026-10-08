# Deep Freeze - Forensics (Hard)

**Flag:** `H7CTF{bf3a8e98115450c654b4}` · Files: `memory.lime.zst` (1.438.796.330 B, sha256 `dcd7cb45...b8810`), `Q3_patient_records.pdf.locked` (672 B, sha256 `5b8701fa...274d6b`)

## Challenge

Ransomware hit the hospital at 03:14 and was still encrypting when the response team arrived. They froze the machine first and pulled the power after, so the malicious process's state is still intact in RAM. The hint "catch the thief while his hand is still holding what he reached for" means: the decryption key was never erased, it is still in that process's memory.

We need to recover the contents of `Q3_patient_records.pdf.locked`.

## Analysis

Two files, each with one role:

- `Q3_patient_records.pdf.locked`: 672 bytes, not recognized by `file`, entropy 7.681/8. Entropy alone does not identify an encryption format; the IV/ciphertext layout is checked against source recovered from RAM.
- `memory.lime.zst`: no `zstd` CLI, the machine's `7z` ships no zstd codec, Python has no `zstandard`. `Git\mingw64\bin\libzstd.dll` (1.5.7) was found, so it was bound directly with `ctypes` - nothing installed (`analysis/zstd_ctypes.py`).

The zstd header self-declares its content size: `Frame_Content_Size = 17.175.761.051` bytes. Decompressing yields exactly that number, `frame 1 complete`, no errors → the downloaded file is complete even though the challenge page says "661.3 MB".

The first thirty-two bytes of the image: `45 4d 69 4c 01 00 00 00 ...` → the `LiME` magic (`0x4C694D45`), version 1. LiME is a format of `raw` regions concatenated back to back, each region having a 32-byte header `{magic, version, start, end, type}` followed by its data, so an offset in the file does not translate linearly into a virtual address. `analysis/lime.py` was written to build the region table and do the two-way conversion file offset <-> virtual address:

```
[0] 0x0000000000001000 - 0x0000000000054ffe   0.33 MiB
[1] 0x0000000000100000 - 0x00000000bd2f7ffe   3025.97 MiB   <- RAM thấp
[2] 0x00000000bd305000 - 0x00000000bf8ecffe   37.91 MiB
[3] 0x00000000bfbff000 - 0x00000000bffdfffe   3.88 MiB
[4] 0x0000000100000000 - 0x000000043ffffffe   13312.00 MiB  <- RAM trên 4G
```

volatility3 is not needed for this challenge; everything was done with the self-written parser.

## Solution

**Step 1 - Reading the `.locked` file's structure.** 672 bytes, and because of CBC + PKCS#7 the length must be a multiple of 16. Split `IV = file[:16] = 866f319940024339a78be5b443ed8289`, `C = file[16:]` (656 bytes). This is confirmed by the very line `f.write(iv + ct)` in the source found in RAM.

**Step 2 - Establish known plaintext.** A PDF carved from the RAM page cache at `0x10b021a90` begins with `%PDF-1.4\n1 0 obj`. Use the first 16 bytes of that observed sample, not an assumption about every PDF. Its tail is incomplete because the pages are not contiguous in the dump. The ciphertext implies `656 - pad(9) = 647` plaintext bytes.

**Step 3 - Building a one-block oracle.** With CBC: `P1 = D_K(C1) XOR IV`, so for each 32-byte window `K` in RAM a single one-block ECB decryption is enough:

```
D_K(C1) == P1 XOR IV      <=>      K is the key
```

`P1 XOR IV = a33f75df6d336d0dadbac5846382e0e3`, `C1 = 184d651fa87011ae7437a09a92e186fa`.

**Step 4 - Narrowing the search space using allocation behaviour.** `os.urandom(32)` and `os.urandom(16)` are called back to back, so the two bytes objects sit next to each other on the heap. Since the IV's 16 bytes are already known, it is enough to locate the IV in the dump and sweep around it. The IV appears 9 times; within an 8 KB radius of those positions, the window at

```
vaddr 0x120a63490 (file offset 0xe067852c), -2064 byte relative to the IV object
key = 21c0780db69f7eabeb3b8dafb1810b9611916c6becdaf0b2b318d40894295d6c
```

satisfied the oracle after 6.129 attempts (~3 seconds). This is exactly the kind of result `aeskeyfind` produces, but no tool had to be installed: we have plaintext to check against, which is stronger still than verifying the key-schedule expansion.

**Step 5 - Decrypt and verify strictly.** AES-256-CBC with (key, IV) over the 656 bytes; the last byte is `0x09` and `pt[-9:] == 9*0x09` → valid PKCS#7. Removing the padding leaves 647 bytes forming a complete PDF, with `xref`, `trailer`, `startxref 465`, `%%EOF`. This is the decisive evidence: a wrong key almost certainly breaks the padding and cannot produce such a closed PDF structure.

Inside the PDF:

```
BT /F1 12 Tf 72 720 Td (CONFIDENTIAL patient record. Recovery token: H7CTF{bf3a8e98115450c654b4}) Tj ET
```

**Step 6 - Independent cross-check.** The string `H7CTF{bf3a8e98115450c654b4}` also appears in two other places in RAM (the PDF stream in the page cache, and the `FLAG='...'` environment variable of the scene-planting script). Three independent sources agree.

## Result
```bash
python exploit.py _scratch/memory.raw files/Q3_patient_records.pdf.locked
```

```
[*] 672 B ciphertext = IV(16) + 656 B
[*] LiME: 5 section(s), 16.00 GiB mapped
[+] key 21c0780db69f7eabeb3b8dafb1810b9611916c6becdaf0b2b318d40894295d6c at vaddr 0x120a63490 (-2064 B from the IV object, 6129 windows tested)
[+] plaintext 647 B, PKCS#7 valid, header b'%PDF-1.4'
[+] flag: H7CTF{bf3a8e98115450c654b4}
```

The decrypted PDF is stored in `recovered.pdf`, the flag in `flag.txt`.
