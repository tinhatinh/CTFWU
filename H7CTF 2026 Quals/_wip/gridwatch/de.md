# GridWatch - H7TEX 2026 (Web / King of the Hill, 1000)

## Đề bài (nguyên văn từ trang challenge)

```
GridWatch
insane
Docker
Hardware
1000 Points

GridWatch is the operator console for a 33kV substation feeder, and only one operator can hold the seat at a time.

King of the Hill: take the operator seat and hold it. The seat resets periodically, so expect to take it again.

Enter the arena for your target and token, then open the console: it lists its own endpoints, and GET /koth/status shows who currently holds the seat.
```

Arena: One shared target the whole field contests. Enter the arena, then plant your token on the target - you score for every tick you hold it.

| Field | Gia trị |
| --- | --- |
| Target | `https://web-f57666ec7cc3ed16.web.h7tex.com` |
| Arena token | `koth_L6CRWckXv3KOpZP1vm7tbuxmxshteyM6` |
| Request secret | `kss_s7g5SWEVaD5JzXvFvm3Yhwy1fiVz5gNI` |

Secret phải gửi kèm request theo đúng cách đề mô tả; chỉ có token công khai thì không hành động được.

## Endpoint app tự liệt kê trên trang chủ

```
GET  /api/telemetry
POST /api/login          {"user","pass"} -> session token (operators get a viewer session)
POST /api/operator/claim {"holder_token","operator_name"} (Authorization: Bearer, admin only)
GET  /koth/status        -> ai đang giữ seat
```

Trang chủ không có JS, không có route ẩn nào khác. Server là gunicorn (Python/Flask).

## Những gì đã thử và kết quả

| Thử | Kết quả |
| --- | --- |
| `GET /koth/status` | 200, `{"holder":...,"since":...}`; holder đổi liên tục trong session (`koth_xjvC...`, `koth_bJju...`, `koth_KuTX...`) => arena đang có người chơi khác |
| `POST /api/login` với `{}` | 500 Internal Server Error |
| `POST /api/login` với admin/admin, operator/operator, root/root, sa/sa | 405 Method Not Allowed (header `Allow: POST, OPTIONS`) |
| `POST /api/login` với user=arena token, pass=request secret | 500 |
| `POST /api/operator/claim` + `Authorization: Bearer <request secret>` | 403 `admin session required` |
| Claim với các body khác nhau (`token`, `holder_token`+`operator_name`, thêm `secret`) | đều 403 như trên |
| Claim với token của holder hiện tại | 403 |
| Header biến thể: `X-Arena-Token`, `X-Holder` | 403 |
| Method khác: `GET`/`PUT` lên `/api/operator/claim` và `/koth/status` | 405 |
| Brute path: `/koth`, `/seat`, `/claim`, `/take`, `/enter`, `/api/koth`, `/api/claim`, `/operator/claim`, `/koth/claim`, `/koth/take`, `/graphql`, `/login`, `/b`, `/h`, `/p` | toàn 404 |
| `OPTIONS /api/operator/claim` | trả lời rỗng |

## Kết luận hiện tại

Chặn ở bước **lấy admin session**. `claim` luôn 403, còn `login` thì 500 với mọi credential đã thử nên không có đường hợp lệ để tới Bearer token.

## Câu hỏi cần trả lời trước khi làm tiếp

1. Trong `KoTH.pdf` (hướng dẫn BTC gửi) có nêu cách tạo tài khoản operator hoặc credential mặc định không? File nằm ở `C:\Users\Administrator\Downloads\KoTH.pdf`, máy này không có poppler nên không đọc được bằng tool hiện có.
2. Arena có cho đăng ký user qua UI không, hay phải xin token/credential từ BTC?
3. Seat reset theo chu kỳ bao lâu (để biết nhịp giữ seat khi đã chiếm được).
