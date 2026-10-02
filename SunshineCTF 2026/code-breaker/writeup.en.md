# Code Breaker — Crypto/Pwn (Hard)

**Flag:** `sun{cr4ck_tHe_ciPh3r_fr33_thE_heaP}` · **Target:** `nc chal.sunshinectf.games 26005`
**Files:** `code_breaker` (PIE, stripped, glibc 2.39), `libc.so.6`, `ld-linux-x86-64.so.2`

## Challenge

"Enterprise-grade encrypted key-value storage, all traffic passes through the proprietary cipher."

## Initial Analysis

Connecting returns 20 binary bytes:

```
00 11 01 q é 9 Á Ï â Ù È Z h Ø Í . n 1 @
```

`00 11` is the big-endian length (17), followed by 17 bytes of data. The binary imports `fopen/fread/system/read/write/malloc/free/atoi` and contains the strings `/dev/urandom`, `true`, `CodeBreaker`, and a 256-byte permutation at `0x2040`. It uses a custom protocol with an S-box.

Traffic is encrypted in both directions. The binary (14 KB) is stripped. 4 main functions: init/handshake `0x1670`, main loop `0x1900`, `send_message` `0x1510`, `recv_message` `0x13f0/0x13a0`.

## Cipher

**Handshake.** The server reads 16 bytes from `/dev/urandom` and sends them to the client:

```
[0x01] || key            (RAW, unencrypted)
```

The client replies with `[0x02] || peer16` (RAW), then an encrypted message `[0x03] || check16`.

**Key schedule** (`window = key || peer`, 32 bytes):

```python
state = bytearray(16)
for outer in range(4):
    for i in range(16):
        x = window[(i + 8*outer) & 0x1f] ^ state[i]
        x = SBOX[x]
        x ^= window[3*outer + i]
        state[i] = rol8(x, 3)
```

**Proof of knowledge:** `check[i] = state[(i+5)&15] ^ SBOX[state[i]]`.

**Stream:** `ks(off, i) = SBOX[(off + i + state[i & 15]) & 0xff]`, with two independent counters for sending and receiving (`0x42c4` and `0x42c0`), each advancing by payload length.

## Instruction table

Jump table at `0x2020`:

| Instruction | Effect |
| --- | --- |
| `10 slot len_be16 value` | PUT: `malloc(len)` + copy |
| `11 slot` | GET: returns `[11][00][len][value]` |
| `12 slot off_be16 data` | WRITE: `memcpy(ptr, data, off)` |
| `13 slot` | FREE: `free(ptr)` then `ref--`, ptr cleared if ref is 0 |
| `14 a b` | ALIAS: slot a (empty) takes b's pointer, `b.ref++` |
| `15 string` | RUN: `call [0x40c0]` with rdi = string copy |
| `16` | INFO: dump 240 bytes of BSS from `0x40c0` |

`[0x40c0]` is initialised to the `endbr64; ret` stub at `0x1390`. Instruction `15` executes the function pointer at this address.

Binary analysis:
- `readelf -l`: GNU_RELRO ends at `0x4000`, `.got.plt` extends to `0x404068` → GOT is writable.
- INFO (`16`) allows reading `[0x40c0]` = `base + 0x1390` → PIE base leak.

## Exploit Chain

**Step 1 - UAF.** `PUT slot1(0x100)` → P1; `ALIAS 0 1` makes slot0 and slot1 point at P1 with `ref=2`; `FREE 1` calls `free(P1)`, ref drops to 1 → ptr is not cleared, slot0 still points to a chunk in the tcache.

**Step 2 - Safe-linking leak.** When the chunk is the only element in the bin, `tcache_put` stores `fd = PROTECT_PTR(pos, NULL) = pos >> 12`. `GET` through the alias returns `P>>12`.

**Step 3 - Tcache poisoning.** Create P1 and P2 of the same size, free P2 then P1. Overwrite `P1->fd`. `counts = 2`: pop 1 takes P1, pop 2 returns the target pointer.

**Step 4 - Overwrite BSS.** Target pointer = `base + 0x40c0`. The second PUT `memcpy`s 256 bytes to `0x40c0`. The first 8 bytes are set to `system@plt = base + 0x1150`.

**Step 5 - RCE.** Instruction `15` calls `[0x40c0](string)` → `system("cat /ctf/flag.txt")`.

```
$ python -u client.py full "cat /ctf/flag.txt"
[*] handshake reply = 0400
[+] fnptr @0x40c0 = 0x56fe8fbbd390  ->  base = 0x56fe8fbbc000
[*] [0x40c0] = 0x56fe8fbbd150
sun{cr4ck_tHe_ciPh3r_fr33_thE_heaP}
```

## Flag
```
sun{cr4ck_tHe_ciPh3r_fr33_thE_heaP}
```
