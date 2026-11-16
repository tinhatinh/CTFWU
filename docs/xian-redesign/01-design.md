# Giai đoạn 2 — Thiết kế và chuẩn bị tranh

Ngày: 2026-11-16 · Nhánh `xian-ui` · Trạng thái: **chờ duyệt**, chưa nối vào site thật.

Preview nằm trong repo: `docs/xian-redesign/preview/` — mở `home.html`, `archive.html`,
`post.html`. Ảnh chụp trong `preview/shots/` (cả hai thư mục ảnh đều bị gitignore, xem mục 4).

## 1. Hướng đã chọn

**“Mực & Kim”**: tranh thiên môn vàng son chìm trong mực xanh đêm, khung thư quyển kẻ vàng,
chữ serif cổ điển nhưng vẫn là tiếng Việt có dấu. Không dùng chữ Hán, không dùng logo hay
nhân vật của trang tham chiếu làm nhận diện.

Lý do:

- Trang tham chiếu mạnh vì **tranh toàn chiều ngang + khung vàng + nhịp dọc**. Giữ ba thứ đó,
  đổi toàn bộ chi tiết sang nội dung CTF.
- Chữ tiếng Việt cần dấu; font Hán tự sẽ vỡ dấu hoặc thiếu glyph. Dùng serif có subset Vietnamese.
- Không scroll hijack, không loading screen, không con trỏ tuỳ biến — đúng ràng buộc.

## 2. Token

| Vai trò | Mã | Tương phản trên nền mực |
|---|---|---|
| Nền mực 0 | `#060a10` | — |
| Nền mực 1 | `#0a0f17` | — |
| Nền mực 2 | `#101823` | — |
| Chữ chính | `#eee7d7` | 16,10:1 |
| Chữ phụ | `#a7b2b0` | 9,10:1 |
| Chữ mờ (nhãn mono) | `#7d8a89` | 5,54:1 (4,99:1 trên nền 2) |
| Vàng cổ | `#c9a24d` | 8,27:1 |
| Vàng sáng | `#e2c88b` | 12,16:1 |
| Ngọc bích (nhấn phụ) | `#4aa896` | dùng cho trạng thái, không dùng cho chữ nhỏ |
| Chu sa (con dấu) | `#a8382f` | nền đặc, chữ kem |
| Chữ trên nền vàng | `#1a1206` | 7,73:1 |

Toàn bộ cặp chữ/nền chính đạt ≥4,5:1. Chưa có theme sáng trong bản này.

**Chữ**: `Noto Serif` 500/600/700 cho tiêu đề và số liệu; `Be Vietnam Pro` cho thân bài;
`IBM Plex Mono` cho nhãn, ngày, số thứ tự. Noto Serif tải qua Google Fonts, có subset tiếng Việt.

**Nhịp**: thang 4px; bán kính gần như bằng 0 (1–2px) để giữ cảm giác khung giấy;
đường kẻ vàng 1px, không dùng bóng lớn trừ khung thẻ.

## 3. Bố cục ba trang

### Home — desktop

- Header 66px dính, nền mực mờ, đường vàng 1px ở đáy. Con dấu đỏ 34px + wordmark serif.
- Hero cao `min(72vh, 660px)`, ảnh phủ toàn chiều ngang, lớp phủ chuyển sắc từ trái sang phải
  để chữ nằm trên vùng tối. Tiêu đề 72px, dòng dẫn 46ch, hai nút 46px.
- Dải số liệu 4 cột, kéo lên chồng mép hero 46px, khung vàng.
- Lưới writeup 3 cột, thẻ có ngoặc vàng ở hai góc đối diện, hover nâng 3px.
- Khối thành tích đội dạng bảng trong khung.
- Footer mực, đường vàng, cụm liên kết mono.

### Home — mobile (390px)

- Header 58px; ẩn nav ngang, còn logo + VI/EN + đổi theme + menu (44×44).
- Hero `78vh`, ảnh dọc riêng, lớp phủ mạnh hơn để chữ không chồng lên chi tiết sáng.
- Một cột; dải số liệu 2×2; thẻ xếp dọc; nút chia đôi hàng ngang, cao 46px.

### Archive

- Đầu trang: eyebrow + h1 serif + mô tả.
- Thanh lọc trong khung: ô tìm kiếm 44px, hai select 44px.
- Chip chuyên mục kiểu thẻ tre; chip đang chọn nền vàng chữ mực.
- Hàng bài kiểu mục lục: số thứ tự vàng, tiêu đề serif, pill chuyên mục, tên giải, ngày mono.
  Hover: nền vàng rất nhạt + vạch vàng 2px bên trái.
