# Tích hợp Jekyll — theme xian (bản xem trước)

Ngày: 2026-11-16 · Nhánh `integrate-xian`, tách từ `38d048d` · `main` = `47cd195`
Trạng thái: **chưa đổi mặc định, chưa merge, chưa deploy**.

## 1. Baseline trước khi sửa

| Mục | Giá trị |
|---|---|
| HEAD lúc bắt đầu | `38d048d` (nhánh `motion`) |
| `origin/main` | `47cd195`, không tiến thêm trong phiên |
| Working tree | sạch, không có thay đổi chưa commit của chủ repo |
| Generator | 12 event, 283 bài mỗi ngôn ngữ |
| `test_editor.py` | 26 test OK |
| `test_github_editor.cjs` | pass |
| Jekyll VI/EN | build xong, cảnh báo sẵn có `tags/log-analysis` trùng slug |
| htmlproofer | 2011 link, 1728 file, pass |

Bản build trước khi sửa lưu ở `/tmp/baseline/{vi,en}` cùng hash phần chữ của 566 trang bài.

## 2. File thay đổi

| File | Việc |
|---|---|
| `site/assets/css/xian.css` | **mới** — toàn bộ theme, scope `html[data-theme="xian"]` |
| `site/assets/css/motion.css` | **mới** — sương/quầng/hạt, reveal, nút bật/tắt |
| `site/assets/js/motion.js` | **mới** — máy trạng thái chuyển động |
| `site/assets/img/hero-fallback.svg` | **mới** — nền mực tự vẽ, dùng khi thiếu tranh |
| `site/_layouts/home.html` | hero + dải số liệu + lưới thẻ, lấy số liệu thật |
| `site/_layouts/default.html` | nạp CSS/JS mới, nút chuyển động, `xian` trong bootstrap và thanh preview, CSP hash mới |
| `site/assets/js/site.js` | `xian` vào danh sách theme; nút sáng/tối nhớ theme tối gần nhất; reveal nhường cho `motion.js` khi ở xian |
| `site/assets/css/campus.css` | khối `prefers-reduced-motion` chỉ áp khi chưa bật lại trong trang |
| `site/assets/css/themes.css` | thêm `xian` vào selector của Theme Lab; giữ khối tiêu đề home đúng kích thước cũ cho terminal/paper/aurora |
| `site/themes.html` | tab/iframe/link thứ tư, sửa lời giới thiệu "bốn hướng" |
| `site/_data/interface.json` | nhãn `motion_off` / `motion_on` cho VI và EN |
| `tools/build_site.py` | hash cache-busting cho `xian`, `motion`, `motion_js` |
| `.gitignore` | chặn hai ảnh hero placeholder của publisher |

Không file nào trong `<Event>/`, `tools/*.json` hay nguồn writeup bị sửa.

## 3. Cách tích hợp

**Theme.** `xian` là theme thứ tư, chỉ bật khi `?theme=xian` hoặc đã lưu trong
`ctf-theme-v2`. Mặc định vẫn là `terminal`. Bootstrap inline trong `default.html` nhận
`terminal|paper|aurora|xian|light`; CSP hash đã tính lại
(`sha256-vmwmu7ivq/dOMYdhLnznJ5jzPAz/tYv7qqN6bywBkdY=`), không nới CSP.

**Nút sáng/tối.** Lưu theme tối gần nhất vào `ctf-theme-dark`. Từ xian bấm nút → `light`;
bấm lần nữa → quay lại `xian`, không mất đường về.

**Chuyển động.** `motion.js` là bộ điều khiển duy nhất khi ở xian; `site.js` bỏ qua reveal
nếu `data-theme="xian"` (đã kiểm: 0 lời gọi `Element.animate` trên xian, 9 trên terminal).
Thanh tiến độ và mục lục vẫn do `site.js` phụ trách, không làm lại.
Ưu tiên trạng thái: `override` trong phiên → `prefers-reduced-motion` → lựa chọn đã lưu;
`pref` được đồng bộ mỗi lần bấm. Khoá lưu riêng `ctfwu-motion`.

