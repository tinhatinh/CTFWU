---
title: "Kelpie"
category: "Reverse"
tags: ["bytecode", "vm"]
solve_date: "2026-10-11T05:55:00+07:00"
language: "vi"
---

# Kelpie

**Flag:** `isfcr{5b2d4c7961307f588d9dd95bada5647b}`
**File:** `kelpie` (19,456 bytes; SHA-256 `7fbcd8688ace4d264c62a69c8aa74503ecc57559d6181afd53584a52116213b9`)

## Đề bài

Binary Kelpie kiểm tra activation key dạng `isfcr{<32 hex>}` bằng byte-machine tùy biến. Mục tiêu là khôi phục input làm firmware unlock routine chấp nhận.

## Phân tích

ELF x86-64 stripped, non-PIE, dùng libc và libcrypto. Interpreter xử lý instruction `[op,A,B]` trên state 16 byte: XOR, cộng/trừ, multiply modulo 256, rotate, S-box, permutation và compare.

Stage 1 có 411 instruction, năm round, không có compare; các phép toán đều đảo được. Nó đóng vai trò block transform E. `selftest` công bố E của vector 00…0f. Khi bị ptrace, state byte 0 bị XOR 0x5a, nên kiểm tra cuối cần chạy process không bị trace.

Firmware gồm 924 byte được AES-GCM khóa bằng HMAC-SHA256 của state sau stage 1. Bản nguồn sử dụng AES key lấy từ nguồn ngoài binary; không mô tả bước tự suy ra key ban đầu. Đây là điều kiện cần của phần tái hiện dưới đây.

| Address | Role |
|---|---|
| `0x401170` | `main` |
| `0x4015e0` | byte-machine interpreter |
| `0x402020` | interpreter jump table (114 x 8-byte absolute pointers) |
| `0x4023c0` | stage-1 program, length `0x4d1` = 1233 bytes |
| `0x4028a0` | `VLT0` record: key(16) `@0x4028a4`, IV(12) `@0x4028b4`, tag(16) `@0x4028c0`, u32 ct_len `@0x4028d0`, ciphertext(924) `@0x4028d4` |
| `0x402c80` | four 16-byte permutation tables (two forward + their exact inverses) |
| `0x402cc0` / `0x402dc0` | AES inverse S-box / AES forward S-box |

| Op | Effect | Op | Effect |
|---|---|---|---|
| `0x00` | halt, return error accumulator | `0x30` / `0x31` | `rotl`/`rotr` state[A] by `B & 7` |
| `0x10`/`0x11`/`0x12` | `A ^= B` / `+= B` / `-= B` (register) | `0x40` / `0x41` | state[A] = AES S-box / inverse S-box |
| `0x13` | swap state[A], state[B] | `0x50` / `0x51` | whole-block gather-permute with table `@0x402ca0 + A*16` / `@0x402c80 + A*16` |
| `0x20`/`0x21`/`0x22`/`0x23` | imm: `^= B` / `+= B` / `-= B` / `*= B` | `0x60` | `state[A] ^= rotl(state[B],3)` |
| | | `0x71` | `err \|= (state[A] != B)` |

```
S  = E(parsed 16 bytes)                    # stage 1, in place
K  = HMAC-SHA256(key = 0x4028a4, msg = S)  # 32 bytes -> AES-256-GCM key
   AES-256-GCM decrypt 924 B @0x4028d4, IV @0x4028b4, tag @0x4028c0
   EVP_DecryptFinal_ex must return 1, then
   interpreter runs again with program = decrypted 924 B, data = S, err must be 0
   -> "Unlocked. Activation accepted."
```

## Lời giải

1. Mô phỏng interpreter và đối chiếu self-test `E(000102...0f)=d3e4dd75211d03215a37de7164eb510a`.
2. Với AES key được cung cấp ngoài binary trong lời giải nguồn, decrypt và verify firmware. Routine có 308 instruction, gồm ba round biến đổi và 16 compare cuối.
3. Lấy vector đích của compare `4c9a3fe619eab4efa7efd87a5c49e4d8`. Duyệt instruction ngược: S-box dùng inverse; XOR tự nghịch; multiply dùng inverse modulo 256 vì multiplier lẻ; rotate đổi chiều; cộng đổi thành trừ; permutation dùng inverse table.
4. Thu state `b0dd9edc83f370dad4f5399447579076`. Chạy routine forward cho err=0; HMAC của state tái tạo đúng key xác thực GCM.
5. Nghịch stage 1 từ state này để lấy 16 byte input `5b2d4c7961307f588d9dd95bada5647b`.
6. Gửi flag vào binary không trace. Binary in `Unlocked. Activation accepted.`; đổi một hex digit trả `Denied.`.

   ```
   4c 9a 3f e6 19 ea b4 ef a7 ef d8 7a 5c 49 e4 d8
   ```

   ```
   S = b0dd9edc83f370dad4f5399447579076
   ```

   ```
   E^-1(S) = 5b2d4c7961307f588d9dd95bada5647b
   ```

## Kết quả

Binary xác nhận activation input tại local.

`isfcr{5b2d4c7961307f588d9dd95bada5647b}`

## Tái hiện

Chạy self-test để kiểm tra mô hình interpreter. Các tham số key, IV, tag và offset được giữ trong bảng. Phần reverse cần firmware đã decrypt: nghịc ba round để lấy S, kiểm tra HMAC, rồi nghịch stage 1. Lệnh dưới đây kiểm tra input cuối; chúng không tự giải bài từ đầu khi chưa có key ngoài binary.

```bash
chmod +x kelpie && ./kelpie selftest
# d3e4dd75211d03215a37de7164eb510a
```

```bash
printf 'isfcr{5b2d4c7961307f588d9dd95bada5647b}\n' | ./kelpie
# KELPIE firmware unlock console
# enter activation key: Unlocked. Activation accepted.
```

### Chuỗi đối chứng trong artifact

`isfcr{",6)`, then 16 hex pairs are parsed from `buf[6..37]` (digits, `a-f`, `A-F`) into a 16-byte state, and `buf[38]` must be `}`
