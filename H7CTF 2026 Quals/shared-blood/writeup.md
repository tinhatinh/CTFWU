# Shared Blood - Crypto (Medium)

**Flag:** `H7CTF{a727587f-67d5-4246-b7c3-e57798659fac}`
**Máy chủ mục tiêu:** `https://web-bd09e5c5af420bbc.web.h7tex.com`

## Đề bài

Hệ thống camera VoltEye phát hành loạt thiết bị có cấu trúc bảo mật thấp, các thiết bị này được cấu hình đồng bộ. Mục tiêu là cần truy cập vào bảng điều khiển (console) của thiết bị.
Hệ thống thiếu tài liệu kỹ thuật, cung cấp 3 endpoint API để phân tích.

## Phân tích

Gửi lệnh truy vấn:
```text
Cổng GET /          -> Trả về lỗi: "Device fleet console. Admin bootstrap required." (Bảng điều khiển hạm đội. Yêu cầu mã khởi động quyền Admin).
                       Gợi ý 3 ngách: GET /fleet · GET /captured · POST /admin với payload {"token":"..."}
Cổng GET /fleet     -> Hiển thị thông tin hệ thống: {"e": 65537, "devices": [{"serial","n"} x30]}    (Sử dụng số hiệu modulus n cỡ 1023/1024 bit).
Cổng GET /captured  -> Lấy được thông điệp: {"note": "RSA/PKCS1v1.5, encrypted to the device cert",
                       "serial": "VE-C1E90650", "e": 65537, "ciphertext": <128 byte mã hex>}
```

Đề không cung cấp decryption oracle. Lời giải kiểm tra quan hệ giữa các modulus trong fleet key dump bằng GCD, thay vì factor modulus 1024-bit trực tiếp. Một cặp có GCD khác 1 có thể làm lộ prime dùng chung.

## Lời giải

### Bước 1: Phân tích GCD toàn hệ thống

```python
hits = [(a, b, math.gcd(an, bn))
        for i,(a,an) in enumerate(devs) for j,(b,bn) in enumerate(devs)
        if j > i and math.gcd(an, bn) > 1]
```

Duyệt tổ hợp C(30,2) = 435 cặp, phát hiện một va chạm duy nhất. Va chạm này liên quan trực tiếp đến thiết bị mục tiêu:

```text
[*] Phát hiện số cặp chia sẻ chung nguyên tố (shared-prime pairs): 1 cặp
    Máy VE-C1E90650 trùng lặp với Máy VE-23795497   -> Phân tách được ước chung gcd = nguyên tố 512-bit
```

### Bước 2: Từ thừa số chung, tính toán chìa khoá riêng tư (Private Key)

```text
Tính p = 792448642746425956602219402032306819204...44085721   (Độ dài 512 bit)
Chia n cho p lấy q = n // p                                           (512 bit)
Xác thực: p * q == n  ->  True
Công thức tạo khoá: phi = (p-1)*(q-1);  d = pow(65537, -1, phi);  m = pow(ct, d, n)
```

### Bước 3: Phân tích chuẩn PKCS#1 v1.5

Kết quả giải mã trả về 128 byte:

```text
0002 81c2c61e...415d5d 00 766c745f343832353238633831343263613962316665353763666533
└loại 2┘└── 97 byte đệm (padding), không có byte 0 ──┘└Mốc chặn┘└──── Lõi thông điệp: "vlt_482528c8142ca9b1fe57cfe3" ────┘
```

Định dạng chuẩn `00 02 PS 00 M` chứng minh chìa khóa tính toán là chính xác (sai số ở biến `d` sẽ tạo ra chuỗi vô nghĩa, không đúng định dạng `00 02`). Chuỗi token `vlt_<hex>` phù hợp với định dạng yêu cầu ở bảng quản trị.

### Bước 4: Thực thi

```bash
$ python solve_blood.py
[+] Trích xuất token = 'vlt_482528c8142ca9b1fe57cfe3'
[*] Thực thi POST /admin -> Phản hồi 200 {"authed": true, "flag": "H7CTF{a727587f-67d5-4246-b7c3-e57798659fac}"}
[+] FLAG: H7CTF{a727587f-67d5-4246-b7c3-e57798659fac}
```

## Kết quả
```text
H7CTF{a727587f-67d5-4246-b7c3-e57798659fac}
```
