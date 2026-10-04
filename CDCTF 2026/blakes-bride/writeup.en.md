# Blake's Bride - Forensics (500 points)

**Flag:** `cdctf{epithalamium738-trousseau201-honeymoon069}`
**Attachment:** `blake.png` (139,894 B, SHA256 `60cfcb420af6bd3b30b6fd0a9ee9abcb5584a2d47cb179dafc8448dac673178c`)

## Challenge

The challenge ships one image, `blake.png`, and states that the bride's three passwords were
"stored and encrypted in an unorthodox manner". The constraints are given: each password is one
wedding-related word followed by three digits, and the flag joins them as
`password1-password2-password3`.

## Initial analysis

`file` and `exiftool` report a 981x731 PNG, 8-bit RGB, non-interlaced. The chunk structure is
clean: `IHDR, sRGB, gAMA, pHYs, iTXt, IDAT x3, IEND`, and `IEND` ends the file - no bytes are
appended after it.

Everything relevant sits in the single `iTXt` chunk (keyword `XML:com.adobe.xmp`). Inside that
XMP block there is an `exif:UserComment` tag:

```text
c2a587abcc00c2837b095e508cacf90f47b1ffd4c765269baabc0a55d5ee5ee1
6f591da144d0d64205899814d786ac3abbdff81a74d5e9b46b0bfd89e71d021a
-6bb9798a3011496566d842e4fd78be4aaa1a683028ddd190aaad374d89db5b02
a26cbed538ebe8baadca4d9c9b167de7f132d5bd30205ad6814b6c865dd7344a
-0fed6e840bbe32beda22f5ae7c0e41bc8c0995103a1ded55c694209f9118f534
908c5d8750b561e81e75b844c1b00e77cabe8866a4d7c97bfb7b719789201dc0
```

Three hex strings, 128 characters (64 bytes) each, separated by `-`. The 64-byte length points
at SHA-512, but that hint is correct only about the size.

## Ruled out

1. **SHA-512 / SHA3-512**: over the `<word> + 000..999` space, both functions match 0/3 digests.
   Ruled out.
2. **LSB steganography in the image**: extracting the low 1, 2 and 3 bits of each channel in both
   bit orders yields printable-byte ratios of only 0.043 / 0.019 / 0.010, and the output is
   noise. Ruled out.
3. **Data appended after `IEND` or hidden chunks**: walking the whole chunk list leaves 0 bytes
   after `IEND`. Ruled out.

The checks above found no useful data outside XMP. Continue testing 64-byte hash functions on the password space specified by the challenge.

## Exploit chain

**Step 1 - Identify the algorithm.** 128 hex characters are 64 bytes, but testing directly
against the given password space shows the function is BLAKE2b (64-byte digest by default). The
artifact name `blake.png` and the line "I wonder if there's something wrong with Blake" refer to
BLAKE2b, not to a person.

```python
import hashlib
hashlib.blake2b(b"honeymoon069").hexdigest()
hashlib.sha512(b"honeymoon069").hexdigest()
```

```text
0fed6e840bbe32beda22f5ae7c0e41bc8c0995103a1ded55c694209f9118f534908c5d8750b561e81e75b844c1b00e77cabe8866a4d7c97bfb7b719789201dc0
44dfa8f69d16d8a4efca3781a29191e1ab4fd65a6b7a2cd765636f466a04120673f5bf30d25426c96521c7a320a32bef1e3e3dcf5f1c4827b41310f311855660
```

The first line is exactly the third digest in `UserComment`; the second matches no position.

**Step 2 - Sweep a wedding dictionary.** For each word, try the 1000 digit suffixes `000..999`,
comparing `.digest()` as `bytes` to avoid the `hexdigest()` cost. A list of roughly 200
wedding-themed words returns one password: `honeymoon069` matches the third digest, while
SHA-512 and SHA3-512 still give 0/3 over the same space. `epithalamium` (a wedding song) and
`trousseau` (a bride's belongings) are not in that short list.

**Step 3 - Widen the dictionary.** Switch to a 369,778-entry English wordlist, same
`<word> + 3 digits` construction, split across 16 processes. The remaining two digests close in
under 75 seconds with no extra constraint:

```text
words 369778 mode lower
HIT trousseau201 6bb9798a3011496566d842e4fd78be4aaa1a683028ddd190aaad374d89db5b02a26cbed538ebe8baadca4d9c9b167de7f132d5bd30205ad6814b6c865dd7344a
HIT epithalamium738 c2a587abcc00c2837b095e508cacf90f47b1ffd4c765269baabc0a55d5ee5ee16f591da144d0d64205899814d786ac3abbdff81a74d5e9b46b0bfd89e71d021a
HIT honeymoon069 0fed6e840bbe32beda22f5ae7c0e41bc8c0995103a1ded55c694209f9118f534908c5d8750b561e81e75b844c1b00e77cabe8866a4d7c97bfb7b719789201dc0
```

**Step 4 - Verify.** Recompute the digest of each candidate and compare it against its own
position in `UserComment`. All three match on both value and position, so the flag is joined in
order 1-2-3.

`exploit.py` merges Steps 1 through 4 into a single run and replaces the full English
dictionary with `files/wedding_words.txt` (521 words, extended with archaic and literary
wedding vocabulary), so the solution reproduces without an external wordlist.

## Flag

```bash
python exploit.py files/blake.png
```

```text
[*] blake.png: 139894 bytes
[*] UserComment: 3 digest, do dai hex [128, 128, 128]
[*] wordlist wedding_words.txt: 521 tu x 1000 so = 521000 hash/thuat toan (jobs=1)
[*] blake2b  : 3/3 digest khop
[+] thuat toan: blake2b
[+] password1: epithalamium738  -> c2a587abcc00c2837b095e508cacf90f...
[+] password2: trousseau201     -> 6bb9798a3011496566d842e4fd78be4a...
[+] password3: honeymoon069     -> 0fed6e840bbe32beda22f5ae7c0e41bc...
[+] flag: cdctf{epithalamium738-trousseau201-honeymoon069}
[+] da luu flag.txt
```

The flag above is assembled locally from `blake.png`; it has not been checked against the
platform by submission.

## Reproduce

```bash
python exploit.py files/blake.png                                    # 6.4 s
python exploit.py files/blake.png /path/to/words_alpha.txt -j 16     # 2 min 11 s
```

`exploit.py` uses only the standard library and takes the artifact and wordlist paths from
`argv`. The first run uses the bundled `files/wedding_words.txt`; the second ignores the wedding
list and sweeps the full English dictionary. Both print the same flag.

`analysis/` keeps the three probes used to rule the other directions out and to reproduce the
numbers in this writeup: `chunk_walk.py` (chunk structure, 0 bytes after `IEND`), `lsb_scan.py`
(printable-byte ratio at 1/2/3 low bits), `dict_sweep.py` (the 16-process full-dictionary pass).
Each script's output is stored next to it.