**Hero.** Ảnh là lớp `background-image` theo media query, không tải cả hai: desktop
`hero-desktop.jpg` → dự phòng `hero-fallback.svg`; mobile `hero-mobile.jpg` → cùng dự phòng.
Ảnh publisher **không nằm trong git**; bản public dùng SVG cho tới khi có tranh có quyền.

**Theme cũ.** Home dùng chung markup `.hero`; ngoài `data-theme="xian"`, khối này được
`themes.css` thu về đúng kích thước `.page-heading` cũ (65px/40px, h1 54px, cột 850px) và ẩn
`.hero-art`, `.hero-stage`, `.hero-ornament`. Đã kiểm terminal ở 1440 và 390: không tràn,
không đổi bố cục.

**Đường dẫn.** Mọi URL đi qua `relative_url`; ảnh trong CSS dùng đường dẫn tương đối nên
đúng cả `/CTFWU/` và `/CTFWU/en/` (đã kiểm `background-image` của bản EN trỏ vào
`/CTFWU/en/assets/img/...`).

## 4. Đối chiếu nội dung

| Kiểm | Kết quả |
|---|---|
| Hash phần chữ của 566 trang bài (VI+EN) | **0 thay đổi**, 0 thiếu |
| Tập URL VI | 864 → 864, không thêm/bớt |
| Tập URL EN | 864 → 864, không thêm/bớt |
| File nguồn writeup | `git status` không có thay đổi ngoài `site/`, `tools/`, `.gitignore` |

Markup bài chỉ đổi ở phần trình bày; phần chữ, code, flag, bảng, math giữ nguyên.

## 5. Kiểm tra

| Hạng mục | Kết quả |
|---|---|
| Generator `--require-solve-dates` | 12 event, 283 bài × 2 |
| `test_editor.py` / `test_github_editor.cjs` | 26 test OK / pass |
| Jekyll VI + EN | build xong, chỉ còn cảnh báo trùng tag sẵn có |
| htmlproofer | 2018 link nội bộ, 1728 file, **pass** |
| Theme xian bật/tắt | xian → light → xian, `ctf-theme-dark` giữ đúng |
| Thanh preview | ẩn khi rời chế độ xem thử |
| Motion + storage `"on"` + reduce | tắt khi tải, storage giữ `"on"` |
| Bấm nút khi reduce đang bật | bật lại được (đã sửa `campus.css`) |
| Reveal trùng | xian: 0 WAAPI, 7/7 `.reveal` do `motion.js`; terminal: 9 WAAPI như cũ |
| Focus vào thẻ chưa reveal | hiện ngay, `opacity: 1`, `transition: 0s` |
| JS tắt | không lớp reveal nào bị giấu, nút chuyển động ẩn, theme rơi về `terminal` |
| Ảnh hero lỗi | nền SVG dự phòng hiện, chiều cao hero không đổi |
| Chuyển tab thật | `hidden: true` → `motion-paused`; quay lại → chạy tiếp |
| Archive lọc thật | `pwn` + chip Pwn → 56 bài, query `?q=pwn&category=Pwn` |
| Post | tiến độ 0 → 444 px khi cuộn, mục lục đổi theo heading |
| EN | nhãn "Turn motion off", hero trỏ `/CTFWU/en/assets/img/` |
| Console | không lỗi trên 6 trang đã kiểm |
| Viewport | 360/390/768/1024/1440 không tràn ngang; bảng thành tích cuộn ngang ở 390 |

## 5b. Sửa sau review

1. **Mất theme xian khi điều hướng / đổi VI–EN.** `?theme=` chỉ nằm trong URL một trang, còn
   `site.js` dựng lại query khi lọc nên làm rơi tham số. Sửa:
   - Bootstrap ghi theme hợp lệ từ URL vào `ctf-theme-preview`; đọc lại khi trang sau không có query.
   - `ctf-theme-v2` vẫn là lựa chọn mặc định của người dùng, không bị preview ghi đè.
   - Bộ lọc và link đổi ngôn ngữ giữ `theme=` nếu đang có.
   - Link "Mặc định" trong thanh preview và nút sáng/tối xoá `ctf-theme-preview`.
