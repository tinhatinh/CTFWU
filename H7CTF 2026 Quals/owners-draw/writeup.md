# Owner's Draw — Crypto (Medium)

**Flag:** `H7CTF{786dff67-75cd-4d4e-8b74-55edb1353aad}`
**Máy chủ mục tiêu:** `https://web-b39cfff63c4c78b9.web.h7tex.com`

## Đề bài

Hệ thống thanh toán OrionPay sử dụng một cổng webhook nhận thông báo, hoạt động nghiêm ngặt theo phương thức xác thực chữ ký số (signature) của yêu cầu gửi lên. 
Hệ thống cung cấp một cơ chế chi trả (payout) yêu cầu quyền hạn tài khoản admin. Thông tin được cung cấp gồm một phiếu thanh toán (slip) hợp lệ (với nội dung và chữ ký số đính kèm), yêu cầu thí sinh tự phân tích để vượt qua cơ chế xác thực và nhận quyền thanh toán đặc biệt.

## Phân tích ban đầu

Lệnh kiểm tra:
```text
Gọi GET /sample -> Trả về thân nội dung body : event=payment.succeeded&amount=500&currency=usd&customer=cus_9f2a&role=guest
                   Kèm chữ ký X-Signature     : 14d500d5...d929f6a7
                   Hệ thức ký signing         : Bằng thuật toán SHA256(secret || body)
```

Gửi lại toàn bộ payload slip gốc vào cổng `POST /webhook`, kết quả trả về `{"ok": true, "role": "guest", "note": "no owner payout"}`. 
Thông tin quan trọng: Hệ thống xác thực chữ ký TRƯỚC KHI xử lý tham số body, và biến `role` là tham số quyết định quyền kích hoạt chi trả payout.

Điểm yếu cấu trúc hệ thống nằm ở công thức tạo mã ký: `SHA256(secret || body)`. Đây là cơ chế tạo Message Authentication Code (MAC) dựa trên nối chuỗi (prefix-based MAC) của hàm băm Merkle - Damgård. Hạn chế của thuật toán là kết quả băm được trả ra công khai thực chất là trạng thái nội bộ (internal state) của chu trình SHA-256 sau khi xử lý thông điệp đã nối thêm dữ liệu đệm (padding). 
Hệ quả: Nếu có được một mã hash hợp lệ và chiều dài thông điệp ban đầu, có thể tiếp tục chu kỳ tạo hash (Length Extension Attack). Việc bổ sung chuỗi văn bản sẽ tạo ra một hàm băm mới hợp lệ cho thông điệp `body || padding || extra`. Không cần biết giá trị khoá bí mật `secret` là gì.

Thử nghiệm với API `/v2/webhook` (sử dụng HMAC-SHA256), máy chủ trả về lỗi 401 khi nhận chữ ký giả mạo bằng SHA-256 LEA. API phiên bản v2 đã khắc phục lỗ hổng bảo mật này. Thử thách yêu cầu khai thác 1 lỗ hổng trên cổng v1.

## Quá trình khai thác

### Bước 1: Tái tạo thuật toán SHA-256 bằng Python

Thư viện `hashlib` mặc định không hỗ trợ API khởi tạo hàm băm từ một digest có sẵn, do đó cần tự triển khai hàm `compress(state, block)` (bao gồm chu kỳ message schedule và 64 chu kỳ tính toán SHA-256). Việc lập trình cần tính chính xác cao, vì lỗi tham số sẽ khiến hệ thống không thể hoạt động đúng cách.

```python
def compress(h, block):
    w = list(struct.unpack(">16I", block))
    for i in range(16, 64):
        s0 = ror(w[i-15],7) ^ ror(w[i-15],18) ^ (w[i-15] >> 3)
        s1 = ror(w[i-2],17) ^ ror(w[i-2],19) ^ (w[i-2] >> 10)
        w.append((w[i-16] + s0 + w[i-7] + s1) & M)
    a, b, c, d, e, f, g, hh = h
    for i in range(64):
        S1 = ror(e,6) ^ ror(e,11) ^ ror(e,25); ch = (e & f) ^ (~e & g)
        t1 = (hh + S1 + ch + K[i] + w[i]) & M
        S0 = ror(a,2) ^ ror(a,13) ^ ror(a,22); mj = (a&b) ^ (a&c) ^ (b&c)
        t2 = (S0 + mj) & M
        hh, g, f, e, d, c, b, a = g, f, e, (d+t1)&M, c, b, a, (t1+t2)&M
    return tuple((x + y) & M for x, y in zip(h, (a,b,c,d,e,f,g,hh)))
```

### Bước 2: Ghép chuỗi padding (Splice)

Thông điệp khởi tạo là `secret || body`, chiều dài toàn cục `L = len(secret) + 76`. (Thông tin thiếu sót là chiều dài `len(secret)`). 
Chuỗi dữ liệu đệm (padding) của SHA-256 có định dạng `0x80 || 00*k || be64(8L)`. Cần phải bao gồm phần đệm đó vào nội dung body nối thêm:

```python
pad  = b"\x80" + b"\x00" * ((55 - L) % 64) + struct.pack(">Q", L * 8)
new  = pad + b"&role=owner"
tag  = struct.unpack(">8I", bytes.fromhex(sig))      # Trạng thái hash sau khi padding
# Tiến hành tiếp tục thực thi hàm (compress) từ state này và bao gồm dữ liệu mới.
```

### Bước 3: Sử dụng Oracle để xác định chiều dài khóa

```python
for s_len in range(65):
    ext, forged = len_extend(tag, s_len + len(body), b"&role=owner")
    # Tấn công: POST /webhook  body=body+ext  X-Signature=forged
```

Máy chủ liên tục trả về lỗi 401, cho đến khi xác định được kết quả hợp lệ tại `s_len = 15`:

```text
[+] Xác định được chiều dài secret = 15   kèm đuôi body tail=b'\x00\x00\x00\x02\xd8&role=owner'
[+] Gõ /webhook -> Nhận mã 200 {"ok": true, "payout": "authorized", "flag": "H7CTF{786dff67-75cd-4d4e-8b74-55edb1353aad}"}
```

Kiểm tra đối chiếu: 8 byte thông tin chiều dài trong phần splice padding là `0x2d8` = 728 bit = 91 byte = 15 (secret) + 76 (body) - Thông số này là minh chứng rõ ràng cho việc tính toán thành công `len(secret)`. Điều này khẳng định thuật toán Length Extension Attack hoạt động hoàn toàn chính xác.

## Flag
```bash
$ python solve_draw.py
[+] FLAG: H7CTF{786dff67-75cd-4d4e-8b74-55edb1353aad}
```
