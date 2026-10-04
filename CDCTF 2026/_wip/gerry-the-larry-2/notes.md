# notes.md - gerry-the-larry-2

Instance: `https://njpwkhrj.i.cdctf.net`. Mọi lệnh bên dưới đều do người chơi dán/chạy
(chính sách CDCTF cấm tool tự động chạm instance), tôi chỉ phân tích artifact đã tải về local.

## N1 - Thu thập tĩnh
cmd: `curl -s $B/ -o index.html`; tải `assets/index.501b4b7d.js`; `grep -oE '(src|href)="[^"]+"'`
evidence: 1 asset JS 152.592 B, 1 CSS, không có API path nào ngoài `/vote` (grep `"/vote"`)
result: OK - đọc bundle là đủ để hiểu toàn bộ phía client

## N2 - Đọc cấu trúc lá phiếu từ bundle
cmd: `grep -o 'ES=function[^}]*}'`, `grep -o 'SS=function[^}]*}'`, `grep -o 'Ys=function[^}]*}'`
evidence: `signature = 8*year+4*lat+2*lon+number`; `uvin = pad4+pad2+pad2+pad4`;
`Ys(n)` = tích Descartes `1..2n+1` × `1..2n+1` với `n = 5` (tìm `RS(5)`/`kS(5)` trong `DS`)
result: OK - mint được UVIN hợp lệ tuỳ ý, không có secret

## N3 - Đo schema bằng 422
cmd: `POST /vote` với `votes=[{"address":[a,b],"payload":true}, ...]` (4 biến thể encode)
evidence: `{"detail":[{"type":"bool_type","loc":["body","votes",0],
"msg":"Input should be a valid boolean","input":{"address":[1,1],"payload":true}}]}`
result: OK - `votes` là danh sách boolean phẳng; mọi cách encode object đều bị pydantic từ chối
(lỗi 422 cũng xác nhận luôn thứ tự field `body,votes,<i>` và `signature` không nằm trong danh sách lỗi)

## N4 - Kiểm signature phía server
cmd: `POST /vote` với `signature:"1"` so với `signature:"16215"`
evidence: `"1"` -> `flag="Error: Invalid UVIN!"`; `"16215"` -> `flag="Error: You have already voted!"`
result: OK - signature được kiểm thật, và công thức của client là đủ để vượt qua

## N5 - `result` có phải kết quả bầu cử không
cmd: ba phiếu khác nhau (121 `true`, 121 `false`, 100 phần tử)
evidence: `result` luôn bằng đúng danh sách vừa gửi, kể cả độ dài 100/121/122/0
result: DEAD - `result` chỉ là echo của lá phiếu đã lưu; mọi kết luận nằm trong `flag`

## N6 - Khoá "already voted" cấp nào
cmd: 10 UVIN có `number` 1..10, cùng `lat_block=1, lon_block=1`
evidence: cả 10 đều `Error: You have already voted!`
result: MỞ - không phải khoá theo UVIN. Phép quét tiếp theo: 121 block × 1 `number` cố định,
in lưới 11×11 `.`/`X` + mọi message khác biệt. `X` rải rác => khoá theo block; `X` theo cụm 2×2 =>
khoá theo precinct; toàn `.` => khoá theo IP/phiên.

## N7 - Schema công khai
cmd: `GET /openapi.json`, `/docs`, `/redoc`
evidence: 404 nginx cả ba
result: DEAD - không có schema, phải đoán model qua 422

## N8 - Arte nhiễu
evidence: `cn2tw_1.json` / `tw2cn_1.json` 404 từ `common.js`, `a450b2acbe1240f6` và
`/cdn-cgi/challenge-platform/...` là script Cloudflare
result: DEAD - không thuộc đề

## Công cụ đã dựng ở local

`analysis/solver.py`: chia lưới precinct thành K khu liền kề, kích thước bằng nhau, tối đa số khu ta thắng
(swap move + ruin&recreate, chỉ duyệt bản đồ hợp pháp). Kiểm chứng bằng 4 bản điều khiển, trong đó
bản đối chứng âm (ta giữ 10%) trả về 0 ghế ⇒ công cụ không tự bịa kết quả.
