# Justified — Web (Medium)

**Flag:** `WEBVERSE{d5f60724dc9f1197140001fa4b24198e}` · Đã nộp thành công trên hệ thống WebVerse (trang trạng thái trả về SOLVED).

## Đề bài

Marlowe & Sons, một hiệu đóng sách và luận văn cổ kính, cung cấp công cụ có tên "Instant Cover Proof" (Duyệt nháp trang bìa nhanh). Hệ thống này tiếp nhận các trường thông tin luận văn từ một biểu mẫu web, dùng phần mềm nội bộ (máy chữ của cửa hàng) chế bản (typeset) trang bìa, và nhả lại cho người dùng một tệp PDF đính kèm một kênh log (nhật ký) để thợ in kiểm tra thông số trước khi đưa lên máy chém giấy. 
Bài toán được gắn nhãn (tag) là `CMDI` (Command Injection - Tiêm lệnh hệ thống). Đoạn mồi nhử "hãy đọc những gì máy chế bản (typesetter) báo cáo về" giống như một mũi tên chỉ thẳng vào kênh log làm bãi đáp khai thác.

Hệ thống tối giản đến mức tàn nhẫn: Không có khái niệm đăng nhập tài khoản, không cho phép tải tệp tin lên. Chỉ có duy nhất một form ném vào cổng `POST /proof.php`.

## Phân tích ban đầu

Mổ xẻ biểu mẫu (form), ta đếm được 9 trường dữ liệu: `title`, `author`, `degree`, `department`, `institution`, `supervisor`, `year`, `abstract`, và `reference`. Trường `reference` tự mô tả là "tên tệp tin tải về của bạn", trong khi trường `title` (tiêu đề) lại đính kèm một dòng hướng dẫn cực kỳ nhạy cảm:

> Mẹo: Bạn có thể nhập các ký tự có dấu và biểu tượng bằng cú pháp LaTeX, ví dụ: `M\"uller`, `\'Etienne`, `\OE`. Máy chế bản của chúng tôi sẽ kết xuất (render) chúng thành hình cho bạn.

Dòng chữ này vừa là một tính năng thân thiện, vừa là một bản thú tội chết người: Mọi chuỗi văn bản mà người dùng nhập vào sẽ bị hệ thống ghép trực tiếp (inject) không che chắn vào mã nguồn LaTeX.

Ném thử một request hợp lệ và ngụp lặn trong khối log trả về, bản chất của cỗ máy chế bản hiện nguyên hình:

```text
This is pdfTeX, Version 3.141592653-2.6-1.40.26 (TeX Live 2025/dev/Debian)
(preloaded format=pdflatex) \write18 enabled.
entering extended mode
(./main.tex
```

Ba phát hiện định đoạt số phận của máy chủ:

1. Ứng dụng web tự động nặn ra tệp `main.tex` nhồi bằng input của ta, sau đó đá cho luồng `pdflatex` thi hành.
2. Cờ `\write18 enabled.` treo lù lù - Cánh cửa thoát hiểm shell (shell escape) đang được bật mở hoàn toàn (full), chứ không hề bị kiểm soát chật hẹp trong chế độ `restricted`.
3. Toàn bộ ruột gan của kênh log (bao gồm cả luồng báo lỗi `stderr`) đều được nhà phát triển hồn nhiên đem hiển thị lại trên màn hình của người gửi.

## Chuỗi khai thác

**Bước 1 - Dùng dao mổ trâu kiểm chứng lỗ hổng LaTeX Injection tại `title`.** 
Gửi một lệnh macro vô hại nhưng để lại tì vết rõ ràng:

```text
A\typeout{ZZMARKERZZ}
```

Nhãn hiệu `ZZMARKERZZ` ung dung hiển thị nguyên vẹn trong bản log báo cáo. Bằng chứng thép: Ký tự gạch chéo ngược (backslash) của ta hoàn toàn không bị hệ thống dùng bộ lọc tẩy rửa, và trình biên dịch TeX vẫn ngoan ngoãn thực thi cái macro rác rưởi do ta ném vào.

