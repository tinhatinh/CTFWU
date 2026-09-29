# Owner's Draw — Crypto (Medium)

**Flag:** `H7CTF{786dff67-75cd-4d4e-8b74-55edb1353aad}`
**Instance:** `https://web-b39cfff63c4c78b9.web.h7tex.com`

## Đề bài

OrionPay nhận webhook và chỉ làm theo giấy tờ nếu giấy tờ "đúng dấu". Có một loại payout chỉ owner được chạm tới. Ta có đúng một slip hợp pháp (body + chữ ký của nó) và curiosity.

## Phân tích ban đầu

```
GET /sample -> body        : event=payment.succeeded&amount=500&currency=usd&customer=cus_9f2a&role=guest
              X-Signature  : 14d500d5...d929f6a7
              signing      : SHA256(secret || body)
```

`POST /webhook` với slip nguyên bản trả `{"ok": true, "role": "guest", "note": "no owner payout"}` -> signature được verify trước khi parse body, và `role` mới là thứ quyết định payout.

Điểm chết nằm ở công thức ký: `SHA256(secret || body)` là MAC kiểu prefix trên một hash Merkle - Damgård. Với loại này, digest công bố chính là trạng thái trong của SHA-256 sau khi xử lý toàn bộ message đã pad, nên ai có (tag, độ dài message gốc) đều có thể tiếp tục chạy vòng compress trên dữ liệu append thêm và cho ra tag hợp lệ cho `body || padding || extra`  -  không cần biết `secret`.

`/v2/webhook` dùng HMAC-SHA256: phép đo trực tiếp cho thấy cùng chữ ký SHA-256 bị 401, tức bản "next-gen" đã đóng đúng lỗ hổng này (HMAC có hai lớp padding trong/ngoài nên không thể tiếp diễn trạng thái). Bài chỉ có một objective, nên v2 là đối chứng.

## Chuỗi khai thác

### Bước 1: dựng lại SHA-256 compression thuần Python

`hashlib` không có API "tiếp tục từ một digest", nên phải tự viết `compress(state, block)` (message schedule + 64 vòng). Đây là chỗ bài này khó hơn vẻ ngoài: chỉ cần sai một hằng số hay một dòng cập nhật state là toàn bộ forge vô hiệu.

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

### Bước 2: splice

Message gốc mà server ký là `secret || body`, độ dài `L = len(secret) + 76` (ta không biết `len(secret)`). Padding mà SHA-256 đã_append vào message gốc là `0x80 || 00*k || be64(8L)`, và chính phần đó ta phải đưa vào body mới:

```python
pad  = b"\x80" + b"\x00" * ((55 - L) % 64) + struct.pack(">Q", L * 8)
new  = pad + b"&role=owner"
tag  = struct.unpack(">8I", bytes.fromhex(sig))      # = trạng thái sau pad
# chạy tiếp từ tag trên (new + padding của chính nó)
```

### Bước 3: dò độ dài secret, server là oracle

```python
for s_len in range(65):
    ext, forged = len_extend(tag, s_len + len(body), b"&role=owner")
    POST /webhook  body=body+ext  X-Signature=forged
```

Bị 401 liên tiếp tới khi `s_len = 15`:

```
[+] secret length guess=15   body tail=b'\x00\x00\x00\x02\xd8&role=owner'
[+] /webhook -> 200 {"ok": true, "payout": "authorized", "flag": "H7CTF{786dff67-75cd-4d4e-8b74-55edb1353aad}"}
```

8 byte độ dài trong padding splice là `0x2d8` = 728 bit = 91 byte = 15 (secret) + 76 (body)  -  con số tự kiểm chứng: nó chỉ ra độ dài secret đúng mà không cần tới phản hồi của server.

## Flag
```
$ python solve_draw.py
[+] FLAG: H7CTF{786dff67-75cd-4d4e-8b74-55edb1353aad}
```
