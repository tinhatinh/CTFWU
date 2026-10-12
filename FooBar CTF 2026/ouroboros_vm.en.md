---
title: "ouroboros_vm"
category: "Reverse"
tags: ["linux-elf", "ptrace", "anti-debug", "custom-vm", "rolling-xor", "feistel"]
solve_date: "2026-10-10T19:57:00+07:00"
language: "en"
points: 450
---

# ouroboros_vm

**Flag:** `foobarctf{vm_tr4c3_sup3rv1s0r_x}`  
**Provided file:** `ouroboros_vm` (Linux x86-64, PIE, stripped ELF)

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `ouroboros_vm` | 14,560 | `800df6ff6c25c9c72c94e095691cb9e09fe9ee887ed81b1702daf58e7df272f0` |

## Challenge

> The serpent devours its own tail. When our analysts tried attaching dynamic debuggers, the process terminated with anti-debugging exceptions. When we fed the executable into symbolic execution solvers, they choked on a multi-process supervisor boundary.
>
> Inside lies a custom register-based architecture whose instruction stream is decrypted on-the-fly and immediately discarded into the void.
>
> Can you trace the supervisor, decode the virtual architecture, reverse the cipher, and extract the flag?

The program accepts a **32-byte flag**. The solution is to reconstruct its VM and reverse its encryption offline, without relying on dynamic debugging or patching the anti-debugging checks.

## 1. ELF reconnaissance

```bash
file ouroboros_vm
sha256sum ouroboros_vm
readelf -Ws ouroboros_vm
objdump -d -M intel ouroboros_vm
strings -a -tx ouroboros_vm
```

The file is a dynamically linked **x86-64 PIE with stripped symbols**. Imported functions include `mmap`, `fork`, `ptrace`, `waitpid`, `raise`, and `munmap`. The strings table exposes:

```text
0x2020 [-] Flag must be exactly 32 bytes.
0x2048 [-] Anti-debugging trap triggered.
0x2070 [+] Access Granted! That is the correct flag.
0x20a0 [-] Access Denied! Invalid key.
```

The function beginning near `0x1130` checks `argc == 2` and `strlen(argv[1]) == 0x20`, then creates a shared `0x22c`-byte memory mapping:

```c
mmap(NULL, 0x22c, PROT_READ | PROT_WRITE,
     MAP_SHARED | MAP_ANONYMOUS, -1, 0);
```

It places the input at `shared + 0x2c`, followed by eight hard-coded 64-bit values starting at `shared + 0x4c`.

## 2. Multi-process supervisor and anti-debugging

The native program forks into two cooperating processes:

- **Child:** calls `ptrace(PTRACE_TRACEME)` and aborts with the anti-debug message if that fails. It raises `SIGSTOP`, then repeatedly executes `ud2` (raising `SIGILL`) while the VM is active.
- **Parent:** coordinates the child using `waitpid` and `ptrace(PTRACE_CONT)`. Upon a `SIGILL` stop (`wait` status checked against `0x047f`), the parent handles **one virtual instruction**.
- After executing that instruction, the parent uses `PTRACE_GETREGS` / `PTRACE_SETREGS` to increment the child's `RIP` by 2, skipping the `ud2` instruction before continuing.

The **parent is the actual VM interpreter**; the child merely supplies a supervised exception-driven execution boundary. This arrangement frustrates ordinary debugging, but all relevant logic can still be recovered statically.

The shared state layout is:

| Offset from `shared` | Purpose |
|---|---|
| `0x00..0x1f` | Eight 32-bit VM registers (`R0..R7`) |
| `0x20` | VM program counter in bytes |
| `0x24` | Equality flag `ZF` |
| `0x28` | Running flag |
| `0x2c..0x4b` | 32-byte input (`guest[0x00..0x1f]`) |
| `0x4c..0x6b` | Eight round keys (`guest[0x20..0x3f]`) |
| `0x6c..0x8b` | Expected 32-byte ciphertext (`guest[0x40..0x5f]`) |
| `0x8c..0xab` | Produced ciphertext (`guest[0x60..0x7f]`) |

