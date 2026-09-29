# Code Breaker — Crypto/Pwn (Hard)

**Flag:** `sun{cr4ck_tHe_ciPh3r_fr33_thE_heaP}` · **Target:** `nc chal.sunshinectf.games 26005`
**Files:** `code_breaker` (PIE, stripped, glibc 2.39), `libc.so.6`, `ld-linux-x86-64.so.2`

## Challenge

"Enterprise-grade encrypted key-value storage, all traffic passes through the proprietary cipher." No other hints. Flag format `sun{...}`.

## Initial Analysis

Connecting for a test returns 20 binary bytes:

```
00 11 01 q é 9 Á Ï â Ù È Z h Ø Í . n 1 @
```

`00 11` is the big-endian length (17), the rest is 17 unreadable bytes. The binary imports `fopen/fread/system/read/write/malloc/free/atoi` and has the strings `/dev/urandom`, `true`, `CodeBreaker`, plus a 256-byte permutation at `0x2040`. A custom protocol with an S-box.

Traffic is encrypted in both directions, so the protocol cannot be probed by trial; the code has to be read. The binary is small (14 KB) and stripped, but only four functions matter: init/handshake `0x1670`, the main loop `0x1900`, `send_message` `0x1510`, `recv_message` `0x13f0/0x13a0`.

## Cipher

**Handshake.** The server reads 16 bytes from `/dev/urandom` and sends them to the client:

```
[0x01] || key            (RAW, chưa mã hoá)
```

The key travels in plaintext on the very channel it is meant to protect. The client must reply with `[0x02] || peer16` (RAW), then an encrypted message `[0x03] || check16`.

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

**Stream:** `ks(off, i) = SBOX[(off + i + state[i & 15]) & 0xff]`, with two independent counters for the sending and receiving directions (`0x42c4` and `0x42c0`), each advancing by exactly the body length of the message just processed.

Reimplemented in Python and let the server itself grade it: the handshake replies `04 00` = correct.

## Instruction table

The jump table at `0x2020` was fully decoded:

| Instruction | Effect |
| --- | --- |
| `10 slot len_be16 value` | PUT: `malloc(len)` + copy |
| `11 slot` | GET: returns `[11][00][len][value]` |
| `12 slot off_be16 data` | WRITE: `memcpy(ptr, data, off)` |
| `13 slot` | FREE: `free(ptr)` then `ref--`, ptr is cleared only when ref reaches 0 |
| `14 a b` | ALIAS: slot a (currently empty) takes b's pointer, `b.ref++` |
| `15 string` | RUN: `call [0x40c0]` with rdi = a copy of the string |
| `16` | INFO: dump 240 bytes of BSS from `0x40c0` |

`[0x40c0]` is initialised to point at the `endbr64; ret` stub at `0x1390`, so instruction `15` is harmless until that slot is overwritten.

Two details decide everything:
- `readelf -l`: GNU_RELRO ends exactly at `0x4000`, while `.got.plt` extends to `0x404068` → GOT writable.
- No further PIE check: it is real PIE, but the INFO instruction lets you read `[0x40c0]` = `base + 0x1390` → a free base leak.

## Approaches Ruled Out

1. Probing the protocol by sending guesses. Every message after the handshake goes through the stream cipher in both directions, so nothing in the responses is readable. Ruled out; the binary had to be dissected and the cipher reimplemented.
2. Poisoning the tcache with a single chunk. The next `PUT` does pop exactly that chunk and sets head = the fake pointer, but `counts` drops to 0, so `_int_malloc` ignores the tcache and allocates from the top chunk. Evidence: the marker `WXYZWXYZ` appears nowhere in the BSS dump after poisoning. Ruled out; two chunks in the same bin are needed.

## Exploit Chain

**Step 1 - UAF.** `PUT slot1(0x100)` → P1; `ALIAS 0 1` makes slot0 and slot1 both point at P1 with `ref=2`; `FREE 1` calls `free(P1)` but ref only drops to 1, so the ptr is not cleared → slot0 still points into a chunk sitting in the tcache.

**Step 2 - leaking to beat safe-linking.** When the chunk is the only element of the bin, `tcache_put` stores `fd = PROTECT_PTR(pos, NULL) = pos >> 12`. `GET` through the live alias returns exactly that value → `P>>12` without knowing P.

**Step 3 - building two chunks in the same bin.** Create P1 and P2 of the same size, free P2 first then P1, and poison `P1->fd` (the head of the list). Now `counts = 2`: pop 1 takes P1 (head becomes the fake pointer, counts drops to 1), pop 2 is the one that actually goes through the tcache.

**Step 4 - landing in BSS.** Fake pointer = `base + 0x40c0`. The second PUT `memcpy`s 256 bytes of our choosing straight into it, so the first 8 bytes are exactly `system@plt = base + 0x1150`. Verified by running INFO again: `[0x40c0] = 0x...bd150` ✓.

**Step 5 - RCE.** Instruction `15` calls `[0x40c0](string)` → `system("cat /ctf/flag.txt")`. The pointer's output is written straight to fd 1 with no length prefix, so it has to be read raw instead of through the protocol parser.

```
$ python -u client.py full "cat /ctf/flag.txt"
[*] handshake reply = 0400  (thành công)
[+] fnptr @0x40c0 = 0x56fe8fbbd390  ->  base = 0x56fe8fbbc000
[*] [0x40c0] = 0x56fe8fbbd150  (kỳ vọng 0x56fe8fbbd150)
---- kết quả ----
sun{cr4ck_tHe_ciPh3r_fr33_thE_heaP}
```

## Flag
```
sun{cr4ck_tHe_ciPh3r_fr33_thE_heaP}
```
