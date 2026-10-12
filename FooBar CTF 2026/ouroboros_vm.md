---
title: "ouroboros_vm"
category: "Reverse"
tags: ["linux-elf", "ptrace", "anti-debug", "custom-vm", "rolling-xor", "feistel"]
solve_date: "2026-10-10T19:57:00+07:00"
language: "vi"
points: 450
---

# ouroboros_vm

**Flag:** `foobarctf{vm_tr4c3_sup3rv1s0r_x}`  
**Tệp cung cấp:** `ouroboros_vm` (Linux x86-64 ELF, PIE, stripped)

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `ouroboros_vm` | 14,560 | `800df6ff6c25c9c72c94e095691cb9e09fe9ee887ed81b1702daf58e7df272f0` |

## Đề bài

> The serpent devours its own tail. When our analysts tried attaching dynamic debuggers, the process terminated with anti-debugging exceptions. When we fed the executable into symbolic execution solvers, they choked on a multi-process supervisor boundary.
>
> Inside lies a custom register-based architecture whose instruction stream is decrypted on-the-fly and immediately discarded into the void.
>
> Can you trace the supervisor, decode the virtual architecture, reverse the cipher, and extract the flag?

Chương trình yêu cầu một flag dài **chính xác 32 byte**. Mục tiêu là khôi phục dữ liệu mà VM dùng để xác thực, không cần bypass `ptrace` hay debug động.

## 1. Khảo sát ELF

```bash
file ouroboros_vm
sha256sum ouroboros_vm
readelf -Ws ouroboros_vm
objdump -d -M intel ouroboros_vm
strings -a -tx ouroboros_vm
```

ELF là chương trình **x86-64 PIE, đã strip**, liên kết động với libc. Các import quan trọng là `mmap`, `fork`, `ptrace`, `waitpid`, `raise`, `munmap`. Các chuỗi đáng chú ý:

```text
0x2020 [-] Flag must be exactly 32 bytes.
0x2048 [-] Anti-debugging trap triggered.
0x2070 [+] Access Granted! That is the correct flag.
0x20a0 [-] Access Denied! Invalid key.
```

Ở `0x1130`, chương trình kiểm tra `argc == 2` và `strlen(argv[1]) == 0x20`. Nó tạo vùng nhớ dùng chung dài `0x22c` byte:

```c
mmap(NULL, 0x22c, PROT_READ | PROT_WRITE,
     MAP_SHARED | MAP_ANONYMOUS, -1, 0);
```

Flag được copy vào vùng `shared + 0x2c` (32 byte). Tiếp đó tám hằng 64-bit được ghi liên tiếp vào `shared + 0x4c` đến `shared + 0x8b`.

## 2. Anti-debugging và supervisor

Sau khi `fork()`:

- **Child:** gọi `ptrace(PTRACE_TRACEME)`; nếu thất bại, in `Anti-debugging trap triggered`. Child phát `raise(SIGSTOP)` rồi lặp với instruction `ud2` (gây `SIGILL`) khi trạng thái VM vẫn đang chạy.
- **Parent:** dùng `waitpid()` đợi các lần child dừng, `ptrace(PTRACE_CONT)` để chạy tiếp. Khi trạng thái stop tương ứng `SIGILL` (kiểm tra `0x047f`), parent đọc và thực thi **một lệnh VM**.
- Sau mỗi bước, parent dùng `PTRACE_GETREGS` / `PTRACE_SETREGS` để tăng `RIP` của child thêm 2 byte, bỏ qua `ud2`, rồi tiếp tục. Hai tiến trình trao đổi thanh ghi VM và trạng thái qua mapping `MAP_SHARED`.

Như vậy native child không trực tiếp thực thi bytecode: **supervisor ở parent là interpreter thật**. Vì toàn bộ logic giải mã và dispatch nằm trong ELF, phân tích tĩnh giúp bỏ qua rào cản `ptrace`.

Vùng shared có bố cục chính:

| Offset từ `shared` | Nội dung |
|---|---|
| `0x00..0x1f` | 8 thanh ghi VM, mỗi thanh ghi 32-bit (`R0..R7`) |
| `0x20` | VM program counter (`PC`, tính bằng byte) |
| `0x24` | Cờ so sánh `ZF` |
| `0x28` | Cờ VM đang chạy |
| `0x2c..0x4b` | Input dài 32 byte (`guest[0x00..0x1f]`) |
| `0x4c..0x6b` | 8 round key (`guest[0x20..0x3f]`) |
| `0x6c..0x8b` | 32 byte ciphertext chuẩn (`guest[0x40..0x5f]`) |
| `0x8c..0xab` | 32 byte ciphertext do VM tạo (`guest[0x60..0x7f]`) |

Bộ nhớ guest bắt đầu tại `shared + 0x2c`, và địa chỉ được mask `& 0x1ff`.

## 3. Giải mã instruction VM

Tại `0x1320..0x1339`, mỗi lệnh mã hóa dài **4 byte** được giải XOR theo vị trí, lấy từ `.rodata` ở file offset `0x2100` (200 byte, **50 instruction**):

