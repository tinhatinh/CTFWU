---
title: "Overgrowth"
category: "Web"
tags: []
solve_date: "2026-10-31"
language: "vi"
---

# Overgrowth

## Đề bài

API GraphQL của cửa hàng vật tư làm vườn có field `flag` chỉ dành cho admin. Cần tìm cách xác thực với tài khoản này thông qua luồng reset mật khẩu.

## Phân tích

Endpoint `/graphql` chạy Ariadne và đã tắt introspection, nhưng lỗi validation vẫn làm lộ một phần schema:

```graphql
type Query { flag: String, me: User, user(username: String!): User, products: [Product] }
type Mutation { login(username: String!, password: String!): Auth,
                requestPasswordReset(username: String!): Boolean,
                resetPassword(username: String!, token: String!, newPassword: String!): Boolean }
```

Query `user(username:"admin")` trả một `apiKey` trông giống flag:

```
hiCTF{n0t_the_flag_keep_diggin_this_is_just_an_apikey}
```

Đây là mồi nhử. Field `flag` thật yêu cầu phiên admin. Điểm yếu hữu ích nằm ở OTP reset bốn chữ số và cách rate limit đếm request HTTP thay vì số operation GraphQL.

## Lời giải

### 1. Tạo OTP của admin

Gọi `requestPasswordReset(username:"admin")`. Sau đó thử các token trong khoảng `0000` đến `9999`, giữ đủ bốn ký tự kể cả số 0 đầu.

### 2. Gom mutation bằng alias

Một request chứa nhiều alias cho cùng mutation `resetPassword`. Với 250 alias/request, toàn bộ không gian 10.000 mã được chia thành 40 request thay vì 10.000 request riêng:

```graphql
mutation {
  a0000: resetPassword(username:"admin", token:"0000", newPassword:"OvergrowthPwn2026!")
  a0001: resetPassword(username:"admin", token:"0001", newPassword:"OvergrowthPwn2026!")
  # ... 248 more aliases ...
}
```

Đoạn trên minh họa cấu trúc; khi chạy cần sinh đủ 250 alias với token liên tiếp. Mật khẩu mới giữ cố định để đăng nhập sau khi có một mutation thành công. Token đúng trong lần chạy đã lưu là `8895`; khi gặp HTTP 429, client chờ rồi thử lại batch bị giới hạn.

### 3. Đăng nhập và đọc field bảo vệ

Gọi `login` với mật khẩu mới, lấy session token và đặt vào header `Authorization` theo dạng raw hoặc `Bearer` mà service chấp nhận. Query cuối:

```graphql
{ flag }
```

Service trả flag. Việc chặn theo số request không ngăn được brute-force nếu mỗi request vẫn thực thi hàng trăm lần kiểm tra OTP.

## Kết quả

```
hiCTF{graphql_al1as_batch1ng_brute_f0rces_the_0tp_fd61a0591a}
```

OTP và session token phụ thuộc instance. Schema và cách chia batch ở trên đủ mô tả cơ chế; bản lưu không kèm client tự động hoàn chỉnh.
