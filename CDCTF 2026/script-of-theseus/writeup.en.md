# Script of Theseus - Forensics (493 points)

**Flag:** `cdctf{0D}` · **Files:** `original_epic_python_script.py` (156 bytes, sha256 `56c4472cb2f3876c86932bfecb18d276af7f8e8a4b6fb146b40d02d8f90f0b3f`) and `replaced_epic_python_script.py` (163 bytes, sha256 `c88ef02ea2a56fdd9957a86f79d8799fe2b2388a06fe4b9b979f34bbfa402c57`)

## Challenge

The challenge provides two copies of the same short Python script: the author's original (a Linux user) and
a version where a friend "deleted and rewrote every line" on Windows. The task is to find the difference
and submit the uppercase hex code of one byte of that difference, as `cdctf{FF}`. The challenge ships
files only, there is no instance.

## Initial analysis

The two files are close in size: 156 and 163 bytes, a 7-byte gap. `file` describes both as
`Python script, ASCII text executable`, but only the `replaced` copy carries the extra note
`with CRLF line terminators`.

```bash
file files/*.py
```

```text
files/original_epic_python_script.py: Python script, ASCII text executable
files/replaced_epic_python_script.py: Python script, ASCII text executable, with CRLF line terminators
```

A hexdump of the first bytes settles it: the original ends each line with `0a`, the replaced copy with
`0d 0a`.

```text
00000000: 2321 2f75 7372 2f62 696e 2f65 6e76 2070  #!/usr/bin/env p
00000010: 7974 686f 6e33 0a0a 636f 6c6f 723d 696e  ython3..color=in         <- original

00000000: 2321 2f75 7372 2f62 696e 2f65 6e76 2070  #!/usr/bin/env p
00000010: 7974 686f 6e33 0d0a 0d0a 636f 6c6f 723d  ython3....color=         <- replaced
```

What still needs proving is not that CRLF exists, but that nothing else changed: if the friend had also
edited a token somewhere, the differing byte would not be unique.

## Routes ruled out

1. **The script body was edited (variable names, strings, indentation, extra lines)**: remove `0d` from
   the replaced copy and compare with the original - `cmp` reports the files as identical, and both
   still have 7 lines (`grep -c ''` returns 7 for each). Ruled out.
2. **The difference is a BOM or a UTF-16 encoding**: the first 8 bytes of both files match byte for byte
   (`23 21 2f 75 73 72 2f 62`), with no `ef bb bf` or `ff fe`; `file` still reports ASCII for both.
   Ruled out.
3. **The replaced copy has extra blank lines**: both files contain exactly 7 `0a` bytes, so no new
   newline was introduced, only bytes inserted before newlines that were already there. Ruled out.
4. **Listing differences with `cmp -l`**: the command prints more than 130 differing positions because a
   single inserted byte at `0x16` shifts every later index, so the two streams are compared out of
   phase. The measurement method is dropped in favour of byte-frequency counts and a normalized compare.

## Exploitation chain

**Step 1 - Count bytes instead of diffing text.** Take the frequency of each byte value in both files and
subtract in both directions. `analysis/byte_freq.py` performs this and also prints the LF/CR totals.

```bash
python analysis/byte_freq.py
```

```text
original_epic_python_script.py: 156 byte, LF(0x0A) 7, CR(0x0D) 0, 8 byte dau 23 21 2f 75 73 72 2f 62
  BOM: khong | phi ASCII in duoc: 149/156
replaced_epic_python_script.py: 163 byte, LF(0x0A) 7, CR(0x0D) 7, 8 byte dau 23 21 2f 75 73 72 2f 62
  BOM: khong | phi ASCII in duoc: 149/163

Them o ban sau : {'0x0D': 7}
Mat di o ban sau: {}

Vi tri 0x0D: ['0x16', '0x18', '0x45', '0x63', '0x7b', '0x82', '0xa1']
Duoc 0x0A di kem: 7/7
Xoa het 0x0D -> khop ban goc: True
```

The replaced copy is 7 bytes longer, every surplus byte is `0x0D`, and the reverse difference is empty,
so no byte of the shared content disappeared.

**Step 2 - Establish what the `0x0D` bytes do.** All seven `0x0D` bytes in the replaced copy sit directly
before a `0x0A` (`Duoc 0x0A di kem: 7/7`), at offsets `0x16 0x18 0x45 0x63 0x7b 0x82 0xa1`. That is
exactly the script's seven line breaks: each `0D 0A` pair is a Windows line ending where the original has
a Linux `0A`.

**Step 3 - Verify with the reverse test.** Deleting every `0x0D` from the replaced copy yields a 156-byte
stream that matches the original byte for byte, so the difference between the two files is only the
`0x0D` bytes.

```bash
tr -d '\r' < files/replaced_epic_python_script.py | cmp - files/original_epic_python_script.py && echo "giong het ban goc"
```

```text
giong het ban goc
```

## Flag

```bash
python exploit.py
```

```text
[*] original: 156 byte, LF 7, CR 0
[*] replaced: 163 byte, LF 7, CR 7
[*] lech do dai: 7 byte
[*] byte them: {'0x0D': 7}
[*] byte mat:  {}
[*] vi tri 0x0D: 0x16 0x18 0x45 0x63 0x7B 0x82 0xA1
[*] 0x0D 0x0A lien ke: 7/7 -> line ending CRLF
[+] xoa 7 byte 0x0D khoi ban replaced -> 156 byte, trung khop ban goc: True
[+] FLAG: cdctf{0D}
```

```
cdctf{0D}
```

## Reproduce

```bash
python exploit.py files/original_epic_python_script.py files/replaced_epic_python_script.py
```

The script reads the two paths from argv (falling back to `files/`), prints the byte-frequency table,
checks that a single byte value accounts for the whole gap and that every occurrence precedes `0A`,
runs the reverse test from Step 3, and writes `flag.txt`. `analysis/byte_freq.py` is the discovery
probe; its output is stored in `analysis/byte_freq.txt`.
