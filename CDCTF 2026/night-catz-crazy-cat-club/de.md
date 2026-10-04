# Đề bài - night-catz-crazy-cat-club

## Nguyên văn đề

```text
Night Catz Crazy Cat Club
500
RevE Crypto
alex

I am trying to sneak into the epic cat club, Night Catz Crazy Cat Club. However, they
have an authentication question that I can't seem to bypass. In order to secure my entry,
please help me figure out the secret response.

Flag format is cdctf{secret cat phrase}

I recommend running the binary with the correct response, even though this is not required
to submit the flag. I intend for it to be amusing.
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/cat_club_authenticator.out` (copy từ: `C:/Users/Administrator/Downloads/cat_club_authenticator.out`) |
| Kích thước | 861072 byte |
| SHA-256 | `4528f8454ae5c2db4b781f74a7e2be8ac1bb46d89218dd2d5b008d6f606b0a04` |
| Loại file | ELF 64-bit LSB executable, x86-64, statically linked (glibc), for GNU/Linux 4.4.0, not stripped |
| Nhiệm vụ | Tìm câu trả lời đúng cho câu hỏi xác thực mà `main()` so sánh |
| Định dạng cờ | `cdctf{secret cat phrase}` |

## Hướng giải (tóm tắt)

`main()` đọc một dòng bằng `fgets`, bắt buộc `strlen(input) == 46`, rồi so từng byte theo công thức
`A[i] == (input[i] ^ 0x67)`. Mảng `A` 46 số nguyên và key `0x67` được dựng tĩnh bằng lệnh `mov` ngay
trong thân `main`, nên chỉ cần trích hai nhóm giá trị đó từ mã máy và XOR ngược là ra cụm từ phải nhập.

## Chạy lại lời giải

```bash
python exploit.py files/cat_club_authenticator.out
```

Kết quả: `cdctf{with a glass in my paw and milk on my whiskers}` (đã lưu trong `flag.txt`).
Bản chạy thật của binary với câu trả lời này nằm ở `analysis/welcome_run.txt`.
