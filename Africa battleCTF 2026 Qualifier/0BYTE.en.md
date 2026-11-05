---
title: "0byte"
category: "RE"
tags: ["reverse-engineering", "pe-binary", "anti-debug", "downloader", "pext", "pdep", "elf-emulation"]
solve_date: "2026-10-07T09:44:00+07:00"
language: "en"
points: 50
---

# 0byte — PE downloader and pext/pdep emulation

**Flag:** `battleCTF{DespairEnergy}` · **Files:** `0byte.exe`, 848 384 byte, sha256 `535436a0403739ae8616755cd67e742fdcb135d0b9df3326ac3f97dc3bb005c4`

## Challenge

A 50-point task in the "out context" group on ctf.bugpwn.com, flag format `battleCTF{....}`. The task
ships a single file: `0byte.zip` (AES-256, password `infected`) containing `0byte.exe`. No other hint
appears on the challenge card.

## Analysis

```text
0byte.exe: PE32+ executable (console) x86-64, for MS Windows
entry 0x4014e0 · .text 0x401000+0xa1cd0 · .data 0x4a3000 · .rdata 0x4a7000
```

Running it in a console draws a snake board and prints the instructions:

```text
######################
# F                  #
#          O         #
######################
Score: 0

Use 'W', 'A', 'S', 'D' to move the snake, 'X' to quit
```

Observations from `.rdata`:

```text
0x4a7060  'Downloader'        0x4a7074  'Failed.'
0x4a707c  'CreateProcess failed: '      0x4a7160  'Banned'
0x4a7157  'kami'               0x4a715c  'ami'
```

The import table only references `KERNEL32`, `msvcrt` and `WININET` (`InternetOpenA`,
`InternetOpenUrlA`, `InternetReadFile`, `InternetCloseHandle`) plus `IsDebuggerPresent`. There is no
registry import. Initial conclusion: a game shell wrapping an **anti-debugged downloader**, and
`'kami'`/`'ami'` are most likely decryption keys rather than display data.

## Approaches tried

1. **Zero-width steganography in the challenge description**: checked `U+200B/200C/200D/FEFF/2060` on the
   raw `/api/v1/challenges/<id>` response — no hidden characters. The hidden data was actually a hex
   string pointing at `github.com/0xbugpwn/AfricabattleCTF2024/.../0byte.zip`, i.e. the artifact source,
   not the solution.
2. **The snake score unlocks the answer**: the score variable at `0x4d0390` only receives `addl $0xa` when
   food is eaten and feeds `printf("Score: ")`. The download branch at `0x4a245e` never reads it; its guard
   is only two non-null string pointers.
3. **Using `plink`/`ssh` against a host from "the PuTTY config"**: the binary does launch `putty.exe`, but
   `CreateProcessA` is called with `lpApplicationName = NULL` and an `lpCommandLine` that is only the path
   of the freshly downloaded `.exe` — no `-load`, no host, no registry. This invocation supplies neither a host nor a saved PuTTY session.
4. **XOR / UTF-16 / length-prefix on the 9 016-byte payload**: that blob is 93% zero bytes with no ASCII
   run longer than 4 characters; every single-byte and repeating-key attempt failed. The real cause was
   misreading the encoding (see Step 3), not undecodable data.

## Solution

**Step 1 - Defeat the anti-debug and capture the real URLs.** `0x4a2330` calls `IsDebuggerPresent` through
IAT slot `0x4d25e8`; if eax is non-zero, the branch at `0x4a249f` prints `Banned` and exits. Break
**after** the call and force eax to zero:

```gdb
break *0x4a2336
commands
  set $eax = 0
  continue
end
break *0x4016d8        # call *InternetOpenUrlA
commands
  x/s $rdx
  continue
end
```

```text
HIT-URL
0x8316b0:     "https://bugpwn.com/drop.ini"
HIT-PATH
0x831700:     "C:\\Users\\ADMINI~1\\AppData\\Local\\Temp\\08914b150cdd6888bf32d668c9336169.ini"
HIT-URL
0x831980:     "https://the.earth.li/~sgtatham/putty/latest/w32/putty.exe"
HIT-PATH
0x835f30:     "C:\\Users\\ADMINI~1\\AppData\\Local\\Temp\\08914b150cdd6888bf32d668c9336169.exe"
```

Filenames are keyed by MD5, and the `putty.exe` here is genuine PuTTY from `the.earth.li` — meaning the
valuable part lives in `drop.ini`.

**Step 2 - Explaining the "0 byte" mechanism.** The four strings (URLs and file paths) do not exist in the
file as plain text. In `.data` at `0x4a3020`, `0x4a30c0`, `0x4a31c0` and a 27-element array on the stack,
each character is stored inside a dword: `1e 00 00 00 0c 00 00 00 13 00 00 00...` — three zero bytes per
data byte,  Two string-building routines:

