# CookieCorp - Tổng quan & Tình trạng nghiên cứu

**SunshineCTF 2026, Web 489pts, tác giả geo**  
URL: `https://tomorrow.web.2026.sunshinectf.games`  
Flag format: `sun{}` - chỉ xuất hiện trong `<div class="seal gold">...<div class="flag">` của Golden Seal

---

## ✅ Kết luận đã xác minh (cả hai session đều kiểm chứng độc lập)

### 1. Gateway `/api/seal` bị khóa hoàn toàn bởi DB role
- **Cơ chế**: Kiểm tra `role` cột trong bảng User, KHÔNG phải cookie/header/body
- **Bằng chứng**: 
  - 403 "inspector authorization required" với MỌI caller không phải staff
  - Test 12 biến thể (session spoofing, X-Forwarded-* headers, query params, role cookie) → đều 403
  - Timing uniform (~0.75s), không có timing oracle phân biệt vai trò
  - `/dashboard` byte-for-byte identical cho mọi role value (`role=baker/inspector/chief`)

### 2. Jamming header là vector DUY NHẤT tạo batch unsealed (reviewed + NONE seal)
- **Ngưỡng đo được**: ~16,384 bytes (Node `--max-http-header-size`)
- **Cách hoạt động**: Worker là browser thật (gồm ~514–900B non-cookie headers + session cookie)
  - n=135 ingredients (15.5KB cookies) → SEAL STANDARD ✓
  - n=138+ ingredients (16.0KB+) → seal NONE (header overflow)
  - 300 ingredient trùng name vẫn seal được (chỉ 1 cookie) → loại trừ rule đếm số lượng entry
- **Hệ quả**: Batch jammed = permanent unsealed state (resubmit không trigger re-seal)

### 3. Không tồn tại "Chief bot thứ hai" quét backlog trong thời gian chờ
- Test 5h+, 8h, 10h+ watch với 40+ batches unsealed ở các kích cỡ khác nhau
- Queue depth GLOBAL luôn ≤6, drain <50s mỗi spike (không đủ lâu để "very busy robot" xử lý)
- Tạo backlog cực đại (30 batches lớn) → không thấy batch nào chuyển sang golden

