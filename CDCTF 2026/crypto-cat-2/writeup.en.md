# Crypto Cat Caticus Catanius (2/5) - Crypto (496 points)

**Flag:** `cdctf{exclus1ve_x0r1n_these_byt3s_and_5tuff}` · **Files:** `files/ciphertext.txt`, 135 bytes, sha256 `fc729a7d866ee019d3da211dd885f86922885d6d2205e51e558c1c318c1360dd`
**Event:** CDCTF 2026 (Crimson Defense CTF) · **Author:** alex

## Challenge

Part 2/5 of the Crypto Cat series. The challenge card prints 45 hex tokens and nothing else: no
download, no instance. The line "it seems you have cracked my first key" points back at part 1,
which was plain Atbash (`xwxgu{...}` to `cdctf{...}`), but the ciphertext itself says nothing about
the algorithm.

## Analysis

- 45 hex tokens, each containing two hex digits, packing into exactly 45 bytes with nothing left over.
- Byte values span `0x85` to `0xfd`, 24 distinct values. No byte is below `0x80`.
- That span is the image of printable ASCII (`0x20`-`0x7e`) under a mask with bit 7 set, which makes
  single-byte XOR the first candidate. The byte `0x85` sits outside the rest of the range
  (`0xba`-`0xfd`) and is the fingerprint of a plaintext `0x0a`: `0x85 ^ 0x8f = 0x0a`, so the
  ciphertext ends with a line feed.

## Approaches tried

1. **Multi-byte XOR / byte-wise Vigenère (L = 2..15 over `xor`, `sub`, `add`, `beaufort`).**
   `analysis/triage.py` keeps a key byte for a column only if every byte in that column decodes to a
   printable value. Under the strict `0x20`-`0x7e` test only `xor` survives, and each column still has
   20-94 candidates, so the key is not determined; `sub`, `add` and `beaufort` have no candidates at the tested lengths.
   Relaxing the test to also allow tab/LF/CR lets `xor` survive at L = 1, leaves `sub`/`add` only at
   L = 8, 9, 10, 15, and finds no `beaufort` candidate. Multi-byte keys remain underdetermined; the single-byte key is selected using the flag prefix below.
2. **Atbash, inherited from part 1.** `analysis/atbash_check.py` tests both levels: Atbash on the hex
   characters maps digits to `0xa2`-`0xab` (non-ASCII), and a bitwise NOT of the bytes leaves only
   11 of 45 bytes printable, first six being `0x13 0x14 0x13 0x04 0x16 0x0b`. As a control, the same
   counter run with the winning key reports 44/45, so "11/45" comes from a probe that can detect a
   positive. Rejected.

## Solution

**Step 1 - Sweep all 256 single-byte keys.** Count keys for which every decoded byte is printable,
under two standards: strictly printable ASCII, and ASCII plus tab/LF/CR.

```python
def dec(k):
    return bytes(b ^ k for b in data)


LOOSE = set(range(0x20, 0x7F)) | {0x09, 0x0A, 0x0D}
loose = [k for k in range(256) if all(c in LOOSE for c in dec(k))]
strict = [k for k in range(256) if all(0x20 <= c < 0x7F for c in dec(k))]
```

```text
[*] XOR 1 byte, 256 khoa: 0 khoa cho ASCII in duoc tuyet doi, 5 khoa neu cho phep them tab/LF/CR
    k=0x8c, k=0x8f, k=0xd9, k=0xda, k=0xdd
```

No key passes the strict test The key selected below decodes the last byte as `0x0a`. The five keys that
pass the relaxed test are the whole solution space, not a sample of it.

**Step 2 - Cut the list with the flag-format crib.** Of those five, one starts with `cdctf{`.

```python
hit = [k for k in loose if dec(k).startswith(b"cdctf{")]
```

```text
[*] khoa vua ASCII vua mo dau bang dinh dang cdctf{: 1 -> k=0x8f
[+] plaintext (repr): b'cdctf{exclus1ve_x0r1n_these_byt3s_and_5tuff}\n'
```

`0x8f` is the only tested single-byte key satisfying the flag-prefix condition. The digits `1`, `0`, `3` in the body come directly from the decoded output.

**Step 3 - Verification.** Re-encrypting the whole plaintext with `0x8f` must reproduce the hex
string printed on the card.

```text
[+] round-trip: ma hoa lai 45 byte voi 0x8f cho ra dung chuoi de ban dau -> True
```

All 45 bytes are consumed, the flag body contains no whitespace, and the `{}` pair closes once.

## Result

```bash
python exploit.py files/ciphertext.txt
```

```text
[*] ciphertext.txt: 45 to hex, goi lai duoc 45 byte
[*] dai byte: 0x85 - 0xfd, 24 gia tri phan biet
[*] so byte duoi 0x80: 0 (0 = khong phai ASCII thuan, nen day la ket qua cua phep doi cho)
[*] XOR 1 byte, 256 khoa: 0 khoa cho ASCII in duoc tuyet doi, 5 khoa neu cho phep them tab/LF/CR
    k=0x8c, k=0x8f, k=0xd9, k=0xda, k=0xdd
[*] khoa vua ASCII vua mo dau bang dinh dang cdctf{: 1 -> k=0x8f
[+] khoa k = 0x8f = 143
[+] plaintext (repr): b'cdctf{exclus1ve_x0r1n_these_byt3s_and_5tuff}\n'
[*] byte cuoi 0x85 XOR 0x8f = 0x0a -> ky tu xuong dong, khong thuoc co
[+] round-trip: ma hoa lai 45 byte voi 0x8f cho ra dung chuoi de ban dau -> True
[+] flag: cdctf{exclus1ve_x0r1n_these_byt3s_and_5tuff}
[+] da luu flag.txt
```

## Reproduce

```bash
python exploit.py files/ciphertext.txt
```

`analysis/triage.py` is the multi-key sweep, `analysis/atbash_check.py` is the Atbash rejection; both
run from the case directory and their recorded output sits next to them as `.out`. There is no
downloaded artifact: `files/ciphertext.txt` is a verbatim copy of the hex line from the challenge card.
