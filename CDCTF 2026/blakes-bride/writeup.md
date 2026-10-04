# Blake's Bride - Forensics (500 điểm)

**Cờ:** `cdctf{epithalamium738-trousseau201-honeymoon069}`
**File đính kèm:** `blake.png` (139.894 B, SHA256 `60cfcb420af6bd3b30b6fd0a9ee9abcb5584a2d47cb179dafc8448dac673178c`)

## Đề bài

Đề cho một ảnh `blake.png` và nói rằng ba mật khẩu của cô dâu "được lưu và mã hoá theo
cách không chính thống". Ràng buộc đã cho: mỗi mật khẩu là một từ liên quan tới đám cưới
nối với ba chữ số, cờ ghép theo thứ tự `password1-password2-password3`.

## Phân tích ban đầu

`file` và `exiftool` trả về một PNG 981x731, 8-bit RGB, không interlace. Cấu trúc chunk
sạch: `IHDR, sRGB, gAMA, pHYs, iTXt, IDAT x3, IEND`, và `IEND` kết thúc file - không còn
byte nào bị nối thêm phía sau.

Toàn bộ dữ liệu cần tìm nằm trong chunk `iTXt` duy nhất (keyword `XML:com.adobe.xmp`).
Bên trong XMP có một thẻ `exif:UserComment`:

```text
c2a587abcc00c2837b095e508cacf90f47b1ffd4c765269baabc0a55d5ee5ee1
6f591da144d0d64205899814d786ac3abbdff81a74d5e9b46b0bfd89e71d021a
-6bb9798a3011496566d842e4fd78be4aaa1a683028ddd190aaad374d89db5b02
a26cbed538ebe8baadca4d9c9b167de7f132d5bd30205ad6814b6c865dd7344a
-0fed6e840bbe32beda22f5ae7c0e41bc8c0995103a1ded55c694209f9118f534
908c5d8750b561e81e75b844c1b00e77cabe8866a4d7c97bfb7b719789201dc0
```

Ba chuỗi hex, mỗi chuỗi 128 ký tự (64 byte), phân tách bằng `-`. Độ dài 64 byte gợi tới
SHA-512, nhưng gợi ý đó chỉ đúng về kích thước.

## Các hướng đã loại

1. **SHA-512 / SHA3-512**: với ràng buộc `<từ> + 000..999`, cả hai hàm cho 0/3 digest khớp.

2. **Stego LSB trong ảnh**: lần lượt trích 1, 2, 3 bit thấp của mỗi kênh theo cả hai thứ tự
   bit, tỉ lệ byte in được chỉ đạt 0,043 / 0,019 / 0,010 và đầu ra là nhiễu.
3. **Dữ liệu nối sau `IEND` hoặc chunk ẩn**: đi hết chuỗi chunk, số byte sau `IEND` là 0.

Các phép thử trên không thu được dữ liệu hữu ích ngoài XMP. Tiếp tục kiểm tra các hàm hash có digest 64 byte trên không gian mật khẩu mà đề mô tả.

## Chuỗi khai thác

**Bước 1 - Định danh thuật toán.** 128 ký tự hex là 64 byte, nhưng phép thử trực tiếp trên
không gian mật khẩu đã cho thấy hàm đúng là BLAKE2b (digest mặc định 64 byte). Tên artifact
`blake.png` và câu "I wonder if there's something wrong with Blake" gợi ý sử dụng BLAKE2b.

```python
import hashlib
hashlib.blake2b(b"honeymoon069").hexdigest()
hashlib.sha512(b"honeymoon069").hexdigest()
```

```text
0fed6e840bbe32beda22f5ae7c0e41bc8c0995103a1ded55c694209f9118f534908c5d8750b561e81e75b844c1b00e77cabe8866a4d7c97bfb7b719789201dc0
44dfa8f69d16d8a4efca3781a29191e1ab4fd65a6b7a2cd765636f466a04120673f5bf30d25426c96521c7a320a32bef1e3e3dcf5f1c4827b41310f311855660
```

Dòng đầu khớp đúng digest thứ ba trong `UserComment`; dòng thứ hai không khớp vị trí nào.

