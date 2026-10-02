# VecNet - Web (Hard)

**Flag:** `sun{k33p_your_emb3ddings_secur3!}`

## Đề bài

> "VecNet makes use of AI embedding technologies to speed up your database needs. Get started today!" 

Mục tiêu tấn công là ứng dụng web tại `https://vec.web.2026.sunshinectf.games/`, không có bất kỳ file suorce nào được cung cấp.

Thử thách này dẫn dắt người chơi qua một hành trình 4 lớp vỏ bọc, mỗi lớp lại mở ra chìa khoá cho lớp tiếp theo: Lỗ hổng rò rỉ thư mục `/.git` công khai giúp khôi phục tệp `config.php` đã bị tác giả revert (thu hồi). Từ `config.php`, ta có thông tin đăng nhập để tiếp cận hòm thư MailHog. Nội dung thư trong MailHog hé lộ thông số cấu hình model `vec2text` và đường link tải kho lưu trữ `specs.7z`. Cuối cùng, dịch vụ cơ sở dữ liệu vector Chroma chạy ngầm trên cổng 8000 chứa ba bản ghi (record), trong đó một bản ghi bị che giấu chữ nhưng lại để lộ nguyên vẹn vector 768 chiều. Công cụ `vec2text` sẽ giải mã vector này thành câu văn tiếng Anh mô tả luật tạo mật khẩu cho kho nén `specs.7z`. Mật khẩu thực sự được vét cạn siêu tốc nhờ việc đối chiếu mã băm (hash) SHA256 đã cho sẵn trong database.

Đối với phần bề mặt còn lại (như SQLi, SSRF, XSS), không có bất kỳ ngõ ngách nào để khai thác. Danh sách các giả thuyết thất bại được tổng hợp ở cuối bài.

## Phân tích ban đầu

Kiểm tra hạ tầng mạng cơ bản:
```text
443   Apache/2.4.68 + PHP/8.2.33   Thư mục gốc (docroot) chính là kho Git, hớ hênh phơi bày /.git
8025  MailHog web UI               Bị chặn bởi cơ chế xác thực Basic Auth của nginx
8000  GET /api/v2 -> {"nanosecond heartbeat": ...}   Đây chính là dịch vụ Chroma
```

Cổng 8000 được phát hiện thông qua kỹ thuật quét cổng (port scan) công khai. Công cụ `paths.py` gọi thử đường dẫn `/api/v2` đồng loạt trên cả ba cổng 443, 8025 và 8000; chỉ có duy nhất cổng 8000 phản hồi một chuỗi JSON nhịp tim (heartbeat) sống động.

## Chuỗi khai thác

### Bước 1 - Phục hồi dữ liệu từ `/.git`

Nhật ký reflog (`/.git/logs/HEAD`) điểm mặt gọi tên đầy đủ 5 mã băm SHA, loại bỏ yếu tố phải đoán mò. Sử dụng đoạn mã tự chế `githist.py` làm trình đọc đối tượng git thô (chạy zlib, áp dụng định dạng `<type> <len>\0<content>`; tree entry `<mode> <name>\0<20-byte sha>`), ta bóc tách từng commit và lần ra nhánh cấu trúc cây thư mục (tree):

```text
3e02a92  initial site deploy
517ac72  add embed preview endpoint
c3cd120  add internal service config          <- Tệp config.php được tạo ở đây
130e195  REVERT: do not commit secrets        <- Tác giả nhận ra sai lầm, xoá file và giấu vào .gitignore
e6a0074  add htaccess                         <- HEAD hiện tại
```

Lệnh `git rm` chỉ có tác dụng cắt bỏ tệp khỏi cây cấu trúc hiện hành; phần thân (blob) cũ vẫn an toạ tại đường dẫn `.git/objects/c3/...`. Máy chủ Apache hồn nhiên phục vụ phân vùng này như một tệp tĩnh:

