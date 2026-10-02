# RoboCall — Pwn (Hard)

**Flag:** `sun{you_must_be_some_sort_of_nimble_space_navigator}`

# RoboCall — Pwn (Hard)

**Flag:** `sun{you_must_be_some_sort_of_nimble_space_navigator}`

## Initial Analysis

The binary is PIE, NX, Partial RELRO, with a full symbol table. It contains no `pop reg; ret` gadgets, no `system`/`execve` in the PLT, and every input buffer restricts the read size accurately.

The function `raw_readline(buf, len)` reads up to `len-1` bytes and writes a `\0` at `buf[len-1]`. With `buf = rbp-0x100, len = 0x100`, the last written byte is `rbp-0x01`. The saved RBP sits at `[rbp]`, which is 1 byte past the writable region, so there is no buffer overflow and no ROP chain opportunity.

## Vulnerability

The vulnerability is an uninitialized stack variable:

```asm
raw_parse_int(rdi=str, rsi=out):
  14c6:  cmp    al,0x2f          ; first char is not a digit
  14c8:  jle    14de
  14de:  mov    eax,0x0
  14e3:  jmp    156a             ; return 0  -> DOES NOT write to *out
```

The early-return branch skips writing to `*out`. Every call site passes an uninitialized local variable. In `cancel_plan`, this variable is printed:

```asm
2f34:  print "You've entered \""
2f4b:  raw_print_int([rbp-0x204])      ; uninitialized slot
2f50:  print "\", are you sure?"
```

Providing non-numeric input causes the program to print 4 bytes of stack data as a signed integer, providing a memory read primitive.

## Exploit Chain

**Step 1 - Flag placement.** The flag is scattered across the stack by `place_flag()` before the menu runs:

```asm
18f8:  open("flag.txt", 0)
1938:  read(fd, rbp-0x2060, 0x3c)          ; 60 byte
loop i = 0..12:
  d    = CHUNK_DEPTH[i]                   ; u32 table at 0x4020
  dest = rbp-0x2020 + (0x19dc - d)        ; = rbp - 0x644 - d
  copy 4 flag bytes flag[i*4 .. i*4+3] to dest
```

The function uses a 0x2060-byte frame, then returns. Relative to main's RBP, the 13 flag fragments sit at:
`rbp_main - {0xb64,0xbe4,0xc84,0xcd4,0xd04,0xda4,0xdf4,0xe24,0xec4,0xf14,0xf44,0xf64,0xfe4}`.
All of them lie inside the stack region that the menu tree frames will reuse.

**Step 2 - Navigating the stack.** Because `rbp_callee = rbp_caller - (frame_size + 16)` and every frame size is a multiple of 0x10, the depth of the leaked slot `rbp_cancel_plan - 0x204` depends strictly on the menu traversal path.

Frame table:
```
start_position 0x110  initial_call 0x170  report_outage 0x150
technical_support 0x160  other_inquiries 0x190  cancel_plan 0x430
```

Each additional menu level shifts the leaked slot deeper by the frame size. A BFS algorithm calculates specific paths to leak all 13 offsets.

Examples:
| fragment | path |
|---|---|
| 0 (`sun{`) | `1 -> 6 -> 2` (call -> other issues -> cancel), leaks at `rbp_main - 0x764` |
| 12 (`tor}`) | `1 -> 6 -> 2` then recursive `cancel_plan` twice (reason = 4) |

**Step 3 - Extraction protocol.** A single `cancel_plan` sequence:
- `start_position` clears the `userData+4` flag, calling `login_roleplay` (3 questions).
- Question 1: input non-numeric text -> the stack slot retains its value.
- Question 2: prints the variable -> leaks 4 flag bytes.
- To nest deeper: Q1=`0`, Q2=`1`, Q3=`4` (recursive call).

By opening 13 separate connections, executing the specific paths, and collecting the leaks, the flag is fully recovered.

Note: Entering `42` at the "Press enter to start." prompt sets `be_annoying = 0`, disabling `nanosleep` delays. To reach `cancel_plan`, select option 2 under "other inquiries" despite the menu text stating "press 3". Menu synchronization is based on distinct prompt text (e.g., `Press 8 for yes.`).
