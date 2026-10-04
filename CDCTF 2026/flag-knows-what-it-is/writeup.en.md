# The flag knows what it is at all times - Crypto (500 points)

**Flag:** `cdctf{it is sure where it isn't, within reason, and it knows where it was}`
**Attached file:** `files/cipher.txt`, 149 bytes, sha256 `23b75625f0b46c16e92de1844d77ece044918557cd472c0a398cb94da2afea75`
**Event:** CDCTF 2026 (Crimson Defense CTF) · **Author:** alex

## Problem Description

The description gives a 148-character hex string and claims the flag "knows what it is because it knows what it isn't". The required format is `cdctf{...}`. There is no attachment and no instance; the hex string in the description is the whole dataset.

## Initial Analysis

- 148 hex characters is an even count, so 74 bytes with no stray separators.
- Measured byte range is `0x82-0xdf`. No byte is below `0x80`, so this is not raw text; that range is exactly the image of printable ASCII (`0x20-0x7e`) under a bitwise NOT (`0xdf-0x81`).
- The phrase "it knows what it isn't" describes the NOT operation: `x ^ 0xFF = ~x`.

## Exploitation Chain

**Step 1 - Apply the bitwise NOT to the first six bytes.** If the cipher really is NOT, those bytes must decode to the `cdctf{` prefix.

```python
>>> h = "9c9b9c8b9984"
>>> [f"{int(h[i:i+2],16):02x} ^ ff = {chr(0xff ^ int(h[i:i+2],16))}" for i in range(0, 12, 2)]
['9c ^ ff = c', '9b ^ ff = d', '9c ^ ff = c', '8b ^ ff = t', '99 ^ ff = f', '84 ^ ff = {']
```

**Step 2 - Sweep all 256 single-byte XOR keys instead of trusting the guess.** A key counts only if it yields printable ASCII and brackets the flag with `cdctf{` / `}`.

```python
data = bytes.fromhex(hexstr)
hits = []
for key in range(256):
    text = "".join(chr(b ^ key) for b in data)
    if text.isprintable() and text.startswith("cdctf{") and text.endswith("}"):
        hits.append((key, text))
```

```text
[*] cipher.txt: 148 hex ky tu
[*] 74 byte, pham vi 0x82-0xdf
[*] quet 256 key XOR 1 byte: 1 kha nang
[+] key duyet = 0xff (XOR 0xff = bitwise NOT)
    9c ^ ff = c
    9b ^ ff = d
    9c ^ ff = c
    8b ^ ff = t
    99 ^ ff = f
    84 ^ ff = {
[+] flag: cdctf{it is sure where it isn't, within reason, and it knows where it was}
```

**Step 3 - Verification.** The sweep can return several keys that all produce printable text; it returned exactly one, under the stated prefix, suffix and printable-ASCII conditions. The plaintext is a coherent English sentence that reuses the wording of the challenge text ("it is sure ... within reason ... it knows where it was"), and all 74 bytes are consumed with nothing left undecoded.

## Flag

```text
cdctf{it is sure where it isn't, within reason, and it knows where it was}
```

## Reproduce

```bash
python exploit.py files/cipher.txt
```

No private keys or instance credentials appear in the script.