```php
define('MAIL_ADMIN_URL',  'http://127.0.0.1:8025');
define('MAIL_ADMIN_USER', 'vecadmin');
define('MAIL_ADMIN_PASS', 'Emb3dPass2026!');
define('INTERNAL_API_KEY', 'vsk_live_aX92kLmNpQrStUvWxYz');
```

Khoá `INTERNAL_API_KEY` hoàn toàn vô dụng. Dịch vụ Chroma tại đây xác thực trực tiếp thông qua HTTP Basic Auth, và khoá này không tạo ra bất kỳ khác biệt nào trong các phản hồi của hệ thống.

### Bước 2 - Manh mối từ hòm thư MailHog

Sử dụng cờ lê `vecadmin:Emb3dPass2026!`, gọi `GET http://...:8025/api/v2/messages` mở toang toàn bộ hòm thư. Trong 3 bức thư nội bộ, không có cờ nào lộ diện, nhưng hai bức thư lại chứa những "bản đồ kho báu":

* Greg gửi cho Mike: "Here are the vec2text specifications you were asking for earlier: `num_steps=4, sequence_beam_width=5`", đính kèm link tải `http://...:8025/files/specs.7z`.
* Greg trấn an Steve: "our ChromaDB database is not exposed to the open Internet, and is only accessible on our local servers, served with proper authentication to our web interface". Lời khẳng định này mang nghĩa đen tuyệt đối: cơ sở dữ liệu Chroma không được mở ra ngoài internet, mà nó đang nằm chình ình ở cổng 8000 của chính máy chủ đó.

### Bước 3 - Lấy file `specs.7z` qua lỗ hổng Local Fetch

Mã nguồn xử lý tệp:
```php
const ALLOWED_URL = 'http://localhost/files/specs.7z';
if (!isset($_GET['url']) || !hash_equals(ALLOWED_URL, $_GET['url'])) fail_request(403, ...);
readfile('/var/www/html/files/specs.7z');
```

Kịch bản rất bảo thủ: Chỉ chấp nhận GET request, ép cứng đúng một giá trị tham số `url`, và không gửi bất kỳ request nào ra ngoài (loại trừ SSRF). Thứ ta tải về được là một tệp nén mật mã:

```text
Method = LZMA2:12 7zAES     1 thành viên: flag.txt, kích thước 34 byte
```

Bảng danh sách nội dung bên trong tệp nén không bị che lấp, nên lệnh `7z l -slt` tiết lộ chính xác chiều dài của cờ. Đáng tiếc là toàn bộ kho từ khoá thu thập được (`Emb3dPass2026!`, `vsk_live_...`, `sunshinectf8_`, và một chuỗi băm sha256) khi thử nghiệm đều va phải thông báo "Wrong password".

### Bước 4 - Dò dẫm trong bóng tối Chroma

Thử gọi `GET /api/v2/collections` nhận về thông báo cụt lủn:

```json
{"error":"route not allowed"}
```

Phản ứng này y hệt 625 định dạng route rác khác, rất dễ gây ảo giác rằng "cần quyền authentication nâng cao". Sự thật là Chroma phiên bản 1.x không hề có route đó; `/api/v2/collections` thuộc về định dạng của bản Chroma v1 cũ, trong khi phiên bản 1.x đã chuyển sang mô hình tổ chức theo người dùng (tenant). Bảng danh sách route chuẩn được trích xuất thẳng từ tệp nguồn wheel của Chroma (`chromadb/server/fastapi/__init__.py`, lấy về qua lệnh `pip download chromadb==1.0.0 --no-deps`):

```text
/api/v2/auth/identity
/api/v2/tenants/{tenant}/databases/{database}/collections
/api/v2/tenants/{tenant}/databases/{database}/collections/{uuid}/get     POST
```

Endpoint `auth/identity` thuộc danh sách công khai, nó khai báo luôn tên tenant và tên cơ sở dữ liệu mặc định:

```json
{"user_id":"","tenant":"default_tenant","databases":["default_database"]}
```

Ráp các mảnh lại với nhau:

```text
GET  /api/v2/tenants/default_tenant/databases/default_database/collections
 -> [{"id":"455b419b-...","name":"VecNetDB","dimension":768,
      "configuration_json":{...,"embedding_function":null}, ...}]

POST /api/v2/tenants/default_tenant/databases/default_database/collections/455b419b-.../get
      {"include":["metadatas","documents","embeddings","uris"]}
```

Hai nguyên tắc ngặt nghèo cần vượt qua: Đường dẫn bắt buộc phải dùng định danh UUID (nếu đưa thẳng tên `VecNetDB` vào sẽ ăn lỗi `route not allowed`), và tham số `include` chỉ duyệt qua 5 khoá giới hạn; nếu gọi sai tên khoá, server sẽ chửi mắng bằng mã lỗi 422 và đọc to luôn đáp án đúng (`distances, documents, embeddings, metadatas, uris`).

Hàng về, cơ sở dữ liệu mở toang:

| ID | Thể loại | Nội dung Document |
| --- | --- | --- |
| `magic_string` | plaintext | `sunshinectf8_` |
| `user_hash_sha256` | plaintext | `d8dd241199d2617765d7613fdd1df5358297b55f258647fe463de586bbfe3ebf` |
| `user_password_requirements` | embedding_only | `null` (Bị xoá chữ), nhưng vẫn nguyên vẹn một vector 768 chiều |

Hai bản ghi chữ nổi (plaintext) không thể mở khoá archive. Điều may mắn là bản ghi ẩn chữ có mang thông tin `embedding_fn` là `jxm/gtr__nq__32` – khớp chính xác với checkpoint mô hình mà phần mềm vec2text cần dùng cho gốc `gtr-base`. Bộ tham số trong thư của Greg đã đến lúc toả sáng.

### Bước 5 - Triệu hồi vec2text giải ngược mô hình

Khâu chuẩn bị gian nan: Việc cài đặt `pip install vec2text sentence-transformers` trên Windows đòi hỏi hai bản vá dị biệt do xung đột thư viện:

* Code gốc `vec2text/__init__.py` vô tình nạp một file gọi thư viện `resource` (chỉ độc quyền trên nền tảng POSIX/Linux). Cách giải quyết: Dùng thủ thuật stub chặn `sys.modules["resource"]` trước khi import.
* Công cụ `vec2text` bị ghim cứng cờ `low_cpu_mem_usage=True`; trong khi đó bản `transformers 5` khởi tạo đồ thị model bằng hàm `init_empty_weights()` ép thiết bị ảo (default device) thành `meta`. Oái oăm thay, class `InversionModel.__init__` lại hì hục nhồi một mô hình T5 thật vào bên trong bối cảnh đó, khiến hàm `check_and_set_device_map()` phát nổ (raise exception). Phải hạ cấp: `transformers==4.53.2` + `sentence-transformers<4`.

Khi chạy rà soát đối chiếu lên vector đã biết trước đáp án:

```text
inversion(vec(magic_string)) -> '   suncf8_ '      (hệ số Cosine 0.85)
```

Kiểu rơi rớt ký tự (`shin`, `t`) là đặc sản của vec2text, nhưng nó khẳng định cỗ máy đã vận hành. Giải mã tiếp vector mật mã `user_password_requirements`:

```text
The user's first and last initials, three special characters followed by the magic string.
(Hai chữ cái đầu tên người dùng, 3 ký tự đặc biệt, theo sau là magic string).
```

Để củng cố niềm tin không phụ thuộc vào con người, ta đo đạc lại: Dùng chính mô hình GTR đóng băng (frozen) nhúng ngược câu tiếng Anh kia thành vector mới rồi đo hệ số cosine với vector ban đầu. Kết quả: cos = 0.9956, vượt bậc so với hệ đối chiếu, khẳng định đây chính là câu văn gốc nguyên bản không sai một dấu phẩy.

### Bước 6 - Sinh mật khẩu: Sức mạnh mã băm thay vì vét cạn file nén

