# HANDOVER — Help Yourself (mobile) — đồng đội đã giải, không đào sâu tiếp

Trạng thái: chưa có cờ. Instance chưa trả lời được route nào (xem mục 4).

## 1. Artifact
`deskline-1.6.0.apk.zip` (11711 B, sha256 `34b13f5bd65a94f6…`) bên trong là 1 APK 16885 B
(sha256 `0b2eb6635e06c092…`), 7 entry: `AndroidManifest.xml`, `res/layout/activity_main.xml`,
`resources.arsc`, `classes.dex` (12568 B), `META-INF/ANDROIDD.SF|.RSA`, `MANIFEST.MF`.
Đã giải nén ở `files/apk/` và `files/dex/`. Package `com.deskline`, min-api 24, D8 debug,
provider `com.deskline.tickets` (authority `com.deskline.tickets`), `usesCleartextTraffic=true`.

## 2. Hợp đồng API rút ra từ classes.dex (bằng `strings`, chưa cần jadx)
- endpoint: `POST /api/v1/auth/device`, `POST /api/v1/sync`
- header: `Authorization: Bearer <token>`, `X-Deskline-Client` (hằng `CLIENT_HEADER`),
  `User-Agent: Deskline-Android/1.6.0`, `Content-Type: application/json`
- `baseUrl` mặc định `http://10.0.2.2:8080` (alias host của Android emulator), ghi đè được
  qua SharedPreferences (`base_url`, `server`) → thiết kế để trỏ vào instance
- key JSON xuất hiện trong dex: `device_id`, `deviceId`, `token`, `status`, `tickets`,
  `subject`, `body`, `server`, `label`, `value`, và **`internal`**
- lớp `TicketProvider` (ContentProvider) + SQLite `deskline.db`, 2 bảng
  `tickets(id,subject,body)` và `credentials(id,label,value)`;
  `SELECT id, subject, body FROM tickets`, `seedFromSync`, `renderTickets`
  → gợi ý mạnh: server trả cả ticket `internal:true` nhưng `renderTickets` lọc bỏ,
  nên "agent-only note" nằm ngay trong response của `/api/v1/sync` (hoặc phải bật
  một flag/đọc qua ContentProvider).

## 3. Cách đi tiếp theo (nếu muốn làm nhanh, không cần chạy app)
```
POST /api/v1/auth/device  {"device_id":"<uuid4>"}   -> token
POST /api/v1/sync         Bearer <token> + X-Deskline-Client + UA Deskline-Android/1.6.0
```
đọc toàn bộ mảng tickets, không lọc `internal`. Nếu response chỉ trả ticket không internal,
thử các biến thể: `{"include_internal":true}`, `{"scope":"agent"}`, header `X-Deskline-Client`
bằng giá trị lấy từ dex (chuỗi `deskline`), hoặc `GET /api/v1/sync?include=internal`.
Hướng备选: cài APK lên MuMu/emulator rồi đọc `SharedPreferences` + `deskline.db` qua adb
(token và credential nằm trong 2 chỗ đó), hoặc dump traffic qua CA tự cài.

## 4. Vì sao chưa đi tiếp
Mọi path trên `https://web-c575bd9f84a3e065.web.h7tex.com` (kể cả `/`) trả đúng
`404 page not found`, `X-Content-Type-Options: nosniff`, **không có header `Server:`** —
đó là 404 của router nền tảng chứ không phải của app (app thật ở các bài trước trả
`Server: BaseHTTP/0.6`/`SimpleHTTP/0.6` riêng). Nhiều khả năng instance chưa được Start,
hoặc mobile task chỉ định mở APK offline. Đã kiểm tra hostname khớp từng ký tự với message
(tránh lỗi typo như bài Ghost on the Bus).
