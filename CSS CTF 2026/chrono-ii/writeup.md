# Chrono II - Crypto (Intermediate)

**Flag:** `CSSCTF{th3_cl0ck_r3m3mb3rs_3very_s3c0nd}`
**Tài nguyên:** Không có file đính kèm. Dữ liệu cần thiết được trích xuất trực tiếp từ một dịch vụ trực tuyến đang vận hành.

## Đề bài

Đề cung cấp một dịch vụ tại địa chỉ `http://34.116.80.78:8001`, kèm theo thông tin rằng đoạn dữ liệu giao tiếp bị đánh chặn có tính chất "thay đổi liên tục". Nhiệm vụ của chuyên viên phân tích là thu thập các bản mã từ dịch vụ này và tái lập lại plaintext gốc.
Bài toán này là phần tiếp theo của "Chrono I". Ở phần trước, hệ mã được xác định là Vigenère dạng số (mật mã Gronsfeld chu kỳ 14) với khóa (key) tĩnh lấy từ mốc thời gian. Trong phiên bản nâng cấp này (Chrono II), mô hình mật mã được giữ nguyên nhưng khóa mã hóa được thiết kế thành một luồng (keystream) thay đổi động dựa trên sự tiến triển của thời gian (đồng hồ).

## Phân tích ban đầu

Giao diện dịch vụ hoạt động như một hệ thống trạm thu tín hiệu, hiển thị các cổng truy cập. Cổng `/api/feed` phản hồi một danh sách gồm 60 bản ghi có cấu trúc `{timestamp, ciphertext}` (tương đương tốc độ cập nhật một bản ghi mỗi giây). Đường dẫn `/capture.json` lưu trữ tĩnh một lô dữ liệu 60 giây đã được trích xuất.

Qua việc kiểm tra ngẫu nhiên 60 dòng dữ liệu, hai đặc điểm kỹ thuật chính được xác định:

- Ciphertext duy trì một cấu trúc định dạng cố định: `UUUUUU{lll_lllll_lllllllll_lllll_llllll}`. Các ký tự số luân phiên hiển thị tại cùng một hệ thống vị trí ở tất cả các dòng. Giả định rằng nếu bản rõ bị thay đổi liên tục, xác suất duy trì một khuôn mẫu cấu trúc cứng nhắc như vậy là bằng không. Suy ra: Plaintext là một hằng số tĩnh, chỉ có khóa mã hóa là biến đổi tuyến tính theo từng giây.
- Các ký tự phân cách như `_`, `{`, và `}` xuất hiện nguyên vẹn và không thay đổi vị trí. Điều này chứng tỏ luồng mã hóa đã được cấu hình để bỏ qua các ký tự này.

Hệ thống xử lý phân tách thành ba miền dữ liệu: Chữ in hoa (modulo 26), chữ in thường (modulo 26), và chữ số (modulo 10).

Vì bản rõ là một giá trị tĩnh và định dạng cờ (flag) là một chuẩn đã biết (`CSSCTF{...}`), sáu ký tự đầu tiên của tất cả các dòng bản mã luôn là kết quả mã hóa của tiền tố `CSSCTF`. Thông tin này đóng vai trò là dữ liệu đối chiếu (crib), giúp phơi bày chính xác 6 ký tự của keystream trên mỗi giây thu thập được.

## Chuỗi khai thác

**Bước 1 - Xây dựng công cụ thu thập luồng dữ liệu (Capture Windows).** 
Các công cụ mạng tiêu chuẩn như `curl` hay thư viện socket của Python không thể thiết lập kết nối tới máy chủ (các gói tin SYN bị từ chối/drop, dẫn đến timeout ở các mốc 8, 12, 30 giây, trong khi kết nối tới các máy chủ thông thường như `example.com:80` lại thành công ngay lập tức). Tuy nhiên, kết nối thông qua trình duyệt web lại khả thi. Do đó, phương pháp tiếp cận tối ưu là trích xuất dữ liệu trực tiếp từ mã nguồn trang web: File `app.js` lưu trữ kết quả fetch trong một biến có tên `capture`.

```javascript
capture.map(r => r.timestamp + ' ' + r.ciphertext).join('\n')
```

Việc cố gắng gọi lệnh `fetch('/api/feed')` từ bảng điều khiển của trang web sẽ bị chặn bởi chính sách bảo mật CSP (Content Security Policy). Điều hướng trực tiếp tới `/capture.json` cũng trả về lỗi `ERR_FAILED`. Trích xuất trực tiếp giá trị của biến `capture` trong bộ nhớ của ứng dụng là phương pháp thu thập dữ liệu an toàn và hiệu quả nhất.

**Bước 2 - Xác định tính chu kỳ của Keystream.** 
phân tích chéo hai khung thời gian thu thập: Cửa sổ A (06:38:27 - 06:39:26) và Cửa sổ B (07:00:51 - 07:01:50). Kết quả cho thấy có 43 bản mã trùng lặp hoàn toàn giữa hai khung thời gian. Độ lệch thời gian (delta) của các bản mã này chỉ rơi vào hai giá trị cố định: 1309 giây và 1386 giây.

