# Đề bài - yummy-rat-toast

## Nguyên văn đề

```text
Yummy Rat Toast
500
Password Cracking
alex

The other day I was making some toast, but I totally burnt it, and I said, "Darn, I guess I just
can't cook," but my friend Remy (who also happens to be a rat), was telling me that his very wise
friend once said, "Anyone can cook." After that, he helped me make some real good and crispy toast.
In return for his help cooking, I offered him some IT service. He asked me if I could test the
security of his password, which he said is based on the name of a good friend of his. He provided
the following hash of his password (which is in md5, of course, a rat's favorite algo).
3f1ebefc63dc39f3c9b934a30accb221
```

Ảnh đề bài gốc, chụp từ thẻ challenge:

*(thẻ bài này không có trong hai docx nguồn của `de-cards.tsv`; `files/hash.txt` chính là chuỗi md5
in trên thẻ, chép nguyên văn)*

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/hash.txt` (copy từ: `C:\Users\Administrator\Downloads\_scratch\yummyrat\case\hash.txt`) |
| Kích thước | 33 byte |
| SHA-256 | `082b5ad8c25c7437967bbb2c0b10c434fb6a95a8529b9d6e7c3fa09aa139f1bb` |
| Loại file | ASCII text |
| Nhiệm vụ | tìm chuỗi có MD5 bằng `3f1ebefc63dc39f3c9b934a30accb221`; mật khẩu "based on the name of a good friend of his" |
| Định dạng cờ | `cdctf{...}` |

## Hướng giải (tóm tắt)

Remy là chuột, câu "Anyone can cook" là khẩu hiệu của đầu bếp Gusteau, tức toàn bộ bối cảnh lấy từ phim
Ratatouille. Không gian cần quét là tên dàn nhân vật của phim, ghép thành tên đầy đủ, có viết hoa và có
hậu tố số. Wordlist mật khẩu phổ biến, danh sách tên người Mỹ, từ điển Anh ngữ và các rule mở rộng của
chúng đều trượt vì chúng không sinh ra dạng "Title Title" + 2 chữ số. Danh sách tự sinh từ đúng dàn cast
(mỗi tên ghép với mọi tên khác, ba dấu nối, ba kiểu hoa thường) rồi đưa qua `dive.rule` là ra cờ.

## Chạy lại lời giải

```bash
python exploit.py files/hash.txt
```

Kết quả: `cdctf{Alfredo Linguini01}` (đã lưu trong `flag.txt`).
