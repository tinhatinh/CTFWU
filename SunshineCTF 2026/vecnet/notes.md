# notes.md - VecNet (SunshineCTF 2026, web 493đ)

Ghi lại những thứ đo được trực tiếp trên instance, không suy luận.

## Định danh dịch vụ

| Cổng | Bề mặt | Đo được |
| --- | --- | --- |
| 443 | Apache/2.4.68 (Debian) + PHP/8.2.33, docroot là repo | `index.html`, `fetch.php`, `/.git/`, `files/` bị `Require local` |
| 8025 | MailHog web UI, chặn sau nginx Basic | `GET /api/v2/messages` trả hết mailbox |
| 8000 | **Chroma** (version `"1.0.0"`), cùng bộ trả lời 403 kiểu Apache/PHP | `GET /api/v2` = heartbeat, `GET /api/v2/version`, `GET /api/v2/auth/identity` |

Toàn bộ payload/credential lấy từ chính artifact: `/.git` (loose object), MailHog REST, Chroma REST.

## 1. `/.git` public, config.php nằm trong history

Reflog (`/.git/logs/HEAD`) liệt kê 5 SHA. `gitdump.py`/`githist.py` là loose-object reader tự viết
(zlib `<type> <len>\0<content>`, tree entry `<mode> <name>\0<20-byte sha>`), đi hết các commit và
in ra tree từng commit. Chuỗi commit:

```
3e02a92  initial site deploy
517ac72  add embed preview endpoint
c3cd120  add internal service config        <- config.php
130e195  REVERT: do not commit secrets      <- xoá config.php, thêm .gitignore
e6a0074  add htaccess                       <- HEAD
```

Object của `config.php` vẫn còn trên disk nên vẫn đọc được:

```php
define('MAIL_ADMIN_URL',  'http://127.0.0.1:8025');
define('MAIL_ADMIN_USER', 'vecadmin');
define('MAIL_ADMIN_PASS', 'Emb3dPass2026!');
define('INTERNAL_API_KEY', 'vsk_live_aX92kLmNpQrStUvWxYz');
```

`INTERNAL_API_KEY` **không** dùng cho đâu cả: Chroma ở đây xác thực bằng HTTP Basic
(`vecadmin:Emb3dPass2026!`). Đã quét 588 tổ hợp header/key với key sai (`thiếu chữ z cuối`) và
không khác gì nhau, nên đừng có quay lại hướng đó.

## 2. MailHog: 3 thư, không có cờ

| Từ | Tới | Nội dung chính |
| --- | --- | --- |
| Steve (CEO) | Greg | forward bài "Vector Database Breaches: how embeddings expose your sensitive data" |
| Greg (sysadmin) | Steve | "ChromaDB không expose ra Internet, chỉ phục vụ qua web interface có authentication" |
| Greg | Mike | **`num_steps=4`, `sequence_beam_width=5`** + link `http://...:8025/files/specs.7z` |

## 3. fetch.php và specs.7z

`fetch.php` (mọi commit từ `517ac72` trở đi giống nhau): GET-only, `hash_equals()` với đúng
chuỗi `http://localhost/files/specs.7z`, rồi `readfile('/var/www/html/files/specs.7z')`. Không có
SSRF. Sản phẩm duy nhất là archive 186 byte:

```
Method = LZMA2:12 7zAES     one member: flag.txt, 34 byte
```

`7z l -slt` lộ tên member và kích thước, đó là lý do biết trước cờ dài 33 ký tự + `\n`.

## 4. Chroma: 403 "route not allowed" không phải tường auth

Sai lầm đắt nhất của vòng này: gọi `GET /api/v2/collections` -> 403, kết luận "cần authentication
đúng". Chroma **1.x không có route đó**, nó là shape của v1. Bảng route thật (rút từ wheel
`chromadb-1.0.0`, file `chromadb/server/fastapi/__init__.py`) là tenant-scoped:

```
/api/v2/auth/identity
/api/v2/tenants/{tenant}/databases/{database}/collections
/api/v2/tenants/{tenant}/databases/{database}/collections/{uuid}
/api/v2/tenants/{tenant}/databases/{database}/collections/{uuid}/get     (POST)
```

`auth/identity` nằm trong nhóm route được phép và **tự khai** tenant + database:

```json
{"user_id":"","tenant":"default_tenant","databases":["default_database"]}
```

