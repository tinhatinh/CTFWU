# Đề bài - tacocat

## Nguyên văn đề

```text
Tacocat
500
alex

This fat cat and I have one thing in common: we both love the classic crunchy tacobell taco.
I freaking love that thing. It's got all the taco things on it; it's got the shell, the meat,
the cheese, the lettuce. The classic crunchy tacobell taco inspires me to be the best version
of myself that I can be. I think that someday the classic crunchy tacobell taco may be the
solution to world hunger. I love the classic crunchy tacobell taco. That said, here's a fat cat
that loves some good classic crunchy tacobell taco. Find the flag. You may need to think about
what you could ever want that's extra or say, in addition to the classic crunchy tacobell taco
in your life; though it's probably nothing, given how good the classic crunchy tacobell taco is.
```

Ảnh đề bài gốc, chụp từ thẻ challenge:

*(chưa có thẻ challenge dạng ảnh cho bài này; artifact `files/fat_tacocat.png` chính là ảnh đề cho)*

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/fat_tacocat.png` (copy từ: `C:\Users\Administrator\Downloads\fat_tacocat.png`) |
| Kích thước | 578053 byte |
| SHA-256 | `11fe22d62e5f8a1fee9cb0d9cdc04efd6d66b20ea860aeb58351bf5b69e1f07f` |
| Loại file | PNG image data, 1244 x 700, 8-bit/color RGBA, non-interlaced |
| Nhiệm vụ | Đọc cờ ẩn trong phần dữ liệu nằm ngoài ảnh hiển thị |
| Định dạng cờ | `cdctf{...}` |

## Hướng giải (tóm tắt)

File có 118876 byte nối sau `IEND`. Bên trong là một PNG thứ hai không có chữ ký `\x89PNG\r\n\x1a\n`,
nên `file`, `strings` và `binwalk` đều bỏ qua. PNG ẩn dùng chunk private `deBG` (de-background):
mọi pixel đều đen, toàn bộ nét vẽ nằm ở kênh alpha. Xuất kênh alpha thành ảnh grayscale thì cờ hiện ra,
viết bằng font tay 4 dòng.

## Chạy lại lời giải

```bash
python exploit.py files/fat_tacocat.png
```

Kết quả: `cdctf{I_really_rea11y_1ik3_th3_tac0b311_classic_crunchy_taco3}` (đã lưu trong `flag.txt`).
