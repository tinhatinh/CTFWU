# Planetary Probe — Sunshine CTF 2026 (web, 500 pts)

Ảnh đề bài gốc, chụp từ thẻ challenge:

![de](files/de.png)


## Đề bài (verbatim)

```
Planetary Probe
500
valiumaggelein

 1 (100% liked)  0
The Galactic Federation has opened public access to its Planetary Probe Directory, a database of known planets and their telemetry signatures. Your mission is to interface with the probe console and uncover hidden data the Federation would rather keep secret.

The console seems… minimal. No verbose errors, no detailed output — just “signal detected” or “no signal”. Can you find a way to communicate with the system, bypass its limited responses, and recover the hidden flag?

https://planetary.web.2026.sunshinectf.games/
```

## Intake

| Field | Value |
| --- | --- |
| Challenge | Planetary Probe |
| Author | valiumaggelein |
| Category | web |
| Points | 500 |
| Solves | 1, 100% liked |
| Flag format | `sun{...}` |
| Target | `https://planetary.web.2026.sunshinectf.games/` |
| Solved nghĩa là | đọc được chuỗi `sun{...}` cất trong DB qua oracle 1 bit |

## Đã xác định được

- Route duy nhất có ích: `GET /probe?planet=<x>`. Response chỉ khác nhau ở `class="is-carrier"` / `is-null` và 3 dòng text (`Signal detected` / `No signal`). Không có bất kỳ echo dữ liệu nào → **kênh thông tin đúng 1 bit/request**.
- `MARS` → carrier; `NOTAPLANET` → null; `MARS'` → null; `MARS' AND 1=1-- -` → carrier; `MARS' AND 1=2-- -` → null. **Boolean-based blind SQLi, ngữ cảnh `WHERE name = '<input>'`, đóng câu lệnh bằng `-- -`.**
- DBMS = **PostgreSQL**: `pg_tables` ✓, `pg_catalog.pg_tables` ✓, `gen_random_uuid()` ✓, `||` ✓, `substring()` ✓, `ILIKE` ✓, `::text` ✓, `current_setting('server_version')` ✓. Loại MySQL (`database()`, `user()`, `@@datadir`, `IF()` đều ✗) và SQLite (`sqlite_master`, `typeof()`, `randomblob()` ✗).
- Hàm bị chặn/không dùng được: `ascii()`, `unicode()`, `md5()`, `group_concat()`, `if()`. Dùng được: `substr()`, `length()`, so sánh chuỗi, `IN (...)`, `COUNT(*)`, `row_to_json()`.
- **Oracle nhiễu một chiều**: khi bắn liên tục, một số query đúng nhận `no signal` giả (timeout). Đếm bảng lần đầu cho ra tên rác (`PrNNETf`, `fNEfN`). Cách khắc phục: nghỉ ≥2s giữa request + retry khi gặp False (True không bao giờ là nhiễu). Đo định lượng: `1=1` bắn 5 lần rời rạc vẫn có 1 lần False (~20%), trong khi `1=2` và `substr2='q'` cho 5/5 False. Nên `bit()` dùng tries=3, "any True wins".
- **So sánh chuỗi của DB là KHÔNG phân biệt hoa/thường**: `(SELECT 'hello')='HELLO'` → True 5/5. Hệ quả: tập ứng viên khi binary-search phải chứa đúng một phần tử mỗi lớp case. `FLAGSET`/`LOWER` hợp lệ; `FULLSET` (32..126) thì sai vì liệt kê cả `'e'` lẫn `'E'` → phép thử đầu tiên đã hội tụ về `H` thay vì `e` (đây chính là bug harness bị phát hiện khi kiểm chứng đáp án đã biết).
- `<>` không dùng được trong payload (`tablename<>'planets'` trả tập rỗng) trong khi `<` đơn lẻ vẫn ổn (`(SELECT 5)<10` → True) → nghi bộ lọc HTML sanitizer nuốt cặp `<>`. Vòng qua bằng `ORDER BY tablename DESC LIMIT 1` và `NOT (tablename='planets')`.
- Toán tử regex `~` trả False dù điều kiện tương đương bằng LIKE trả True → chỉ dùng LIKE/substr.
- Độ trễ tăng dần theo tải: 2–5s → 5–12s → 10–25s/request.
- `planets` tồn tại, có đúng 2 bảng public (`>=2` True, `>=3` False), số dòng `planets` trong khoảng 2..9, số cột 4..5. `planets` KHÔNG phải bảng cuối theo bảng chữ cái, nên bảng cần tìm là `ORDER BY tablename DESC LIMIT 1`.

## BƯỚC NGOẶT: app lowercase toàn bộ payload

