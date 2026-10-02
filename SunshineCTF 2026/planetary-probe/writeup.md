# Planetary Probe - Web (Hard)

**Flag:** `sun{bl1nd_psqli_2_rc3_p4Nd0FyZt8k2}`
**URL:** `https://planetary.web.2026.sunshinectf.games/`, không có file đi kèm.

## Đề bài

Ứng dụng web đóng vai trò như một sổ tay tra cứu hành tinh của "Galactic Federation". Khi người dùng nhập tên hành tinh để tra cứu, bảng điều khiển (console) chỉ phản hồi lại đúng một trong hai trạng thái, tương đương với một bit thông tin duy nhất: "signal detected" (tìm thấy tín hiệu) hoặc "no signal" (không có tín hiệu). Ứng dụng không hề hiển thị thông báo lỗi hệ thống và cũng không in lại chuỗi người dùng đã nhập.

Thực tế, tham số `planet` trên URL dính lỗ hổng SQL Injection nghiêm trọng tác động trực tiếp vào cơ sở dữ liệu PostgreSQL. Cờ (flag) không được lưu trữ trong cơ sở dữ liệu mà nằm dưới dạng một tệp văn bản trên hệ thống (file system). Vì user `probe` kết nối với cơ sở dữ liệu được phân quyền thuộc nhóm `pg_execute_server_program`, kẻ tấn công hoàn toàn có thể lợi dụng quyền hạn này để thực thi các lệnh hệ thống (shell command) thông qua mệnh đề `COPY ... TO PROGRAM`. Từ đó, dựa vào mã thoát (exit code) của lệnh shell làm phép thử mù (oracle), ta có thể lần mò đọc từng byte nội dung của tệp cờ.

## Phân tích ban đầu

### Bề mặt tấn công

Ứng dụng chỉ có duy nhất một form tra cứu giao tiếp qua `GET /probe?planet=<x>`. Phản hồi trả về chỉ hiển thị một trong hai giao diện HTML tĩnh:

```html
<body class="is-carrier"> ... "Signal detected"
<body class="is-null">    ... "No signal"
```

Bất kỳ đường dẫn (route) nào khác đều trả về lỗi 404 mang đặc trưng của web framework Flask. Việc can thiệp vào HTTP header, cookie hay các tham số bổ sung đều không gây ra tác động gì. Lỗ hổng hoàn toàn nằm ở cách ứng dụng xử lý tham số trên chuỗi truy vấn (query string).

### SQL injection và phép thử mù một bit (One-bit oracle)

Thử nghiệm payload `MARS' OR 1=1-- ` trả về kết quả "signal detected" (carrier), trong khi `MARS' OR 1=1#` lại trả về "no signal" (null). Hành vi này không chỉ xác nhận hệ quản trị cơ sở dữ liệu phía sau là PostgreSQL mà còn khẳng định truy vấn gốc được ghép chuỗi một cách sơ hở:

```sql
SELECT id FROM planets WHERE name = '<payload>'
```

Ta có thể chuẩn hoá phép thử mù (oracle) dưới dạng: `MARS' AND (<expr>)-- `. Phản hồi sẽ là carrier khi và chỉ khi biểu thức `<expr>` mang giá trị đúng (true).

**Lưu ý quan trọng:** Ứng dụng có cơ chế tự động chuyển đổi toàn bộ payload sang chữ in thường (lower-case) trước khi đưa vào cơ sở dữ liệu. Điều này khiến biểu thức `ascii('A')=65` trở thành sai vì nó đã bị ép thành `ascii('a')=65`, trong khi `ascii('A')=97` và `ascii(chr(65))=65` lại đánh giá là đúng. Chính vì vậy, tuyệt đối không được sử dụng ký tự in hoa trực tiếp trong chuỗi truy vấn; mọi phép so sánh đều phải được quy về các hàm toán học hoặc chuỗi như `ascii` và `length`.

Quá trình rà quét dữ liệu các bảng nội bộ (`pg_class`, `planets`, `zleak`) cho thấy chuỗi cờ `sun{` không hề tồn tại trong bất kỳ cột nào của CSDL. Do đó, cờ chắc chắn phải được giấu trên hệ thống tệp tin.

## Chuỗi khai thác

### Bước 1 - Oracle thứ hai: Khai thác qua mã thoát của tiến trình

Thực thi payload `MARS'; SELECT pg_sleep(3); -- ` làm cho request bị treo đúng 3.8 giây, chứng tỏ hệ thống hoàn toàn cho phép chạy nhiều câu lệnh SQL nối tiếp nhau (stacked statements). Tuy nhiên, để tránh trường hợp driver `psycopg2` báo lỗi khiến ứng dụng sập và luôn báo "no signal", khối truy vấn bắt buộc phải được kết thúc bằng một câu lệnh `SELECT` trả về ít nhất một hàng dữ liệu.