```text
1309 = 17 * 77
1386 = 18 * 77
Ước số chung lớn nhất: gcd(1309, 1386) = 77
```

Dựa trên kết quả này, hàm vị trí keystream có tính tuần hoàn: `o(t + 77) = o(t)`, xác nhận chu kỳ của hệ thống là 77. Con số 77 cũng phù hợp với dữ kiện thống kê: Trong một cửa sổ thu thập 60 giây, sẽ có 17 dòng không có dữ liệu tiếp nối tương ứng, bởi `77 - 60 = 17` khoảng trống (offset).

**Bước 3 - Tính toán bước nhảy của hàm tịnh tiến theo thời gian.** 
Đối với mọi cặp dòng dữ liệu mà chuỗi 6 ký tự của chúng có thể xếp chồng lên nhau với một độ dịch (shift offset) `d` nhất định (trong khoảng 1 đến 5), chạy mô hình hồi quy tuyến tính theo công thức `d == (g * dt) mod 77`, với biến `g` chạy từ 1 đến 76.

```text
Bước nhảy tối ưu g = (43, 460)   # Kết quả: 460/965 cặp dữ liệu khớp (Trong khi nhiễu ngẫu nhiên chỉ đạt xấp xỉ 12.5)
```

Kết luận hàm vị trí của keystream: `o(T) = (43 * T) mod 77`.

**Bước 4 - Tái lập Keystream toàn phần.** 
Mỗi dòng dữ liệu cung cấp 6 giá trị (symbol) cho keystream tại các vị trí từ `o(T)` đến `o(T)+5`. Sử dụng tập dữ liệu 120 dòng thu thập từ hai cửa sổ, hệ thống có khả năng phủ kín toàn bộ 77 vị trí mà không ghi nhận bất kỳ sự xung đột nào.

```python
K = {}
for T, ct in rows:
    base = (43 * T) % 77
    for j, (a, b) in enumerate(zip(ct[:6], "CSSCTF")):
        K[(base + j) % 77] = (ord(a) - 65 - (ord(b) - 65)) % 26
# Quá trình hoàn tất: Khôi phục 77/77 symbol, tỷ lệ xung đột bằng 0
```

**Bước 5 - Thiết kế thuật toán giải mã.** 
Điểm mấu chốt của thuật toán: Chỉ số con trỏ của khóa (key index) chỉ tiến lên khi hệ thống xử lý một ký tự thực sự bị mã hóa. Các ký tự như `_`, `{`, và `}` sẽ được chuyển tiếp thẳng ra bản rõ mà không tiêu tốn bất kỳ một ký tự nào từ keystream.

```python
def dec(T, ct):
    i = 0
    o = (43 * T) % 77
    out = []
    for ch in ct:
        if ch in "_{}":
            out.append(ch)
            continue          # Bỏ qua, không tịnh tiến con trỏ i
        base, m = (65,26) if ch.isupper() else (97,26) if ch.islower() else (48,10)
        out.append(chr(base + (ord(ch) - base - K[(o+i) % 77]) % m))
        i += 1
    return "".join(out)
```

Toàn bộ 120 bản mã đều giải mã thành công và hội tụ về một bản rõ duy nhất.

**Bước 6 - Xác thực mô hình trên tập dữ liệu độc lập (Validation).** 
Để đảm bảo tính toàn vẹn của mô hình giải mã, một bộ dữ liệu mới (chưa qua huấn luyện) từ cửa sổ thời gian 07:09:46 - 07:10:45 (gồm 60 dòng) được thu thập. Áp dụng keystream đã tái lập từ bước trước để giải mã:

```text
Tập huấn luyện (train rows) = 120  | Tập kiểm thử (held-out rows) = 60
Kết quả giải mã thành công: n= 60/60 -> CSSCTF{th3_cl0ck_r3m3mb3rs_3very_s3c0nd}
```

Kết quả không phát sinh bất kỳ một độ lệch nào. Chu kỳ 77 cũng được chứng minh thêm một lần nữa qua việc đối chiếu trực quan: Dòng dữ liệu `HIWLWH{bp6_...}` tại mốc 06:38:58 xuất hiện lại một cách trùng khớp tại mốc 07:09:46. Khoảng thời gian chênh lệch là chính xác 1848 giây, tương đương với hệ số nhân `24 x 77` giây.

## Flag

Chạy script giải mã:

```bash
python exploit.py analysis/rows.txt analysis/feed2.txt
```

```text
[*] 120 rows, 1 distinct plaintexts, best has 120
[flag] CSSCTF{th3_cl0ck_r3m3mb3rs_3very_s3c0nd}
```

Kết quả:
```text
CSSCTF{th3_cl0ck_r3m3mb3rs_3very_s3c0nd}
```