Cạm bẫy kỹ thuật chết người ở khâu này: Nếu bạn ném lệnh thông qua hàm `fetch()` trong giao diện F12 (devtools) của trình duyệt, chuỗi JS `'A\typeout{...}'` sẽ bị triệt tiêu dấu backslash ngay ở tầng thoát chuỗi (escape) của ngôn ngữ JavaScript (ví dụ, cụm `\t` biến hình thành phím tab). Điều này sẽ dắt mũi bạn đưa ra kết luận sai lầm rằng biến `title` đã bị server cắm bộ lọc. Để vượt qua, payload phải được tiêm một cách vô trùng bằng lệnh `String.fromCharCode(92)` thì mới phán xét được.

**Bước 2 - Bật tung cánh cửa Shell Escape.** 
Với sức mạnh của bộ quyền `\write18` thả rông, ta chỉ cần một dòng macro duy nhất là đủ để kích hoạt quyền thực thi lệnh hệ thống tùy ý (RCE):

```latex
\immediate\write18{<câu_lệnh_system_ở_đây>}
```

**Bước 3 - Định tuyến kênh vớt dữ liệu (Data Exfiltration).** 
Sau khi lệnh chạy trót lọt, kết quả nôn ra sẽ đổ đi đâu? Có ba bãi đáp: 
Hoặc ta lưu nó ra một file rồi dùng lệnh `\input` để nhúng vào trang văn bản (đáp án sẽ hằn lên tệp PDF, ta phải tải xuống và soi PDF); 
Hoặc ta bẻ lái (redirect) luồng dữ liệu đó tống thẳng vào ống xả `stderr` của luồng pdflatex - chính là cái ống xả mà ứng dụng web đang cắm thẳng vào màn hình người dùng. Đương nhiên ta chọn con đường thứ hai cho nhanh:

```latex
C\immediate\write18{cat /flag.txt 1>&2}
```

Macro `\write18` sinh ra một tiến trình con (child process) được thừa kế trọn vẹn bộ mô tả tệp (file descriptor) của tiến trình mẹ pdflatex. Cú pháp `1>&2` bóp luồng đầu ra `stdout` của lệnh `cat` và xả thẳng vào dòng suối `stderr` (luồng dữ liệu mà ứng dụng web hứng trọn để làm log). Trò ảo thuật này hoàn tất mà không cần phải tải hay động chạm một ngón tay vào cái file PDF, cũng chẳng cần phải ghi ra bất kỳ một file rác nào trên máy chủ.

Kết quả nảy tung tóe ngay trên màn hình log:

```text
WEBVERSE{d5f60724dc9f1197140001fa4b24198e}
```

**Bước 4 - Đóng gói vũ khí và vận hành độc lập.** 
Kịch bản Python `exploit.py` dùng thư viện `requests`, rũ bỏ gánh nặng phải ôm cookie hay đăng nhập tài khoản. Kịch bản này sẽ thả một lệnh dò (probe) `id` để thăm dò xem cánh cửa shell escape có thực sự mở hay không, trước khi nã lệnh kết liễu. 
Hai hạt sạn đã được gỡ bỏ trong quá trình tinh chỉnh mã: Dữ liệu log bị kẹt trong thẻ `<pre class=...>` của HTML nên lệnh bóc tách (regex) phải dùng khuôn `<pre[^>]*>`; và máy chủ sẽ giở mặt trả về một trang báo lỗi nếu vắng mặt trường `User-Agent` hợp lệ của trình duyệt web.

## Flag
```bash
python exploit.py https://978870f9-5765-justified-06d98.mystery-challenges.webverselabs-pro.com
```

Kết quả báo về mượt mà:
```text
[*] Cửa shell escape đã mở toang: uid=33(www-data) gid=33(www-data) groups=33(www-data)
[+] flag: WEBVERSE{d5f60724dc9f1197140001fa4b24198e}
```