Control `(SELECT 'A')=chr(65)` → **False**, trong khi `(SELECT 'A')=chr(97)` → **True** và
`(SELECT 'a')=chr(97)` → True. Nghĩa là input bị biến đổi thành chữ thường TRƯỚC khi vào SQL.
Hệ quả — mọi kết luận sau đây trước đó đều SAI:

| Kết luận cũ (sai) | Sự thật |
| --- | --- |
| "DB có collation không phân biệt hoa/thường" | Không. `hello`=`HELLO` True là do payload bị lowercases cả hai vế |
| "`ascii()` / `unicode()` / `md5()` / `if()` / `~` / `<>` không tồn tại" | `ascii()` chạy tốt; `ascii('A')` trả **97** vì 'A' đã bị hạ thành 'a' |
| "engine không phải PostgreSQL thuần" | Vẫn là PostgreSQL (`version()` chứa "ostgre" khớp mẫu chữ thường) |
| "flag không có trong DB" (từ ~40 phép thử `LIKE '%sun%'`) | Vô hiệu: các mẫu tìm đều chữ thường. DB **phân biệt case** nên `Sun`/`SUN` bị bỏ sót |

Tìm lại bằng chuỗi dựng qua `chr()` (không bị lowercases vì được sinh phía server):
`position(chr(83)||chr(117)||chr(110) in planets::text)` → **TRUE**, đúng **1 dòng duy nhất = MERCURY**.
Không dòng nào chứa `sun` viết thường. Nhưng ký tự kế tiếp là `, th` → "Sun, the ..." → nhiều khả năng
là văn xuôi mô tả, không phải flag.

Cùng lý do làm vô hiệu kết luận về `zleak`: trước đây test "ký tự đầu không phải chữ cái" dùng
IN-list chữ thường, nên một chữ hoa ở vị trí đó sẽ không khớp. `zleak` (bảng tên "leak", 1 cột,
1 dòng 21 ký tự, **xuất hiện dòng này giữa session trong khi trước đó đo là rỗng**) vẫn là ứng viên
số 1 → đang rút lại toàn bộ giá trị bằng `ascii(substr(...))` để giữ đúng case.

## Kiểm chứng harness (làm trước khi tin kết quả)

Bắn `(SELECT 'hello')`: `length` → 5 đúng, nhưng `substr(...,2,1)` → `H` (sai, phải là `e`). Nhờ cắm sẵn đáp án đã biết mà phát hiện ra collation không phân biệt case + `FULLSET` không dùng được, trước khi kịp rút ra một tên bảng rác khác.

## Ảnh đầy đủ của DB (tính đến hiện tại)

- Engine giống PostgreSQL (có `pg_tables`, `gen_random_uuid()`, `ILIKE`, `::text`) nhưng **so sánh chuỗi không phân biệt hoa/thường** và **không có `ascii()`/`unicode()`/`md5()`** → không phải PG thuần; hành vi giống CockroachDB (ICU collation primary-strength). Không kết luận được cũng không sao, mọi primitive đang dùng đã kiểm chứng trực tiếp trên target.
- `planets`: **8 dòng × 4 cột**. 7 designation khớp qua chính matcher của app: MERCURY, EARTH, MARS, JUPITER, SATURN, URANUS, NEPTUNE. **VENUS KHÔNG khớp** → dòng thứ 8 có designation lạ.
- `zleak`: **0 dòng, đúng 1 cột, tên cột dài 1 ký tự**. Không phải generated column, không identity, không default chứa flag.
- Không có: bảng/view/materialized view/foreign table/temp table nào khác; không schema người dùng nào khác; không RLS; không rule; không large object.
- Chuỗi `sun` và ký tự `{` **không xuất hiện** ở: mọi giá trị của `planets` (quét qua `planets::text`, đã chứng minh primitive này chạy được), mọi tên bảng/cột/schema/role/database, comment (`pg_description`, `pg_shdescription`), seclabel, reloptions, default, constraint def, `pg_settings`, `pg_views.definition` (chỉ hit ở pg_catalog = nhiễu hệ thống). Also hex (`73756e`), base64 (`c3Vue`), reversed (`}nus`), rot13 (`fha`) đều False.
- Quyền: **không superuser**, không có `pg_execute_server_program`/`pg_read_server_files`, không tạo được bảng, `pg_read_file`/`pg_ls_dir`/`lo_import` đều không dùng được → không đọc được file.
- **Stacked queries chạy được** (chứng minh bằng thời gian: `MARS' AND 1=1; SELECT pg_sleep(5)-- -` chậm hơn baseline đúng 5s), nhưng chỉ có tác dụng với statement mà role được phép.
- HTTP: chỉ `/`, `/probe`, `/static/styles.css`. Không có route nào khác (28 đường dò đều 404 207 byte), không echo input, không leak source. CSS không chứa gì ẩn.
- `pg_stat_activity` có dòng chứa `sun{` nhưng **là của người chơi khác** (position 124 > length 99 → hai dòng khác nhau khi `LIMIT 1` không ORDER BY). Không dùng làm kênh được.