- Mobile: hàng gập thành hai dòng — tiêu đề, rồi `pill · tên giải · ngày`. Không mất thông tin.
- Chip cuộn ngang có mask mờ ở mép để thấy còn nội dung.

### Post

- Đầu bài: eyebrow giải, h1 serif, mô tả, byline mono.
- Cột đọc tối đa 800px, khung vàng, ngoặc vàng ở hai góc, nền mực sáng hơn nền trang.
- TOC dính bên phải, đường kẻ vàng, mục đang đọc chuyển vàng.
- Code block nền `#04070b`, viền trái vàng, mono 12,5px, cuộn ngang.
- Bảng cuộn ngang trên mobile, không đẩy vỡ bố cục.

## 4. Danh mục asset

| Asset | Kích thước | Dung lượng thực | Ngân sách | Ghi chú |
|---|---|---|---|---|
| `hero-desktop.jpg` | 1600×900 | **126 KB** | ≤600 KB | đạt |
| `hero-mobile.jpg` | 1080×1350 | **121 KB** | ≤300 KB | đạt, crop dọc riêng |
| CSS toàn theme | — | ~23 KB raw / ~4 KB gzip | — | một file, không thư viện |
| JS trang trí | — | 0 KB | ≤20 KB gzip | bản preview chưa cần JS |
| Font serif | woff2 subset | ~23 KB (cả CSS font) | — | một họ, ba độ đậm |
| Ngoặc vàng, con dấu, divider | CSS/SVG | 0 KB file rời | — | vẽ bằng CSS |

Tổng trang chủ: **152 KB**, 4 request, FCP 268 ms (localhost, cache tắt).

**Ảnh hero hiện tại lấy từ trang tham chiếu** (tranh không có chữ). File nằm ở
`preview/assets/`, **bị gitignore**, tải lại bằng `bash preview/fetch-assets.sh`.
Đây là tranh có bản quyền của nhà phát hành game; đăng công khai là rủi ro pháp lý.
Trước khi deploy cần một trong ba:

1. Bạn xác nhận có quyền dùng, mình đưa ảnh vào `site/assets/img/` và ghi nguồn; hoặc
2. Thay bằng tranh bạn sở hữu / đặt vẽ theo brief ở mục 5; hoặc
3. Mình dựng nền SVG thủ công (núi mực, mây, hạt vàng) — nhẹ hơn, không vướng bản quyền.

Khung, bố cục, tỉ lệ đã tính theo ảnh 16:9 và 4:5, đổi ảnh không phải sửa CSS.

## 5. Art brief (nếu đặt vẽ)

> Tranh phong cảnh tiên hiệp, khổ ngang 16:9 và một bản dọc 4:5. Thiên môn/đền đài xếp lớp
> lùi vào sương, bậc đá dẫn lên, vài tháp chuông xa, mây cuộn ở chân. Bảng màu: mực xanh đêm
> `#060a10` → `#0d1620`, ánh vàng cổ `#c9a24d` ở cổng và viền mây, điểm ngọc bích `#4aa896`
> rất nhỏ. Có hạt sáng li ti, không chói. **Chừa 45% bên trái thoáng và tối** để đặt tiêu đề.
> Không chữ, không logo, không nhân vật có mặt rõ. Chất liệu: sơn mực đương đại, nét cọ rõ.

## 6. Đã kiểm trong bản preview

- Tương phản: mọi cặp chữ/nền chính ≥4,99:1 (bảng ở mục 2).
- Mobile 390px: không tràn ngang; hàng archive đủ chuyên mục, giải, ngày.
- Nút và vùng chạm ≥44px (search, select, chip, nút hero, icon header).
- `prefers-reduced-motion` đã tắt transition.
- Bàn phím: thứ tự tab theo header → hero → nội dung; chưa kiểm focus-visible đầy đủ.

## 7. Chưa làm (giai đoạn 3–4)

- Chưa nối `?theme=xian` vào Jekyll; chưa sửa CSP hash, chưa thêm vào `themes.html`.
- Chưa có theme sáng, chưa có nút đổi theme thật trong preview.
- Chưa làm trang Thành tích, chứng chỉ, giới thiệu, categories/tags, 404, event.
- Chưa có hiệu ứng vào trang, chưa tối ưu archive index.
- Chưa chạy Lighthouse; số ở trên là đo phòng lab bằng script.

## 8. Cần duyệt

1. Hướng “Mực & Kim” và bố cục ba trang như ảnh trong `preview/shots/`.
2. Nguồn tranh hero: xác nhận quyền dùng, hay đặt vẽ, hay chuyển sang SVG thủ công.
3. Font Noto Serif (thêm ~23 KB) — giữ hay đổi sang serif hệ thống.
4. Theme sáng: hiểu là giấy ngà + cùng hoa văn vàng; xác nhận lại nếu ý bạn khác.