```python
import struct
blob = open('ouroboros_vm', 'rb').read()
for pc in range(0, 200, 4):
    enc = struct.unpack_from('<I', blob, 0x2100 + pc)[0]
    instruction = enc ^ ((pc * 0x41c64e6d + 0x3039) & 0xffffffff) ^ 0x5a17f82c
    print(f'{pc//4:02d}: {instruction:08x}')
```

Từ `0x133f`, word plaintext được tách thành **opcode** (byte cao), các trường thanh ghi và immediate. Jump table ở `0x20c0` dẫn đến các handler:

| Opcode | Nghĩa | Opcode | Nghĩa |
|---|---|---|---|
| `01` | `MOVI` | `02` | `MOV` |
| `03` | `LOAD8` | `04` | `STORE8` |
| `05` | `ADD` | `06` | `SUB` |
| `07` | `XOR` | `08` | `AND` |
| `09` | `ROL` | `0a` | `CMP` |
| `0b` | `JMP` | `0c` | `JZ` |
| `0d` | `JNZ` | `0e` | `LOAD32` |
| `0f` | `STORE32` | `ff` | Kết thúc (ngoài opcode hợp lệ) |

Ví dụ các word thực sự giải được:

```text
PC    Encoded-decoded word     Ý nghĩa
0x00  01010000                 MOVI R1, 0
0x04  02000100                 MOV  R0, R1
0x08  09000003                 ROL  R0, 3
0x0c  0e020000                 LOAD32 R2, guest[R0+0]
0x10  0e030004                 LOAD32 R3, guest[R0+4]
0x20  0e050520                 LOAD32 R5, guest[R5+0x20]
0x34  07060700                 XOR R6, R7
0x3c  05060500                 ADD R6, R5
0x60  0d000018                 JNZ 0x18
0xc0  01000000                 MOVI R0, 0 (nhánh thất bại)
```

Bytecode dùng các vòng lặp để biến đổi **4 block, mỗi block 8 byte**, mỗi block được mã hóa **8 round**, ghi output tại `guest[0x60..0x7f]`, rồi đối chiếu với `guest[0x40..0x5f]`. Khớp hết thì đặt `R0 = 1`, ngược lại đặt `R0 = 0`.

## 4. Khôi phục Feistel cipher

Xét một block gồm `L, R` là hai số unsigned 32-bit little-endian. Vòng mã hóa nằm ở các instruction từ `0x18` đến `0x60`:

```text
R6 = ROL32(R, 5)
R7 = ROL32(R, 25)
R6 = R6 XOR R7
R5 = key[round] XOR R
R6 = (R6 + R5) mod 2^32
L, R = R, L XOR R6
```

Suy ra hàm round và Feistel:

```text
F(R, K) = ( (ROL32(R,5) XOR ROL32(R,25)) + (R XOR K) ) mod 2^32
(L_next, R_next) = (R, L XOR F(R, K))
```

Feistel **luôn đảo được mà không cần đảo hàm F**:

```text
R_old = L_next
L_old = R_next XOR F(L_next, K)
```

Chỉ cần lấy 8 key theo đúng thứ tự, rồi chạy inverse round theo thứ tự **key đảo ngược** là có plaintext.

Tám hằng `movabs rax, imm64` tại `.text` được đặt ở `0x11b2`, `0x11c0`, `0x11ce`, `0x11dc`, `0x11ea`, `0x11f8`, `0x1206`, `0x1214`. Các immediate dài 8 byte bắt đầu tại `+2`, ghép lại được **64 byte**; 32 byte đầu là key, 32 byte sau là ciphertext. Phải đọc **little-endian**:

```text
Round keys (u32):
1337beef cafef00d deadc0de feedface
8badf00d 0d15ea5e c001d00d 5ca1ab1e

Expected ciphertext (u32):
cd16f561 ad998fab fa22a0b0 23f0d893
4f273c07 04acb6c9 33847cf1 fc956577
```

## 5. Lời giải hoàn chỉnh — solve.py

Lưu code dưới đây thành `solve.py`, đặt cùng thư mục với file gốc. Script chỉ đọc bytes ELF: **không attach debugger, không cần quyền `ptrace`, không phụ thuộc thư viện ngoài Python 3**.

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

Chạy:

```bash
python3 solve.py ouroboros_vm
```

Output thực tế:

```text
Round keys: 1337beef cafef00d deadc0de feedface 8badf00d 0d15ea5e c001d00d 5ca1ab1e
Ciphertext: cd16f561 ad998fab fa22a0b0 23f0d893 4f273c07 04acb6c9 33847cf1 fc956577
Flag: foobarctf{vm_tr4c3_sup3rv1s0r_x}
```

## 6. Kiểm chứng trực tiếp với binary

Trên Linux cho phép parent trace child của chính nó:

```bash
chmod +x ouroboros_vm
./ouroboros_vm 'foobarctf{vm_tr4c3_sup3rv1s0r_x}'
```

Kết quả đã kiểm tra:

```text
[+] Access Granted! That is the correct flag.
```

Exit code: `0`.

## Kết luận

Phân tích tĩnh đủ để khôi phục phép kiểm tra: phục hồi interpreter ở parent, giải XOR instruction stream tĩnh, xác định phép Feistel 8 vòng, lấy key và ciphertext từ immediate của native code, rồi giải ngược từng block. Binary chấp nhận flag đã khôi phục:

```text
foobarctf{vm_tr4c3_sup3rv1s0r_x}
```
