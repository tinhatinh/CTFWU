# Excavation - Reverse Engineering (100 pts)

**Flag:** `POCTF{2VE5EKXUA5IV2R57}` 
(Lưu ý: Hệ thống chỉ chấp nhận thân cờ `2VE5EKXUA5IV2R57` không có tiền tố bọc ngoài)

```http
POST /challenges/excavation/submit  {"flag":"2VE5EKXUA5IV2R57"}
{"correct":true,"message":"Correct."}
```

## 1. Đề bài

Thử thách cung cấp 4 file có phần mở rộng `.sav`, mô phỏng bản lưu (save data) của một trò chơi nhập vai (RPG). Ba file là các bản lưu mẫu, và file thứ tư mang tên `team.sav` được sinh riêng cho từng đội chơi, kèm theo thông báo chứa một token dài 16 ký tự. Không có công cụ giải mã hay định nghĩa cấu trúc dữ liệu nào được cung cấp. Người chơi cần phân tích định dạng file và trích xuất dữ liệu.

## 2. Phân tích ban đầu

Kiểm tra các file bằng trình hex editor, 12 byte đầu tiên của cả bốn file đều giống nhau:

```text
9e e1 c7 21 | 02 00 | 02 00 | d2 01 00 00     (sample1)
9e e1 c7 21 | 02 00 | 02 00 | 59 03 00 00     (sample2)
9e e1 c7 21 | 02 00 | 02 00 | 78 04 00 00     (sample3)
9e e1 c7 21 | 02 00 | 02 00 | 66 05 00 00     (team)
```

Bốn byte cuối cùng của phần header là số nguyên không dấu 32-bit (u32) định dạng little-endian, khớp với kích thước của từng file: 466, 857, 1144 và 1382. Điều này cho thấy phần dữ liệu (body) bắt đầu từ mốc offset 12, và phần header này không bị mã hoá.

Phân tích độ tự tương quan (autocorrelation) trên phần body bằng cách thống kê xác suất `body[i] == body[i+L]`, nhận thấy tỷ lệ cao ở các vị trí là bội số của 8:

```text
sample1: độ trễ (lag) 8 = 0.058, lag 16 = 0.043, lag 24 = 0.044, các vị trí khác <= 0.015
team   : độ trễ (lag) 8 = 0.045, lag 16 = 0.048, lag 24 = 0.047, các vị trí khác <= 0.008
```

Kết quả này là dấu hiệu đặc trưng của phương pháp mã hoá XOR với khoá (key) lặp lại có độ dài 8 byte.

## 3. Đánh giá các giả thuyết

**Giả thuyết 1: Dùng chung một khoá cho tất cả các file.** 
Nếu áp dụng khoá tìm được từ `team.sav` cho các file khác, tỷ lệ các byte thuộc dải ký tự in được (printable) chỉ ở mức 10-17%, so với 72% trên file gốc. Thực tế, mỗi file sử dụng một mã khoá riêng biệt:

```text
sample1:  bff366a0192308a7
sample2:  8ee28d4183df8c1b
sample3:  e62903e8dcf7b038
team   :  1337df4e77c16cc7
```

**Giả thuyết 2: Toàn bộ dữ liệu là văn bản thuần tuý (Plaintext).** 
Sau khi giải mã XOR, file `team.sav` vẫn chứa khoảng 260/1370 byte ngoài dải ký tự in được, phân bố đều theo 8 cột ma trận. Điều này cho thấy định dạng file bao gồm cả các trường nhị phân (binary fields) đan xen với chuỗi ký tự.

**Giả thuyết 3: Khoá thay đổi theo từng bản ghi.** 
Khi so sánh các bản ghi của cùng một vật phẩm giữa hai file khác nhau, dữ liệu trùng khớp trên đoạn dài hơn 60 ký tự:

```text
sample1: 21 20 37 72 55 53 54 45 44 00 53 50 49 52 49 54 0d 4d ... 4c 45 00 57 45 49 47 48 54 0e
team   : 21 20 37 72 55 53 54 45 44 00 53 50 49 52 49 54 0d 4d ... 4c 45 00 57 45 49 47 48 54 0e
```

Sự trùng khớp này xác nhận khoá không thay đổi, và các byte ngoài dải văn bản là các metadata định dạng nhị phân.

**Giả thuyết 4: Token nằm ở 14 byte cuối cùng của bản ghi cuối.** 
Cả bốn file đều kết thúc bằng đoạn dữ liệu dài 14 byte:

```text
sample1  00 00 00 00 00 00 fd ff ff ff 8a 3a 82 c6
sample2  30 fd ff 79 05 00 d6 ff ff ff 9c 45 62 ea
sample3  c6 07 00 75 f3 ff e0 ff ff ff c0 51 d5 eb
team     fc fa ff 60 02 00 9f ff ff ff 5f 53 9d 05
```

Đoạn dữ liệu này chứa các trường nhị phân như số nguyên âm `i32`, marker `ff ff ff`, và 4 byte mã kiểm tra (checksum). Độ dài 14 byte không tương ứng với token 16 ký tự theo yêu cầu.

## 4. Phương pháp mã hoá hai lớp

Dữ liệu văn bản gặp một đặc điểm bất thường: ký tự đầu tiên của mỗi từ in thường, các ký tự còn lại viết hoa. Phép cộng `byte + 0x20` giúp văn bản đọc được nhưng làm hỏng các byte chỉ định độ dài.

