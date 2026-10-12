---
title: "Oatmeal"
category: "Mobile"
tags: ["Reverse", "android", "vm"]
solve_date: "2026-10-11T09:25:00+07:00"
language: "vi"
---

# Oatmeal

**Flag:** `isfcr{5958fbb07efd243b}`
**Artifact:** `silvergate.apk` (12,921 bytes), `base.odex` (6,355 bytes)

| Artifact | SHA-256 |
|---|---|
| `silvergate.apk` | `704eaa66777b99a627f571a1be10446b61f40d855cbf3b48e69bb0ef4b568572` |
| `base.odex` | `3c10c7bcffee3f0487fad24c876d976cb07fcf739beb8b9d856628046a98b9c8` |

## Đề bài

Khôi phục unlock material và flag của SilverGate từ APK cùng `base.odex` lấy trong device image.

## Phân tích

APK có SHA-256 checker và hàm deriveFlag XOR từng ký tự với 0x55. Notes ghi staging v1.3.2 và một thay đổi format chưa triển khai ở v1.4.

ODEX có magic OAT nhưng dùng layout tùy biến. Nó chứa ba bảng A/B/C dài 24 byte, SHA constant, format `isfcr{%016llx}`, VM legacy tại 0x4b0, checker v2 tại 0x7e0 và finalizeFlag tại 0x820. VM legacy giữ input có thể khôi phục; SHA constant của passphrase đã rotate không đủ để đảo hash.

| Offset | Content |
|---|---|
| `0x180` / `0x198` / `0x1b0` | three 24-byte tables `A`, `B`, `C` |
| `0x1c8` | 32-byte SHA-256 constant, identical to the APK's `EXPECTED` |
| `0x1e8` | format string `isfcr{%016llx}` |
| `0x220`, `0x246` | two literal decoy flags (see below) |
| `0x290`..`0x4a2` | 530 bytes of custom bytecode (265 two-byte instructions) |
| `0x4b0` | `checkFlag_v1_LEGACY` - a bytecode-interpreting VM |
| `0x7e0` | `checkFlag_v2` - 32-byte `memcmp` against `0x1c8` |
| `0x820` | `finalizeFlag` - 24-byte FNV-1a-64 hash, then a final XOR |

## Các hướng đã kiểm tra

Hai flag literal là decoy và không phù hợp format 16 hex. Hàm deriveFlag của APK cho format khác với staging ODEX. Vùng DEX cuối có header không hợp lệ và không cung cấp lời giải. Những vocabulary candidate được thử không khớp SHA constant.

## Lời giải

1. Khôi phục ISA 2-byte trên tám register: load input/table/immediate, cộng modulo 256, XOR, rotate, compare và accept. A/B/C bị mask theo index, 0xa7 và 0x5c. Bytecode gồm 24 block, mỗi block xác định một input byte ở index xáo trộn.
2. Nghịch phép toán của từng block, bỏ sequence dead code `r7=imm; r6=imm; r7^=r6`. Thu passphrase 24 byte `art_image_took_the_cake!`; forward simulation tới accept opcode.
3. finalizeFlag chạy FNV-1a 64-bit trên 24 byte với offset basis `0xcbf29ce484222325`, prime `0x100000001b3`, rồi XOR `0xa55a96693c3cd2ad`. Kết quả `0x5958fbb07efd243b` được định dạng theo string trong ODEX.

   ```
   v = ROTL8( (input[idx] + (A[idx] ^ maskA(idx))) ^ (B[idx] ^ maskB(idx)) , rot)
   accept iff v == (C[idx] ^ maskC(idx))
   ```

## Kết quả

Flag được tính từ hai artifact và kiểm tra qua VM local.

`isfcr{5958fbb07efd243b}`

## Tái hiện

Đặt APK và ODEX trong working directory. Python block dưới đây thực hiện recovery; jadx và Capstone phục vụ phân tích. Các output giúp đối chiếu passphrase, VM acceptance và giá trị finalizeFlag.

```python
d = open("base.odex", "rb").read()
A, B, C = d[0x180:0x198], d[0x198:0x1b0], d[0x1b0:0x1c8]
bc = d[0x290:0x290 + 0x212]

def rol(v, n): n &= 7; return ((v << n) | (v >> (8 - n))) & 0xFF
def ror(v, n): n &= 7; return ((v >> n) | (v << (8 - n))) & 0xFF
mA = lambda i: ((i * 0xA7) ^ 0x5C) & 0xFF
mB = lambda i: (((i + 24) * 0xA7) ^ 0x5C) & 0xFF
mC = lambda i: (((i + 48) * 0xA7) ^ 0x5C) & 0xFF

# invert the 24 per-byte blocks
pw = [0] * 24
for k in range(24):
    b = bc[k * 22 : k * 22 + 22]
    idx, rot = b[7], b[17]
    v = ror((C[idx] ^ mC(idx)) & 0xFF, rot) ^ ((B[idx] ^ mB(idx)) & 0xFF)
    pw[idx] = (v - ((A[idx] ^ mA(idx)) & 0xFF)) & 0xFF
passphrase = bytes(pw)

# forward-simulate checkFlag_v1 over the real bytecode to confirm acceptance
R, ip, ok = [0] * 8, 0, False
while ip < len(bc):
    op, dst, arg = bc[ip] >> 4, bc[ip] & 0xF, bc[ip + 1]
    ip += 2
    if   op == 1:  R[dst] = passphrase[arg]
    elif op == 2:  R[dst] = (A[arg] ^ mA(arg)) & 0xFF
    elif op == 3:  R[dst] = (B[arg] ^ mB(arg)) & 0xFF
    elif op == 4:  R[dst] = (C[arg] ^ mC(arg)) & 0xFF
    elif op == 5:  R[dst] = arg
    elif op == 6:  R[dst] = (R[dst] + R[arg & 7]) & 0xFF
    elif op == 7:  R[dst] = (R[dst] ^ R[arg & 7]) & 0xFF
    elif op == 8:  R[dst] = rol(R[dst], arg & 7)
    elif op == 9:
        if R[dst] != R[arg & 7]:
            break
    elif op == 10:
        ok = True
        break

# finalizeFlag: FNV-1a-64 over 24 bytes, XOR post-mix constant
x = 0xCBF29CE484222325
for c in passphrase:
    x = (x ^ c) * 0x100000001B3 & (2**64 - 1)
x ^= 0xA55A96693C3CD2AD

print("passphrase :", passphrase.decode())
print("VM accepts :", ok)
print("FLAG isfcr{%016x}" % x)
```

```text
passphrase : art_image_took_the_cake!
VM accepts : True
FLAG isfcr{5958fbb07efd243b}
```

### Chuỗi đối chứng trong artifact

`isfcr{dev_overlay_do_not_submit_18ca3b}`