Guest memory begins at `shared + 0x2c`; guest addresses are masked with `& 0x1ff`.

## 3. Recovering the encrypted VM bytecode

Code near `0x1320..0x1339` reads **50 encoded 32-bit words** from `.rodata` at file offset `0x2100`. Each word is XOR-decoded using its byte offset `pc`:

```python
import struct
blob = open('ouroboros_vm', 'rb').read()
for pc in range(0, 200, 4):
    enc = struct.unpack_from('<I', blob, 0x2100 + pc)[0]
    instruction = enc ^ ((pc * 0x41c64e6d + 0x3039) & 0xffffffff) ^ 0x5a17f82c
    print(f'{pc//4:02d}: {instruction:08x}')
```

The high byte is the opcode; the remaining bytes encode register operands and an immediate. A dispatch table at `0x20c0` identifies the operations:

| Opcode | Operation | Opcode | Operation |
|---|---|---|---|
| `01` | `MOVI` | `02` | `MOV` |
| `03` | `LOAD8` | `04` | `STORE8` |
| `05` | `ADD` | `06` | `SUB` |
| `07` | `XOR` | `08` | `AND` |
| `09` | `ROL` | `0a` | `CMP` |
| `0b` | `JMP` | `0c` | `JZ` |
| `0d` | `JNZ` | `0e` | `LOAD32` |
| `0f` | `STORE32` | `ff` | Termination (invalid opcode) |

Representative decoded instructions:

```text
PC    Decoded word    Meaning
0x00  01010000       MOVI R1, 0
0x04  02000100       MOV  R0, R1
0x08  09000003       ROL  R0, 3
0x0c  0e020000       LOAD32 R2, guest[R0+0]
0x10  0e030004       LOAD32 R3, guest[R0+4]
0x20  0e050520       LOAD32 R5, guest[R5+0x20]
0x34  07060700       XOR R6, R7
0x3c  05060500       ADD R6, R5
0x60  0d000018       JNZ 0x18
0xc0  01000000       MOVI R0, 0 (failure path)
```

The VM iterates over **four 8-byte blocks**, encrypts each for **eight rounds**, writes the results to `guest[0x60..0x7f]`, and compares the eight resulting 32-bit words with the expected data in `guest[0x40..0x5f]`. It sets `R0 = 1` on full success and `R0 = 0` on failure.

## 4. Identifying and inverting the Feistel network

An input block consists of two little-endian unsigned 32-bit words `(L, R)`. The loop at VM byte offsets `0x18..0x60` computes:

```text
R6 = ROL32(R, 5)
R7 = ROL32(R, 25)
R6 = R6 XOR R7
R5 = key[round] XOR R
R6 = (R6 + R5) mod 2^32
L, R = R, L XOR R6
```

Thus, the round function and forward transformation are:

```text
F(R, K) = ((ROL32(R,5) XOR ROL32(R,25)) + (R XOR K)) mod 2^32
(L_next, R_next) = (R, L XOR F(R, K))
```

Importantly, **a Feistel round is invertible without inverting `F`**:

```text
R_old = L_next
L_old = R_next XOR F(L_next, K)
```

Apply that inverse for each of the eight round keys **in reverse order**.

Eight `movabs rax, imm64` native instructions at `.text` offsets `0x11b2`, `0x11c0`, `0x11ce`, `0x11dc`, `0x11ea`, `0x11f8`, `0x1206`, and `0x1214` contain the complete constant region. Each little-endian `imm64` starts two bytes after its instruction. Concatenating the eight immediates yields **64 bytes**: the first 32 bytes are round keys, and the next 32 bytes are expected ciphertext.

```text
Round keys (u32):
1337beef cafef00d deadc0de feedface
8badf00d 0d15ea5e c001d00d 5ca1ab1e

Expected ciphertext (u32):
cd16f561 ad998fab fa22a0b0 23f0d893
4f273c07 04acb6c9 33847cf1 fc956577
```

