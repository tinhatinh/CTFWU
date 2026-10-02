# Parcel Bomb — Pwn (Medium)

**Flag:** `H7CTF{0b79ca94-3b66-4509-9365-34d224d5cfe2}`
**Remote:** `nc pwn.h7tex.com 41136`
**Files:** `dispatch.zip` (1.03 MiB, sha256 `72f6e078…`) containing `dispatch` (ELF64 ET_EXEC, sha256 `d946ba60…`), `libc.so.6` (glibc 2.39-0ubuntu8.9), `ld-linux-x86-64.so.2`, `README.txt`.

## Challenge

A "Sparrow Freight dispatch" terminal asks for a waybill number and then logs it. The buffer is 64 bytes but
`read` takes 512, and the binary hands you no `system` and no `/bin/sh` string. Objective: take the flag from
the running instance.

## Initial Analysis

```
$ node ~/.qoder/skills/ctf-solve/scripts/triage.cjs dispatch
class=64-bit type=ET_EXEC (no PIE)  entry=0x401090  PIE=no RELRO=yes STACK=non-exec
$ readelf --dyn-syms -W dispatch
puts  read  setvbuf  __libc_start_main  stdout      # no system/execve
```

`objdump -d -M intel` shows the whole program has only three functions worth caring about:

| address | contents |
| --- | --- |
| `0x401176` | `pop rdi ; ret` (a gadget deliberately embedded), `0x401177` = `ret` |
| `0x401178` | `vuln()`: `puts(prompt)`; `read(0, rbp-0x40, 0x200)`; `puts("waybill logged.")`; `leave; ret` |
| `0x4011bb` | `main()`: `setvbuf(stdout, NULL, _IONBF, 0)`; `puts(banner)`; `call vuln` |

The mitigations, one at a time:

- No canary. The symtab has no `__stack_chk_fail`, so the 512-byte `read` into a 64-byte buffer writes
  straight over the saved rbp and the return address. Offset to the return address = `0x40 + 8 = 72`.
- No PIE, so every gadget and every GOT slot of the binary is a known constant.
- Full RELRO. `GNU_RELRO` covers `0x403df8 + 0x208`, so `.got`/`.got.plt` are read-only, ruling out ret2got-plt.
- NX, so no shellcode on the stack.

One obstacle remains: the program never prints the contents of the buffer, so this single-shot overflow
cannot leak libc on its own, and libc is somewhere inside the 512 bytes that `read` allows.

The banner received from `pwn.h7tex.com:41136` matches the string inside `dispatch` byte for byte, confirming the
instance runs exactly the binary provided, so static analysis is enough (the win32 host has no qemu/docker, so the
ELF was never executed locally).

## Exploit Chain

### Step 1: manufacture the leak with ROP, no libc base needed

`puts` has already been called to print the prompt, so lazy binding has resolved `puts@GOT` at `0x404000` into a real
pointer inside libc. Calling `puts@plt` again with `rdi = 0x404000` prints exactly the 6 bytes of that pointer
(`stdout` is `_IONBF`, so it returns immediately). Then return to `vuln` (`0x401178`) for a second overflow on the
same connection; since there is no PIE, the second stack layout is identical to the first.

```
pad(72) | pop_rdi_ret | 0x404000 | ret | puts@plt | ret | 0x401178(vuln)
```

### Step 2: 16-byte alignment

In `vuln`, `rsp` at function entry is `≡ 8 (mod 16)` (inferred from `and rsp,-16` in `_start` and `push rbp` in
`main`). After `leave; ret` we have `rsp ≡ 0`, and the ABI requires the callee to see `rsp ≡ 8` at its first
instruction, so:

- a `ret` (`0x401177`, taken for free from the tail of `pop_rdi_ret`) must be inserted before `puts@plt`, otherwise
  `puts` runs with a stack misaligned by 8 bytes and eats a `SIGSEGV` inside `movaps`;
- stage 1 must pop an even number of qwords. With 6 qwords (48 bytes) the second `vuln` frame is entered with
  `rsp ≡ 8`, exactly as on the first pass, meaning neither the two `puts` calls inside `vuln` nor `system` in stage 2
  need any further adjustment;
- for the same reason, stage 2 also keeps the `pop_rdi_ret | arg | ret | target` shape.

### Step 3: spending the leak

```
$ python exploit.py pwn.h7tex.com 41136 "id; ls -la; cat flag flag.txt /flag /flag.txt 2>/dev/null; ls /"
[*] leaked bytes: c07c88edae7f0a (7)
[+] puts -> 0x7faeed887cc0, libc base = 0x7faeed800000
[*] post-exploitation output (1378 bytes):
waybill logged.
uid=0(root) gid=0(root) groups=0(root)
...
-rw-r--r--  1 root root   44 Sep 26 05:28 flag
H7CTF{0b79ca94-3b66-4509-9365-34d224d5cfe2}
```

`0x7faeed887cc0 - 0x87cc0 = 0x7faeed800000` (page-aligned, `0x7f…` right in the mmap region), with
`system = base + 0x58750` and `"/bin/sh" = base + 0x1cc42f` taken from the challenge's `libc.so.6`:

```
pad(72) | pop_rdi_ret | base+0x1cc42f | ret | base+0x58750(system)
```

`system()` inherits stdin/stdout as the socket, so the shell is interactive directly on the connection, running as
`uid=0` inside the container, and the flag sits at `/flag`.

Both payloads are sent over a single connection because ASLR re-randomises on every connect: the first three attempts
leaked three different bases (`0x7f57a5a00000`, `0x7f57c4c00000`, `0x7f3bfbc00000`), so a leak is only worth
something inside the very connection that produced it.

## Flag
```
H7CTF{0b79ca94-3b66-4509-9365-34d224d5cfe2}
```

Rerun: `python exploit.py pwn.h7tex.com 41136 "cat /flag"`
