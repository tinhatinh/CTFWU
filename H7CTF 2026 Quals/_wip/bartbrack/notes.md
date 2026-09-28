# notes.md - bartbrack

Instance: `82d6b903-5765-bartbrack-130c9.mystery-challenges.webverselabs-pro.com`
Stack: Apache/2.4.68 (Debian) + PHP/8.2.33, Cloudflare trước mặt. Cờ dạng `WEBVERSE{...}`.

## H1 - Tìm endpoint GraphQL
cmd: `curl /graphql /api/graphql /gql /graph /console ...`
evidence: tất cả 404 của Apache. Fuzz thêm đuôi `.php` thì `/graphql.php` trả 200
  `{"errors":[{"message":"Sign in first."}]}`
result: OK - GraphQL ở `/graphql.php`, nhưng chặn chưa đăng nhập. App chỉ có duy nhất
  `/index.php` (form login) ngoài `/static/`.

## H2 - SQLi ở form đăng nhập
cmd: POST `/` với `admin' OR '1'='1' -- `, `admin' or 1=1#`, `admin" or "1"="1`
evidence: mọi payload đều trả lại đúng trang login với `Incorrect username or password.`
  (thông báo chung, không phân biệt user tồn tại hay không)
result: DEAD - không có SQLi, không có user enumeration.

## H3 - Lấy session hợp pháp
cmd: POST `/` với `admin` / `admin`
evidence: **302 -> /verify.php**. Cặp credential mặc định hợp lệ thật.
  `/verify.php`: "We sent a 5-digit code...", input `maxlength=5`, cảnh báo
  "Repeated failures will lock this session".
result: OK - có session `flux_sid`, còn kẹt ở bước 2FA (không có đăng ký user khác).

## H4 - Đọc client JS để tìm sink
cmd: `curl /static/js/verify.js`
evidence: client gọi
  `mutation { verifyOtp(code: "<code>") { ok token } }` tới `/graphql.php`, và comment đầu file ghi rõ:
  *"The endpoint is rate-limited per request; that is what an attacker bypasses with alias batching."*
result: OK - mục tiêu là `verifyOtp`, không gian 10^5 code, cách đánh là alias batching.

## H5 - Introspection với session đã đăng nhập
cmd: `POST /graphql.php {"query":"{ __schema { queryType{fields{name args{name type{name}}}} mutationType{...} } }"}`
evidence: schema tối giản - query `status`, mutation `verifyOtp(code) -> OtpResult{ok token}`.
  Lưu ý: gửi `verifyOtp` trong **query root** thì server trả `{"data":[]}` chứ không báo lỗi
  (GraphQL tự viết), phải dùng `mutation { ... }` mới resolve.
result: OK - xác nhận chỉ có đúng một cửa 2FA.

## H6 - Kiểm tra giới hạn alias
cmd: 1 request chứa 300 alias `verifyOtp`
evidence: trả về dict 300 phần tử, không lỗi, không bị chặn -> server chỉ giới hạn theo request.
result: OK - nâng lên 1000 alias/request, 100 request là quét hết không gian.

## H7 - Khoá session do fail?
cmd: brute force liên tục trên cùng session
evidence: không thấy message khoá trong suốt quá trình quét (message sẽ hiện trong `errors[0].message`),
  dashboard vẫn tiếp cận được sau khi có code đúng.
result: OK - "lock this session" chỉ là mô tả; rate limit per-request chính là lỗ hổng.

## Kết quả
(chờ exploit in ra: code OTP hợp lệ, token, và trang dashboard chứa cờ)
