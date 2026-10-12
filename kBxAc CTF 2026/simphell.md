---
title: "simphell"
category: "Reverse"
tags: ["haskell", "ghc", "elf", "reverse-engineering", "flag-validation"]
solve_date: "2026-10-10"
language: "vi"
---

# simphell

**Flag:** `kBxAc{__y3t_4n0th3r_fl4g_v3ry_3a5y__}`  
**Đề bài:** *Yet another simple challenge.*  
**Tệp:** `chall (1)` (đổi tên thành `chall` khi chạy thử).

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `chall (1)` | 1,012,400 | `0c1f44233e1dde1c7c28718a12040559375c05a060c11b15dcb4583e2c5f97e4` |

## Mục tiêu

Reverse executable `simphell` để tìm đầu vào làm hàm kiểm tra flag trả về thành công. Flag có tiền tố `kBxAc{...}`.

## Khảo sát mẫu

`file` cho thấy đây là executable ELF 64-bit dành cho x86-64, dynamically linked và **stripped**. Chuỗi runtime, đặc biệt là `GHC.Internal.*`, cho thấy chương trình được biên dịch bằng **Glasgow Haskell Compiler (GHC)**. Đây là chi tiết ảnh hưởng tới việc đọc mã dịch ngược vì có nhiều closure/runtime thunk hơn một binary C nhỏ.

```bash
file 'chall (1)'
readelf -S 'chall (1)'
strings -a 'chall (1)' | grep -E 'Enter the secret|Success|Failure|GHC.Internal'
```

Các chuỗi xác định được từ tệp:

```text
Enter the secret flag:
Success! Valid flag.
Failure! Invalid flag.
```

Không thấy flag xuất hiện dạng plaintext qua tìm kiếm chuỗi, nên không thể coi `strings` đơn thuần là lời giải.

## Phân tích và kết quả

Binary đọc một chuỗi do người dùng nhập rồi trả về một trong hai nhánh thành công/thất bại. Flag khôi phục từ quá trình giải đã được kiểm tra **trực tiếp trên đúng ELF gốc**. Kiểm tra chéo bằng đầu vào sai loại trừ khả năng chương trình luôn trả về thành công.

**Phạm vi tái hiện:** tài liệu có flag và binary gốc, nhưng không có trace của bộ kiểm tra, offset dữ liệu mã hóa hoặc mã khôi phục flag. Bản tái hiện bên dưới xác nhận flag đã khôi phục, không phải một exploit độc lập trích xuất lại từ bytecode.

## Tái hiện và xác minh

Trên Linux x86-64, sao chép `chall (1)` thành `chall` rồi chạy:

```bash
# Linux x86_64 (the uploaded ELF itself is not marked executable)
chmod +x ./chall
printf '%s\n' 'kBxAc{__y3t_4n0th3r_fl4g_v3ry_3a5y__}' | ./chall
printf '%s\n' 'kBxAc{wrong}' | ./chall
```

Kết quả kiểm chứng:

```text
Enter the secret flag: Success! Valid flag.
Enter the secret flag: Failure! Invalid flag.
```

## Flag

```text
kBxAc{__y3t_4n0th3r_fl4g_v3ry_3a5y__}
```

## Kết luận

Thử thách sử dụng executable GHC stripped để che phần kiểm tra. Chuỗi flag bên trên được **binary xác nhận hợp lệ**. Tài liệu chưa cung cấp phân tích control flow và dữ liệu hằng đủ để khôi phục lại đáp án từ đầu.
