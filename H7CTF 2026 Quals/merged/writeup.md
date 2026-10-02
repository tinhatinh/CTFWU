# Merged - Web (Medium)

**Flag:** `WEBVERSE{8ba2f569dafeedea7f4f6848757e1917}`

## Đề bài

Hệ thống mục tiêu là Certmarq, nền tảng dịch vụ cấp phát chứng chỉ khóa học. Quy trình hoạt động: nhà phát hành thiết kế mẫu cấu trúc chung, nền tảng tự động kết hợp (merge) thông tin học viên vào mẫu và tạo ra chứng chỉ. 
Điểm yếu của hệ thống nằm ở tính năng: trình thiết kế (designer) cho phép nhà phát hành xem trước (preview) bản chứng chỉ bằng cách render trực tiếp trên máy chủ. Đặc tính không giới hạn quyền của người thiết kế này là dấu hiệu cho thấy có lỗi trong quy trình.

## Phân tích ban đầu

Người dùng có thể truy cập hệ thống để tạo tài khoản nhà phát hành (issuer) dễ dàng mà không yêu cầu xác thực email, cho phép vào thẳng trang quản lý `/designer`. Trên giao diện, hệ thống hiển thị thông báo: 
*"mọi bản mẫu (template) đều phải qua quy trình kiểm duyệt (content filter) trước khi kết xuất"* - Cảnh báo này cho thấy lỗ hổng SSTI (Server-Side Template Injection) đã được nhận dạng và thiết lập bộ lọc (filter) phòng chống.

Điểm tiếp nhận (sink) của quá trình nằm ở cổng `POST /designer/preview`, chỉ yêu cầu trường dữ liệu `body`. Sử dụng chuỗi kiểm tra (fingerprint) để xác định cấu trúc nền tảng:

| Chuỗi kiểm tra (Probe) | Phản hồi |
| --- | --- |
| `{{7*7}}` | Trả về `49` |
| `{{7*'7'}}` | Trả về `7777777` -> Xác nhận nền tảng Jinja2 (Với Twig sẽ trả về `77`). |
| `${7*7}` | Giữ nguyên văn -> Loại trừ nhánh Twig/EJS. |
| `{{ ''\|class }}` | Trả về lỗi `TemplateAssertionError` -> Chính xác cú pháp bộ lọc Jinja. |
| `{{config.items()}}` | Hiển thị toàn bộ cấu trúc config của Flask. |
| `{{ ''.__class__ }}` | Ngăn chặn với thông báo: *the pattern "__" is not allowed* |

Đánh giá thông tin thu thập: Lỗ hổng của bộ lọc đơn giản là hệ thống chỉ kiểm tra một chuỗi văn bản là `__` (hai dấu gạch dưới - dunder). Mọi chuỗi (literal) chứa cụm dunder bên trong template sẽ bị hệ thống loại bỏ, nhưng bộ lọc không kiểm tra phần biến số truyền qua tham số url (query string).

## Quá trình khai thác

Phương pháp xử lý: Thiết lập khối template không chứa mã cấm `__`. Thay vào đó, chuỗi dunder cần thiết sẽ được truyền vào từ bên ngoài thông qua tham số `request.args`:

```jinja
{{(lipsum|attr(request.args.g))['os'].popen(request.args.c).read()}}
```

Phân tích cú pháp:
- Biến `lipsum` là một hằng số toàn cục (global) được nhúng mặc định bên trong Jinja2. Việc gọi `attr(request.args.g)` kèm tham số `g=__globals__` ở chuỗi truy vấn giúp truy xuất trực tiếp từ điển biến toàn cục của module `jinja2.utils`. Trong tập dữ liệu này, thư viện `os` quan trọng đã được khai báo (import) sẵn.
- Cấu trúc lệnh `['os'].popen(request.args.c).read()` có chức năng thực thi mã hệ thống (thông qua biến `c`), và lấy kết quả trả về hiển thị trên màn hình xem trước (preview).
- Cấu trúc template nội bộ không chứa cụm mã cấm `__`, dễ dàng vượt qua bộ lọc. Cụm từ nhạy cảm `__globals__` được cấu hình trên thanh URL (query string), nằm ngoài phạm vi kiểm tra của bộ lọc.

Kiểm tra lệnh cơ sở với `c=id`: Hệ thống trả về `uid=33(www-data)`. Sau khi cấu hình thành công, thiết lập tham số `c=cat /flag.txt` để lấy cờ. 
Theo nội dung file `/entrypoint.sh` được đính kèm, tác giả mô tả: *"Direct, unsandboxed Jinja2 SSTI ... a standard Jinja2 RCE chain reads /flag.txt"* (Lỗ hổng SSTI không được cô lập... chuỗi lệnh RCE cơ bản của Jinja2 đã truy cập được file /flag.txt).

Cấu trúc payload hoàn chỉnh và định dạng qua khối mã Javascript `fetch()` được tài liệu hóa trong thư mục `analysis/payload.md`.

## Flag
```text
WEBVERSE{8ba2f569dafeedea7f4f6848757e1917}
```

Lưu ý: Không cung cấp file `exploit.py` để tự động hóa. Mã script sử dụng thư viện `requests` đã được thiết kế, tuy nhiên chưa được xác nhận tính ổn định: Khi chạy lệnh, môi trường (instance) đã bị máy chủ vô hiệu hóa (WebVerse quy định chỉ một instance hoạt động duy nhất), và định danh các tham số form chưa được kiểm tra.
Tài liệu cung cấp chuỗi payload chuẩn và cấu trúc JS nhúng trong `analysis/payload.md`. Lệnh này được thiết kế để thực thi trực tiếp trên giao diện console của môi trường duyệt web hiện tại.
