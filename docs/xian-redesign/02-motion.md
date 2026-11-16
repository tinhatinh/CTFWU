# Gói chuyển động P0 — preview "Mực & Kim"

Ngày: 2026-11-16 · Nhánh `motion`, tách từ `xian-ui` tại `c17c304` · Baseline site: `47cd195`

Phạm vi: **chỉ `docs/xian-redesign/preview/` và tài liệu**. Không nối vào Jekyll, không sửa
nguồn writeup, không merge, không deploy.

## 1. Kiến trúc

| File | Vai trò |
|---|---|
| `preview/motion.css` | toàn bộ animation, reveal, focus/press, thanh tiến độ |
| `preview/motion.js` | máy trạng thái, lưu lựa chọn, pause, reveal, tiến độ + mục lục |
| `preview/xian.css` | chỉ sửa một khối `prefers-reduced-motion` để không đè lựa chọn bật lại |

Trạng thái nằm trên `<html>`:

| Class | Nghĩa |
|---|---|
| `motion-on` | bật; **mọi** khai báo `animation` chỉ tồn tại dưới class này |
| `motion-off` | tắt; `animation-name` về `none`, `.hero-stage` ẩn |
| `motion-paused` | hero ngoài màn hình **hoặc** tab ẩn; đặt `animation-play-state: paused` |
| `js-motion` | reveal đang hoạt động; gỡ class là mọi nội dung hiện ngay |
| `motion-init` | JS đã chạy xong; chỉ khi có class này nút bật/tắt mới hiện |

Không có `requestAnimationFrame` cho trang trí. Sương, quầng và 18 hạt đều là CSS animation,
nên "dừng" là đổi thuộc tính CSS, không phải huỷ vòng lặp.

Reveal dùng `translate` + `opacity` (không dùng `transform`) để không đè `transform` của hover thẻ.
Mỗi phần tử chỉ nhận `is-in` một lần rồi `unobserve` — cuộn lên xuống không chạy lại.

## 2. Hành vi

- **Nút bật/tắt**: icon sóng trên header, `aria-pressed`, nhãn đổi theo trạng thái.
  Lưu ở `ctfwu-motion`, **riêng** với `ctf-theme-v2`. Storage bị chặn thì vẫn dùng được
  trong phiên, chỉ mất ghi nhớ.
- **Reduced motion**: mặc định tắt khi `prefers-reduced-motion: reduce`. Đổi trong lúc mở trang
  → hệ thống thắng, lựa chọn đã lưu bị bỏ. Người dùng vẫn có thể chủ động bật lại bằng nút.
- **Pause**: `IntersectionObserver` trên `.hero` + `visibilitychange`. Hero ra khỏi màn hình
  hoặc tab ẩn → `motion-paused`. Quay lại → chạy tiếp.
- **Hero mobile**: `<picture>` với `source (max-width: 640px)` trỏ `hero-mobile.jpg` (1080×1350).
  `object-position` đặt riêng cho mobile (`50% 50%`) và desktop (`62% 42%`); toạ độ quầng sáng
  cũng đặt riêng (`--gate-x/--gate-y` = `50%/40%` và `62%/42%`), không suy từ desktop.
- **Mobile mặc định**: một lớp sương (ẩn `::after`), 6 hạt, cùng microinteraction và reveal.
- **Trang post**: không có `.hero-stage`, không có `.reveal`. Thanh tiến độ và mục lục đang đọc
  lấy trực tiếp `getBoundingClientRect()`, gán `scaleX()` không transition, không easing.

## 3. Ngân sách đo được

| Hạng mục | Thực tế | Ngân sách |
|---|---|---|
| `motion.css` | 5.118 B raw / **1.851 B gzip** | ≤5 KB gzip |
| `motion.js` | 5.505 B raw / **2.058 B gzip** | ≤12 KB gzip |
| Asset trang trí mới | **0 KB** (gradient + CSS, không tải ảnh) | ≤120 KB desktop / ≤60 KB mobile |
| Ảnh hero | 126 KB / 121 KB (không đổi) | 600 / 300 KB |

Không thêm request nào. Không thư viện ngoài.

## 4. Kết quả kiểm

Đo trên Chromium 154 và Firefox (geckodriver), máy ảo, GPU phần mềm, localhost.