**Bước 2 - Quét từ điển đám cưới.** Với mỗi từ, thử 1000 bộ số `000..999`, so bằng `.digest()`
và `bytes` để tránh chi phí `hexdigest()`. Danh sách khoảng 200 từ về chủ đề đám cưới trả về
một mật khẩu: `honeymoon069` khớp digest thứ ba, trong khi SHA-512 và SHA3-512 vẫn cho 0/3 trên
cùng không gian đó. `epithalamium` (khúc hát mừng cưới) và `trousseau` (đồ hồi môn) không có
trong danh sách gọn này.

**Bước 3 - Mở rộng từ điển.** Chuyển sang từ điển tiếng Anh 369.778 mục từ, cùng phép nối
`<từ> + 3 chữ số`, chia đều cho 16 tiến trình. Hai mật khẩu còn lại được tìm thấy trong chưa tới 75
giây, không cần thêm ràng buộc nào khác:

```text
words 369778 mode lower
HIT trousseau201 6bb9798a3011496566d842e4fd78be4aaa1a683028ddd190aaad374d89db5b02a26cbed538ebe8baadca4d9c9b167de7f132d5bd30205ad6814b6c865dd7344a
HIT epithalamium738 c2a587abcc00c2837b095e508cacf90f47b1ffd4c765269baabc0a55d5ee5ee16f591da144d0d64205899814d786ac3abbdff81a74d5e9b46b0bfd89e71d021a
HIT honeymoon069 0fed6e840bbe32beda22f5ae7c0e41bc8c0995103a1ded55c694209f9118f534908c5d8750b561e81e75b844c1b00e77cabe8866a4d7c97bfb7b719789201dc0
```

**Bước 4 - Kiểm chứng.** Tính lại digest của từng ứng viên và so với đúng vị trí của nó trong
`UserComment`. Ba chuỗi khớp cả về giá trị lẫn thứ tự, nên cờ ghép theo thứ tự 1-2-3.

`exploit.py` gộp Bước 1 tới Bước 4 thành một lần chạy và thay từ điển đầy đủ bằng
`files/wedding_words.txt` (521 từ, đã bổ sung nhóm từ cổ và từ văn học về đám cưới), nên lời
giải reproduce được mà không cần file từ điển ngoài.

## Flag

```bash
python exploit.py files/blake.png
```

```text
[*] blake.png: 139894 bytes
[*] UserComment: 3 digest, do dai hex [128, 128, 128]
[*] wordlist wedding_words.txt: 521 tu x 1000 so = 521000 hash/thuat toan (jobs=1)
[*] blake2b  : 3/3 digest khop
[+] thuat toan: blake2b
[+] password1: epithalamium738  -> c2a587abcc00c2837b095e508cacf90f...
[+] password2: trousseau201     -> 6bb9798a3011496566d842e4fd78be4a...
[+] password3: honeymoon069     -> 0fed6e840bbe32beda22f5ae7c0e41bc...
[+] flag: cdctf{epithalamium738-trousseau201-honeymoon069}
[+] da luu flag.txt
```

Cờ trên do ba mật khẩu tính ra cục bộ từ `blake.png`, chưa nộp lên nền tảng để đối chiếu.

## Reproduce

```bash
python exploit.py files/blake.png                                   # 6,4 s
python exploit.py files/blake.png /duong/dan/words_alpha.txt -j 16   # 2 phut 11 giay
```

`exploit.py` chỉ dùng stdlib, nhận đường dẫn artifact và wordlist qua `argv`. Lần chạy đầu
dùng `files/wedding_words.txt` đi kèm; lần thứ hai bỏ qua danh sách đám cưới và quét toàn bộ
từ điển tiếng Anh, cả hai đều in ra cùng một cờ.

`analysis/` giữ ba phép thử đã dùng để loại hướng sai và để dựng lại con số trong bài:
`chunk_walk.py` (cấu trúc chunk, 0 byte sau `IEND`), `lsb_scan.py` (tỉ lệ byte in được theo
1/2/3 bit thấp), `dict_sweep.py` (lần quét từ điển đầy đủ 16 tiến trình). Output của từng lệnh
lưu cạnh script.
