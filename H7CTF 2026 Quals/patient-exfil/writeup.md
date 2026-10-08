# Patient Exfil - Forensics (Medium)

**Flag:** `H7CTF{6787b86cc777f426b9c0}`
**File cung cấp:** `capture (2).pcap`, dung lượng 108.604 byte, mã băm sha256 `3ab17689659f80efadceea1adc2eea5e9bddfcc3254ad85e89c4c75ee20bbb76`

## Đề bài

Bối cảnh: Hệ thống giám sát ghi nhận một máy tính trong hệ thống gửi dữ liệu trái phép ra ngoài. Phần mềm mã độc này hoạt động với tần suất rất chậm - không gây ra bất kỳ cảnh báo nào trong suốt thời gian hoạt động.
Đề cung cấp một file mạng (`capture.pcap`) và yêu cầu trích xuất thông điệp mà mã độc truyền tải.
Định dạng của cờ thu được phải là `H7CTF{...}`.

## Phân tích

Phân tích file bằng công cụ `node ~/.qoder/skills/ctf-solve/scripts/triage.cjs`:

- Hồ sơ file: `magic = libpcap capture (mã hoá little-endian)`, giá trị entropy = 5.084/8. Kiểm tra chuỗi cho thấy có 87 chuỗi hiển thị được, nhưng không có dữ liệu khớp định dạng cờ (flag-pattern hits = 0).
  Kết luận: Flag không nằm trực tiếp trong file mạng. Dữ liệu đã bị mã hóa hoặc phân mảnh.
- Trích xuất thông tin qua `survey.py`: Ghi nhận 1260 gói tin (packet) được ghi nhận trong 148,31 giây, tất cả đều kết nối đến địa chỉ loopback `127.0.0.1`.
  Phân tích bao gồm 1080 gói TCP và 180 gói DNS. Không có gói ICMP hay các giao thức bất thường.
- Phân tích cổng đích: Cổng `8080` (có 534 gói), cổng `8443` (có 114 gói), phần còn lại là cổng truy cập ngẫu nhiên, mỗi cổng ghi nhận khoảng 4 gói.
- Phân tích giao thức HTTP:
  - Trên cổng 8080 chỉ có 5 loại truy vấn lặp lại (`/assets/app.js` 28 lần, `/api/health` 22 lần, `/index` 20 lần, `/` 19 lần).
  - Đáng chú ý là trên cổng 8443 có 19 lệnh `GET /api/v2/checkin` với header `User-Agent: telemetry-agent/1.4`. Đây xác nhận là tín hiệu giao tiếp (heartbeat) với máy chủ C2 của mã độc như được mô tả. Tuy nhiên, 100% phản hồi đều trả về mã `ok`, cùng định dạng độ dài 66 byte.
- Phân tích luồng DNS: Phát hiện 10 truy vấn (qname) duy nhất. Trong đó 7 truy vấn thông thường (`pool.ntp.org`, `updates.ubuntu.com`, `mirror.lab.local`, `grafana.internal.lab`, `logging.googleapis.com`, `api.weather.example`, `cdn.jsdelivr.net`).
  Xác nhận 3 truy vấn có cấu trúc chung từ một tên miền gốc:

```text
  00ja3ugvcgpm3doobx.sync.cdn-telemetry-lab.net.
  01mi4dmy3dg43tozru.sync.cdn-telemetry-lab.net.
  02gi3geoldgb6q.sync.cdn-telemetry-lab.net.
  ```

Nhận dạng: Đây là phương thức DNS tunneling. Tên miền giả mạo `cdn-telemetry-lab.net` mô phỏng dịch vụ telemetry. Các tiền tố `00/01/02` xác định chỉ mục (index) của dữ liệu phân mảnh. Phương thức sử dụng truy vấn DNS là kỹ thuật phổ biến để vượt qua giám sát bảo mật.

## Lời giải

**Bước 1 - Phân loại dữ liệu theo tên miền.**
Sử dụng bộ lọc rà quét toàn bộ truy vấn DNS, xác định các gói tin có `qname` kết thúc bằng `.sync.cdn-telemetry-lab.net.`.
Kết quả có 12 gói packet, với 3 giá trị thành phần. Đáng chú ý, mỗi gói dữ liệu được gửi thành một cặp (cơ chế dự phòng), kéo dài tới giây 47,02 của quá trình. Kỹ thuật này tuân thủ chiến lược truyền tin chậm, gửi 12 truy vấn trong 148 giây nên hệ thống không phát hiện bất thường.

**Bước 2 - Tách chỉ mục khỏi payload.**
Sử dụng biểu thức chính quy `^(\d{2})([a-z2-7]+)\.sync\.cdn-telemetry-lab\.net$`.
Phân tích payload (phần chữ cái sau số chỉ mục), ghi nhận chỉ sử dụng ký tự trong nhóm `[a-z2-7]`. Tập dữ liệu này thuộc định dạng base32.
Lưu ý: Cần xác định `00/01/02` là giá trị chỉ mục, không phải dữ liệu mã hoá. Nếu chưa loại bỏ số chỉ mục, kết quả sẽ không chính xác khi giải mã.

**Bước 3 - Khôi phục dữ liệu và giải mã base32.**

```python
# Kết hợp các khối theo mã số
blob = "".join(chunks[k] for k in sorted(chunks))     # Trình tự nạp: 00, 01, 02
# Bổ sung padding cho định dạng base32
pad  = blob.upper() + "=" * ((8 - len(blob) % 8) % 8)
# Giải mã
data = base64.b32decode(pad)
```

Kết quả quá trình:
```text
Dữ liệu khối (44 ký tự): ja3ugvcgpm3doobxmi4dmy3dg43tozrugi3geoldgb6q
Dữ liệu giải mã (27 byte): H7CTF{6787b86cc777f426b9c0}
```

**Bước 4 - Đối chiếu cấu trúc đầu ra.** Chuỗi base32 dài 44 ký tự và giải mã thành 27 byte; `44 % 8 = 4` phù hợp với khối base32 cuối ngắn hơn các khối trước. Chuỗi có prefix `H7CTF{` và kết thúc bằng `}`. Đây là các kiểm tra cấu trúc bổ sung; prefix và suffix riêng lẻ chưa chứng minh mọi fragment được ghép đúng. Dùng thứ tự fragment từ dữ liệu đã phân tích để tái hiện kết quả.

## Kết quả
Thực thi công cụ:

```bash
python _ctf/patient-exfil/exploit.py "C:/Users/Administrator/Downloads/capture (2).pcap"
```

Kết quả:
```text
[+] Trích xuất được 3 khối: ['00', '01', '02']
[+] Dữ liệu gốc định dạng base32 (chứa 44 ký tự): ja3ugvcgpm3doobxmi4dmy3dg43tozrugi3geoldgb6q
[+] Giải mã được 27 bytes -> b'H7CTF{6787b86cc777f426b9c0}'
[+] Cờ thu được: H7CTF{6787b86cc777f426b9c0}
```
