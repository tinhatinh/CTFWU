# Đề bài - crypto-cat-3

## Nguyên văn đề

```text
The Epic Adventures of Crypto Cat Caticus Catanius (3/5)
498
Crypto
alex

Meow meow, Crypto Cat Caticus Catanius, meow meow. It would seem that you're quite
the cryptographer! This is my third key, which I'm confidant is unbreacatable!

wcwpl{qgj shghquzmqkrpew nvk'npepvpehg wezmrf wqg kr wfqwyrc pmfhvom npq'penpewqu
qgqujnen oetrg nv'llewergp wezmrf prdp lhf pmr gvskrfn ph kr leovfrc hvp
sqpmrsqpewquuj qgc nvwm}
```

*(chưa có thẻ challenge dạng ảnh cho chuỗi này; phần text trên là toàn bộ nội dung thẻ,
kể cả bản mã. Không có file tải về và không có instance.)*

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/ciphertext.txt` (chép lại nguyên văn bản mã trong thẻ đề) |
| Kích thước | 180 byte (179 ký tự bản mã + xuống dòng) |
| SHA-256 | `742a5555bc13ed0d6336b29673baba2dca97ebfc77ad905989ca4015083233ed` |
| Loại file | ASCII text |
| Dữ liệu | 151 chữ cái, 22 chữ phân biệt, IC = 0.0580; 24 token; `wezmrf` và `kr` mỗi từ lặp hai lần |
| Mồi trong đề | ba dấu nháy đơn (`nvk'n...`, `npq'p...`, `nv'll...`) khiến người giải đọc ra `can't`/`you've`/`we'll` và đoán sai sang Vigenère |
| Nhiệm vụ | Recover plaintext của bản mã, đúng định dạng cờ |
| Định dạng cờ | `cdctf{...}` |

## Hướng giải (tóm tắt)

Phep the hoa don (monoalphabetic substitution), không phải Vigenère: IC 0.0580 là mức của một bảng
chữ cái, và hai từ lặp lại (`wezmrf` cách nhau 59 chữ cái, `kr` cách 75) có gcd bằng 1 nên khóa tuần
hoan theo chữ cái không tồn tại. Crib `cdctf{` mở đầu bảng ánh xạ, các từ lặp và tần suất cho ra
`cipher`, `cracked`, `figured`, `through`; 22 ánh xa don anh decode trọn 24 token thành tiếng Anh.

## Chạy lại lời giải

```bash
python exploit.py files/ciphertext.txt
```

Kết quả: `cdctf{any monoalphabetic sub'stitution cipher can be cracked through sta'tistical analysis
given su'fficient cipher text for the numbers to be figured out mathematically and such}`
(đã lưu trong `flag.txt`).
