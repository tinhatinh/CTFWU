# STATUS — CookieCorp: ĐÃ GIẢI

`https://tomorrow.web.2026.sunshinectf.games/` · web 479đ · cờ `sun{c00kie_jar_0verfl0w_ev1cts_the_chief}`

Lời giải nằm trong `writeup.md`, cờ trong `flag.txt`. Bài này đã chuyển từ `_wip/` ra thư mục
chính của SunshineCTF.

## Cơ chế thắng

`mixer.js` đặt mỗi ingredient thành một cookie (`document.cookie = name + '=' + value + '; path=/'`)
rồi mới gọi `POST /api/seal`, nên request stamp của bot mang đúng jar mà mình điều khiển. Cookie
`role` do server set là `HttpOnly` nên JavaScript không ghi đè được, nhưng jar của Chromium chỉ
chứa khoảng 180 cookie mỗi domain: **250 ingredient giả ngắn** (`x0000=v0` ...) tràn jar, cookie
`role` cũ bị evict, và `role=chief` đặt ở cuối danh sách trở thành cookie `role` duy nhất bot gửi
lên. `/api/seal` thấy `chief` → Golden Seal → cờ.

## Chỉnh lại các kết luận sai trong hồ sơ cũ

Ba chỗ dưới đây từng bị ghi là "đã loại", và chúng sai ở chỗ cùng một chỗ:

- **"role cookie chỉ để trang trí"**. Đúng là `/dashboard` giống nhau từng byte với mọi giá trị
  `role`, nhưng `/api/seal` lại đọc `role` để quyết định loại dấu. Đo ở trang không có nghĩa là đo
  ở quyết định.
- **"Chrome không evict cookie của worker"**. Test cũ gửi 290 ingredient tối đa độ dài (5-6 KB) và
  thấy vẫn `standard`, rồi kết luận không có eviction. Thật ra nó chạm **ngưỡng byte** của header
  trước khi chạm **ngưỡng số lượng**, nên phép thử không bao giờ ở trong vùng mà jar bị tràn. Với
  cookie ngắn (250 cái, ~2.3 KB) thì ngưỡng số lượng mới là thứ kích hoạt, và eviction xảy ra.
  Hai giới hạn này phải thử riêng.
- **"mỗi batch chỉ có đúng một lần inspector"** vẫn đúng, nên payload phải đủ ngay từ lần submit
  đầu; không có chuyện resubmit để sửa.

Ghi chú thêm: `name`/`value` ingredient bị strip `;`, dấu cách và `=`, nên không inject được cookie
attribute; con đường duy nhất là số lượng.

## Còn giữ lại

Toàn bộ nhánh đã loại thật (mass assignment, prototype pollution, NoSQL, SSTI/EJS, XSS, prompt
injection vào title, credential attack vào username nghi của staff) vẫn có giá trị và nằm trong
`notes.md` / `notes-closed.md` / `analysis/`.
