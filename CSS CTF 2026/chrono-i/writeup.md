# Chrono I - Crypto (Beginner)

**Flag:** `CSSCTF{every_second_hides_a_secret}`
**Tài nguyên:** Không có file đính kèm. Dữ kiện phân tích được cung cấp trực tiếp trong văn bản mô tả của đề bài.

## Đề bài

Đề cung cấp một thông điệp văn bản (message) và một ciphertext tương ứng:

```text
Message:    2026-09-21 14:35:07 - "As always, The time is always the key to unlock it"
Ciphertext: ESUITO{gwfvb_xejqnf_nimgt_b_whhrlv}
```
Đề cho format `CSSCTF{...}`. Dùng sáu chữ `CSSCTF` làm known-plaintext crib để tính các độ dịch ban đầu.

## Phân tích

đối chiếu giá trị chênh lệch (shift) modulo 26 cho từng vị trí dựa trên manh mối đã có:

| Vị trí | Bản rõ (Plain) | Bản mã (Cipher) | Độ dịch (Shift) Modulo 26 |
|---|---|---|---|
| 1 | C | E | 2 |
| 2 | S | U | 0 |
| 3 | S | I | 2 |
| 4 | C | T | 6 |
| 5 | T | O | 0 |
| 6 | F | O | 9 |

Dãy độ dịch thu được là `2 0 2 6 0 9`. Đối chiếu chuỗi số này với dữ liệu đầu vào, có thể nhận thấy nó trùng khớp với sáu chữ số đầu tiên của mốc thời gian trong message: `20260921143507` (loại bỏ các ký tự phân cách từ `2026-09-21 14:35:07`). Câu hướng dẫn "the time is always the key" có giá trị tham chiếu trực tiếp: khóa giải mã chính là chuỗi ký tự số của mốc thời gian, áp dụng trên hệ mã Vigenère dạng số (Mật mã Gronsfeld) với chu kỳ là 14.

## Lời giải

**Bước 1 - Trích xuất khóa (Key) từ thông điệp.**
Sử dụng biểu thức chính quy để loại bỏ tất cả các ký tự phi số, giữ lại chuỗi số thuần túy làm khóa:

```python
key = re.sub(r"\D", "", "2026-09-21 14:35:07")   # Kết quả: '20260921143507'
```

**Bước 2 - Xác thực bằng manh mối ban đầu (Crib).**
Thực hiện mã hóa thử sáu ký tự đầu tiên của bản rõ bằng sáu chữ số đầu của khóa để kiểm chứng mô hình:

```text
CSSCTF -> ESUITO : Áp dụng độ dịch (shift) [2, 0, 2, 6, 0, 9]   # Khớp hoàn toàn với key[0:6]
```

**Bước 3 - Giải mã toàn bộ bản mã.**
Thiết kế logic giải mã: Hệ số đếm (index) của khóa chỉ tiến lên khi gặp các ký tự thuộc bảng chữ cái. Các ký tự đặc biệt như `{`, `}`, và `_` sẽ được bỏ qua trong bước tính độ dịch và giữ nguyên trong kết quả cuối cùng. Việc áp dụng sai bộ đếm (bao gồm cả ký tự đặc biệt) sẽ dẫn đến giải mã lỗi.

```python
for ch in text:
    if not ch.isalpha():
        out.append(ch)          # Bảo lưu nguyên vẹn các ký tự '{', '}', '_'
        continue
    k = int(key[i % len(key)])
    i += 1
    base = 65 if ch.isupper() else 97
    out.append(chr((ord(ch) - base - k) % 26 + base))
```

Chạy toàn bộ bản mã qua kịch bản, hệ thống xuất ra chuỗi: `CSSCTF{every_second_hides_a_secret}`. Chuỗi kết quả có ngữ nghĩa hoàn chỉnh, phù hợp với gợi ý tổng thể của thử thách.

Mã hóa lại plaintext bằng khóa đã tìm được cho đúng ciphertext ban đầu. Plaintext cũng khớp mẫu `[a-z0-9_]*` ở phần thân. Các ca thay đổi chữ hoa, giờ thành `15:35:07` hoặc crib `ESUITO` thành `XSUITO` được dùng để kiểm tra các điều kiện của script.

## Kết quả

Chạy script:

```bash
$ python exploit.py
1) key = chu so cua message : 20260921143507 (14 chu so)
2) crib CSSCTF -> ESUITO : shift [2, 0, 2, 6, 0, 9]
   khop 100% so chu cai dau cua key -> Gronsfeld voi key = 20260921143507
3) giai ma toan bo : CSSCTF{every_second_hides_a_secret}
4) phep giai la nghich dao dung cua phep ma hoa
5) du dinh dang CSSCTF{...}, than co la snake_case

FLAG: CSSCTF{every_second_hides_a_secret}
```

Kết quả:
```text
CSSCTF{every_second_hides_a_secret}
```
