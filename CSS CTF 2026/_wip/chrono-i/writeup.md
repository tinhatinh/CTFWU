# Chrono I — Crypto (Beginner)

**Flag:** `CSSCTF{every_second_hides_a_secret}` · **Files:** không có artifact, dữ kiện nằm trong thẻ đề

## Đề bài

Đề cho một message và một ciphertext:

```text
Message:    2026-09-21 14:35:07 - "As always, The time is always the key to unlock it"
Ciphertext: ESUITO{gwfvb_xejqnf_nimgt_b_whhrlv}
```

Cờ có dạng `CSSCTF{...}`, nên sáu ký tự đầu của ciphertext tương ứng với `CSSCTF`.
Đó là crib sẵn, không cần đoán.

## Phân tích ban đầu

So crib theo từng vị trí:

| vị trí | plain | cipher | shift mod 26 |
|---|---|---|---|
| 1 | C | E | 2 |
| 2 | S | U | 0 |
| 3 | S | I | 2 |
| 4 | C | T | 6 |
| 5 | T | O | 0 |
| 6 | F | O | 9 |

Dãy shift `2 0 2 6 0 9` chính là sáu chữ số đầu của `20260921143507`, tức cái
message bỏ dấu phân cách: `2026-09-21 14:35:07`. Đề nói "the time is always the key"
là nói đúng nghĩa đen: key là mốc thời gian, mã là Vigenère số (Gronsfeld), chu kỳ 14.

## Các hướng đã loại

Trước khi chốt đã loại các kênh sau (log đầy đủ ở `notes.md`):

1. **Thay thế một bảng chữ**: chữ `S` ở vị trí 2 và 3 cho ra `U` rồi `I`, một bảng chữ
   không làm được. Loại.
2. **Hoán vị thuần**: đa thức của `ESUITO` khác hẳn `CSSCTF`, transpose không đổi đa thức. Loại.
3. **Beaufort và variant**: với cùng crib, Beaufort đòi key `6 10 12 10 12 19`, variant đòi
   `24 0 24 20 0 17`; không dãy nào đọc ra dữ kiện thời gian. Loại.
4. **Các cách sinh key thời gian khác**: epoch giây (UTC, UTC+7, AEST, EDT), tổng chữ số
   lũy tiến, ghép từng cặp chữ số, cơ số 26, hex, từng trường ngày-giờ nhân chỉ số.
   95 nguồn được thử, chỉ dãy chữ số thô của `20260921...` khớp crib. Loại hết.

## Chuỗi khai thác

**Bước 1 - Lấy key từ message.** Bỏ mọi ký tự không phải số:

```python
key = re.sub(r"\D", "", "2026-09-21 14:35:07")   # '20260921143507'
```

**Bước 2 - Xác nhận crib.** Dịch sáu ký tự đầu của ciphertext bằng sáu chữ số đầu:

```
CSSCTF -> ESUITO : shift [2, 0, 2, 6, 0, 9]   # khop key[0:6]
```

**Bước 3 - Giai ma phần thân, bộ đếm chỉ tiến trên chữ cái.** Nếu đếm cả `{` và `_`
thì kết quả là rác, nên key chạy theo thứ tự chữ cái còn ký tự giữ nguyên:

```python
for ch in text:
    if not ch.isalpha():
        out.append(ch)          # giu nguyên '{', '}', '_'
        continue
    k = int(key[i % len(key)]); i += 1
    base = 65 if ch.isupper() else 97
    out.append(chr((ord(ch) - base - k) % 26 + base))
```

Ra `CSSCTF{every_second_hides_a_secret}`, đúng câu gợi ý của đề.

**Bước 4 - Kiểm chứng.** Hai chiều đều khớp: mã hoá lại bản rõ bằng cùng key trả về
đúng ciphertext gốc, và phần thân thuần `[a-z0-9_]*`. Thử phá ba chỗ (đổi một chữ cái
cuối thành in hoa, sửa giờ trong message thành `15:35:07`, sửa `ESUITO` thành `XSUITO`)
thì script dừng ở bước kiểm tra tương ứng, không còn là vòng lặp tự khẳng định.

## Flag

```
$ python exploit.py
1) key = chu so cua message : 20260921143507 (14 chu so)
2) crib CSSCTF -> ESUITO : shift [2, 0, 2, 6, 0, 9]
   khop 100% so chu cai dau cua key -> Gronsfeld voi key = 20260921143507
3) giai ma toan bo : CSSCTF{every_second_hides_a_secret}
4) phep giai la nghich dao dung cua phep ma hoa
5) du dinh dang CSSCTF{...}, than co la snake_case

FLAG: CSSCTF{every_second_hides_a_secret}
```

## Reproduce

```bash
python exploit.py
```
