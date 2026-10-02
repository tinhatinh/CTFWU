# Owner's Draw — Crypto (Medium)

**Flag:** `H7CTF{786dff67-75cd-4d4e-8b74-55edb1353aad}`
**Máy chủ mục tiêu:** `https://web-b39cfff63c4c78b9.web.h7tex.com`

## Đề bài

Hệ thống thanh toán OrionPay mở một cổng webhook nhận thông báo. Nó hành xử rất nguyên tắc: chỉ gật đầu làm theo giấy tờ nếu giấy tờ được "đóng mộc" (đúng dấu) hợp lệ. 
Trong hệ thống, có một chế độ chi trả (payout) độc quyền mà chỉ có giới chủ (owner) mới được phép chạm tay vào. Đề bài chỉ quăng cho ta một phiếu thanh toán (slip) hợp pháp của khách thường (bao gồm phần body và phần chữ ký dính kèm), phần còn lại ta phải tự xử.

## Phân tích ban đầu

Đẩy lệnh thăm dò:
```text
Gọi GET /sample -> Phun ra thân nội dung body : event=payment.succeeded&amount=500&currency=usd&customer=cus_9f2a&role=guest
                   Kèm chữ ký X-Signature     : 14d500d5...d929f6a7
                   Hệ thức ký signing         : Bằng thuật toán SHA256(secret || body)
```

Ném lại toàn bộ cục slip nguyên bản vào cổng `POST /webhook`, máy chủ nhả về `{"ok": true, "role": "guest", "note": "no owner payout"}`. 
Thông tin đắt giá rút ra: Hệ thống sẽ đè chữ ký ra xét duyệt (verify) TRƯỚC KHI thèm mổ xẻ phần thân body, và cái nhãn `role` chính là cái công tắc quyết định số phận dòng tiền payout.

Tử huyệt của nền tảng nằm chình ình ở cái công thức ký: `SHA256(secret || body)`. Đây là trò tạo mã xác thực (MAC) theo phương pháp cắm tiền tố (prefix) dựa trên kiến trúc băm Merkle - Damgård. Ác mộng của kiến trúc này là: cái chuỗi băm (digest) công bố ra ngoài thực chất chính là trạng thái nội bộ (internal state) của động cơ SHA-256 sau khi nó nhai cắn xong toàn bộ thông điệp đã được bọc độn (padded). 
Hậu quả nhãn tiền: Bất cứ gã nào lượm được cặp (dấu băm, độ dài thông điệp gốc) đều có thể cưỡi tiếp lên cái vòng lặp nén (compress) đó. Hắn cứ việc gắn đuôi (append) thông điệp rác vào, máy sẽ nôn ra một cái dấu băm mới toanh, hợp lệ hoàn toàn cho cái chuỗi `body || padding || extra`. Gã chẳng cần thèm biết cái khoá `secret` thực chất là cái gì.

Đảo mắt qua cổng `/v2/webhook`, thấy nó xài HMAC-SHA256. Đem đồ nghề đo thử thì thấy ngay cái chữ ký SHA-256 ma giáo của ta bị nó vả cho cái lỗi 401 thẳng mặt. Tức là cái phiên bản "next-gen" (v2) này đã đổ bê tông bịt kín cái lỗ hổng lố bịch kia (Bởi vì thuật toán HMAC có cấu trúc kẹp tới hai tầng padding trong/ngoài, chặn đứng trò nối dáo trạng thái). Dù sao thì bài này chỉ khoét 1 lỗ, nên cổng v2 chỉ đóng vai trò bức tường kiểm chứng (đối chứng).

## Chuỗi khai thác

### Bước 1: Tay không dựng lại lò nén SHA-256 compression bằng Python thuần

Bởi vì bộ thư viện `hashlib` của Python không thèm hỗ trợ cái trò API "chạy nối đuôi từ một digest có sẵn", nên ta buộc phải xắn tay tự code lại cái động cơ `compress(state, block)` (bao gồm lịch trình phân mảnh thông điệp message schedule + 64 vòng lặp nhào nặn). Đây chính là cái bẫy mồ hôi của bài này: chỉ cần gõ sai một hằng số hay trật một dòng cập nhật state, là toàn bộ công trình giả mạo (forge) đổ sông đổ biển.

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

### Bước 2: Nhồi bông (Splice)

Thông điệp gốc mà máy chủ đem đi ký là `secret || body`, với tổng chiều dài `L = len(secret) + 76` (Cái dở là ta hoàn toàn mù tịt về thông số `len(secret)`). 
Cái đuôi padding mà thuật toán SHA-256 đã tự động gắn (append) vào cục thông điệp gốc có dạng `0x80 || 00*k || be64(8L)`. Chân lý là ta BẮT BUỘC phải ôm trọn cục đuôi đó, ném thẳng vào cái body mới:

```python
pad  = b"\x80" + b"\x00" * ((55 - L) % 64) + struct.pack(">Q", L * 8)
new  = pad + b"&role=owner"
tag  = struct.unpack(">8I", bytes.fromhex(sig))      # Đây chính = trạng thái sau khi pad
# Cứ thế nhắm mắt chạy tiếp (compress) từ cái tag này (ôm theo cục dữ liệu mới + phần padding tự chế của chính nó)
```

### Bước 3: Đem máy chủ ra làm bù nhìn bói độ dài secret (Oracle)

```python
for s_len in range(65):
    ext, forged = len_extend(tag, s_len + len(body), b"&role=owner")
    # Lệnh bắn: POST /webhook  body=body+ext  X-Signature=forged
```

Hệ thống nhè ra hàng loạt lỗi 401 như vả vào mặt, cho đến khi vòng quay dừng ở mốc `s_len = 15`:

```text
[+] Đã bắt mạch được độ dài secret = 15   kèm đuôi body tail=b'\x00\x00\x00\x02\xd8&role=owner'
[+] Gõ /webhook -> Bùng nổ mã 200 {"ok": true, "payout": "authorized", "flag": "H7CTF{786dff67-75cd-4d4e-8b74-55edb1353aad}"}
```

Kiểm tra đối chứng: 8 byte độ dài trong cục đệm splice bóc ra là `0x2d8` = 728 bit = 91 byte = 15 (của secret) + 76 (của body) - Con số này chính là lời thú tội hoàn hảo tự nó nói lên tất cả: Nó khẳng định mốc độ dài secret vớt được là chuẩn không cần chỉnh, mà chẳng thèm mượn đến một lời xác nhận (phản hồi) nào từ cái máy chủ ngu ngốc kia.

## Flag
```bash
$ python solve_draw.py
[+] FLAG: H7CTF{786dff67-75cd-4d4e-8b74-55edb1353aad}
```