- `0x401cf0` reads dwords with stride 4: `ebp = movzbl [rsi]; ebp ^= i; ebp -= 5` → `A[i] = ((v[i] ^ i) - 5) & 0xff`.
- `0x401dd0` mixes in a key via modulo: `divq [rsp+0x38]` then `xor (%rax,%rbx,1),%bpl`
  → `out[i] = A[i] ^ key[i % len(key)]`.

The keys come from `.rdata`: `0x402660` assigns `"kami"` to the first array and `"ami"` to the other three.
Verification: the 27-dword array decodes to exactly `https://bugpwn.com/drop.ini`, matching the URL
captured in Step 1.

**Step 3 - `drop.ini` decoding.** The 912-byte string unwraps as base64 → gzip → pickle
(`PROTO 4`, `FRAME`, `BINBYTES8` of length 18 032). The pickle payload is a hex string. Decoding it
forward yields 9 016 meaningless bytes. Look at the **last 8 characters** of the string:

```text
...010102064C454F7
```

`64C454F7` is `7f454c46` reversed — the ELF magic. The hex string is **fully reversed**, so the correct
read is:

```python
elf = bytes.fromhex(hexstr[::-1])
```

which yields a 9 016-byte static ELF64:

```text
Type: EXEC · Machine: x86-64 · entry 0x401000 · 3 program headers · 7 sections
.text 0x401000 size 0x1ec · .data 0x402000 size 0x17 · .bss 0x402018 size 0x18
symtab: flag.asm, mask (0x402000), message (0x402008), msg_len = 0xf, output (0x402018), _start
```

`.data` holds the qword `mask = 0xb0bababa` and the string `Here We Go...!\n`.

**Step 4 - The `pext`/`pdep` machinery and why emulation is required.** `.text` is 492 bytes of
straight-line code with no loop: 16 pairs of `mov ebx, imm32` + `pext rcx, rbx, rax`, each result stored as
one byte into `.bss`, then:

```asm
4011c7: mov eax, 0x1          ; SYS_write
4011d1: movabs rsi, 0x402008  ; message, NOT output
4011db: mov edx, 0xf          ; msg_len = 15
4011e0: syscall
4011e2: mov eax, 0x3c         ; SYS_exit
```

The binary only prints `Here We Go...!\n`; the flag is computed into `0x402018` but **never written out**.
Running the program yields nothing further, The solution emulates the instructions to recover that buffer; inspecting memory with a debugger before exit is another option.

Operand order matters here. In Intel syntax `PEXT dest, src1, src2`, `src1` is the **value** and
`src2` is the **control**. In `pext rcx, rbx, rax`, `rbx` holds the immediate such as `0x890`... and `rax`
holds the `mask` qword. Treating the immediate as the mask produces only unprintable bytes
(`\x0f\x04\x00X[G...`); the correct orientation is `value = imm`, `control = 0xb0bababa`:

```python
def pext(value, control):
    res = j = 0
    for i in range(64):
        if (control >> i) & 1:
            if (value >> i) & 1:
                res |= 1 << j
            j += 1
    return res
```

The remaining transforms are read directly from the machine code: `st8(0x402020, ld64(0x40201f) ^ 0x12)`,
`st8(0x40202f, 0x3b ^ ld64(0x402020))`, `pdep(rdx, 0x62) + 5`, `popcnt(0x1337) + 0x3d` and one constant
byte `0x6e`.

**Step 5 - Run and verify.**

```bash
python exploit.py drop.ini
```

```text
drop.ini        : 912 byte
ELF recovered   : 9016 byte, magic 7f454c46, machine 0x3e, entry 0x401000
.data mask      : 0xb0bababa
.data message   : b'Here We Go...!\n'
output (.bss)    : b'battleCTF{DespairEnergy}'
all printable   : True
flag            : battleCTF{DespairEnergy}
```

Verification checks: the string is exactly 24 bytes, matching the `.bss` size
(`output 0x402018.. _end 0x402030`); 24/24 characters are printable; it begins with `battleCTF{` as the
challenge requires and ends with `}` in the final byte; and everything derives from a single input,
`drop.ini`, with no flag constant hand-written into the script.

## Result

```text
battleCTF{DespairEnergy}
```

Submitted on ctf.bugpwn.com and accepted.

## Reproduce

```bash
cd "0byte"
python exploit.py drop.ini          # base64 -> gzip -> pickle -> hex reversed -> ELF -> emulate
```

To fetch `drop.ini` from the challenge server yourself:

```bash
curl -sSL -o drop.ini https://bugpwn.com/drop.ini
```

To re-capture the runtime URLs and paths (needs gdb, and the binary must reach the downloader branch):

```bash
gdb -batch -nx -x capture.gdb ./0byte.exe
```

`0byte.exe` is a Windows PE binary; the emulation part of `exploit.py` is pure Python, so it runs on any
platform without Windows and without executing the binary.