Câu văn giải mã không trao tận tay mật khẩu, mà nó trao công thức:

```text
<2 chữ cái tên><3 ký tự đặc biệt>sunshinectf8_
```

Không gian vét cạn ước tính: `26*26` (cặp chữ cái) × 4 (kiểu viết hoa/thường) × `32^3` (ký tự đặc biệt) = 88.6 triệu tổ hợp. Nếu tấn công thô bạo thẳng vào file nén 7z, mỗi lượt cần tốn ~0.2 giây, tính ra mất hơn 200 giờ ròng rã. Tuy nhiên, nhờ cơ sở dữ liệu ban nãy đã hào phóng để lại chuỗi `user_hash_sha256`, và thời gian sinh một mã sha256 chỉ mất cỡ ~1µs, toàn bộ không gian tổ hợp khổng lồ này bị phá tan tành chỉ trong ~35 giây nhờ chia tải (multiprocessing) 8 luồng (`crack2.py`).

```text
[+] Mật khẩu trùng khớp: GR$*#sunshinectf8_
```

`GR` hiển nhiên là cụm viết tắt tên của anh chàng Greg Roberts trong nhóm. Ba ký tự đặc biệt đi kèm là `$*#`.

### Bước 7 - Mở kho báu

```bash
$ python -c "subprocess.run(['7z','x','-y','-pGR$*#sunshinectf8_','-oanalysis/unpacked','files/specs.7z'])"
Everything is Ok
Size: 34

$ cat analysis/unpacked/flag.txt
sun{k33p_your_emb3ddings_secur3!}
```

## Flag
```
sun{k33p_your_emb3ddings_secur3!}
```

## Khám nghiệm các giả thuyết đã chết (Rabbit Holes)

| Giả thuyết | Nguyên nhân tử vong |
| --- | --- |
| Lỗi SSRF qua cổng `fetch.php` | Hệ thống kiểm tra chặt chẽ `hash_equals` với một chuỗi cố định tĩnh, chỉ nhận GET, và chỉ đọc tệp tin cục bộ qua lệnh `readfile` |
| Hòm thư IMAP/SMTP mailstore | Có dấu hiệu chỉ điểm trong tệp `index.html` nhưng cổng không cho phép kết nối ngoại mạng |
| Token uỷ quyền cho Chroma | Biến `INTERNAL_API_KEY` hoàn toàn vô dụng, không thay đổi phản ứng của 626 route API đã bị rà quét |
| Route `/api/v2/collections` | Đây là bóng ma của phiên bản v1; bản Chroma 1.x thẳng thừng báo `route not allowed` vì endpoint này đã bị khai tử |
| Cờ nằm rải rác trong MailHog | Đã cày xới nát 3 bức thư nội bộ, hoàn toàn vắng bóng từ khoá `sun{` |
| Mật khẩu nằm trong số các mật khẩu nhặt được | Mọi ứng viên đều bị tiện ích 7z từ chối với thông báo "Wrong password" |
| Sử dụng thư viện sentence-transformers để sinh vector đối chiếu | Mô hình `jxm/gtr__nq__32` trên HuggingFace là điểm neo dành riêng cho phần mềm vec2text chứ không phải là mô hình của ST (sentence-transformers); hướng đi này cụt lủn. May thay, khối sửa lỗi (corrector) đã tích hợp sẵn cơ chế nhúng (embedder) nội bộ nên ta vẫn tính toán được chỉ số cosine oracle |

## Phục dựng (Reproduce)

```bash
python exploit.py            # Quét mã băm, thời gian ~40 giây, không đòi hỏi PyTorch
python exploit.py --invert   # Buộc khởi chạy cỗ máy vec2text giải mã ngược, mất ~3 phút (do mô hình đã lưu vào bộ đệm cache)
```

Cả hai kịch bản đều đã được thử lửa trên môi trường máy chủ (instance) thật sau thời điểm thu được cờ, và đều tự động khôi phục hoàn hảo lá cờ được trình bày ở trên.
