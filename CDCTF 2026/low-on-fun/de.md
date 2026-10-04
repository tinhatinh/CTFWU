# Đề bài - Low on function names

## Nguyên văn đề

```text
Low On Fun
500
Rev Eng
b0b

Hey guys, bad news. Now that (in this dystopian future) Python is considered too zen, it evolved into a noisy monthly subscription service, Rattlesnake. Tragically, our company has nearly run out of function names for our scripts... and we never got the premium plan that includes lambda functions! My boss says I need to find a more "efficient" way to declare functions in my code, can you figure out what I did?

Flag format is cdctf{ex4mpl3_fl4g}
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/low_on_fun.py` (copy từ: `C:\Users\Administrator\Downloads\low_on_fun.py`) |
| Kích thước | 8690 byte |
| SHA-256 | `cb043a7dc96d316c7e46825268511bf5b0c2da38599ede991af237ccb7edff5f` |
| Loại file | ASCII text, very long line (8323 ký tự), CRLF |
| Nhiệm vụ | Đọc ngược checker để tìm chuỗi đầu vào hợp lệ |
| Định dạng cờ | `cdctf{...}`, tổng độ dài 40 ký tự |

## Hướng giải (tóm tắt)

File chỉ khai báo một hàm rỗng `changing()` và nạp các code object `marshal` đè lên `changing.__code__` theo từng giai đoạn; ba code object tương ứng `get_flag`, `init_checks`, `checker`. `checker` là RC4 với khóa nhúng 128 byte và chuỗi đích `check` 40 byte ghép từ 36 hằng số hex tái sử dụng. Vì keystream của RC4 không phụ thuộc plaintext, cờ thu được bằng cách XOR `check` với keystream, không cần brute-force.

## Chạy lại lời giải

```bash
python exploit.py files/low_on_fun.py
```

Kết quả: `cdctf{Y_m4ny_functi0s_wh3n_f3w_d0_trick}` (đã lưu trong `flag.txt`).
