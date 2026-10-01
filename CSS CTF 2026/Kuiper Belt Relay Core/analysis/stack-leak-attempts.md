# Stack Leak Attempts - Kuiper Belt Relay Core

## Goal
Leak return address and other stack values through `%s` format string vulnerability after echoed buffer.

## Command

```bash
python fine.py  # Output offsets 63-96 with hex dump of trailing bytes
```

## Evidence

```
n= 63 echoedA= 63 gb=1 extra_hex=b'0a476f6f64627965210a'
n= 64 echoedA= 64 gb=1 extra_hex=b'0a476f6f64627965210a'
...
n= 71 echoedA= 71 gb=1 extra_hex=b'0a476f6f64627965210a'
n= 72 echoedA= 72 gb=0 extra_hex=b'0a'
n= 73 echoedA= 73 gb=0 extra_hex=b'0a'
n= 74 echoedA= 74 gb=0 extra_hex=b'0a'
```

## Result: DEAD - NUL terminator from gets()

`gets()` writes `\x00` immediately after user input. With 64-bit addresses starting at 0x40xxxxxx, the low byte (e.g., 0x16) occupies position 72. Writing this byte first causes `gets()` to inject NUL at LSB(return_address), truncating any subsequent `%s` read.

This explains why no stack leak is possible — not a sign of null bytes in memory, but the inherent behavior of `gets()` on non-null-terminated payloads.

Alternative: oracle-based scanning on live service (confirmed successful).