## 5. Complete offline solver — solve.py

Save the following as `solve.py` beside the challenge binary. This solver uses only **Python 3 standard-library functions**, reads the original ELF, verifies representative decoded instructions, extracts the keys and ciphertext, and inverts all four blocks. No debugger, `ptrace`, or native execution is required.

```python
#!/usr/bin/env python3
"""Offline static solver for the original ouroboros_vm ELF (Python 3)."""
import struct
import sys
from pathlib import Path

MASK = 0xffffffff

def rol32(x, n):
    n &= 31
    return ((x << n) | (x >> (32 - n))) & MASK if n else x

def round_f(right, key):
    mixed = rol32(right, 5) ^ rol32(right, 25)
    return (mixed + (right ^ key)) & MASK

def solve(path):
    elf = Path(path).read_bytes()

    # Decode the VM instruction stream from .rodata (file offset 0x2100).
    instructions = []
    for pc in range(0, 200, 4):
        encrypted = struct.unpack_from('<I', elf, 0x2100 + pc)[0]
        mask = ((pc * 0x41c64e6d + 0x3039) & MASK) ^ 0x5a17f82c
        instructions.append(encrypted ^ mask)
    assert len(instructions) == 50
    assert instructions[0] == 0x01010000  # MOVI r1, 0
    assert instructions[47] == 0xff000000 # VM termination

    # File offsets of the 8 MOVABS RAX, imm64 operands in .text.
    imm64_offsets = (
        0x11b4, 0x11c2, 0x11d0, 0x11de,
        0x11ec, 0x11fa, 0x1208, 0x1216,
    )
    assert all(elf[o-2:o] == b'\x48\xb8' for o in imm64_offsets)
    constants = b''.join(elf[o:o+8] for o in imm64_offsets)
    keys = struct.unpack('<8I', constants[:32])
    ciphertext = struct.unpack('<8I', constants[32:64])

    plaintext = bytearray()
    for i in range(0, 8, 2):
        left, right = ciphertext[i], ciphertext[i+1]
        for key in reversed(keys):
            # Inverse Feistel: R_old = L_new; L_old = R_new XOR F(L_new, K)
            left, right = right ^ round_f(left, key), left
        plaintext.extend(struct.pack('<II', left, right))

    print('Round keys:', ' '.join(f'{k:08x}' for k in keys))
    print('Ciphertext:', ' '.join(f'{c:08x}' for c in ciphertext))
    print('Flag:', plaintext.decode('ascii'))

if __name__ == '__main__':
    solve(sys.argv[1] if len(sys.argv) > 1 else 'ouroboros_vm')
```

Execute:

```bash
python3 solve.py ouroboros_vm
```

Observed output:

```text
Round keys: 1337beef cafef00d deadc0de feedface 8badf00d 0d15ea5e c001d00d 5ca1ab1e
Ciphertext: cd16f561 ad998fab fa22a0b0 23f0d893 4f273c07 04acb6c9 33847cf1 fc956577
Flag: foobarctf{vm_tr4c3_sup3rv1s0r_x}
```

## 6. Verification against the original binary

On a Linux system where a parent process can trace its own child:

```bash
chmod +x ouroboros_vm
./ouroboros_vm 'foobarctf{vm_tr4c3_sup3rv1s0r_x}'
```

Verified output:

```text
[+] Access Granted! That is the correct flag.
```

Exit status: `0`.

## Conclusion

The `fork`/`ptrace`/`SIGILL` protection only hides the VM's control flow from ordinary dynamic debuggers. By statically decoding its 50 instructions, locating the eight embedded round keys and 32-byte ciphertext, and reversing an eight-round Feistel network over four blocks, we recover a flag accepted by the original executable:

```text
foobarctf{vm_tr4c3_sup3rv1s0r_x}
```
