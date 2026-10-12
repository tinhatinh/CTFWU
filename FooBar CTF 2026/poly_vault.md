---
title: "poly_vault"
category: "Reverse"
tags: ["linux-elf", "sigusr1", "signal-trampoline", "sbox", "matrix", "xor", "permutation"]
solve_date: "2026-10-10T19:56:00+07:00"
language: "vi"
points: 250
---

# poly_vault

**Flag:** `foobarctf{s1gn4l_m4tr1x_v4ult_x}`  
**Artifact:** `poly_vault` — Linux x86_64 ELF, stripped, non-PIE, 14.600 bytes.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `poly_vault` | 14,600 | `838d664d9a32550fe3f19d6196ed7bbb7f0da9457ca51aa446cf0bf5f7dbc7a6` |

## Đề bài

Một binary kiểm tra khóa bảo vệ vault được dùng signal để chuyển hướng luồng thực thi. Thay vì gọi những hàm biến đổi theo cách thông thường, chương trình chuyển hướng qua signal trap, khiến call graph trong decompiler bị rời rạc. Mục tiêu là vượt qua signal trampoline, đảo ngược các lớp biến đổi và khôi phục passphrase theo dạng `foobarctf{...}`.

## Khảo sát ban đầu

```bash
file poly_vault
sha256sum poly_vault
readelf -h -S poly_vault
objdump -d -M intel poly_vault
objdump -s -j .rodata poly_vault
```

ELF là executable x86_64 đã bị strip, loại `EXEC` (địa chỉ cố định, không phải PIE). Chương trình nhận đúng **một tham số dài 32 byte**, nếu sai độ dài sẽ in `[-] Key must be exactly 32 bytes.`. Các chuỗi thành công/thất bại nằm ở `.rodata`:

```text
[+] Access Granted! Flag verified.
[-] Access Denied! Invalid key.
[-] Key must be exactly 32 bytes.
Usage: %s <flag_key>
```

Những chuỗi này không chứa flag. Cần đảo hàm kiểm tra thay vì tìm string đơn thuần.

## Phân tích signal trampoline

Trong đoạn xử lý tham số ở `0x4010e0`, chương trình:

1. Kiểm tra `strlen(argv[1]) == 0x20` rồi chép 32 byte vào buffer tại `0x404080`.
2. Đăng ký `sigaction(SIGUSR1, ..., SA_SIGINFO)` với handler tại `0x4012e0`.
3. Gọi `raise(10)` để bắt đầu chuỗi xử lý.

Điểm quan trọng là handler **không gọi** từng stage bằng `call`. Nó ghi đè instruction pointer trong `ucontext_t` (trên Linux x86_64, saved RIP ở offset `0xa8`) để lúc thoát khỏi signal, chương trình tiếp tục tại một địa chỉ do handler chọn:

```c
// Pseudocode của handler ở 0x4012e0
void signal_handler(int sig, siginfo_t *info, void *ctx) {
    if (round < 4) {
        saved_RIP(ctx) = stage_table[stage];
        if (++stage == 4) { stage = 0; round++; }
    } else {
        saved_RIP(ctx) = 0x4014a0; // final comparison
    }
}
```

Bảng 4 con trỏ tại `0x403dc0` là:

| Stage | Address | Chức năng |
|---|---|---|
| 0 | `0x401340` | Thay thế từng byte bằng S-box |
| 1 | `0x401380` | Nhân ma trận 4×4 trên từng block 4 byte (mod 256) |
| 2 | `0x401400` | XOR với khóa của vòng hiện tại |
| 3 | `0x401450` | Hoán vị 32 byte |

Mỗi stage kết thúc bằng `raise(SIGUSR1)`, để handler chuyển sang stage tiếp theo. Tổng cộng có **4 vòng × 4 stage = 16 phép biến đổi**; sau đó nhảy tới verifier `0x4014a0`. Các transition này không thể hiện dưới dạng call thông thường trong call graph.

## Dữ liệu và công thức biến đổi

Các constant đều nằm trong `.rodata`, đọc trực tiếp từ ELF. Với binary non-PIE này, địa chỉ `.rodata` trừ `0x400000` chính là file offset.

| Virtual address | File offset | Size | Purpose |
|---|---:|---:|---|
| `0x4020a0` | `0x20a0` | 16 | 4×4 matrix, row-major |
| `0x4020c0` | `0x20c0` | 32 | Byte permutation, `out[p[i]] = in[i]` |
| `0x4020e0` | `0x20e0` | 32 | Expected transformed bytes |
| `0x402100` | `0x2100` | 128 | Four round-dependent XOR keys, 32 bytes each |
| `0x402180` | `0x2180` | 256 | Substitution table / S-box |

Ma trận từ `0x4020a0` là:

```text
M = [ [1, 9, 4, 9],
      [7, 4, 8, 5],
      [1, 3, 7, 6],
      [5, 3, 4, 6] ]
```

Cho trạng thái 32 byte `x`, mỗi vòng `r ∈ {0,1,2,3}` gồm:

```text
1. x[i] = S[x[i]]                                  (S-box)
2. x[4b:4b+4] = M * x[4b:4b+4] mod 256             (8 block)
3. x[i] ^= K[r*32 + i]                             (XOR khóa vòng)
4. out[P[i]] = x[i]                                (permutation)
   x = out
```

Verifier tại `0x4014a0` so sánh 32 byte kết quả với target ở `0x4020e0` (các so sánh 64-bit bằng XOR/OR). Khi giống hoàn toàn, chương trình in `Access Granted`.

## Đảo ngược để lấy key

Các bước đều khả nghịch:

- S-box chứa đủ 256 giá trị khác nhau ⇒ lập bảng `S_inv[S[x]] = x`.
- Phép XOR tự nghịch đảo.
- Hoán vị là song ánh ⇒ nếu chiều thuận `out[P[i]] = in[i]` thì chiều ngược `in[i] = out[P[i]]`.
- Ma trận có `det(M) = -981 ≡ 43 (mod 256)`; vì `gcd(43, 256) = 1`, có thể tính `M⁻¹` trên vành `Z/256Z`.

Bắt đầu từ **target** và xử lý các vòng `3, 2, 1, 0`. Trong mỗi vòng, thực hiện nghịch đảo theo thứ tự **permutation → XOR → matrix → S-box**. Toàn bộ phép toán ma trận phải lấy modulo 256, không phải modulo một số nguyên tố bất kỳ.

### Solver (Python 3, không cần thư viện ngoài)

Lưu đoạn sau thành `solve_poly_vault.py`:

```python
#!/usr/bin/env python3
"""Offline solver for poly_vault (Linux x86_64, non-PIE ELF)."""
from pathlib import Path
import sys

MOD = 256
N = 32


def invert_matrix_mod256(matrix):
    """Gauss-Jordan elimination over Z/256Z (requires odd pivots)."""
    a = [row[:] + [int(i == j) for j in range(4)]
         for i, row in enumerate(matrix)]
    for col in range(4):
        pivot = next((row for row in range(col, 4) if a[row][col] % 2), None)
        if pivot is None:
            raise ValueError("Matrix is not invertible modulo 256")
        a[col], a[pivot] = a[pivot], a[col]
        scale = pow(a[col][col], -1, MOD)
        a[col] = [(v * scale) % MOD for v in a[col]]
        for row in range(4):
            if row != col:
                factor = a[row][col]
                a[row] = [(x - factor * y) % MOD
                          for x, y in zip(a[row], a[col])]
    return [row[4:] for row in a]


def mul_blocks(data, matrix):
    out = []
    for pos in range(0, N, 4):
        block = data[pos:pos + 4]
        out.extend(sum(matrix[i][j] * block[j] for j in range(4)) % MOD
                   for i in range(4))
    return out


def solve(path):
    blob = Path(path).read_bytes()
    # For this non-PIE ELF, the .rodata VA 0x402000 maps to file offset 0x2000.
    matrix_data = blob[0x20A0:0x20B0]
    matrix = [list(matrix_data[i:i+4]) for i in range(0, 16, 4)]
    permutation = list(blob[0x20C0:0x20E0])
    goal = list(blob[0x20E0:0x2100])
    keys = blob[0x2100:0x2180]
    sbox = list(blob[0x2180:0x2280])
    assert len(matrix_data) == 16 and len(goal) == N and len(keys) == 128
    assert sorted(permutation) == list(range(N))
    assert sorted(sbox) == list(range(MOD))

    inv_sbox = [0] * MOD
    for x, y in enumerate(sbox):
        inv_sbox[y] = x
    inv_matrix = invert_matrix_mod256(matrix)

    state = goal
    for round_index in range(3, -1, -1):
        # Forward permutation: out[permutation[i]] = in[i].
        state = [state[permutation[i]] for i in range(N)]
        # XOR is its own inverse.
        state = [value ^ keys[round_index * N + i]
                 for i, value in enumerate(state)]
        # Undo 4x4 matrix on eight 4-byte blocks.
        state = mul_blocks(state, inv_matrix)
        # Undo the substitution table.
        state = [inv_sbox[value] for value in state]

    candidate = bytes(state).decode('ascii')
    assert len(candidate) == N

    # Independent verification: re-encrypt recovered input using forward layers.
    check = list(candidate.encode('ascii'))
    for round_index in range(4):
        check = [sbox[v] for v in check]
        check = mul_blocks(check, matrix)
        check = [value ^ keys[round_index * N + i]
                 for i, value in enumerate(check)]
        permuted = [0] * N
        for i, value in enumerate(check):
            permuted[permutation[i]] = value
        check = permuted
    assert check == goal, "Forward transform does not match stored target"
    print('FLAG:', candidate)
    print('Verification: forward transform matches the 32-byte target')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python3 solve_poly_vault.py <path-to-poly_vault>')
    solve(sys.argv[1])
```

## Tái hiện và xác minh

Đặt `poly_vault` và `solve_poly_vault.py` cùng thư mục rồi chạy:

```bash
python3 solve_poly_vault.py ./poly_vault
chmod +x ./poly_vault
./poly_vault 'foobarctf{s1gn4l_m4tr1x_v4ult_x}'
```

Output thực tế:

```text
FLAG: foobarctf{s1gn4l_m4tr1x_v4ult_x}
Verification: forward transform matches the 32-byte target
[+] Access Granted! Flag verified.
```

Thử đổi byte cuối của key sẽ nhận:

```bash
./poly_vault 'foobarctf{s1gn4l_m4tr1x_v4ult_y}'
# [-] Access Denied! Invalid key.
```

Solver còn thực hiện **forward transform** trên passphrase đã khôi phục và kiểm tra bằng `assert` rằng kết quả bằng đúng target 32 byte trong ELF. Đây là kiểm chứng offline độc lập trước khi chạy lại binary.

## Kết quả

Signal trampoline chỉ che giấu trình tự thực thi, không làm các phép biến đổi một chiều. Sau khi dựng lại thứ tự 4 stage và đảo 4 vòng theo dữ liệu `.rodata`, thu được chính xác passphrase:

```text
foobarctf{s1gn4l_m4tr1x_v4ult_x}
```
