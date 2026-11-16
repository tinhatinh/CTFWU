# CTFWU → giao diện tiên hiệp: Audit giai đoạn 1

Ngày: 2026-11-16 · Nhánh `xian-ui` · Chưa thay đổi UI.

## 0. Cảnh báo bảo mật

Một GitHub personal access token đã được dán trực tiếp vào phiên chat. Giá trị đó phải coi như
đã lộ: nó nằm trong lịch sử hội thoại và log. **Hãy thu hồi (revoke) ngay** tại
<https://github.com/settings/tokens> và tạo token mới nếu cần. Tài liệu này không ghi lại token,
không dùng token cho bất kỳ lệnh nào. Editor trên site đã có luồng nhập token riêng, không cần
đưa token vào code hay prompt.

## 1. Baseline

| Mục | Giá trị |
|---|---|
| Commit gốc | `47cd195` (2026-11-16), `origin/main` |
| Nhánh làm việc | `xian-ui`, tách từ `main` tại commit trên |
| Working tree trước khi sửa | sạch |
| Site đang chạy | <https://tinhatinh.github.io/CTFWU/> |
| Tham chiếu mỹ thuật | <https://xian.leiting.com/> (chỉ tham chiếu bố cục/không khí, không dùng asset) |

Ghi chú: đầu phiên `main` ở `93ed9a1`; trong lúc làm, CI đẩy thêm ba commit
"Update CTFTime team results" lên `47cd195`. Baseline lấy theo `origin/main` mới nhất.

Lệnh build đúng theo workflow, chạy lại tại máy:

```bash
python3 tools/build_site.py --require-solve-dates
python3 tools/test_editor.py
node tools/test_github_editor.cjs
bundle exec jekyll b -s _site_src    -d _build/vi/CTFWU
bundle exec jekyll b -s _site_src_en -d _build/en/CTFWU/en
bundle exec htmlproofer _site --disable-external \
  --ignore-urls "/^http:\/\/127.0.0.1/,/^http:\/\/0.0.0.0/,/^http:\/\/localhost/"
```

Kết quả baseline:

- Generator: `[vi] 12 event, 283 bai` / `[en] 12 event, 283 bai`, ~81 MB mỗi cây.
- `tools/test_editor.py`: 26 test, OK.
- `tools/test_github_editor.cjs`: pass (owner, UTF-8, conflict, bilingual commit, logout, concurrent push).
- Jekyll: build xong cả hai cây, có **cảnh báo sẵn có** `Conflict: tags/log-analysis/index.html`
  (hai tag cùng slug). Không phải lỗi mới, ghi nhận để không quy sai khi so sánh.
- `_site`: 2118 file, 211 MB; htmlproofer: **2011 internal link, 1728 file, pass**.

## 2. Stack thật

```
<Event>/<challenge>.md | writeup.md        ← nguồn nội dung (không sửa)
site/                                      ← nguồn giao diện Jekyll (sửa ở đây)
tools/build_site.py                        ← sinh _site_src, _site_src_en
        ↓
_site_src (VI, baseurl /CTFWU)  +  _site_src_en (EN, baseurl /CTFWU/en)
        ↓  jekyll build
_build/vi/CTFWU  +  _build/en/CTFWU/en  →  _site/CTFWU  (+ /en)
        ↓  upload-pages-artifact → deploy-pages
```

- `_site_src`, `_site_src_en`, `_build`, `_site`, `vendor` đều **sinh tự động và bị gitignore**.
  Mọi thay đổi giao diện phải nằm trong `site/`; sửa thẳng thư mục sinh sẽ bị ghi đè.
- CI (`pages-deploy.yml`) chạy: fetch CTFTime → generator `--require-solve-dates` → 2 test →
  Jekyll 2 cây → htmlproofer → deploy. Lịch chạy 07:00 và 19:00 UTC+7.
- Plugin `site/_plugins/ctfw.rb` tự thêm baseurl vào mọi `src|href="/assets/…"` sau khi render.
  Vì vậy trong layout nên viết `/assets/...`, không tự ghép baseurl.

## 3. Bản đồ route và chức năng