Khảo sát bảng `pg_auth_members` xác nhận tài khoản `probe` hiện tại có đặc quyền `pg_execute_server_program`. Quyền này cho phép ta chạy trực tiếp các lệnh shell dưới danh nghĩa user hệ điều hành `postgres` thông qua cú pháp:

```sql
MARS'; COPY (SELECT 1) TO PROGRAM '<cmd>'; SELECT 1; -- 
```

Nếu câu lệnh `<cmd>` kết thúc thất bại (exit code khác 0), PostgreSQL sẽ ném ra ngoại lệ (exception) khiến ứng dụng trả về "no signal". Ngược lại, nếu thực thi thành công (exit code bằng 0), kết quả sẽ là "signal detected". Chẳng hạn: `test -f /etc/passwd` trả về carrier (vì file tồn tại), trong khi `test -f /no.such` trả về null. Phản ứng này tạo nên một phép thử mù (oracle) thứ hai vô cùng đắc lực, giúp ta tương tác và thăm dò hệ thống tệp.

Lệnh shell dùng để tìm vị trí file cờ: `find / -name "*flag*" -type f -exec grep -ls sun{ {} +`.

### Bước 2 - Đọc nội dung tệp tin từng ký tự một

Do máy chủ web có thể chạy trên hạ tầng gồm nhiều bản sao (replica), ta không thể lưu trữ trạng thái hay file tạm giữa hai request khác nhau. Mọi lệnh thực thi phải được đóng gói và trả về kết quả ngay trong một payload duy nhất:

```bash
f=$(find / -name "*flag*" -type f -exec grep -ls sun{ {} + 2>/dev/null | grep -v /tmp/ | sort | head -1);
grep -aoE "sun[{][^}]*[}]" "$f" | head -1 | cut -c<K> | grep -qE "[class]"
```

Các giải pháp kỹ thuật cụ thể đã được áp dụng để quá trình đọc tệp tin diễn ra ổn định:
1. Tuyệt đối không luân chuyển dữ liệu trung gian qua thư mục `/tmp/` vì request tiếp theo có thể được điều hướng sang một máy chủ bản sao khác, nơi dữ liệu tạm không tồn tại.
2. Việc sử dụng `find -name` kết hợp `cut -c<K>` có ưu điểm là tối ưu hoá tốc độ. Nếu các probe chạy quá chậm, máy chủ sẽ xem như request bị lỗi và ngắt kết nối. Phương pháp tách rời từng byte (`index`) để truy vấn còn mở ra khả năng chạy đa luồng để tăng tốc độ khai thác.
3. Cần hết sức thận trọng khi dùng các lớp phủ định (negative class) trong regex. Chẳng hạn, nếu dùng `[^d]` để suy luận một chữ cái có phải là viết hoa (vd: `D`) hay không, ta có thể dễ dàng bị đánh lừa bởi những lỗi timeout ngẫu nhiên khiến lệnh kết thúc sớm. Phương án an toàn là luôn phải kiểm tra trước xem nó có thuộc lớp chữ hoa `[[:upper:]]` hay không.

Lưu ý rằng bản thân chuỗi cờ `sun{}` cần được biểu diễn dưới định dạng bracket class (`[s][u][n][{]...`) để không phá hỏng cú pháp regex của grep.

## Flag

Kết quả quá trình rà quét (nhật ký debug):
```text
[*] exact string, end-anchored: True
[*] negative control (last char 3 instead of 2): False
[*] negative control (one uppercase where there is none): False
[*] length 35 and nothing more: True True
```

Xác nhận độ dài cờ chính xác là 35 ký tự. Sau khi chạy script trích xuất, nội dung cờ hiện ra:

```text
sun{bl1nd_psqli_2_rc3_p4Nd0FyZt8k2}
```

## Tổ chức mã nguồn

| File | Chức năng |
| --- | --- |
| `exploit.py` | Script chính điều phối toàn bộ chuỗi tấn công: xác nhận oracle, đọc cờ và kiểm tra tính toàn vẹn. |
| `extract.py` | Thư viện gọi SQL Oracle và helper hỗ trợ gửi request đọc cờ song song. |
| `definitive.py` | Script chốt các ký tự đặc biệt dựa vào phương pháp bằng chứng dương (positive evidence). |
| `po.py`, `shell.py`, `flagpos.py`, `final_read.py` | Các script kiểm thử trung gian dùng trong quá trình khám phá. |
| `sweep3.py` | Script hỗ trợ quét nhanh chuỗi `sun{` ở bất kỳ thư mục nào trên hệ thống. |
| `analysis/` | Thư mục lưu trữ log request và bản sao (dump) của schema CSDL. |
| `flag.txt` | File kết quả chứa cờ cuối cùng. |

## Reproduce

```bash
python exploit.py        # Kích hoạt chuỗi tấn công tự động để trích xuất cờ
```
