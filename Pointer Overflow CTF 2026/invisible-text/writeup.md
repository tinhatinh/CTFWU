# Invisible Text — STEG (200 pts)

**Flag:** `POCTF{PIEMPAOSMHDLEGRT}`
**Files:** `invisible_text.py` (4245 B, sha256 `f027442b37a521f4a775ec56d37336df446d83e7acd641042e28af030f745320`)

## Đề bài

Tác giả úp mở rằng có một thông điệp bí mật được cất giấu ngay bên trong tệp tin, và chỉ cần "nhìn đúng chỗ" là sẽ thấy. Thử thách cung cấp duy nhất một tệp mã nguồn `invisible_text.py` (tệp này được sinh riêng biệt cho từng đội, máy chủ phát tệp dưới tên `invisible_text_612.py`). Không có bất kỳ tệp nhị phân nào đi kèm, cũng không có hệ thống hay dịch vụ từ xa nào để kết nối. Nhiệm vụ duy nhất là trích xuất thông điệp ẩn bên trong mã nguồn và nộp nó.

## Phân tích ban đầu

Tệp tin hoàn toàn là mã Python thuần tuý, nặng 4245 byte, gồm 81 dòng văn bản được mã hoá ở chuẩn UTF-8. Khi kiểm kê từng byte một, ta nhận thấy cả tệp chỉ chứa duy nhất một ký tự nằm ngoài dải ASCII chuẩn, đó là dấu gạch ngang `—` vô thưởng vô phạt nằm gọn trong một dòng comment. Hoàn toàn không có sự xuất hiện của các kỹ thuật giấu tin tàng hình kinh điển như Zero Width Space, không có dấu định dạng BOM, không có NBSP (khoảng trắng không ngắt), và cũng không có bất kỳ ký tự đồng dạng (homoglyph) nào.

Man mối duy nhất còn sót lại lại là một sự bất thường cực kỳ tinh tế: **47 trên tổng số 81 dòng mã đều kết thúc bằng một khoảng trắng (whitespace) thừa thãi**. Cụ thể hơn:

```text
dòng 1   SSSTSTSSSS        (chứa 10 ký tự khoảng trắng/tab)
dòng 2   T                 (chứa đúng 1 ký tự tab)
dòng 3   SSSSSTSSTTTT      (chứa 12 ký tự)
dòng 4   T
dòng 5   SSSSSTSSSSTT
...
dòng 45  SSSSSTTTTTST
dòng 46  T
dòng 47  SS                (chứa 2 ký tự)
```
*(Trong đó `S` đại diện cho Space, `T` đại diện cho Tab).*

Điểm thú vị là các dòng số lẻ luôn có độ dài cố định là 12 ký tự (ngoại trừ dòng đầu tiên bị lẹm còn 10), trong khi các dòng chẵn chỉ chứa duy nhất một phím tab. Chắc chắn lời gợi ý "look closely" của tác giả đang ám chỉ thẳng vào vùng dữ liệu vô hình này.

Nội dung bề nổi của file là một công cụ `diary_reader.py` thực hiện nhiệm vụ nối 46 khối base64 thành một chuỗi duy nhất, giải mã bằng `b64decode`, bung nén bằng `zlib.decompress`, rồi in kết quả ra màn hình. Khi chạy thử script này (cần lưu ý phải ghi kết quả ra tệp UTF-8 vì giao diện console của Windows dùng bảng mã cp1252, nếu dùng lệnh `print` thẳng ra sẽ bị văng lỗi `UnicodeEncodeError`), thứ ta nhận được là một văn bản gồm 2145 ký tự braille (chữ nổi) trải dài trên 33 dòng. Đó chỉ là một lớp mồi nhử.

## Chuỗi khai thác

**Bước 1 — Nhận diện khuôn mẫu dữ liệu (Fixed-length groups).** 
Quan sát kỹ, mỗi dòng dữ liệu chính đều chứa chính xác 12 ký tự khoảng trắng, trong đó vị trí thứ sáu **luôn luôn là một dấu tab**. Đây là một dấu ấn kinh điển của mô hình mã hoá 7-bit: năm dấu cách đầu tiên chỉ đóng vai trò đệm (padding) để căn lề, còn bảy ký tự cuối cùng mới thực sự mang dữ liệu mã hoá.

**Bước 2 — Trích xuất dữ liệu, quy ước `tab = 1`, `space = 0`.** 
Theo tiêu chuẩn, các ký tự ASCII in được luôn có bit cao nhất (MSB) bằng 1. Vì thế, việc nhóm 7 bit luôn bắt đầu bằng một phím tab (tương đương với số 1) chính là cọc tiêu định vị hoàn hảo.

```python
flag = ""
for line in src.split("\n"):
    tail = line[len(line.rstrip()):]
    if len(tail) < 7:
        continue
    bits = tail[-7:].replace(" ", "0").replace("\t", "1")
    flag += chr(int(bits, 2))
```

Chạy đoạn mã trên, ta giải mã thành công:

```text
  dòng   1  TSTSSSS  =  80  'P'
  dòng   3  TSSTTTT  =  79  'O'
  dòng   5  TSSSSTT  =  67  'C'
  dòng   7  TSTSTSS  =  84  'T'
  dòng   9  TSSSTTS  =  70  'F'
  dòng  11  TTTTSTT  = 123  '{'
  ...
  dòng  45  TTTTTST  = 125  '}'
MESSAGE: POCTF{PIEMPAOSMHDLEGRT}
```

**Bước 3 — Khẳng định tính lô-gíc.** 
Có ba mảnh ghép xác nhận độ chuẩn xác của phương pháp này, loại trừ hoàn toàn yếu tố ăn may: 
(a) Trọn vẹn 22/22 nhóm 12 ký tự đều có dấu tab nằm ở đúng một vị trí cố định (bit đầu tiên của nhóm).
(b) Tổng số dòng dữ liệu mang thông điệp là 23, khớp hoàn hảo với công thức độ dài cờ: `POCTF{` (6 ký tự) + thân cờ (16 ký tự) + `}` (1 ký tự).
(c) Chuỗi 16 ký tự viết hoa ở phần thân hoàn toàn phù hợp với định dạng cờ truyền thống của giải. 
Những dấu cách thừa thãi ở phần đầu (5 dấu cách, riêng dòng đầu chỉ có 3 do dòng đó được bắt đầu sớm hơn) thực chất chỉ dùng để căn dòng và không hề mang thông tin.

**Bước 4 — Nộp cờ.**

```http
POST /challenges/invisible-text/submit
{"flag":"POCTF{PIEMPAOSMHDLEGRT}"}
```

Hệ thống ghi nhận:
```json
HTTP 200 :: {"correct":true,"message":"Correct."}
```

## Flag

```
POCTF{PIEMPAOSMHDLEGRT}
```

Máy chủ đã xác nhận tính chính xác và không trả về thêm bất kỳ chuỗi cờ nào khác. Ý tưởng cốt lõi của thử thách nằm ở chỗ: thông điệp bí mật không nằm ở output sinh ra khi chạy script, mà lại cư ngụ ở vùng **khoảng trắng cuối dòng** của tệp mã nguồn. Toàn bộ lớp vỏ bọc base64 + zlib + braille chỉ là một hệ thống mồi nhử tinh vi để đánh lạc hướng người chơi.

## Phục dựng (Reproduce)

```bash
python exploit.py files/invisible_text.py
```
