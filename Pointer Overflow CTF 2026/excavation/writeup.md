# Excavation - Reverse Engineering (100 pts)

**Flag:** `POCTF{2VE5EKXUA5IV2R57}` 
(Lưu ý: Hệ thống chỉ chấp nhận thân cờ `2VE5EKXUA5IV2R57` không có tiền tố bọc ngoài)

```http
POST /challenges/excavation/submit  {"flag":"2VE5EKXUA5IV2R57"}
{"correct":true,"message":"Correct."}
```

## 1. Đề bài

Thử thách quẳng cho ta 4 tệp tin có phần mở rộng `.sav` thuộc về một trò chơi nhập vai (RPG) giả định. Trong số đó, ba file được giới thiệu là các bản lưu (save data) mẫu của những lần chơi (run) khác nhau, và file thứ tư mang tên `team.sav` được sinh cấp phát riêng cho từng đội chơi, với lời nhắn nó "mang theo một token dài 16 ký tự". Hoàn toàn không có một công cụ giải mã hay một định nghĩa cấu trúc (struct) nào đi kèm. Nhiệm vụ của ta là dùng kỹ thuật dịch ngược tự lột trần cấu trúc dữ liệu và giải mã chúng.

## 2. Phân tích ban đầu

Mở các file dưới trình hex editor, 12 byte đầu tiên của cả bốn tệp tin giống hệt nhau như đúc:

```text
9e e1 c7 21 | 02 00 | 02 00 | d2 01 00 00     (sample1)
9e e1 c7 21 | 02 00 | 02 00 | 59 03 00 00     (sample2)
9e e1 c7 21 | 02 00 | 02 00 | 78 04 00 00     (sample3)
9e e1 c7 21 | 02 00 | 02 00 | 66 05 00 00     (team)
```

Bốn byte cuối cùng của phần header này là số nguyên không dấu 32-bit (u32) hệ little-endian, và giá trị của chúng trùng khớp hoàn toàn với kích thước thực tế của từng tệp: 466, 857, 1144 và 1382. Điều này tiết lộ hai chân lý: khối dữ liệu thân (body) bắt đầu từ mốc offset 12, và 12 byte header này hoàn toàn trong suốt (không bị mã hoá).

Tiến hành phép đo độ tự tương quan (autocorrelation) trên phần thân - bằng cách đếm xác suất trùng lặp `body[i] == body[i+L]`, ta nhận thấy một đỉnh cộng hưởng cực mạnh lặp lại ở các bội số của 8:

```text
sample1: độ trễ (lag) 8 = 0.058, lag 16 = 0.043, lag 24 = 0.044, các vị trí khác <= 0.015
team   : độ trễ (lag) 8 = 0.045, lag 16 = 0.048, lag 24 = 0.047, các vị trí khác <= 0.008
```

Đây là bản phác hoạ không thể chối cãi của một thuật toán mã hoá XOR với khoá (key) xoay vòng dài đúng 8 byte.

## 3. Khám nghiệm các giả thuyết đã sụp đổ

**Ảo tưởng 1: Dùng chung một chìa khoá cho cả làng.** 
Nếu ta cưỡng ép dùng khoá bẻ được từ `team.sav` lên các file mẫu khác, tỷ lệ các byte lọt vào vùng bảng chữ cái (alphabet) chỉ lẹt đẹt ở mức 10-17%, trong khi file chủ lại đạt tới 72%. Sự thật là mỗi file sở hữu một mã khoá hoàn toàn riêng biệt:

```text
sample1:  bff366a0192308a7
sample2:  8ee28d4183df8c1b
sample3:  e62903e8dcf7b038
team   :  1337df4e77c16cc7
```

**Ảo tưởng 2: Bản rõ (Plaintext) thuần tuý là chữ (text).** 
Ngay cả sau khi đã lột bỏ lớp XOR bằng đúng khoá gốc, tệp `team.sav` vẫn còn tới 260/1370 byte nằm vương vãi ngoài vùng ký tự in được. Hơn thế nữa, chúng rải đều một cách hệ thống trên cả 8 cột ma trận mã (dao động từ 28 đến 36 byte mỗi cột). Điều này chứng minh rằng không có cột khóa nào bị nứt, mà bản thân cấu trúc file thực sự chứa xen kẽ các trường (field) nhị phân.

**Ảo tưởng 3: Khoá bị xoay hoặc thay đổi theo từng bản ghi.** 
Đây là cạm bẫy dễ sập nhất, bởi các byte "kỳ dị" cứ liên tục chêm vào giữa các đoạn văn bản đọc được. Nhưng hãy nhìn vào bằng chứng thép: khi đối chiếu bản ghi (record) của cùng một vật phẩm (item) giữa hai file khác nhau, chúng giống nhau y đúc đến từng byte trên những phân đoạn kéo dài hơn 60 ký tự:

```text
sample1: 21 20 37 72 55 53 54 45 44 00 53 50 49 52 49 54 0d 4d ... 4c 45 00 57 45 49 47 48 54 0e
team   : 21 20 37 72 55 53 54 45 44 00 53 50 49 52 49 54 0d 4d ... 4c 45 00 57 45 49 47 48 54 0e
```