| Route | Layout | Chức năng phụ thuộc JS | Ghi chú |
|---|---|---|---|
| `/` | `home.html` | reveal on scroll, đếm số liệu | 283 bài, 12 event, 22 category |
| `/archives/` | `archives.html` | search, lọc category, lọc event, sort, reset, empty state, đồng bộ query, phím `/` | **1.43 MB HTML** |
| `/posts/<key>/` | `post.html` | TOC, reading progress, copy code, KaTeX lazy, dialog editor | 566 URL (283×2) |
| `/competitions/` | `competitions.html` | lọc chứng chỉ, copy mã | bảng CTFTime + 13 chứng chỉ |
| `/events/<slug>/` | `event.html` | không | 12 trang |
| `/about/` | `about.html` | không | |
| `/categories/` | `categories.html` | không | 22 category |
| `/categories/<slug>/` | `category.html` | không | |
| `/tags/`, `/tags/<slug>/` | `tags.html`, `tag.html` | không | ~270 tag |
| `/themes/` | `themes.html` | iframe 3 theme | phòng thí nghiệm theme |
| `/404.html` | `404.html` | không | |

Tổng: **1728 URL HTML**, 283 bài mỗi ngôn ngữ, 12 event, 22 category, 13 chứng chỉ
(12 ảnh + 10 PDF), 2 năm kết quả CTFTime (2025, 2026; snapshot 2026-11-13).

## 4. Manifest nội dung

Cách dựng lại manifest (chạy ở gốc repo):

```bash
python3 - <<'EOF'
import os, json, hashlib
ROOT = os.getcwd()
SKIP = {".git", ".github", "site", "tools", "_site_src", "_site_src_en", "_site",
        "_build", "node_modules", "_template", "_wip", "_de_raw", "docs", "vendor"}
EXT = (".md", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".pdf",
       ".zip", ".tar.gz", ".txt", ".py", ".c", ".cpp", ".java", ".js", ".rb",
       ".sh", ".pcap", ".pcapng")
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()
out = []
for ev in sorted(os.listdir(ROOT)):
    d = os.path.join(ROOT, ev)
    if not os.path.isdir(d) or ev in SKIP or ev.startswith((".", "_")):
        continue
    for dp, _, fs in os.walk(d):
        for f in sorted(fs):
            if f.lower().endswith(EXT):
                p = os.path.join(dp, f)
                out.append({"path": os.path.relpath(p, ROOT).replace(os.sep, "/"),
                            "size": os.path.getsize(p), "sha256": sha(p)})
json.dump(out, open("/tmp/manifest_sources.json", "w"), ensure_ascii=False, indent=1)
print(len(out), "file")
EOF
```

Kết quả lần chạy baseline: **4912 file** nguồn (writeup `.md`, ảnh, PDF, script, artifact),
kèm `size` và `sha256`; **1728 URL HTML** VI/EN.

Đối chiếu sau khi làm UI:

```bash
python3 - <<'EOF'
import json, hashlib
old = {r["path"]: r["sha256"] for r in json.load(open("/tmp/manifest_sources.json"))}
bad = []
for p, h in old.items():
    try:
        new = hashlib.sha256(open(p, "rb").read()).hexdigest()
    except FileNotFoundError:
        bad.append((p, "missing")); continue
    if new != h:
        bad.append((p, "changed"))
print("sai lech:", len(bad))
for b in bad[:10]:
    print(" ", b)
EOF
```

Ngoài hash nguồn, cần so **nội dung render**: chữ, code, flag, bảng, math, ảnh, anchor.
Cách làm: chuẩn hoá DOM bài (bỏ nút copy do JS thêm, bỏ class trang trí) rồi so text
trước/sau. Không sửa thuật ngữ, không dịch, không rút gọn.

## 5. Hợp đồng DOM phải giữ

JS hiện tại bám vào các điểm sau; đổi tên là hỏng chức năng:

