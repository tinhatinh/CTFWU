# Justified - Web (Medium)

**Flag:** `WEBVERSE{d5f60724dc9f1197140001fa4b24198e}` · Đã nộp thành công trên hệ thống WebVerse (trang trạng thái trả về SOLVED).

## Đề bài

Marlowe & Sons, một cửa hàng sách truyền thống, cung cấp hệ thống "Instant Cover Proof" (Duyệt nháp trang bìa nhanh). Hệ thống xử lý thông tin biểu mẫu thông qua phần mềm nội bộ và trả về cho người dùng một file PDF đính kèm file log (nhật ký) để kiểm tra thông số in.
Thử thách có nhãn `CMDI` (Command Injection - Tiêm lệnh hệ thống). Hướng dẫn "hãy đọc những gì máy chế bản (typesetter) báo cáo" cung cấp gợi ý rõ ràng về việc sử dụng file log làm cơ sở khai thác.

Ứng dụng không yêu cầu tài khoản hoặc tải file. Form gửi POST request tới `/proof.php`.

## Phân tích

Kiểm tra biểu mẫu cho thấy có 9 trường dữ liệu: `title`, `author`, `degree`, `department`, `institution`, `supervisor`, `year`, `abstract`, và `reference`. Trường `reference` là tên file tải về, trong khi trường `title` (tiêu đề) cung cấp tài liệu hướng dẫn:

> Mẹo: Bạn có thể nhập các ký tự có dấu và biểu tượng bằng cú pháp LaTeX, ví dụ: `M\"uller`, `\'Etienne`, `\OE`. Máy chế bản của chúng tôi sẽ kết xuất (render) chúng thành hình cho bạn.

Hướng dẫn này chỉ ra lỗ hổng: Dữ liệu người dùng cung cấp được chèn trực tiếp, không thông qua bước lọc (sanitize), vào mã nguồn LaTeX.

Phân tích log trả về từ một request hợp lệ, cấu trúc của hệ thống chế bản được phát hiện:

```text
This is pdfTeX, Version 3.141592653-2.6-1.40.26 (TeX Live 2025/dev/Debian)
(preloaded format=pdflatex) \write18 enabled.
entering extended mode
(./main.tex
```

Các kết luận quan trọng từ log:

1. Ứng dụng tự động khởi tạo file `main.tex` chứa dữ liệu người dùng, sau đó chuyển cho tiến trình `pdflatex` biên dịch.
2. Log có dòng `\write18 enabled.`. Để xác định shell escape có cho phép lệnh cần dùng hay không, đối chiếu với output của payload thực thi lệnh ở bước sau; không kết luận full/restricted mode chỉ từ một đoạn log thiếu ngữ cảnh.
3. Toàn bộ thông tin từ quá trình xử lý (bao gồm luồng báo lỗi `stderr`) đều được ứng dụng web trả về và hiển thị trực tiếp cho người dùng.

## Lời giải

**Bước 1 - Xác minh lỗ hổng LaTeX Injection tại trường `title`.**
Sử dụng một đoạn mã macro cơ bản để kiểm tra:

```text
A\typeout{ZZMARKERZZ}
```

Chuỗi `ZZMARKERZZ` xuất hiện trong bản log trả về. Dấu gạch chéo ngược (backslash) không bị lọc, chứng minh trình biên dịch TeX xử lý trực tiếp lệnh đầu vào.

Lưu ý kỹ thuật: Khi thực thi lệnh qua hàm `fetch()` trong công cụ devtools trình duyệt, chuỗi ký tự `'A\typeout{...}'` sẽ bị xử lý ở lớp escape của JavaScript (dấu backslash bị triệt tiêu). Để đảm bảo payload chính xác, dữ liệu cần được xử lý thông qua `String.fromCharCode(92)`.

**Bước 2 - Khai thác quyền Shell Escape.**
Tận dụng tính năng `\write18`, hệ thống cho phép thực thi lệnh mức hệ điều hành (RCE):

```latex
\immediate\write18{<câu_lệnh_system_ở_đây>}
```

**Bước 3 - Truy xuất dữ liệu (Data Exfiltration).**
Kênh luân chuyển dữ liệu cần được điều hướng về người dùng. Có hai phương thức được nêu ở đây:
Lưu kết quả ra file và dùng `\input` để xuất vào PDF;
Hoặc chuyển hướng (redirect) luồng dữ liệu sang `stderr` của pdflatex để hiển thị trực tiếp trong log. Phương án thứ hai được áp dụng:

```latex
C\immediate\write18{cat /flag.txt 1>&2}
```

Macro `\write18` khởi tạo tiến trình con được thừa kế cấu trúc mô tả file (file descriptor) từ `pdflatex`. Cấu trúc `1>&2` chuyển hướng đầu ra `stdout` sang `stderr`. Dữ liệu sẽ được truyền trực tiếp vào log hiển thị trên ứng dụng web mà không cần thao tác với file PDF trung gian.

Kết quả hiển thị trong file log:

```text
WEBVERSE{d5f60724dc9f1197140001fa4b24198e}
```

**Bước 4 - Tự động hóa quá trình.**
Python script `exploit.py` sử dụng thư viện `requests` để tương tác trực tiếp. Kịch bản thực thi một lệnh kiểm tra hệ thống (`id`) để xác thực tính khả dụng của shell escape trước khi đọc file đích.
Trong quá trình phát triển kịch bản, các vấn đề về hiển thị thẻ HTML `<pre class=...>` được xử lý bằng biểu thức chính quy (regex) `<pre[^>]*>`, và header `User-Agent` hợp lệ được bổ sung để tránh hệ thống trả về lỗi.

## Kết quả
```bash
python exploit.py https://978870f9-5765-justified-06d98.mystery-challenges.webverselabs-pro.com
```

Kết quả thực thi:
```text
[*] Cửa shell escape đã mở toang: uid=33(www-data) gid=33(www-data) groups=33(www-data)
[+] flag: WEBVERSE{d5f60724dc9f1197140001fa4b24198e}
```
