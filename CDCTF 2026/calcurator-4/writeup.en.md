# CalcuRATor (4/4) - Forensics + Rev Eng + OSINT (500 points)

**Flag:** `cdctf{libqalculate/prism}` · **Files:** `files/calculator`, 7868520 bytes, sha256 `c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6`

## Challenge

Identify the two source repositories merged into the binary.

## Initial analysis

All four inputs share the same SHA-256. Analysis used Python 3.12 and GNU objdump without executing the sample.

The binary contains libqalculate, qalc, QALCULATE environment names, and documentation URLs. The backdoor implements raw ICMP reception, callback parsing, and argv rewriting.

## Discarded approaches

Search hits for icmpdoor/icmpsh did not establish a match merely by protocol. The attempted JadedWraith repository returned HTTP 404. PRISM provides concrete parser and process-renaming matches.

## Solution chain

Qalculate/libqalculate contains the qalc CLI. andreafabrizi/prism matches the 1024-byte buffer, ICMP_ECHO check, `%15s %d` callback parser, positive-port and address-length checks, fork, and reverse shell. Its strncpy/memset argv rewriting also matches. The challenge changes the label to wpad and adds XOR checking; repository names remain libqalculate/prism.

```bash
objdump -d -M intel --start-address=0x12b330 --stop-address=0x12b5a7 files/calculator
```

```python
import argparse, hashlib
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument("artifact", type=Path)
a = p.parse_args()
b = a.artifact.read_bytes()
assert hashlib.sha256(b).hexdigest() == "c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6", "Unexpected artifact"
assert b"libqalculate\0" in b and b"QALCULATE_USER_DIR\0" in b
assert b"%15s %d\0" in b and b"/bin/sh\0" in b
assert b[0x12b4c8:0x12b4cd] == bytes.fromhex("807c243408")
src = (Path(__file__).parent / "analysis" / "prism.c").read_text()
for token in ["socket(AF_INET, SOCK_RAW, IPPROTO_ICMP)", '"%15s %d"', "strncpy(argv[0], PROCESS_NAME, strlen(argv[0]))"]:
    assert token in src
# Attribution follows the documented manual source comparison, not strings alone.
print("cdctf{libqalculate/prism}")
```

The flag was derived and printed locally; no accepted submission was recorded.

Source references:

- https://github.com/Qalculate/libqalculate/blob/master/man/qalc.1
- https://github.com/andreafabrizi/prism/blob/master/prism.c

## Flag

```bash
python exploit.py files/calculator
```

```text
cdctf{libqalculate/prism}
```

## Reproduce

```bash
python exploit.py files/calculator
```
