# CalcuRATor (1/4) - Forensics + Rev Eng (491 points)

**Flag:** `cdctf{wpad}` · **Files:** `files/calculator`, 7868520 bytes, sha256 `c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6`

## Challenge

Recover the name adopted by the malicious component after startup.

## Initial analysis

All four inputs share the same SHA-256. Analysis used Python 3.12 and GNU objdump without executing the sample.

Strings reveals `wpad` at offset `0x5c832d`. Its code reference distinguishes a process label from an unrelated string.

## Discarded approaches

The original calculator name is excluded because daemon code overwrites argv[0]. No PR_SET_NAME call was established; the evidence concerns the command-line name.

## Solution chain

At `0xf0f58` the code calls setsid(), followed by chdir(). At `0xf0f7e` it loads `0x5c832d`, and at `0xf0f8a` calls strncpy(argv[0], "wpad", strlen(argv[0])). Remaining arguments are overwritten with spaces.

```bash
objdump -d -M intel --start-address=0xf0f58 --stop-address=0xf0fde files/calculator
```

```python
import argparse, hashlib
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument("artifact", type=Path)
a = p.parse_args()
b = a.artifact.read_bytes()
assert hashlib.sha256(b).hexdigest() == "c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6", "Unexpected artifact"
assert b[0xf0f7e:0xf0f85] == bytes.fromhex("488d35a8734d00")
name = b[0x5c832d:].split(b"\0", 1)[0].decode()
print(f"cdctf{{{name}}}")
```

The flag was derived and printed locally; no accepted submission was recorded.

## Flag

```bash
python exploit.py files/calculator
```

```text
cdctf{wpad}
```

## Reproduce

```bash
python exploit.py files/calculator
```