| Hạng mục | Kết quả |
|---|---|
| Pause khi hero offscreen | `glow/mist/mote` → `paused`, có class `motion-paused` |
| Pause khi tab ẩn (giả lập `document.hidden`) | `paused` |
| Quay lại | `running`, không nhân node (18 hạt trước/sau) |
| Tắt bằng nút | `animation-name: none`, `.hero-stage` `display:none` |
| Bật lại | animation trở lại, tổng node `.mote` + `.reveal` không đổi (28 → 28) |
| Long task khi cuộn | **0** task >50 ms ở 1440/1024/768/390/360 |
| Long task khi tải | **0** sau khi bỏ một lần đọc layout cưỡng bức (xem mục 5) |
| FPS (rAF đếm trong 3,2 s) | 60 desktop, 60 tablet, 60 mobile |
| CLS | 0,0037 home desktop; 0 archive/post; 0 mobile |
| Tràn ngang | 0 ở 360/390/768/1024/1440 và zoom 200% (layout 720) |
| JS tắt | không class nào được thêm, `.reveal` opacity 1, nút ẩn |
| Ảnh hero lỗi | chiều cao hero giữ nguyên, không tràn, chữ vẫn hiện |
| Storage bị chặn | trang chạy, nút vẫn đổi trạng thái trong phiên |
| Back/Forward | giữ `motion-on`, 18 hạt, không nhân bản |
| Firefox | bật/tắt đúng; `ui.prefersReducedMotion=1` → tắt khi tải, bật lại được |
| Post | thanh tiến độ `scaleX` 0 → 0,3455 → 0,9144; mục lục đổi theo heading |

Không có tác vụ JS trang trí >50 ms. Con số 60 fps là **đếm khung bằng rAF trên máy ảo**,
không phải kết luận về máy thật.

## 5. Lỗi phát hiện và đã sửa

1. **Long task 60–71 ms lúc tải.** Nguyên nhân: `hero.getBoundingClientRect()` trong lúc khởi tạo
   buộc layout đồng bộ ngay sau khi parse. Bỏ lần đọc đó (observer tự báo ở frame sau) → 0 long task.
   Đã xác nhận bằng cách chặn `motion.js`/`motion.css`: có file thì có task, chặn thì hết.
2. **Pause không có tác dụng.** Shorthand `animation` khai báo sau đã reset `animation-play-state`
   về `running`. Chuyển khối pause xuống cuối file → pause thắng.
3. **Tràn ngang 2 px ở 360/390 và 58 px ở 768.** Nút mới làm `.header-actions` vượt khung.
   Sửa: gap header nhỏ lại, icon 44×44, ẩn `.gh` dưới 900 px, bảng prose cuộn ngang từ 900 px.

## 6. Bằng chứng

Trong `preview/shots/` (không commit vì chứa tranh có bản quyền):

| File | Nội dung | Dài |
|---|---|---|
| `motion_desktop.mp4` | hero, cuộn xuống/lên, tắt rồi bật | 13,9 s, 432 khung |
| `motion_mobile.mp4` | hero 390px, cuộn, về đầu trang | 11,6 s, 569 khung |
| `motion_pause.mp4` | tắt → bật → tắt | 9,5 s, 180 khung |
| `p0_d_on.png` / `p0_d_off.png` | so bố cục bật/tắt desktop | — |
| `p0_m_on.png` / `p0_m_off.png` | so bố cục bật/tắt mobile | — |
| `hdr_m.png` | header mobile sau khi thêm nút | — |

Video quay bằng CDP screencast ở đúng viewport, không cắt ghép.

## 7. Chưa làm và giới hạn

- **P1 (parallax con trỏ) không làm** — theo yêu cầu, chỉ xem xét sau khi P0 được duyệt.
- **P2 (video nền) không làm.**
- Chưa có điện thoại thật: không đo pin, không đo cảm giác cuộn trên máy thật.
- Chưa kiểm Safari/iOS.
- Số liệu là **phòng lab** (localhost, máy ảo, GPU phần mềm). Không phải LCP/INP thực địa.
- Menu, đổi theme, VI/EN, ô tìm kiếm, select sắp xếp trong mock vẫn là placeholder.
- Nút theme và nút chuyển động nằm cạnh nhau; khi mở menu thật cần kiểm lại z-index, focus trap
  và anchor offset (hiện mock chưa có menu mở).

## 8. Khi tích hợp vào site thật

- Map selector preview sang `site/_layouts` + `site/_includes`; giữ nguyên ID/`data-*` trong
  `00-audit.md` mục 5.
- Thêm `xian` vào script inline đọc `?theme=` → **tính lại CSP hash**.
- Tránh chạy trùng reveal với `site.js` (site.js đã có `IntersectionObserver` cho
  `.page-heading, .stats-strip, .feature-card, .certificate-card`). Chọn một nơi duy nhất.
- Ảnh hero phải thay bằng tranh có quyền dùng trước khi deploy.
- Chạy lại toàn bộ kiểm tra baseline: generator `--require-solve-dates`, `test_editor.py`,
  `test_github_editor.cjs`, Jekyll VI/EN, htmlproofer.