Khoá đúng, văn bản khớp hoàn hảo, vậy thì đám byte dị hợm kia bắt buộc phải là dữ liệu hệ thống (metadata) hợp lệ của file.

**Ảo tưởng 4: Token là một chuỗi 16 ký tự nằm lộ thiên.** 
Quét biểu thức chính quy `re.finditer(rb'[A-Z0-9]{16,}')` và `[A-Za-z0-9_]{14,}` trên cả 4 file đều trả về con số không tròn trĩnh.

**Ảo tưởng 5: Token nằm ở 14 byte cuối cùng của bản ghi cuối.** 
Đúng là cả bốn file đều kết thúc bằng một đoạn vĩ thanh dài đúng 14 byte:

```text
sample1  00 00 00 00 00 00 fd ff ff ff 8a 3a 82 c6
sample2  30 fd ff 79 05 00 d6 ff ff ff 9c 45 62 ea
sample3  c6 07 00 75 f3 ff e0 ff ff ff c0 51 d5 eb
team     fc fa ff 60 02 00 9f ff ff ff 5f 53 9d 05
```

Nhưng hãy nhìn kỹ, đó rặt là các trường nhị phân: một số nguyên âm `i32`, một lính gác (sentinel) `ff ff ff`, và 4 byte cuối nghi ngờ là mã checksum. Chúng có độ dài cố định là 14, không thể nào chuyển hoá thành một token 16 ký tự. Lối đi này hoàn toàn tắc.

## 4. Điểm kỳ dị: Mã hoá hai lớp, không phải một

Có một hiện tượng quái gở cản trở việc đọc luồng văn bản: Ký tự **đầu tiên** của mỗi từ lại bị in thường, trong khi toàn bộ các chữ cái còn lại đều bị VIẾT HOA (ví dụ: `mIDDLE RANK OF A DISCONTINUED ORDER`). Tạm bợ bẻ lại bằng lệnh `byte < 0x20 -> byte + 0x20` thì chữ đọc được trôi chảy, nhưng các thông số báo chiều dài chuỗi lại trở thành những con số vô hồn vô nghĩa.

Cú chốt hạ (breakthrough) nằm ở việc mổ xẻ 6 byte nhị phân đứng ngay trước mỗi chuỗi văn bản. Bảng chữ cái trong file thực chất là bảng mã ASCII đã bị đánh ngất bằng một lớp XOR `0x20` nữa. Hệ quả là dấu cách (space) biến thành byte null `0x00`, dấu gạch ngang `-` hoá thành `0x0d`, dấu chấm `.` thành `0x0e`, nháy đơn `'` thành `0x07`, dấu hai chấm `:` thành `0x1a`. **Kinh hoàng hơn, các byte quy định độ dài chuỗi cũng vô tình bị lật luôn bit số 5**:

```text
'/' = 0x2f  ^0x20 = 15   "Obsidian censer"                        (Dài 15 byte)
 0x05       ^0x20 = 37   "Fingerprints of five different hands."  (Dài 37 byte)
 0x3c       ^0x20 = 28   "Warm regardless of the room."           (Dài 28 byte)
 0x28       ^0x20 =  8   "K. Ansen"                               (Dài 8 byte)
```

Chỉ cần vung đòn `^ 0x20` phủ lên toàn bộ phần thân, mọi thứ lập tức quy tụ về chuẩn mực: văn bản lấy lại định dạng Title Case nguyên bản, dấu cách trả về đúng dấu cách, và các trường nhị phân điều khiển biến thành những số nguyên có giá trị nhỏ rất hợp lý. Hoá ra, phần thân bị khoá cứng bởi **hai lớp mã hoá chồng lên nhau**:

```python
body = struct ^ 0x20 ^ key[i % 8]
```

## 5. Phục dựng cấu trúc (Struct)

Khối Header (12 byte) trong suốt:
```text
u8[4]  Magic bytes: 9e e1 c7 21
u16    Phiên bản/cờ: 0x0002
u16    Phiên bản/cờ: 0x0002
u32    Kích thước tổng file (hệ Little-Endian)
```

Khối Body là một đoàn tàu chở các toa bản ghi (record). Mỗi toa đều tự cất lên tiếng nói khai báo chiều dài của chính nó thông qua các tiền tố điều khiển:

```text
Bản ghi Nhân vật (01): 01 | u32 | u8 namelen | name | ... | u16 item_count | u8 0
Bản ghi Vật phẩm (10): 10 | u8 idx | u8 a | u8 b | u8 namelen | name | u16 desclen | desc
Bản ghi Nhật ký  (02/03): 02 hoặc 03 | u8 0 | u8 idlen | "S<run>D<n>" | u16 desclen | text
Bản ghi Vị trí   (04): 04 | u32 | u8 5 | u32 size | u8 namelen | name | 14 byte vĩ thanh
```

