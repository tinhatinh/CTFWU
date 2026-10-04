# CalcuRATor (3/4) - Forensics + Rev Eng (500 points)

**Flag:** `cdctf{1CMP_TR1GG3R$}` · **Files:** `files/calculator`, 7868520 bytes, sha256 `c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6`

## Challenge

Recover the missing information required in the Echo Request payload.

## Initial analysis

All four inputs share the same SHA-256. Analysis used Python 3.12 and GNU objdump without executing the sample.

After checking the type, the first payload byte must be c; the next 19 bytes undergo an XOR comparison.

## Discarded approaches

An Echo Request alone is insufficient because the first-byte check and XOR loop reject an incorrect payload. The stored target is not the plaintext key: received bytes are XORed before comparison.

## Solution chain

Packet offset 28 must contain 0x63. The loop at `0x12b500` uses key indices 2..20 at `0x5e700f` and target indices 1..19 at `0x5c62db`. XOR them and prepend c. The subsequent parser also requires a callback address and positive port after the key; it uses `%15s %d` and requires an address string of at least 7 characters.

```bash
objdump -d -M intel --start-address=0x12b4c8 --stop-address=0x12b5a7 files/calculator
```

```python
import argparse, hashlib
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument("artifact", type=Path)
a = p.parse_args()
b = a.artifact.read_bytes()
assert hashlib.sha256(b).hexdigest() == "c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6", "Unexpected artifact"
assert b[0x12b4cf:0x12b4d4] == bytes.fromhex("807c243c63")
target = b[0x5c62db:0x5c62db + 21]
key = b[0x5e700f:0x5e700f + 24]
trigger = b"c" + bytes(target[i - 1] ^ key[i] for i in range(2, 21))
print(trigger.decode())
```

The flag was derived and printed locally; no accepted submission was recorded.

## Flag

```bash
python exploit.py files/calculator
```

```text
cdctf{1CMP_TR1GG3R$}
```

## Reproduce

```bash
python exploit.py files/calculator
```
