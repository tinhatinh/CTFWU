---
title: "End of Life"
category: "Pwn"
tags: ["text-binary-mode-mismatch", "stack-overwrite", "16-bit-rop", "dos-int21h"]
solve_date: "2026-10-10"
language: "en"
---

# End of Life

**Flag:** `FortID{3oF_15_JU57_4_5u993571On_829c948e61}`  
**Service:** `ncat --ssl end-of-life-ee7d2f4fa278.inst20.ctf.fortid.com 1337` (TLS on port 1337; the flag was taken on instance `ee7d2f4fa278`, the first connection was to `a36309e460e2`). Handout: `handout.zip` 10 KB. Author: ante.

## Challenge

The target is a CP/M-style DOS `.COM` program: the service accepts input, runs the program inside its own dosbox, then prints the file the program produced (`OUTPUT.TXT`) as base64. That environment holds a `flag.txt`; the objective is to make the program read it and push its contents into the output the service echoes back.

## Analysis

**The bug: two mismatched file-open modes.** `check_input()` opens the input file in text mode, so byte `0x1A` is treated as EOF; `process_input()` opens that same input file in binary mode and reads all of it. The consequence is that input after a `0x1A` is never seen by the checker but still reaches the processing step. In that step, `fscanf("%[^ ]")` loads the string into `char name[17]` located at `[bp-0x12]` without bounding the conversion to the buffer size, so input longer than 17 bytes keeps writing past that region.

**The 16-bit stack layout.** `name` starts at `bp-0x12`, i.e. `bp-18`; the saved instruction pointer (the near return of a `call` in real mode, with BP pushed first) sits at `name+20`, i.e. `[bp+2]`. So the first 20 bytes of the payload are filler and the 2 overwriting IP bytes come right after; in the 16-bit mode of a `.COM`, the value written is only an IP offset inside the program's own code segment.

**The exploit: a 16-bit ROP chain over `int 21h`.** Because control can only jump to offsets inside that same segment, the chain is built from sites already present in the file:

| Syscall | Offset in the program |
|---|---|
| `_open` | `0x1cf3` |
| `_read` | `0x05ed` |
| `_write` | `0x2366` |
| `_exit` | `0x0197` |

The chain uses offset `0xFFE0` in the data segment and handles 5/6 from the saved run. Handle allocation depends on process file-table state. `_exit` finishes the program so the service can return `OUTPUT.TXT`.

**Byte constraint.** The two sites `0x0d97` and `0x0d96` were excluded from the chain because their high byte is `0x0d`, meaning that writing them in the byte order a real IP uses puts a CR byte into the payload; the input handling is CR/LF-sensitive. The four selected offsets (`0x1cf3`, `0x05ed`, `0x2366`, `0x0197`) contain neither a `0x0d` nor a `0x0a` byte.

## Solution

1. Build the input for the `.COM` program: 20 filler bytes up to the saved IP position, then the chain of offsets above, with a `0x1A` placed where it stops `check_input()` but not `process_input()`.
2. Send the payload to the instance; the program runs in the service's dosbox, opens `flag.txt`, reads it into `DGROUP 0xFFE0`, writes that buffer out to `OUTPUT.TXT`, then `_exit`.
3. The service prints the contents of the file the program just produced:

   ```text
   Your OUTPUT.TXT: Rm9ydElEezNvRl8xNV9KVTU3XzRfNXU5OTM1NzFPbl84MjljOTQ4ZTYxfQoA…
   ```

4. Decoding the base64 yields the flag string:

   ```text
   FortID{3oF_15_JU57_4_5u993571On_829c948e61}
   ```

The retained base64 is 60 characters, a multiple of 4, and decodes completely into 45 bytes: the 43-byte flag string, one `0x0A` byte and one trailing `0x00` byte. That `0x00` comes from the service's own output (the buffer written to the file), not from the decoding step. The `…` at the end of the line is the record's truncation marker; it is not part of the base64 alphabet and it sits after enough data to decode the whole flag string.

## Result

```text
FortID{3oF_15_JU57_4_5u993571On_829c948e61}
```

The flag was read directly from the challenge service, through the `Your OUTPUT.TXT:` line it printed (base64 of the remote `flag.txt`). No submission response recorded.

## Reproduce

A TLS client that can talk to port 1337 (nmap-ncat or equivalent) plus a running instance, since the chain only executes inside the service's dosbox:

```text
ncat --ssl end-of-life-ee7d2f4fa278.inst20.ctf.fortid.com 1337
```

The record is insufficient to rebuild a complete payload; this description is not a runnable solver.