| Chức năng | Điểm bám |
|---|---|
| Theme | `html[data-theme]`, `#theme-toggle`, `#theme-preview-bar`, `[data-theme-choice]`, key `ctf-theme-v2` |
| Menu mobile | `.menu-toggle`, `#main-nav`, `.is-open` |
| Archive | `#archive-list`, `.writeup-row` + `data-categories/event/date/title/search`, `#archive-search`, `#event-filter`, `#sort-order`, `[data-filter]`, `#result-count`, `#empty-state`, `#reset-filters`, `#clear-filters` |
| Post | `#article-content`, `#toc`, `#toc-links`, `#reading-progress`, `.prose pre`, `.prose table` |
| Editor | `#writeup-editor`, `#editor-login`, `#editor-form`, `#editor-content-vi/en`, `.writeup-edit-actions[data-*]` |
| Chứng chỉ | `#certificate-grid`, `.certificate-card[data-type][data-search]`, `#certificate-search`, `#certificate-type`, `#certificate-empty`, `.copy-certificate[data-copy]` |
| Về đầu trang | `#back-to-top`, `#top-progress` |
| Ngôn ngữ | `.language-switch a` (site.js gán lại query) |

Thêm class/khối trang trí thì tự do, miễn không đổi các ID/attribute trên và không đổi thứ tự
`row.hidden` / `list.append` mà logic lọc dựa vào.

## 6. Audit cơ chế hiện có

**Theme.** Ba theme `terminal` (mặc định), `paper`, `aurora`. Chọn qua `?theme=`, ghi
`localStorage.ctf-theme-v2`. Nút sáng/tối chỉ đảo `light ↔ terminal`. Nếu thêm `xian` mà không
sửa, bấm nút sẽ nhảy về `light` rồi `terminal` — **mất theme xian**. Cần: nhớ theme tối gần nhất,
hoặc cặp `xian` / `xian-light`.

**CSP.** `script-src 'self' 'sha256-4mgsJjkXGVRKXJbDk4Iq02ef7P3zkOVqLSpqQ4eIaZE='`. Hash này ứng
đúng đoạn script inline đọc `?theme=` trong `default.html` (đã kiểm bằng sha256 thật). Thêm
`xian` vào danh sách cho phép **bắt buộc tính lại hash**, nếu không theme sẽ không áp và CSP báo lỗi.
`style-src` cho phép `fonts.googleapis.com`, `font-src` cho phép `fonts.gstatic.com` — thêm font
Google là hợp lệ, không cần nới CSP.

**Asset hashing.** `build_site.py` ghi sha256[:12] của css/js vào `_data/portfolio.json`
(`assets.css/themes/js/editor/github_editor`) và layout dùng `?v=`. Sửa CSS/JS là tự đổi query,
không cần làm tay.

**baseurl VI/EN.** VI `/CTFWU`, EN `/CTFWU/en`. Nút đổi ngôn ngữ hardcode `/CTFWU{{page.url}}`
và `/CTFWU/en{{page.url}}` — giữ nguyên. Mọi ảnh mới phải đi qua `relative_url` hoặc
`/assets/...` để plugin thêm baseurl.

**Editor.** `post.html` nạp `github-editor.js` + `editor.js` trên **mọi** trang bài. Hai file này
gọi API GitHub và API loopback (`tools/serve_site.py`). Không được đổi ID form, không được đổi
`data-writeup-key`, và **không được để test ghi dữ liệu thật**.

**KaTeX.** 1.5 MB vendored, chỉ tải khi phát hiện math trong prose (bỏ qua `pre/code`). Giữ nguyên
cơ chế dò; nếu đổi cấu trúc `.prose` phải kiểm lại.

**Service worker.** `site/sw.min.js` chỉ để tự huỷ worker Chirpy cũ, không đăng ký ở đâu. Bỏ qua.

**Dữ liệu không dùng.** `_data/share.yml`, `_data/contact.yml` không được layout nào tham chiếu.
Không phải việc của đợt này.

## 7. Đo baseline (lab, mạng tại máy, cache tắt)

| Trang | HTML gzip | Tổng transfer | Request | FCP | Load |
|---|---|---|---|---|---|
| Home | 4.9 KB | 77 KB | 7 | 628 ms | 726 ms |
| Archive | **475 KB** | ~500 KB | 5 | 340 ms | 371 ms |
| Post | 14.9 KB | 31 KB | 7 | 284 ms | 283 ms |
| Competitions | 7.6 KB | 694 KB (ảnh cover) | 18 | 536 ms | 751 ms |

