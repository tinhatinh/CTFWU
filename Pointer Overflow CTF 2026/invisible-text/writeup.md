# invisible-text — STEG (200 pts)

**Flag:** `POCTF{PIEMPAOSMHDLEGRT}` · **Files:** `invisible_text.py`, 4245 B, sha256 `f027442b37a521f4a775ec56d37336df446d83e7acd641042e28af030f745320`

## Đề bài

Tác giả nói trong file có một thông điệp bí mật, và "nhìn đúng chỗ" thì sẽ thấy. Đề cho duy nhất `invisible_text.py` sinh riêng cho team (server phát tệp dưới tên `invisible_text_612.py`), không có tệp nhị phân, không có dịch vụ từ xa. Việc phải làm: đọc ra thông điệp cất trong chính file nguồn rồi nộp nó.

## Phân tích ban đầu

File là Python thuần, 4245 byte, 81 dòng, UTF-8. Kiểm kê byte cho thấy cả file chỉ có một ký tự ngoài dải ASCII, là dấu `—` trong một comment. Không có Zero Width Space, không có BOM, không có NBSP, không có ký tự đồng dạng.

Điểm bất thường duy nhất còn lại: **47/81 dòng kết thúc bằng whitespace**. Cụ thể:

```
dòng 1   SSSTSTSSSS        (10 ký tự)
dòng 2   T                 (1 tab)
dòng 3   SSSSSTSSTTTT      (12 ký tự)
dòng 4   T
dòng 5   SSSSSTSSSSTT
...
dòng 45  SSSSSTTTTTST
dòng 46  T
dòng 47  SS                (2 ký tự)
```

Dòng lẻ dài 12 ký tự (riêng dòng đầu chỉ 10), dòng chẵn chỉ đúng một tab. Câu "look closely" trong đề trỏ thẳng vào chuỗi này.

Nội dung hiển nhiên của file: `diary_reader.py` nối 46 chunk base64 thành một xâu, `b64decode` rồi `zlib.decompress`, in kết quả ra. Chạy thử (phải ghi ra tệp UTF-8 vì console Windows là cp1252, `print` sẽ raise `UnicodeEncodeError`) thì thấy 2145 ký tự braille, 33 dòng.

## Các hướng đã loại

Log đầy đủ ở `notes.md`. Tóm tắt:

1. **Unicode vô hình cất trong chuỗi**: đếm tần suất U+200B-U+200F, U+FEFF, U+00A0 -> không bắt được ký tự nào. Loại.
2. **Payload base64 + zlib là nơi cất flag**: giải mã ra tranh braille, không ra chữ. Loại.
3. **Braille giấu dữ liệu ở số chấm từng ô**: histogram cho 115 ô tròn 8 chấm (255), 85 ô 251, 79 ô 253 -> đó là vùng tô đặc của một bức tranh, không phải mã. Loại.
4. **Whitespace cuối dòng là nhị phân 8 bit nối liền**: ghép 299 ký tự rồi cắt theo 8 bit, thử cả `space=0/tab=1`, `space=1/tab=0` và đảo ngược bit -> bốn biến thể đều ra byte rác, không có `POCTF`. Loại.
5. **Ngôn ngữ Whitespace (esolang)**: Whitespace cần LF để kết thúc một số, ở đây trong mỗi nhóm không có LF và độ dài nhóm cố định 12. Loại.

## Chuỗi khai thác

**Bước 1 — Nhận ra độ dài nhóm cố định.** Mỗi dòng dữ liệu có 12 ký tự whitespace, trong đó vị trí thứ sáu **luôn luôn là tab**. Đó là dấu hiệu của mô hình 7 bit: năm space đầu là padding căn cột, bảy ký tự cuối là mã.

**Bước 2 — Cắt bảy ký tự cuối, `tab = 1`, `space = 0`.** Ký tự ASCII in được luôn có MSB bằng 1, nên nhóm 7 bit bắt đầu bằng 1 chính là vùng chứa tên của nó - đây là điểm định vị:

```python
for line in src.split("\n"):
    tail = line[len(line.rstrip()):]
    if len(tail) < 7:
        continue
    bits = tail[-7:].replace(" ", "0").replace("\t", "1")
    flag += chr(int(bits, 2))
```

Output thật:

```
  line   1  TSTSSSS  =  80  'P'
  line   3  TSSTTTT  =  79  'O'
  line   5  TSSSSTT  =  67  'C'
  line   7  TSTSTSS  =  84  'T'
  line   9  TSSSTTS  =  70  'F'
  line  11  TTTTSTT  = 123  '{'
  ...
  line  45  TTTTTST  = 125  '}'
MESSAGE: POCTF{PIEMPAOSMHDLEGRT}
```

**Bước 3 — Kiểm chứng không trùng hợp.** Ba mối khớp: (a) 22/22 nhóm 12 ký tự đều có tab ở đúng một vị trí (bit đầu của nhóm), (b) số dòng dữ liệu = 23 = độ dài `POCTF{` + 16 + `}`, (c) thân flag 16 ký tự hoa khớp định dạng flag của event. Phần space thừa phía trước (5 space, riêng dòng 1 còn 3 vì dòng đó bắt đầu sớm hơn) chỉ là căn cột, không mang thông tin.

**Bước 4 — Nộp.**

```
POST /challenges/invisible-text/submit
{"flag":"POCTF{PIEMPAOSMHDLEGRT}"}
```

```
HTTP 200 :: {"correct":true,"message":"Correct."}
```

## Flag

```
POCTF{PIEMPAOSMHDLEGRT}
```

Server xác nhận đúng và không trả về xâu flag nào khác, nên đây là toàn bộ giá trị thu được. Ý tưởng quyết định: thông điệp nằm ở **whitespace cuối dòng** của file nguồn, không nằm ở output của script; và toàn bộ lớp base64 + zlib + braille chỉ là mồi hướng.

## Reproduce

```bash
python exploit.py files/invisible_text.py
```