Phân tích 6 byte nhị phân đứng trước văn bản cho thấy bảng chữ cái đã bị mã hoá thêm một lớp XOR `0x20`. Kết quả là dấu cách trở thành `0x00`, gạch ngang thành `0x0d`, dấu chấm thành `0x0e`. Điều kiện này cũng ảnh hưởng đến các byte quy định độ dài:

```text
'/' = 0x2f  ^0x20 = 15   "Obsidian censer"                        (Dài 15 byte)
 0x05       ^0x20 = 37   "Fingerprints of five different hands."  (Dài 37 byte)
 0x3c       ^0x20 = 28   "Warm regardless of the room."           (Dài 28 byte)
 0x28       ^0x20 =  8   "K. Ansen"                               (Dài 8 byte)
```

Khi áp dụng phép XOR `0x20` cho toàn bộ dữ liệu, định dạng văn bản trở lại bình thường và các trường độ dài nhận giá trị chuẩn xác. Điều này chứng minh dữ liệu được bảo vệ bởi hai lớp mã hoá:

```python
body = struct ^ 0x20 ^ key[i % 8]
```

## 5. Cấu trúc dữ liệu (Struct)

Phần Header (12 byte):
```text
u8[4]  Magic bytes: 9e e1 c7 21
u16    Phiên bản: 0x0002
u16    Cờ: 0x0002
u32    Kích thước tổng (Little-Endian)
```

Phần Body gồm các bản ghi với tiền tố xác định độ dài:

```text
Nhân vật (01): 01 | u32 | u8 namelen | name | ... | u16 item_count | u8 0
Vật phẩm (10): 10 | u8 idx | u8 a | u8 b | u8 namelen | name | u16 desclen | desc
Nhật ký  (02/03): 02 hoặc 03 | u8 0 | u8 idlen | "S<run>D<n>" | u16 desclen | text
Vị trí   (04): 04 | u32 | u8 5 | u32 size | u8 namelen | name | 14 byte cuối
```

Lưu ý khi phân tích: độ dài tên là 1 byte (`u8`), độ dài mô tả là 2 byte (`u16 LE`), và cả hai đều bị mã hóa XOR `0x20`. 

Sau khi giải mã, số lượng vật phẩm đếm được khớp với thông số khai báo:

| Tên File | Thông số item_count | Số bản ghi `0x10` thực tế |
|---|---|---|
| sample1 | 5 | 5 |
| sample2 | 10 | 10 |
| sample3 | 13 | 13 |
| team | 16 | 16 |

## 6. Tìm kiếm Token

Dựa vào gợi ý trong mục nhật ký của `team.sav`: *"I notice its voice most in the items I've collected in a particular order. First things first, I think"*, phương pháp giải mã yêu cầu ghép các ký tự đầu tiên của tên vật phẩm theo thứ tự xuất hiện.

```text
[sample1]
Talcum-stained token, Obsidian censer, Rusted spirit-medallion, Cracked seance disc, Hair-braid amulet
-> Kết quả: T O R C H

[sample2]
Silver-thread bandage, Ivory dial-plate, Lead-bound envelope, Vessel-key, Ember-in-glass, Rusted spirit-medallion, Marrow-quill pen, Obsidian censer, Obsidian censer, Needle of the Bureau
-> Kết quả: S I L V E R M O O N

[sample3]
Needle, Ivory, Ghost-key, Hair-braid, Talcum, Ember, Needle, Doubling mirror, Silver, Silver, Obsidian, Obsidian, Needle
-> Kết quả: N I G H T E N D S S O O N
```

Đối với `team.sav`, thao tác này trả về một chuỗi 16 ký tự:

```text
 0: 2-star runic band        -> 2      8: Ash-glazed lantern        -> A
 1: Vessel-key               -> V      9: 5-knot cord               -> 5
 2: Ember-in-glass           -> E     10: Ivory dial-plate          -> I
 3: 5-knot cord              -> 5     11: Vessel-key                -> V
 4: Ember-in-glass           -> E     12: 2-star runic band         -> 2
 5: Knotted willow charm     -> K     13: Rusted spirit-medallion   -> R
 6: Xylophone plate          -> X     14: 5-knot cord               -> 5
 7: Uncoiling rope           -> U     15: 7-day candle              -> 7
```

Chuỗi nhận được: **`2VE5EKXUA5IV2R57`**

Ba vật phẩm bắt đầu bằng chữ số (`2-star runic band`, `5-knot cord`, `7-day candle`) là các thành phần chỉ xuất hiện trong file `team.sav`, được sử dụng để mã hóa các chữ số vào token.

Quy trình nộp Token qua API:

```bash
$ curl -s -X POST https://pointeroverflowctf.com/challenges/excavation/submit \
    -H 'Content-Type: application/json' -b cookies.txt \
    -d '{"flag":"2VE5EKXUA5IV2R57"}'
{"correct":true,"message":"Correct."}
```

Hệ thống không chấp nhận định dạng `POCTF{...}` và sẽ trả về lỗi `Incorrect. Keep working.` nếu nhập sai định dạng.

## 7. Reproduce

```bash
cd excavation
python exploit.py
```

Công cụ `exploit.py` thực hiện tự động hóa các bước: trích xuất khóa 8 byte, giải mã lớp XOR `0x20`, phân tích các bản ghi `0x10` và in ra kết quả. Quá trình giải mã có độ chính xác cao đối với tất cả các file dữ liệu được cung cấp. Các kết quả phân tích có thể tìm thấy trong thư mục `analysis/`.