Cạm bẫy cực hiểm khi viết công cụ phân tích (parser): Độ dài của trường tên chỉ là một byte (`u8`), trong khi độ dài của trường mô tả là hai byte (`u16 LE`), và **cả hai trường số học này đều phải chịu trận bị lật bit 5** trước khi được sử dụng.

Khi parser chạy, số lượng vật phẩm (item) đếm được khớp hoàn hảo với con số được niêm phong trong bản ghi nhân vật:

| Tên File | Thông số item_count | Số lượng record `0x10` móc ra được |
|---|---|---|
| sample1 | 5 | 5 |
| sample2 | 10 | 10 |
| sample3 | 13 | 13 |
| team | 16 | 16 |

## 6. Săn Token

Đề bài đã ngầm rải thính: *"The flag for this challenge is a little different"*. Trong mục nhật ký của `team.sav`, tác giả nhét một câu thoại: *"I notice its voice most in the items I've collected in a particular order. First things first, I think."* (Tôi để ý thấy tiếng nói của nó rõ nhất qua các vật phẩm được tôi nhặt theo một trình tự nhất định. Việc đầu tiên là ghép các từ đầu tiên lại với nhau).

Rút ngay ký tự đầu tiên của tên các vật phẩm, tuân thủ nghiêm ngặt theo thứ tự chúng nằm trong túi đồ:

```text
[sample1]
Talcum-stained token, Obsidian censer, Rusted spirit-medallion, Cracked seance disc, Hair-braid amulet
-> Ghép lại: T O R C H

[sample2]
Silver-thread bandage, Ivory dial-plate, Lead-bound envelope, Vessel-key, Ember-in-glass, Rusted spirit-medallion, Marrow-quill pen, Obsidian censer, Obsidian censer, Needle of the Bureau
-> Ghép lại: S I L V E R M O O N

[sample3]
Needle, Ivory, Ghost-key, Hair-braid, Talcum, Ember, Needle, Doubling mirror, Silver, Silver, Obsidian, Obsidian, Needle
-> Ghép lại: N I G H T E N D S S O O N (NIGHT ENDS SOON)
```

Cả ba mẫu đều trả về những từ vựng tiếng Anh sắc lẹm. Bộ quy tắc (Acrostic) này đã được khẳng định bằng chính kho dữ liệu nội bộ của tác giả, đập tan mọi nghi ngờ về trò đoán chữ (guess) rẻ tiền. Chuyển hướng sang file `team.sav` sở hữu 16 item, nó nôn ra đúng một chuỗi 16 ký tự:

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

Kết quả: **`2VE5EKXUA5IV2R57`**

Chú ý kỹ: Ba vật phẩm có tên khởi đầu bằng một chữ số (`2-star runic band`, `5-knot cord`, `7-day candle`) chỉ xuất hiện đặc cách trong file `team.sav`. Đó chính là dàn đạo cụ được tác giả nhào nặn ra để mã hoá ép các con số vào trong token cấp cho các đội.

Quy trình nộp Token:

```bash
$ curl -s -X POST https://pointeroverflowctf.com/challenges/excavation/submit \
    -H 'Content-Type: application/json' -b cookies.txt \
    -d '{"flag":"2VE5EKXUA5IV2R57"}'
{"correct":true,"message":"Correct."}
```

Lưu ý chết người: Nếu bạn nhiệt tình bọc cờ dưới dạng `POCTF{2VE5EKXUA5IV2R57}`, máy chủ sẽ lạnh lùng từ chối (`Incorrect. Keep working.`). Điểm khốn nạn là API endpoint này không hề dội lại chuỗi flag để ta sao chép. Dấu hiệu chiến thắng duy nhất là dòng trạng thái `>> ACK :: Correct.` nhấp nháy trên giao diện.

## 7. Phục dựng (Reproduce)

```bash
cd excavation
python exploit.py
```

Công cụ `exploit.py` là một cỗ máy nghiền nát tự động: nó tự thân vận động tìm lại các chìa khoá 8 byte của cả bốn file (không cần bất kỳ sự can thiệp mớm cung nào từ con người), đập nát lớp nguỵ trang `^0x20`, phân tích (parse) trọn vẹn toàn bộ các bản ghi `0x10` và kiêu hãnh in ra chuỗi Acrostic cuối cùng. Lõi giải mã học được mô hình phân bố byte ưu việt đến mức file `sample3` cũng bị vắt ra đúng chìa gốc (`e62903e8dcf7b038`), vượt trội hoàn toàn so với kiểu tính điểm thô thiển bị lệch byte trước đó.

Thư mục `analysis/` đóng vai trò như phòng mổ lưu giữ các tiêu bản: `*.pt` là cơ thể sau khi bị lột lớp XOR thứ nhất, `*.dec` là bản nháp thử máu bằng phép tịnh tiến `+0x20` (chỉ áp dụng giới hạn trên các byte điều khiển), và `*.true` chính là cấu trúc (struct) nguyên sinh lộ diện sau khi cả hai bức màn mã hoá bị xé toạc.
