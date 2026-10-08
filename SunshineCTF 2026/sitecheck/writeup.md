# SiteCheck - Web (Hard)

Điểm: 498 · **Flag:** `sun{fr4gm3nt3d_r3fl3ct10ns_1n_th3_futur3}`
**Instance:** `https://spaceship.web.2026.sunshinectf.games` (no files provided nguồn)

## Đề bài

SiteCheck là dịch vụ kiểm tra website. Đăng ký tài khoản inspector rồi gửi vào một URL, "drone" của SiteCheck sẽ tự tới địa chỉ đó, đo thời gian tải, đếm số file tải về, rồi trả về một ảnh chụp viewport. Drone từ chối địa chỉ nội bộ và local. Bài toán là vượt qua lời từ chối đó để đọc thứ mà site không bao giờ trả thẳng ra ngoài.

## Recon

App Express render phía server, không có bundle JS. Route lấy được từ HTML: `/register`, `/login`, `/dashboard`, `POST /scan`, `/result/<uuid>`, `/profile`, `/logout`, `/static/`, `/screenshots/`.

Luồng scan như sau: `POST /scan` → 302 → `/result/<uuid>`. Trang báo cáo có Status, Load time, Files fetched và một thẻ `<img src="/screenshots/<uuid>.png">`.

Ba con số kia chỉ là oracle phụ. Ảnh snapshot mới là kênh đọc nội dung, và việc có ảnh cũng cho biết drone là một trình duyệt thật (Playwright/Chromium headless, viewport 1280x800), không phải `requests.get` rồi đếm bừa.

## Bộ lọc SSRF chặn gì và không chặn gì

Mỗi dòng dưới đây là một phép thử, chi tiết nằm trong `notes.md`.

| Thử với drone | Kết quả |
| --- | --- |
| `http://127.0.0.1/`, `http://localhost/`, `http://LOCALHOST/` | bị chặn |
| `http://2130706433/`, `http://0x7f000001/`, `http://017700000001/`, `http://127.1/`, `http://0/` | bị chặn |
| `http://example.com@127.0.0.1/` | bị chặn |
| `file:///etc/passwd` | bị chặn bởi rule protocol riêng |
| `http://[::1]/`, `http://[::ffff:127.0.0.1]/` | lọt |
| `http://localtest.me/`, `http://127.0.0.1.nip.io/` | lọt |

Bốn dòng đầu cho thấy họ không so chuỗi. Mã đã parse IP literal ra số rồi mới kiểm tra dải, nên mấy trò viết `127.0.0.1` ở dạng thập phân, thập lục phân, bát phân hay giấu sau `@` đều chết từ trứng nước.

Hai dòng cuối lại lọt, và vì hai lý do khác nhau hoàn toàn: IPv6 loopback bị bỏ sót khỏi deny list, còn hostname thì không bao giờ được resolve để kiểm tra. Bằng chứng là drone trả `ERR_CONNECTION_REFUSED` cho cả bốn cái tên đó, tức nó đã bắt TCP thật, chỉ là cổng 80 không có ai nghe.

## Lời giải

**Bước 1: tìm cổng mở trên loopback.** `http://[::1]:3000/` trả Status 200, Files fetched 10, có snapshot. Cổng 80, 8080, 3001 đều `ERR_CONNECTION_REFUSED`. 3000 là app SiteCheck; nginx phía trước chỉ forward traffic từ ngoài vào.

**Bước 2: app tin vào địa chỉ socket.** Ảnh snapshot của `http://[::1]:3000/dashboard` hiện rõ `Logged in as: admin - CLEARANCE: OMEGA`, trong khi drone gửi request không kèm cookie nào. Nghĩa là kết nối đến từ loopback được coi là phiên admin.

Đối chứng lại: gắn `X-Forwarded-For`, `X-Real-IP`, `Client-Ip` bằng `127.0.0.1` hoặc `::1` vào session đang kiểm tra thì vẫn là `h7tex_probe01`, vẫn `REDACTED`. Nên đây là địa chỉ socket thật, không phải header.

**Bước 3: đọc `/profile`.** Trang Personnel File có section `#clearance` với phần `.flag-plate`, ghi "Restricted personnel token - visible only to holders of this file". Với tài khoản BRONZE, plate chỉ đề `REDACTED · insufficient clearance`.

**Bước 4: plate nằm ngoài viewport.** Đầu trang có `<div class="spacer" style="height:1400px">` và một `.spacer.tall` nữa, nên bản admin dù có token thật vẫn bị đẩy xuống dưới điểm cắt 1280x800. Screenshot chỉ chụp được phần đầu trang.

Đây là chỗ dễ bỏ nhất của bài. Chain SSRF đã thông hết, admin đã có, mà vẫn không thấy cờ ở đâu.

**Bước 5: dùng fragment để Chromium tự scroll.** `page.goto()` với fragment sẽ cuộn phần tử mang id tương ứng vào trong viewport trước khi chụp, và trang `/result/<uuid>` echo lại TARGET nguyên văn, kể cả `#clearance`. Payload cuối:

```
POST /scan   url=http://[::1]:3000/profile#clearance
```

Ảnh trả về hiện nguyên plate. Crop và phóng to lên để đọc từng ký tự, vì số `0` trong `ct10ns` là chữ số không có gạch chéo chứ không phải chữ O.

## Kết quả
```
sun{fr4gm3nt3d_r3fl3ct10ns_1n_th3_futur3}
```

Chạy lại `python exploit.py` từ đầu để xác nhận:

```
[*] /register said: That callsign is already taken.
[+] 201352-byte viewport snapshot -> flag_shot.png
```

Ảnh mới vẫn ra đúng chuỗi cờ đó.