Ghép lại là đọc được hết. Bài học: 403 đều nhau trên mọi route lạ là *bộ lọc route*, không phải
câu trả lời "sai mật khẩu"; phải lấy bảng route thật của sản phẩm rồi mới kết luận.

`POST .../get` với `include` sai thì server trả 422 **liệt kê luôn các giá trị hợp lệ**
(`distances, documents, embeddings, metadatas, uris`): đọc error text của target là tài liệu.

## 5. Ba record

| id | type | document |
| --- | --- | --- |
| `magic_string` | plaintext | `sunshinectf8_` |
| `user_hash_sha256` | plaintext | `d8dd241199d2617765d7613fdd1df5358297b55f258647fe463de586bbfe3ebf` |
| `user_password_requirements` | **embedding_only** | `null`, vector 768 dim |

`embedding_fn` của cả ba: `jxm/gtr__nq__32` - cũng chính là checkpoint mà vec2text nạp cho
đường "gtr-base", nên tham số inversion trong thư của Greg là dùng được ngay.

## 6. vec2text trên Windows

* `pip install vec2text sentence-transformers` kéo theo transformers 5.x -> **vỡ**. vec2text 0.0.13
  pin `low_cpu_mem_usage=True`, transformers 5 khởi tạo model trong `init_empty_weights()` đặt
  default device = `meta`, rồi `InversionModel.__init__` nạp T5 thật từ trong context đó và
  `check_and_set_device_map()` raise. Chốt lại ở `transformers==4.53.2` + `sentence-transformers<4`.
* `vec2text/__init__.py` import `experiments`, file này `import resource` (chỉ có trên POSIX),
  nên phải stub `sys.modules["resource"]` trước khi import.
* Điều khiển tích hợp sẵn trong `invert.py`: vector của `magic_string` (đoạn text đã biết) phải
  ngược ra gần đúng. Nó trả `'  suncf8_ '` với cos 0.85 -> harness sống, kết quả target đáng tin.
* Oracle độc lập với chất lượng inversion: dùng chính GTR frozen bên trong corrector nhúng lại
  hypothesis rồi so cosine với vector đã lưu. Target đạt **cos 0.9956**.

Câu recovered:

> The user's first and last initials, three special characters followed by the magic string.

## 7. Password: tìm bằng sha256, không phải bằng 7z

Không gian: `26*26` cặp chữ cái × 4 dạng hoa/thường × `32^3` ký tự đặc biệt = **88.6M**.

* Thử trực tiếp lên 7zAES: mỗi lần thử ~0.2s -> hơn 200 giờ.
* `user_hash_sha256` chính là oracle: một lần sha256 ~1µs -> toàn bộ không gian chạy hết trong
  ~35 giây với 8 process (`crack2.py`).

Kết quả: `GR$*#sunshinectf8_` khớp digest, và `7z x` xác nhận ("Everything is Ok", 34 byte).

Đình chỉ search giữa chừng bằng cách chỉ in khi `done % 200 == 0`: đừng dùng một generator chung
rồi `islice` theo offset cho từng chunk, generator có state nên các worker ăn lặp và cạn rất nhanh
(bản `crack.py` đầu tiên báo "31808M tried" là do bug đó, không phải do máy nhanh).

## 8. Cờ

```
sun{k33p_your_emb3ddings_secur3!}
```

## File

| file | vai trò |
| --- | --- |
| `exploit.py` | chuỗi đầy đủ 5 bước, chạy thật trên target (`--invert` để chạy lại vec2text) |
| `gitdump.py`, `githist.py` | đọc `/.git`, đi hết reflog |
| `paths.py`, `raw.py`, `probe8000.py` | quét cổng/route, xác định 8000 là Chroma |
| `sw.py` | 90 từ vựng × 4 extension trên 443 (anon + auth): không có app nào khác, mọi thứ 404 |
| `embed.py` | quét 626 shape route trên :8000, gom theo (status, length, prefix) |
| `ten.py`, `coll.py`, `getemb.py` | đúng đường đi tenant-scoped, dump collection + embeddings |
| `invert.py` | vec2text: control + target + cosine oracle |
| `crack2.py` | search sha256 theo cấu trúc |
| `files/repo-history/cN/` | source PHP theo từng commit |
| `analysis/` | log, dump JSON, mail, archive đã giải nén |