2. **Nút tắt chuyển động không điều khiển `site.js`.** `animate()` chỉ kiểm reduced motion.
   Sửa: `animate()` trả về sớm khi `<html>` có `motion-off`; `site.js` mở hook
   `window.CTFWU.cancelMotion` để `motion.js` huỷ animation đang chạy lúc tắt.
3. **Storage bị chặn làm `?theme=xian` mất tác dụng.** Cả khối bootstrap nằm trong một `try`,
   nên `localStorage.getItem` ném lỗi là bỏ luôn phần đọc URL. Sửa: đọc storage trong `try`
   riêng; theme hợp lệ từ URL vẫn áp. CSP hash tính lại (`sha256-rAt6crw3RPcg0NWgBNe6jt8sRReoXNBH7EUnv7OlUEU=`).

Kiểm lại chuỗi thao tác:

| Bước | Kết quả |
|---|---|
| `/archives/?theme=xian` → tìm `pwn` | URL `?q=pwn&theme=xian`, theme xian |
| → chip Pwn | `?q=pwn&category=Pwn&theme=xian`, 56 bài, theme xian |
| → EN | `/CTFWU/en/archives/?q=pwn&category=Pwn&theme=xian`, 56 bài, theme **xian** |
| → EN home không query, rồi reload | vẫn xian (`ctf-theme-preview`) |
| → "Mặc định" | xoá preview, về terminal |
| `?theme=default` trực tiếp | về terminal, preview bị xoá |
| Motion ON rồi lọc | 5 animation (đo được) |
| Tắt giữa lúc lọc | 2 animation đang chạy → `idle` |
| Motion OFF rồi lọc + đổi sort | **0** animation |
| Storage bị chặn + `?theme=xian` | theme xian, hero 648 px |

## 6. Đo (lab, localhost, cache tắt)

| Trang | HTML gzip | Tổng transfer | Request | FPS | Long task |
|---|---|---|---|---|---|
| Home xian, motion ON | 5,4 KB | 331 KB | 12 | 61 | 0 |
| Home xian, motion OFF | 5,4 KB | 331 KB | 12 | 60 | 0 |
| Home xian, reduce | 5,4 KB | 331 KB | 12 | 61 | 0 |
| Archive | 475 KB | — | — | — | — (nặng sẵn từ trước) |

CSS/JS thêm vào: `xian.css` 6,2 KB gzip, `motion.css` 2,2 KB, `motion.js` 2,2 KB.

## 7. Còn thiếu và giới hạn

- **Tranh hero cuối chưa có.** Bản local dùng JPG của publisher (đã gitignore); bản public
  sẽ dùng `hero-fallback.svg` cho tới khi có tranh có quyền.
- **Archive 475 KB gzip** vẫn là vấn đề lớn nhất về hiệu năng, nằm ngoài phạm vi vòng này.
- Chưa kiểm Safari/iOS và thiết bị thật; số FPS là đếm khung trên máy ảo.
- Với JS tắt, `?theme=xian` không áp được (theme do JS đọc), trang rơi về `terminal`.
- Bảng thành tích trên mobile phải cuộn ngang; chưa có `tabindex` cho vùng cuộn đó.

## 8. Rollback

Toàn bộ nằm trên `integrate-xian`. `git checkout main` là về nguyên trạng; hoặc revert
commit tích hợp. Không có thay đổi dữ liệu, không có migration.

## 9. Xem trước

```bash
cd /home/tinhatinh/CTFWU
bash /tmp/rebuild.sh            # generator + jekyll + lắp _site
python3 -m http.server 8800 --bind 127.0.0.1 --directory _site
# mở http://127.0.0.1:8800/CTFWU/?theme=xian
```

Bằng chứng trong `docs/xian-redesign/preview/shots/`:
`motion_jx_home.mp4`, `motion_jx_archive.mp4`, `motion_jx_post.mp4`,
`jx_home_d.png`, `m_top.png`, `jx_arch_filtered.png`, `jx_post_top.png`,
`jx_comp_d.png`, `jx_fallback.png`, `jx_en_home.png`.
