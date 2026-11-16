# Preview giao diện "Mực & Kim"

Mock tĩnh của giai đoạn 2, **chưa nối vào Jekyll**. Dùng để duyệt hướng mỹ thuật trước khi
động vào `site/`.

## Xem

Mở trực tiếp bằng trình duyệt:

```
home.html      trang chủ
archive.html   thư viện writeups
post.html      một bài dài (OT#007)
```

Hoặc chạy server tĩnh nếu muốn kiểm trên điện thoại cùng mạng LAN:

```bash
cd docs/xian-redesign/preview
python3 -m http.server 8799
```

## Ảnh hero

`assets/hero-desktop.jpg` và `assets/hero-mobile.jpg` **không nằm trong git** — đây là tranh
promotional lấy từ trang tham chiếu, có bản quyền của nhà phát hành. Chạy lại khi cần:

```bash
bash fetch-assets.sh
```

Script tải tranh gốc rồi cắt hai kích thước (1600×900 và 1080×1350), đúng ngân sách
600 KB / 300 KB.

Trước khi đưa lên production phải thay bằng tranh bạn có quyền dùng, hoặc dựng nền SVG.
Bố cục đã tính theo tỉ lệ 16:9 và 4:5 nên đổi ảnh không phải sửa CSS.

## Ảnh chụp

`shots/` chứa ảnh chụp desktop 1440px và mobile 390px của ba trang. Cũng không nằm trong git
vì chứa tranh có bản quyền.

## Chuyển động

Gói hiệu ứng nằm ở `motion.css` + `motion.js`, tách khỏi `xian.css`. Gỡ hai file là về bản tĩnh.

- Nút sóng trên header bật/tắt. Trạng thái lưu ở `ctfwu-motion`, **riêng** với theme
  (`ctf-theme-v2`). `prefers-reduced-motion` thắng khi tải, **kể cả khi storage đã lưu "on"**;
  chỉ cú bấm trong phiên mới bật lại được. Đổi trong lúc mở trang thì cắt ngay.
- Sương, quầng sáng và hạt vàng là CSS animation, chỉ khai báo dưới `html.motion-on`.
  Không có `requestAnimationFrame` cho trang trí.
- Hero ra khỏi màn hình hoặc tab bị ẩn → `html.motion-paused` → `animation-play-state: paused`.
  Không có vòng lặp nào chạy tiếp.
- Reveal dùng `translate` + `opacity`, chỉ gắn khi có `IntersectionObserver`; JS lỗi thì gỡ
  `js-motion` và nội dung hiện ngay. Mỗi phần tử chỉ hiện một lần, không chạy lại khi cuộn lên.
  Khối hero không nằm trong reveal nên luôn hiện; focus vào khối chưa reveal thì hiện tức thì.
- `post.html` không có nền chuyển động. Thanh tiến độ và mục lục đang đọc lấy trực tiếp từ
  `getBoundingClientRect()`, không easing, không transition trên vị trí.

Kiểm nhanh bằng DevTools:

```js
document.documentElement.className          // motion-on / motion-off, motion-paused
document.querySelectorAll('.mote').length   // 18, mobile hiện 6
```

Các control còn lại trong mock — đổi theme, VI/EN, menu, ô tìm kiếm, select sắp xếp — vẫn là
placeholder, bấm không có tác dụng. Chỉ nút chuyển động là hoạt động thật.