Đây là **số đo phòng lab**, không phải INP/LCP thực địa. LCP không lấy được qua
`getEntriesByType` khi không đăng ký `PerformanceObserver`; sẽ đo bằng Lighthouse ở giai đoạn 3.

CSS/JS hiện tại (gzip): `campus.css` 10.2 KB, `themes.css` 5.6 KB, `site.js` 5.4 KB,
`editor.js` 3.5 KB, `github-editor.js` 2.7 KB. JS trang trí thực chất chỉ ~5.4 KB — còn dư
địa rất nhiều so với ngân sách 20 KB.

## 8. Phát hiện và rủi ro

1. **Archive quá nặng (ưu tiên cao).** 1.43 MB HTML, 475 KB gzip; **87.9% là `data-search`**
   (trung bình 3747 ký tự/bài, cắt từ 12000 ký tự đầu của bài). Trang này sẽ là chỗ LCP/INP khó
   đạt nhất, và thêm ảnh trang trí chỉ làm tệ hơn. Đã được chủ repo cho phép xử lý ở giai đoạn 4:
   giảm `search_text` hoặc tách index ra JSON tải sau.
2. **Nút sáng/tối sẽ phá theme xian** nếu giữ logic `light ↔ terminal`.
3. **CSP hash** phải tính lại khi thêm theme vào script inline.
4. **Font serif cho tiếng Việt.** Nhiều font Hán tự không có dấu Việt. Ứng viên có subset
   Vietnamese: Noto Serif, Lora, Playfair Display.
5. **Ảnh cover event rất nhỏ** (đa số 150×150). Nếu phóng to thành tranh nền sẽ vỡ nét.
   Phải vẽ lại hoặc chỉ dùng ở kích thước thumbnail.
6. **Chưa có công cụ tạo ảnh** trong môi trường này (chỉ có VideoGen, tốn credit và ra video).
7. **Cảnh báo Jekyll trùng tag** có sẵn, không liên quan đợt đổi UI.
8. **Trang `/themes/`** dùng iframe cứng 3 theme; thêm theme phải sửa cả trang này.
9. **Không có Lighthouse** trên máy; muốn số liệu chuẩn phải cài `lighthouse` (npm).

## 9. File sẽ sửa (giai đoạn 3–4)

| File | Việc |
|---|---|
| `site/_layouts/default.html` | thêm `xian` vào script inline + CSP hash, nav, footer, thanh preview |
| `site/_layouts/home.html` | hero, khối số liệu, lưới thẻ |
| `site/_layouts/archives.html`, `competitions.html`, `event.html`, `about.html`, `categories.html`, `category.html`, `tags.html`, `404.html`, `page.html` | bọc khung, đổi class trình bày |
| `site/_layouts/post.html` | khung đọc, TOC, giữ nguyên editor |
| `site/_includes/writeup-row.html`, `team-results.html`, `certificates.html` | thêm lớp trang trí, giữ data-* |
| `site/assets/css/xian.css` (mới) | theme xian, tách khỏi `themes.css` để dễ rollback |
| `site/assets/css/themes.css` | chỉ thêm biến/tham chiếu, không nhồi |
| `site/assets/js/site.js` | nhớ theme tối, thêm `xian` vào preview, hiệu ứng nhẹ |
| `site/assets/favicon.svg`, `site/themes.html` | con dấu, phòng thí nghiệm theme |
| `site/assets/img/…` (mới) | hero desktop/mobile, divider, texture |

**Không sửa:** mọi thư mục `<Event>/`, `tools/*.json`, `_site_src*`, `_build`, `_site`.

## 10. Commit, rollback

- Baseline giữ nguyên ở `main` / `47cd195`; toàn bộ việc nằm trên `xian-ui`.
- Mỗi giai đoạn một commit nhỏ, thông điệp rõ; không amend commit đã đẩy.
- Rollback: `git checkout main` (bỏ toàn bộ), hoặc revert đúng commit UI.
  Dữ liệu CTFTime cập nhật sau đó không bị ảnh hưởng.
- Không merge, không deploy production khi chưa có duyệt.
