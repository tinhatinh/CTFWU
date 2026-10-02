# Shared Blood — Crypto (Medium)

**Flag:** `H7CTF{a727587f-67d5-4246-b7c3-e57798659fac}`
**Máy chủ mục tiêu:** `https://web-bd09e5c5af420bbc.web.h7tex.com`

## Đề bài

Hãng camera VoltEye vừa tung ra thị trường cả một hạm đội (fleet) thiết bị giống hệt nhau, đúc chung từ "một dây chuyền, chung một sự vội vã". Trong đám cừu nhân bản đó, có một thiết bị mục tiêu mà ta khao khát được mở khoá bảng điều khiển (console) của nó. 
Thử thách câm như hến: Hệ thống không cho một mảnh mã nguồn nào, chỉ ném lại đúng 3 đầu mối (endpoint) API để tự bơi.

## Phân tích ban đầu

Đẩy lệnh thăm dò:
```text
Cổng GET /          -> Chặn cửa: "Device fleet console. Admin bootstrap required." (Bảng điều khiển hạm đội. Yêu cầu mã khởi động quyền Admin).
                       Gợi ý 3 ngách: GET /fleet · GET /captured · POST /admin kẹp theo {"token":"..."}
Cổng GET /fleet     -> Bê ra nguyên cả hạm đội: {"e": 65537, "devices": [{"serial","n"} x30]}    (Sử dụng số hiệu modulus n cỡ 1023/1024 bit).
Cổng GET /captured  -> Túm được 1 thông điệp: {"note": "RSA/PKCS1v1.5, encrypted to the device cert",
                       "serial": "VE-C1E90650", "e": 65537, "ciphertext": <128 byte mã hex>}
```

Hoàn toàn không có cửa cho chiêu lợi dụng máy tiên tri giải mã (decrypt oracle): Ta chỉ có lót tay duy nhất một bản mã (ciphertext). Chân lý là: con đường độc đạo dẫn tới bản rõ (plaintext) bắt buộc phải cày qua việc phân tích toàn bộ modulus của thiết bị đích. 
Khổ nỗi, một con số nguyên khổng lồ 1024 bit thì cày chay phân tích là chuyện viễn tưởng. Nhưng câu sấm truyền "family resemblance runs deeper than you'd think" (sự giống nhau của dòng họ sâu đậm hơn bạn tưởng) lại chĩa thẳng mũi giáo vào một tử huyệt kinh điển của việc sinh khoá hàng loạt (fleet keygen): Đó là lỗi hai thiết bị ngẫu nhiên gắp trúng cùng một số nguyên tố.

## Chuỗi khai thác

### Bước 1: Tính ước số chung lớn nhất chéo cặp (pairwise GCD) cày nát cả hạm đội

```python
hits = [(a, b, math.gcd(an, bn))
        for i,(a,an) in enumerate(devs) for j,(b,bn) in enumerate(devs)
        if j > i and math.gcd(an, bn) > 1]
```

Trong tổng số tổ hợp chéo C(30,2) = 435 cặp, thật may mắn chỉ nảy ra đúng duy nhất một pha đụng hàng (va chạm). Và kỳ diệu thay, vụ tai nạn đó lại dính líu trực tiếp tới thiết bị mục tiêu của ta:

```text
[*] Phát hiện số cặp xài chung nguyên tố (shared-prime pairs): 1 cặp
    Máy VE-C1E90650 va chạm Máy VE-23795497   -> Phân tách được ước chung gcd = một số nguyên tố bự 512-bit
```

### Bước 2: Từ giọt máu chung (thừa số), rèn ra chìa khoá riêng tư (Private Key)

```text
Rút ra p = 792448642746425956602219402032306819204...44085721   (Độ dài 512 bit)
Chia n lấy q = n // p                                           (Cũng 512 bit)
Xác thực ngược: p * q == n  ->  True (Đúng)
Lập công thức rèn khoá: phi = (p-1)*(q-1);  d = pow(65537, -1, phi);  m = pow(ct, d, n)
```

### Bước 3: Lột xác chuẩn mã PKCS#1 v1.5

Khối giải mã phơi bụng ra nguyên dải 128 byte:

```text
0002 81c2c61e...415d5d 00 766c745f343832353238633831343263613962316665353763666533
└kiểu 2┘└── 97 byte đệm (padding), tuyệt đối vắng bóng byte 0 ──┘└Mốc chặn┘└──── Lõi thông điệp: "vlt_482528c8142ca9b1fe57cfe3" ────┘
```

Khuôn mẫu chuẩn đét `00 02 PS 00 M` (với khoảng đệm PS hoàn toàn không dính một hạt sạn byte 0 nào) là lời chứng thực đanh thép: chìa khoá riêng (d) ta vừa đúc ra là hàng thật giá thật (chỉ cần sai lệch 1 bit ở biến `d` là nguyên khối sẽ nát bươm thành rác, khỏi hy vọng nhô ra được cái mào đầu `00 02`). Khúc token `vlt_<hex>` vừa vặn như in với cái lỗ khoá "admin bootstrap token" mà form đăng nhập yêu cầu.

### Bước 4: Mở két

```bash
$ python solve_blood.py
[+] Đào được token = 'vlt_482528c8142ca9b1fe57cfe3'
[*] Dập POST /admin -> Phản hồi 200 {"authed": true, "flag": "H7CTF{a727587f-67d5-4246-b7c3-e57798659fac}"}
[+] FLAG: H7CTF{a727587f-67d5-4246-b7c3-e57798659fac}
```

## Flag
```text
H7CTF{a727587f-67d5-4246-b7c3-e57798659fac}
```
