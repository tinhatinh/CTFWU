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
- **Thứ tự ưu tiên**: `override` (chỉ đặt khi bấm nút trong phiên) → `prefers-reduced-motion`
  → lựa chọn đã lưu. Nghĩa là **reduce thắng khi tải, kể cả storage đã lưu `"on"`**; lựa chọn
  đã lưu chỉ được dùng lại khi hệ thống không giảm chuyển động. Đổi reduce trong lúc mở trang
  thì `override` bị xoá và hiệu ứng dừng ngay, nhưng storage vẫn giữ nguyên.
  `pref` trong bộ nhớ **luôn được cập nhật cùng lúc với storage** mỗi lần bấm nút; nếu không,
  sau khi `override` bị xoá, `enabled()` sẽ đọc lại giá trị cũ lúc tải.
- **Reveal an toàn**: khối hero **không** nằm trong reveal nên luôn hiện, không phụ thuộc JS.
  Khối khác chỉ ẩn khi có `js-motion`; lỗi script bất kỳ → gỡ `js-motion` và hiện tất cả;
  focus bàn phím vào khối chưa reveal → hiện ngay, không transition; có lưới an toàn 1,2 s
  ép hiện những khối đang nằm trong màn hình.
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
| `motion.css` | 5.333 B raw / **1.929 B gzip** | ≤5 KB gzip |
| `motion.js` | 6.875 B raw / **2.505 B gzip** | ≤12 KB gzip |
| Asset trang trí mới | **0 KB** (gradient + CSS, không tải ảnh) | ≤120 KB desktop / ≤60 KB mobile |
| Ảnh hero | 126 KB / 121 KB (không đổi) | 600 / 300 KB |

Không thêm request nào. Không thư viện ngoài.

## 4. Kết quả kiểm

Đo trên Chromium 154 và Firefox (geckodriver), máy ảo, GPU phần mềm, localhost.

| Hạng mục | Kết quả |
|---|---|
| Pause khi hero offscreen | `glow/mist/mote` → `paused`, có class `motion-paused` |
| Pause khi chuyển sang tab khác **thật** | tab 2 active → tab 1 `hidden:true`, `motion-paused`; đóng tab 2 → `visible`, chạy lại |
| Quay lại | `running`, không nhân node (18 hạt trước/sau) |
| Tắt bằng nút | `animation-name: none`, `.hero-stage` `display:none` |
| Bật lại | animation trở lại, tổng node `.mote` + `.reveal` không đổi (28 → 28) |
| Long task khi cuộn | **0** task >50 ms ở 1440/1024/768/390/360 |
| Long task khi tải | **0** ở 5/5 lần chạy lại (xem mục 5) |
| FPS (rAF đếm trong 3,2 s) | 60 desktop, 60 tablet, 60 mobile |
| CLS | 0,0037 home desktop; 0 archive/post; 0 mobile |
| Tràn ngang | 0 ở 360/390/768/1024/1440 và zoom 200% (layout 720) |
| JS tắt | không class nào được thêm, `.reveal` opacity 1, nút ẩn |
| Ảnh hero lỗi | chiều cao hero giữ nguyên, không tràn, chữ vẫn hiện |
| Storage bị chặn | trang chạy, nút vẫn đổi trạng thái trong phiên |
| Back/Forward | giữ `motion-on`, 18 hạt, không nhân bản |
| Firefox | bật/tắt đúng; `ui.prefersReducedMotion=1` → tắt khi tải, bật lại được |
| Đồng bộ: bật → tắt → reduce on → reduce off (Chromium) | off → off → **off** |
| Đồng bộ: tắt → bật → reduce on → reduce off (Chromium) | on → off → **on** |
| Bật/tắt + reload (Chromium và Firefox) | giữ đúng on/off mới nhất |
| Post — thanh tiến độ | đếm pixel vàng ở hàng 0: **0** (đầu) → **620** (giữa, `scaleX` 0,489) → **1271** (hết, `scaleX` 1) |
| Post — mục lục | mục đang đọc đổi theo heading, có `aria-current` |
| Focus vào khối chưa reveal | `is-in` + `opacity: 1` ngay, `transition: 0s` |
| Lỗi script (`ErrorEvent`) | gỡ `js-motion`, 8 khối đang ẩn → 0 |

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

4. **Thanh tiến độ không hiện.** `.reading-progress > div` đặt `width: 0` nên `scaleX()` nhân
   với 0. Lần kiểm trước chỉ đọc `getComputedStyle().transform` nên vẫn "đạt" — sai cách kiểm.
   Sửa `width: 100%` + `transform: scaleX(0)`, và từ giờ kiểm bằng **pixel** trên ảnh chụp.

5. **`storage = "on"` vượt `prefers-reduced-motion` khi tải.** `enabled()` trả thẳng `pref`.
   Sửa bằng mô hình `override`: reduce luôn thắng lúc tải, chỉ cú bấm trong phiên mới bật lại được.

6. **Reveal có thể giấu nội dung.** Hero từng nằm trong reveal và được mở bằng rAF; nếu rAF bị
   hoãn hoặc script lỗi thì chữ bị ẩn. Bỏ hero khỏi reveal, thêm `:focus-within` hiện tức thì,
   `focusin` mở khối, `window.onerror` gỡ `js-motion`, và lưới an toàn 1,2 s.
   Đo lại: long task lúc tải 63–68 ms biến mất 5/5 lần — thủ phạm là lớp compositor cho khối
   chữ hero `opacity: 0` ở lần paint đầu.

7. **Lựa chọn mới không được ghi vào `pref`.** Handler nút chỉ đặt `override` và `save()`, nên
   sau khi `override` bị media change xoá, `enabled()` đọc lại `pref` cũ lúc tải. Chuỗi tái hiện:
   đang bật → tắt (storage `"off"`, `pref` vẫn `null`) → reduce bật → reduce tắt → hiệu ứng tự bật
   lại. Sửa: `pref = override` trước `save()`.
   Phạm vi kiểm: **Chromium** kiểm đủ chuỗi reduce on/off trong cùng trang, cả hai chiều bật→tắt và
   tắt→bật, cộng reload. **Firefox** chỉ kiểm bật/tắt và reload — `ui.prefersReducedMotion` đặt lúc
   khởi động nên không đổi media trong phiên được; chuỗi reduce on/off **chưa** kiểm trên Firefox.

## 6. Bằng chứng

Trong `preview/shots/` (không commit vì chứa tranh có bản quyền):

| File | Nội dung | Dài |
|---|---|---|
| `motion_desktop.mp4` | hero, cuộn xuống/lên, tắt rồi bật | 13,9 s, 432 khung |
| `motion_mobile.mp4` | hero 390px, cuộn, về đầu trang | 11,6 s, 569 khung |
| `motion_pause.mp4` | tắt → bật → tắt | 9,5 s, 180 khung |
| `motion_reading.mp4` | cuộn trang bài, thanh tiến độ và mục lục chạy theo | 12,0 s, 148 khung |
| `progress_top/mid/end.png` | thanh tiến độ ở 0 / 49% / 100% | — |
| `reduced_stored_on.png` | storage `"on"` + reduce → giao diện tĩnh | — |
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
- Hero **không còn hiệu ứng vào trang**: đổi lấy việc nội dung trên màn hình đầu luôn hiện
  và bỏ được 63–68 ms long task ở lần paint đầu. Sương/quầng/hạt vẫn tạo chuyển động ở hero.
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