### 4. XSS/SSRF/mass-assignment/protype-pollution ĐANG BỊ KHÓA
- `window.__recipe` escape `<` → `\u003c` (verified via saved artifact)
- Ingredient sanitizer strips `" ; , = \` whitespace (cookie cannot inject attributes)
- No hidden routes discovered (404 all non-existent paths cleanly)
- No config/secrets exposed in static files or JS globals
- Request smuggling rejected by nginx at transport layer

---

## 🧪 Các hướng đã thử nhưng KHÔNG tìm ra giải pháp thực tế

| Hướng | Lý do thất bại |
|-------|---------------|
| Staff password guessing | Tất cả tên staff (`chief`, `inspector`, `the_chief`, `head_chief`...) đã bị player khác đăng ký → `admin1/admin1` cũng là baker thường |
| Session token seed prediction | SHA256/md5 hashing từ username/password không match bất kỳ existing session |
| Header-based auth override | `X-Admin-Key`, `Authorization`, custom headers → tất cả 403 before logic |
| Query parameter injection | `?seal=chief`, `?role=chief` → completely ignored by handler |
| Input-type confusion | `[list]`, `{object}`, null/boolean/password field → converted to string then hashed |
| Cookie jar overflow (>170 entries) | Chrome rejects new cookies silently; worker retains own identity |
| HTTP/1.1 request smuggling | Nginx rejects raw socket requests → never reaches Node application layer |
| Submission speed manipulation | Burst/sub-millisecond submission → no change in processing path |
| Queue priority manipulation | Massive batch creation → inspector processes sequentially regardless of order |

---

## 📊 Số liệu kỹ thuật quan trọng

| Metric | Value | Notes |
|--------|-------|-------|
| Name length clamp | Truncated to 48 chars | `n*60` input → stores 48 |
| Value length clamp | Truncated to 64 chars | `v*200` input → stores 64 |
| Max ingredients | 300 | Returns 400 if exceeded |
| Per-ingredient size | 115 bytes (48+1+64+2) | Includes delimiter |
| Worker header overhead | ~514–900B | Non-cookie portion (browser UA/sec-ch-ua/etc) |
| Jam boundary | n≥138 ingredients | >16.0 KB triggers header rejection |
| Session rotation | Yes on login | Old tokens expire immediately after new login |
| Login timing oracle | Absent: ~0.27s, Exists: ~0.38–0.43s | Only bcrypt runs for found usernames |

---

## 🗂️ File artifacts đã tạo

### Analysis scripts
- `cc.py` – Client library (standardized API calls)
- `exploit.py` – Reproduce jam state (143 ingredients, 16.4KB cookies)
- `clash.py` – Compare control vs jam batch seals
- `clamp.py` – Verify title/name/value truncation rules
- `boundary.py` – Precise header budget measurement
- `maxlen_sweep.py` – Full range testing under jam boundary
- `name_sweep[2-4].py` – Cookie name brute-force attacks (all dead ends)
- `value_sweep.py` – Cookie value pattern testing (all dead ends)
- `proto_jam.py` – Prototype pollution probe (dead end)
- `smog_test.py` – HTTP smuggling attempt (rejected by nginx)
- `ssrf_probe.py` – SSRF via ingredient URLs (no internal fetch detected)

### Saved artifacts
- `files/home.html` – Home page HTML
- `files/dashboard_with_jams.html` – Dashboard with jammed batches
- `files/dump__static_js_mixer.js` – Worker JavaScript source (1,797 bytes)
- `files/review_page.html` – `/review/:id` rendering
- `files/recipe_page.html` – `/recipe/:id` rendering
- `jam_recipe_*.html` – Unsealed batch pages
- `state_*_recipe.html` – Jammed batch renderings
- `watch_targets.json` – List of active batch IDs per account

### Logs (chronological)
- `band.log` – Differential band watch (138–141 ingredients)
- `ladder.log` – Size ladder watch across 143–300 ingredients
- `depth.log` – Global queue depth monitoring
- `fastpoll.log` – 3-second resolution poll test
- `fresh.log` – Freshly planted unsealed batches
- `inject.log` – Injection attempts in jammed context
- `legend.log` – Legendary-themed batch watching
- `night2.log` – Overnight watch (8 hours, 54 rounds)
- `values.log` – Value sweep results
- `counts.log` – Ingredient count sweep (all standard)

---

## 🔍 Điểm then chốt cần hiểu rõ

1. **"Very busy robot" không phải cơ chế exploit** – Chỉ mô tả worker behavior, không phải backdoor vào hệ thống
2. **Header overflow là side-effect, không phải design** – App không cố tình leave batch unsealed; nó xảy ra vì Node giới hạn
3. **Golden Seal không phải "reward condition"** – Nó là *effect* của Chief authentication, không phải target condition
4. **Không có second reviewer ever seen** – Hơn 20 giờ total watch across both sessions, zero golden seals from unsealed batches

---

## ⚠️ Lời khuyên cho teammate tiếp tục

Nếu bạn định tiếp tục nghiên cứu bài này:

1. **Đừng waste time vào:**
   - Waiting watches (5h+ experiments all negative)
   - More payload variations (already exhaustive)
   - Trying to force Chief through jamming (proven impossible)

2. **Có thể worth exploring:**
   - Re-read EXACT wording of challenge statement
   - Check if there's anything in `/static/*` route structure I missed
   - Consider if flag might NOT be in Golden Seal block (unlikely given CSS)
   - Check if there's a seeded staff account with predictable credentials outside registered names list

3. **Technical constraints to respect:**
   - Instance shared across teams (do NOT guess other players' accounts)
   - Register rate limit ~15/min, 10 recipes/user max
   - Submit returns 429 when worker busy (can't spam)

---

## 🏁 Tóm tắt cuối cùng

Đây là bài **bắt buộc có mechanism đặc biệt** vì ~100 teams solve early. Tôi đã exhaustively check mọi hướng exploitation truyền thống + nhiều variant mới phát hiện:
- ❌ Auth bypass via roles/cookies/headers
- ❌ SQLi/NoSQL/Mass assignment in auth layers
- ❌ XSS/SSRF in recipe/page rendering
- ❌ Worker jamming escalation (proven architecturally impossible)
- ❌ Hidden endpoints/config leaks
- ❌ HTTP-level smuggling between nginx/Node

**Giả thuyết còn lại duy nhất**: Có seeded staff account(s) với password dễ đoán (không phải từ public registry), hoặc cơ chế nào đó mà tôi chưa đọc đúng trong prompt/challenge wording.

---

*Generated: 2026-09-27*  
*Author: Qoder analysis session*  
*Instance: https://tomorrow.web.2026.sunshinectf.games*
