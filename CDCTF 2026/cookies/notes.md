# notes.md - cookies

Input: không có artifact; target `https://xhlvnfzc.i.cdctf.net` (instance sống tới 2026-10-03)
Định dạng cờ đề yêu cầu: `cdctf{Fl4gGo3sH3re!}`

## H1 - Balance là một cookie thường, server chỉ kiểm tra truthiness
cmd: `curl -i https://xhlvnfzc.i.cdctf.net/get_cookie`
evidence: `Set-Cookie: user_cookie_balance=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2Nvb2tpZV9iYWxhbmNlIjowfQ.tZe...`
value là JWT 3 segment, không phải chuỗi số thô.
result: DEAD - giá trị do server ký, sửa tay thì chữ ký hỏng.

## H2 - Server không thẩm định chữ ký (chỉ decode payload)
cmd: `POST /purchase_flag` với `Cookie: user_cookie_balance=garbage` và với token balance=1 ký bằng
secret đoán (`secret`, `cookies`, `Cookies-and-All-That`, `alex`, `cdctf`, `chocolate`, `jwt`,
`hs256`, `user_cookie_balance`, `trickster`, rỗng)
evidence: tất cả trả `Invalid token!` trên HTTP 200; token gốc trả `Flag request: DENIED`.
result: DEAD - có verify signature thật, nhưng đồng thời loại luôn mọi secret đoán trước.

## H3 - `alg=none`
cmd: `POST /purchase_flag` với `<b64u({"alg":"none","typ":"JWT"})>.<b64u({"user_cookie_balance":1})>.`
evidence: nhận 404 do nginx, không phải phản hồi của app Flask. Lúc này instance đã báo
`Challenge Deployment Service ... may not be ready yet, or has expired`.
result: UNVERIFIED - phép thử rơi vào lúc instance chết, không có bằng chứng app từ chối hay chấp nhận.

## H4 - Bẻ khoá HMAC bằng wordlist
cmd: `node brute.js` (8 worker, `C:/Tools/rockyou.txt`, 14344392 dòng) trên token gốc
evidence: `SECRET="COOKIEMONSTER" line=251496`, `FOUND after 35.9s`.
Self-test trước khi tin kết quả: gài secret `taetae07` (dòng 777777 của chính rockyou) vào một JWT
giống hệt về cấu trúc, chạy cùng harness -> `SECRET="taetae07" line=777777`. Harness tìm được
positive nên kết quả các secret đoán ở H2 là âm tính thật.
result: PENDING -> xác nhận ở H5.

## H5 - Forge balance=1
cmd: `python exploit.py --token '<token gốc>' --secret COOKIEMONSTER` rồi `POST /purchase_flag`
evidence: token ký bằng Python `eyJ...eyJ1c2VyX2Nvb2tpZV9iYWxhbmNlIjoxfQ.sXJ5IOw2YDk6_guPpvWkeu8Pp7H8reIzI6MnlS-OXo4`
trùng từng ký tự với token Node đã gửi lúc solve. Response lúc instance còn sống:
HTTP 200, thân có `<p>cdctf{0mNomN0mNomC00k1E5!_24a480be}</p>`. balance=999 cũng cho cùng cờ,
không có upper bound.
result: DONE.

## Ghi chú tái hoà

- Instance hết hạn nên `POST /purchase_flag` hiện trả `403 error code: 1010` (Cloudflare browser
  signature), không chạy lại được bước cuối. Các block output trong writeup lấy từ lệnh đã chạy
  thật trong phiên 2026-10-03 và phiên verify offline 2026-10-04.
- `python exploit.py --wordlist C:/Tools/rockyou.txt --token '<token gốc>'` chạy đơn luồng mất
  19.2s để tới dòng 251497, vẫn tìm ra `COOKIEMONSTER`: script đóng gói hoạt động độc lập với
  bản Node.
