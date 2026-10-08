# CalcuRATor (2/4) - Forensics + Rev Eng (500 points)

**Flag:** `cdctf{ICMP ECHO REQUEST}` · **Files:** `files/calculator`, 7868520 bytes, sha256 `c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6`

## Challenge

Identify the packet type accepted by the backdoor handler.

## Analysis

All four inputs share the same SHA-256. Analysis used Python 3.12 and GNU objdump without executing the sample.

Function `0x12b460` opens a raw socket with arguments 2, 3, 1, then compares the ICMP type byte with 8.

## Approaches tried

HTTP/TLS is excluded by the IPPROTO_ICMP socket. An ordinary Echo Request passes only the type check, not the later key check.

## Solution

At `0x12b490`, socket(2,3,1) means AF_INET/SOCK_RAW/IPPROTO_ICMP. The receive buffer starts at rsp+0x20; at `0x12b4c8`, [rsp+0x34] is compared with 8. Offset 20 is the ICMP type after a 20-byte IPv4 header. Type 8 is Echo Request.

```bash
objdump -d -M intel --start-address=0x12b460 --stop-address=0x12b536 files/calculator
```

```python
import argparse, hashlib
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument("artifact", type=Path)
a = p.parse_args()
b = a.artifact.read_bytes()
assert hashlib.sha256(b).hexdigest() == "c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6", "Unexpected artifact"
assert b[0x12b461:0x12b46b] == bytes.fromhex("be03000000bf02000000")
assert b[0x12b48b:0x12b490] == bytes.fromhex("ba01000000")
assert b[0x12b4c8:0x12b4cd] == bytes.fromhex("807c243408")
protocol = {1: "ICMP"}[int.from_bytes(b[0x12b48c:0x12b490], "little")]
packet = {8: "ECHO REQUEST"}[b[0x12b4cc]]
print(f"cdctf{{{protocol} {packet}}}")
```

The flag was derived and printed locally; no accepted submission was recorded.

## Result

```bash
python exploit.py files/calculator
```

```text
cdctf{ICMP ECHO REQUEST}
```

## Reproduce

```bash
python exploit.py files/calculator
```
