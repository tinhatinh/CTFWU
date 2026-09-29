# RoboCall — Pwn (Hard)

**Flag:** `sun{you_must_be_some_sort_of_nimble_space_navigator}`

## 1. Ruling things out before finding the real bug

The binary is PIE, NX, Partial RELRO, with a full symbol table. Sweeping the whole file:

- not a single `pop reg; ret` (the sequences `5f c3`, `5e c3`, `5a c3` all return 0 results),
- no `system`/`execve` in the PLT,
- every input buffer is bounded to exactly its size.

`raw_readline(buf, len)` reads one byte at a time and stops at `count = len-1`, then writes NUL at
`buf[len-1]`. With `buf = rbp-0x100, len = 0x100` the last byte that can be written is `rbp-0x01`.
The saved RBP sits at `[rbp]`, not at `[rbp-8]`, so it lies exactly 1 byte past the writable region.
Dynamic verification: sending 255 'A' bytes into the last prompt of `payment_info`, the program still
prints the lines that follow, meaning nothing was overwritten.

Conclusion: no overflow, no ROP. So what does "navigate this stack" mean?

## 2. The real bug: a stack slot that is never written

```asm
raw_parse_int(rdi=str, rsi=out):
  14c6:  cmp    al,0x2f          ; ký tự đầu không phải chữ số
  14c8:  jle    14de
  14de:  mov    eax,0x0
  14e3:  jmp    156a             ; return 0  -> KHÔNG ghi *out
```

The early-return branch skips writing `*out`. Every call site passes an uninitialized local variable
(only `main`, `start_position`, `initial_call` assign themselves 0 at the top of the function). And
`cancel_plan` prints that variable:

```asm
2f34:  print "You've entered \""
2f4b:  raw_print_int([rbp-0x204])      ; ô chưa được ghi
2f50:  print "\", are you sure?"
```

Answering with something non-numeric is enough for the program to print 4 bytes of stack garbage as a
signed integer. That is a memory read primitive.

## 3. The flag is scattered across the stack

`place_flag()` runs before the menu:

```asm
18f8:  open("flag.txt", 0)
1938:  read(fd, rbp-0x2060, 0x3c)          ; 60 byte
loop i = 0..12:
  d    = CHUNK_DEPTH[i]                   ; bảng u32 tại 0x4020
  dest = rbp-0x2020 + (0x19dc - d)        ; = rbp - 0x644 - d
  sao chép 4 byte flag[i*4 .. i*4+3] vào dest
```

place_flag uses a 0x2060-byte frame (probing twice with 0x1000), then returns without printing
anything. Measured against main's rbp, the 13 flag fragments sit at:

```
rbp_main - {0xb64,0xbe4,0xc84,0xcd4,0xd04,0xda4,0xdf4,0xe24,0xec4,0xf14,0xf44,0xf64,0xfe4}
```

All of them lie inside the region that the frames of the menu tree reuse later on.

## 4. "Navigating the stack"

Since `rbp_callee = rbp_caller - (frame_size + 16)` and every frame is a multiple of 0x10, the depth
of the leaked slot `rbp_cancel_plan - 0x204` depends only on the menu sequence that was pressed. Frame
table:

```
start_position 0x110  initial_call 0x170  report_outage 0x150
technical_support 0x160  other_inquiries 0x190  cancel_plan 0x430
```

The shortest path to cancel_plan is `1 -> 6 -> 2` (make a call -> other issues -> cancel), which puts
the leak slot at `rbp_main - 0x764`. Each extra level of nesting shifts that slot down by exactly one
frame size. A BFS over the menu graph (`analysis/paths.py`) finds the walks that touch all 13 offsets;
the results are encoded in `EDGES`/`plan()` of `solve.py`.

Two pragmatic example paths:

| fragment | choice sequence |
|---|---|
| 0 (`sun{`) | `1 6 2` |
| 12 (`tor}`) | `1 6 2` then cancel_plan calling itself twice more (cancellation reason = 4) |

The protocol inside a single cancel_plan:

- the first time it calls `login_roleplay` (3 questions), because `start_position` clears the `userData+4` flag;
- q1: answer with something non-numeric -> the slot keeps its old value;
- q2: prints `You've entered "<that cell>"` -> 4 bytes read;
- to nest deeper: q1 = `0`, q2 = `1` (to continue into the reason menu), q3 = `4`
  (fun fact, then a recursive `cancel_plan()`).

Run 13 connections, one walk per connection, and concatenating the 13 x 4 bytes gives the flag.

## 5. Small details that kept the run alive

- Entering `42` at the "Press enter to start." prompt sets `be_annoying = 0`, turning off every
  `nanosleep`, so there is no longer tens of seconds of waiting per `speak_with_an_operator` call.
- The menu tree lies in true dark-pattern fashion: reaching `cancel_plan` means pressing 2 under
  "other inquiries", even though the menu says "press 3 to speak with an operator". Two `call`
  instructions sitting next to each other in the disassembly made me guess the other way around; one
  probing connection settles it.
- There is no `>>>` marker in the `start_position` menu, so synchronization keys off each prompt's own
  signature string (`Press 8 for yes.`, `Please enter the name of your first pet`, ...).