## Hướng đang chạy

Rút `planets::text` của dòng thứ 8 (`getrow8.py`, resume được) để đọc designation lạ. Đây là dữ kiện cụ thể duy nhất chưa từng được nhìn; nếu nó là một từ/cluster thì cờ nhiều khả năng là `sun{<designation>}`.

## KẾT QUẢ: chưa có flag. Những gì đã chốt (có bằng chứng)

| Đối tượng | Kết quả |
| --- | --- |
| `planets` | 8 dòng = 8 hành tinh thật, tất cả đều match được qua UI (MERCURY..NEPTUNE, gồm cả venus). Cột đã xác định: `id`, `name`, `description` + 1 cột chưa rõ tên (36 ứng viên đều False). Giá trị `description` là tính từ mở đầu câu mô tả (Closest/Dense/.../Windy) → acrostic `CDBRGRIW` vô nghĩa, không phải thông điệp ẩn |
| `zleak` | 1 dòng, 1 cột tên `v`, `v = 'select v from zleak'` (19 ký tự; `zleak::text` dài 23 vì PostgreSQL bọc thêm nháy kép khi render row). Không đổi trong suốt session. Là object duy nhất chưa giải thích được |
| Tìm flag trong DB | Vô vọng: không có `{`/`}` ở bất kỳ đâu (test bằng `chr(123)` nên không bị lowercase phá), không có `_`, không có `sun`/`SUN`/`Sun` trong giá trị; đã quét giá trị + tên bảng/cột/schema/role/database + comment + default + constraint + setting + view def + large object + trigger + policy + rewrite + function; hex/base64/rot13/reversed cũng False |
| Quyền | Chỉ đọc. `INSERT` và `CREATE TEMP` đều lỗi dù stacked query chạy được (`pg_sleep` chứng minh). Không superuser, không `pg_read_file`/`pg_ls_dir`/`lo_import` |
| Kênh | Đúng 2 trạng thái (carrier/null), 3 class `is-*` trong CSS, không route ẩn, không header ẩn, không source leak. `pg_stat_activity` chỉ thấy query của chính mình + của player khác (app dùng 1 connection nên query của app luôn bị ghi đè trước khi mình đọc) |
| WAF | Không có: `current_database()`, `version()`, `current_user`, `ascii()` đều hoạt động. Các kết quả False đáng tin |

## Bẫy chí mạng của bài này (đã rút ra thành memory)

App **lowercase toàn bộ payload**. Hệ quả liên đới:
- Mọi tìm kiếm `LIKE '%sun%'` chỉ quét được chữ thường → phải dựng chuỗi bằng `chr()`.
- Hàng loạt kết luận sai ban đầu: "`ascii()`/`md5()` không tồn tại", "collation không phân biệt case", "không phải PostgreSQL".
- Control để phát hiện: `(SELECT 'A')=chr(65)` → False, `(SELECT 'A')=chr(97)` → True.

## Nhật ký giả thuyết

| H | Nội dung | Kết quả |
| --- | --- | --- |
| H1 | UNION SELECT để đọc trực tiếp | DEAD — trang không render bất kỳ field nào, UNION không thêm được bit nào |
| H2 | time-based (`pg_sleep`) mang nhiều bit hơn | DEAD — boolean đã đúng và nhanh hơn; sleep chỉ tổ tăng tải |
| H3 | flag nằm trong `planets` | **DEAD** — đã xác nhận bằng primitive hợp lệ: `(SELECT planets::text FROM planets LIMIT 1) LIKE '(%'` → True (cast cả row ra text dùng được), nhưng `planets::text LIKE '%sun%'` và `'%{%'` đều False. Lưu ý phép thử trước đó dùng `row_to_json()` là **mồi giả**: `row_to_json` bị chặn nên nó trả False bất kể dữ liệu |
| H4 | có bảng thứ 2 tên dễ đoán | DEAD cho `flags`, `secrets`, `probe`, `stars`, `vault`, `world`, `venus`, `pluto`, `relic` (test `COUNT(*)>=0`, query lỗi khi bảng không tồn tại). Không có cột nào chứa `flag`/`secret` trong `information_schema.columns` |
| H5 | tên bảng thứ 2: 5 ký tự, xếp sau `planets` | ĐANG RÚT bằng `substr(...) IN (...)` trên `(SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename<>'planets' LIMIT 1)` |
| H6 | toán tử regex `~` | DEAD — `(SELECT ... WHERE planets::text ~ '^[(')` trả False dù cùng điều kiện bằng LIKE trả True; chỉ dùng LIKE/substr |
