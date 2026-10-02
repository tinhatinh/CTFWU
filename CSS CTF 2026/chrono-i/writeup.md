# Chrono I — Crypto (Beginner)

**Flag:** `CSSCTF{every_second_hides_a_secret}`
**Tài nguyên:** Không có tệp đính kèm. Dữ kiện phân tích được cung cấp trực tiếp trong văn bản mô tả của đề bài.

## Đề bài

Hệ thống cung cấp một thông điệp văn bản (message) và một bản mã (ciphertext) tương ứng:

```text
Message:    2026-09-21 14:35:07 - "As always, The time is always the key to unlock it"
Ciphertext: ESUITO{gwfvb_xejqnf_nimgt_b_whhrlv}
```

Dựa trên cấu trúc chuẩn của hệ thống, cờ (flag) luôn bắt đầu bằng định dạng `CSSCTF{...}`. Theo đó, sáu ký tự đầu tiên của ciphertext chắc chắn ánh xạ tương ứng với chuỗi `CSSCTF`. Thông tin này là một manh mối (crib) tường minh, không yêu cầu các kỹ thuật phán đoán.

## Phân tích ban đầu

Thực hiện việc đối chiếu giá trị chênh lệch (shift) modulo 26 cho từng vị trí dựa trên manh mối đã có:

| Vị trí | Bản rõ (Plain) | Bản mã (Cipher) | Độ dịch (Shift) Modulo 26 |
|---|---|---|---|
| 1 | C | E | 2 |
| 2 | S | U | 0 |
| 3 | S | I | 2 |
| 4 | C | T | 6 |
| 5 | T | O | 0 |
| 6 | F | O | 9 |

Dãy độ dịch thu được là `2 0 2 6 0 9`. Đối chiếu chuỗi số này với dữ liệu đầu vào, có thể nhận thấy nó trùng khớp hoàn toàn với sáu chữ số đầu tiên của mốc thời gian trong message: `20260921143507` (loại bỏ các ký tự phân cách từ `2026-09-21 14:35:07`). Câu hướng dẫn "the time is always the key" có giá trị tham chiếu trực tiếp: khóa giải mã chính là chuỗi ký tự số của mốc thời gian, áp dụng trên hệ mã Vigenère dạng số (Mật mã Gronsfeld) với chu kỳ là 14.

## Chuỗi khai thác

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

**Bước 4 - Khâu tự kiểm chứng (Verification).** 
Quá trình thực thi có tính hai chiều đồng nhất: nếu thực hiện mã hóa lại bản rõ bằng chính khóa đó, hệ thống sẽ trả về đúng bản mã gốc ban đầu. Ngoài ra, phần thân của bản rõ tuân thủ chặt chẽ cấu trúc `[a-z0-9_]*`. Để khẳng định độ tin cậy của mã kịch bản, việc đưa vào các lỗi nhân tạo (như thay đổi một chữ cái thành in hoa, sửa đổi thông số giờ thành `15:35:07`, hoặc thay đổi manh mối `ESUITO` thành `XSUITO`) đều kích hoạt cơ chế báo lỗi của kịch bản, xác nhận rằng quy trình không hoạt động dựa trên cơ chế tự khớp mù quáng.

## Flag

Quá trình thực thi mã kịch bản tự động hóa:

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
