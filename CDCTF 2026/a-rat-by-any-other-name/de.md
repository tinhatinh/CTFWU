# Đề bài - a-rat-by-any-other-name

## Nguyên văn đề

```text
A rat by any other name
500
Password Cracking
alex

I have this buddy, who just happens to be a rat, but has a totally non-rat
name, which is just simply a name, though it is a bit unconventional. The name
is no more than 8 characters long, begins with a capitol, and the rest is lower
case. I hear that he always makes his password his name. Now, I forgot his name,
which I feel pretty bad about. To avoid an awkward encounter with my rat friend,
can you please figure out his name for me?

Here is an md5 hash of one of his passwords: fe00ab6a1d242513c9f246344bf7da1d

Flag format is cdctf{Name}
```

Ảnh đề bài gốc, chụp từ thẻ challenge: chưa lưu được - thẻ chỉ tồn tại dưới dạng ảnh dán trong chat, không có file gốc trên đĩa.

## Thông tin đã xác minh

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/hash.txt` (chứa đúng chuỗi hash trong đề) |
| Kích thước | 33 byte |
| SHA-256 | `66ad6348fc38d1a583218d15f277fe3abb25f2d8c53632e96f3c2520c0d1c48f` (`sha256sum` đầy đủ ở `analysis/hashes.txt`) |
| Loại file | ASCII text |
| Hash cần bẻ | MD5, `fe00ab6a1d242513c9f246344bf7da1d` |
| Ràng buộc của mật khẩu | bằng tên; dài <= 8; ký tự đầu in hoa; các ký tự còn lại in thường |
| Không gian tìm | `?u?l{1,7}`, 217.180.147.132 ứng viên |
| Nhiệm vụ | thu hồi tên từ hash, không có dịch vụ hay file nhị phân kèm theo |
| Định dạng cờ | `cdctf{Name}` |

## Hướng giải (tóm tắt)

Ba ràng buộc chính tả của tên vừa đủ chặt để biến bài toán thành một mask brute-force: toàn bộ không gian chỉ 2.17e11 chuỗi dạng một chữ hoa đầu rồi tới chữ thường, MD5 lại không chậm hoá, nên GPU laptop phủ hết trong khoảng hai phút. Wordlist chỉ dùng để loại sớm, không dùng để kết luận; script kèm theo tán exhaustively mask đó bằng hashcat và có self-test chứng minh bộ sinh ứng viên tìm thấy mật khẩu cắm sẵn trong cùng family mask.

## Chạy lại lời giải

```bash
python exploit.py --selftest    # kiem machine sinh ung vien: crack md5("Felix")
python exploit.py               # tan cong mask ?u?l{1,7}, in co cdctf{...}
```

Cần hashcat; đường dẫn mặc định `C:\Tools\hashcat\hashcat-6.2.6\hashcat.exe`, đổi bằng biến môi trường `HASHCAT`.
