# shape-of-query — WEB (300 pts)

**Flag:** `POCTF{81.612.EB7ZOZUZT7FJHWR2.YQXWHGRFYSBYU46VGKVYD22DNN}` · **Target:** `https://shape-of-query.pointeroverflowctf.com`

## Đề bài

Tác giả tự dựng một "Collaborative Research Portal" và mời tester vào chọc. Điều anh ta lo nhất là **user security**, vì "researchers meddling with each others' stuff". Portal nằm ở một subdomain riêng, đăng nhập bằng session token của team (trang challenge sinh token mới mỗi lần reload, hạn 15 phút), và sau khi vào thì làm việc với một **GraphQL API ở `/graphql`, introspection bật**.

## Phân tích ban đầu

Trang login chỉ có một ô token; `POST /session/exchange` với token hợp lệ trả `{"ok":true,"team_id":612}` và set cookie `session`. Vào `/graphql` là GraphiQL.

Introspection cho đúng bốn type kinh tế:

```graphql
type Query { me: User   user(id: ID!): User }
type User  { id: ID!  username: String!  role: UserRoleEnum  team: Team  privateNotes: String }
type Team  { id: ID!  name: String  members: [User] }
enum UserRoleEnum { ADMIN MEMBER }
```

Mô tả field trên server tự viết đã chỉ thẳng vào chỗ nghi ngờ: `user` là "You may only view yourself", `privateNotes` là "Visible to the account owner only", `members` là "Cross-team enumeration is blocked". Vậy mục tiêu là `privateNotes` của một tài khoản khác tài khoản mình.

`me` trả về `researcher_612` với `privateNotes` là "Grocery list, personal reminders. Nothing worth reading." - mồi.

## Các hướng đã loại

Log đầy đủ ở `notes.md`.

1. **IDOR trên `user(id:)`**: `user(id:"user_1")`, `user(id:"612")`, `user(id:"1")` đều trả `null`, không lỗi. Loại.
2. **SQLi trong tham số `id`** (tên bài gợi "query"): `user_1' OR '1'='1`, `user_612' OR '1'='1`, `user_612'--`, `user_612 ` - mọi payload vẫn trả `null`, hình dạng kết quả không đổi, tức resolver dùng truy vấn tham số hoá. Loại.
3. **Field ẩn ở gốc `Query`**: dò 46 tên hay dùng (`flag`, `secret`, `notes`, `token`, `debug`, `sql`, `exec`, `members`, ...) -> cả 46 báo `Cannot query field`. `Query` chỉ có `me` và `user`. Loại.
4. **Alias confusion / thứ tự field**: `{ one: user(id:"user_1"){...} six: user(id:"user_612"){...} }` và bản đảo ngược - mỗi field vẫn bị định giá độc lập. Loại.
5. **Query batching**: gửi body là mảng request thì server **HTTP 500** (trang lỗi Flask), không trả dữ liệu. Đây là bug implementation, không phải đường vòng qua quyền. Loại (không khai thác tiếp).

## Chuỗi khai thác

**Bước 1 - Vẽ đồ thị đường đi tới field đích.** `privateNotes` không chỉ tới từ `Query.user`; còn một đường nữa: `Query.me -> User.team -> Team.members -> privateNotes`. Mô tả "chỉ xem được chính mình" chỉ gắn vào `Query.user`.

**Bước 2 - Đi theo đường lồng.**

```graphql
{ me { team { members { id username role privateNotes } } } }
```

```json
{"data":{"me":{"team":{"members":[
  {"id":"user_612","privateNotes":"Grocery list, personal reminders. Nothing worth reading.","role":"MEMBER","username":"researcher_612"},
  {"id":"admin_612","privateNotes":"POCTF{81.612.EB7ZOZUZT7FJHWR2.YQXWHGRFYSBYU46VGKVYD22DNN}","role":"ADMIN","username":"admin_612"}
]}}}}
```

`Team.members` trả mỗi thành viên kèm `privateNotes` **thô**, không qua phép kiểm tra quyền nào. Team nào cũng có một tài khoản `admin_<team_id>`, và cờ nằm trong ghi chú riêng của admin team mình.

**Bước 3 - Kiểm chứng không phải dữ liệu của team khác.** `user(id:"admin_612")` vẫn trả `null`, dù admin đó cùng team - chứng tỏ bộ kiểm tra quyền chỉ tồn tại ở resolver `Query.user`, còn `Team.members` thì không. Thêm nữa, nonce `EB7ZOZUZT7FJHWR2` trong cờ trùng đúng nonce trong session token của trang challenge, nên đây là cờ của team 612.

**Bước 4 - Nộp.**

```
POST /challenges/shape-of-query/submit
{"flag":"POCTF{81.612.EB7ZOZUZT7FJHWR2.YQXWHGRFYSBYU46VGKVYD22DNN}"}
{"correct":true,"message":"Correct."}
```

## Flag

```
POCTF{81.612.EB7ZOZUZT7FJHWR2.YQXWHGRFYSBYU46VGKVYD22DNN}
```

Ý tưởng quyết định: trong GraphQL, quyền thường được cài ở **resolver của một field gốc**, nên cùng một field dữ liệu có thể lộ hoàn toàn khi đi theo **một đường khác** trong type graph. Đừng kiểm tra "endpoint có chặn không", hãy liệt kê mọi đường đi tới field đích.

## Reproduce

```bash
python exploit.py "<session token trên trang challenge>"
```
