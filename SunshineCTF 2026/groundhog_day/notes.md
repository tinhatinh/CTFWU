# Groundhog Day - notes

Log theo gia thuyet. Moi lan thu = 1 connection, goi tuan tu, co timeout.
Uoc soan: ~370 request lenh `odyssey.web.2026.sunshinectf.games` (khong quet mang ngoai).

---

## H1 - "comment ops trong HTML la chan dung dan"

`files/root.html` cuoi trang:

```
<!-- ops: console pulls station JSON at boot from http://127.0.0.1:8000/feed.
     override it with feed=<url> when PUNX-1 is down ... manual override panel below... -->
<!-- feed-debug: source=http://127.0.0.1:8000/feed bytes=350 -->
```

Thu `GET /?feed=...` va `POST / feed=...`: ca hai deu fetch, `source=` echo lai dung URL
toi gui, `bytes=` = do dai body response.

result: OK - SSRF co that, GET duoc o ca hai phuong thuc, va co 2 oracle (`source`, `bytes`).

## H2 - "client la requests/urllib3, khong phai curl"

`file://`, `gopher://`, `dict://`, `ftp://`, `data:` deu tra `bytes=0`.
curl se chay duoc `file://` va `gopher://`. urllib3 chi co 2 adapter http/https.
Them: `bytes=0` khi URL chua CRLF that (urllib3 `InvalidURL`).

result: OK - client kieu requests. Khong co nguom "scheme duoc phep" rieng, chi là do
chinh client khong ho tro. Nghia la `file://` va gopher-smuggling khong phai la loi giai.

## H3 - "SSRF doc duoc het network nội bộ"

`nip.io` giai duoc (DNS ngoai hoat dong). `169.254.169.254` va `metadata.google.internal`
deu tra ve duoc data. Nhung `http://127.0.0.1:80|443|8080|8001|5001|3000|9000|6379|5432|11211`
-> `bytes=0`.

result: MOT PHAN - DNS ok nhung khong co egres TCP ra ngoai (xem H9). Port quét trên
`127.0.0.1` (24 port) chi ra 5000 va 8000.

## H4 - "internal station co nhieu endpoint hon docs"

Docs (`/`) ke 3 endpoint. Toiquet **139 tu** (theme + chuan Flask) tren ca `:8000` lan
`:5000`, cong them **~30 path nhieu tang** (`/api/v1/report`, `/internal/render`,
`/report/pdf`, `/microfilm/scan`...). Oracle: 404 = 207 byte, 405 = 153 byte ( khong phan
anh URL nen do dai khong doi).

result: DEAD - khong co route moi. Station dung chinh xac 3 rule._console_ chi co `/`.
Dac biet: moi rule POST-only se lo 153 byte khi goi bang GET, nen phep thu cung da lo
duoc "endpoint bi an" dang POST.

## H5 - "co cach bien GET thanh POST /report"

Da thu va bat 405 (=GET) trong moi truong hop:

- `?method=POST`, `?_method=POST`, `?__method`, `?http_method`, `?verb`, `?request_method`,
  `?mode=POST` (tren upstream va tren console)
- GUI: `X-HTTP-Method-Override`, `X-Method-Override` (khong co passthrough header - xem H7)
- POST toi console voi `feed` o query / o body / multipart / `application/json` / `text/plain`
- method cau than: console goi PUT/PATCH/DELETE/HEAD/OPTIONS -> khong tao noi dung khac
- routing quirk: `//report`, `/./report`, `/%72eport`, `/report;`, `/report.`, `/report/`,
  `/report/..` (-> 1045 = index, chi la normalize), `/report%2f`, `/report%00`
- Host khac nhau: `localhost`, `0`, `127.1`, `2130706433`, `nip.io` -> cung 1045/153,
  nghia la khong co host_matching / vhost
- 19 ten tham so khac tren console (`url`, `spare`, `station_url`, `feed_url`, `upstream`,
  `origin`, `target`, `endpoint`, `proxy`, `src`, `uri`...) -> chi `feed` duoc nghe

result: DEAD cho den khi co them thong tin. Console luon luon GET.

## H6 - "doc co may GCP metadata la huong chot"

`/` -> listing `computeMetadata/ `; `/computeMetadata/` -> `v1/ `; moi thu duoi
`/computeMetadata/v1/*` -> **403** kem dung dong:

```
Your client does not have permission to get URL <path> from this server.
Missing Metadata-Flavor:Google header.
```

Mock co router rieng (trang 404/403 cua no, echo lai chinh xac `path?query` ma console da
xin - day la mot request-echo rong rat huu ich). Toi que 23 path khac tren host nay:
tat ca deu 404/403 hoac listing.

result: DEAD - mock nay gateway bang header, va GET-SSRF khong them duoc header.
Kha nang cao day la infra chia cua toan cloud-category, khong phai sink cua bai nay.

## H7 - "console forward header cua nguoi goi"

Gui `Metadata-Flavor: Google` (va 3 hoa thuong khac nhau), `X-Forwarded-For`, `Referer`
trong ch chinh request toi console. Mock van 403 y het.

result: DEAD - khong co header passthrough.

## H8 - "SSTI o cho render"

- `feed={{7*7}}` khong phai URL -> fetch fail, nen phep thu nay **vo nghia** (loi cua toi).
- Test dung dan: dua payload vao **body** thong qua trang 403/404 cua mock (no echo
  duong dan). `{{7*7}}`, `{{config}}`, `${7*7}`, `<%= 7*7 %>` -> trang console tra ve
  dung van ban goc, khong co `49`, khong co traceback.

result: DEAD cho duong "body non-JSON" (toan bo duoc escape).
**CHUA THE TEST** duong "JSON field" (`sky`, `advisory` duoc chen vao template), vi muon
vay phai tu controller duoc JSON - ma egress bi chan (H9).

## H9 - "mang spare station nhu docs gay thach"

Docs/ops noi "override ... point at a spare station" -> toi deploy mot JSON tinh
(`station.json`, 532 byte) tren Qoder Sites cua chinh nguoi dung (da xin phep, va da
public roi doi lai private khi xong).

- Tu may toi: `https://.../station.json` -> **200**, 532 byte.
- Tu console: cung URL -> `bytes=0`, ca https lan http:80 (va sau khi da flip public).

result: DEAD ve mat thuc tien - container khong co egres ra ngoai.
Khong phan biet duoc WAF-chan-UA va het-egres vi analytics tra ve
`ingestion_watermark_unavailable` (khong phai so 0 that).

## H10 - "Groundhog Day nghia la lap lai cho toi khi khac"

Every reading is fresh -> moi lan `/feed` re-roll. Lay **80 mau** `/feed` qua SSRF:

- kich thuoc: 339-359, 20 gia tri lien tuc, khong co outlier > 365
- tap hop key: **80/80 giong het nhau** (13 key), khong lo `flag`/`note`/`data`
- 5 chuoi `advisory`, 7 chuoi `sky`, khong co hang tu hiem

result: DEAD (o mau 80). Khong co "rare reading".

## H11 - loi do cua chinh toi (ghi lai)

1. Lan dau test SSTI toi dat payload vao `feed` - doan nay sai vi payload khong bao gio
   vao duoc body. Phai mao qua echo cua mock moi ra kết quả có nghĩa.
2. Toi tung bao "khong co egress" dua theo `nip.io` -> sai: DNS duoc, TCP moi khong.
3. Mot lan toi dung `base = <leak cua connection A>` cho cac connection B/C trong phan
   internal path; khong anh huong ket luan SSRF (khong co ASLR o day) nhung van la
   mot thoi quen xau can tranh.

## H12 - "đọc thông báo lỗi do chính template in ra" (bước ngoặt)

Tôi bỏ qua một kênh có sẵn từ đầu: state lỗi của trang in exception ra
`<p class="fault">...</p>`. Quét 18 lớp lỗi khác nhau cho ra:

```
file://, data:, "hello"  -> unsupported transport for station feed
http:// (khong host)     -> station unreachable - URL rejected: No host part in the URL
port >= 65536            -> station unreachable - URL rejected: Port number was not a decimal number between 0 and 65535
127.0.0.1:1              -> station unreachable - Failed to connect to 127.0.0.1 port 1 after 0 ms: Could not connect to server
URL co space             -> station unreachable - URL rejected: Malformed input to a URL function
```

Ba chuoi do la cua **libcurl** (`Failed to connect to ... port N after M ms`,
`URL rejected: ...`, `Could not resolve host:`). requests/urllib3 khong bao gio in ra nhu
vay.

=> **client là libcurl** (curl CLI hoac pycurl). `file://` chet vi **allow-list cua tac
gia** (thong bao tu che "unsupported transport"), khong phai vi client. Nhung
**`gopher://` lot qua allow-list**, va libcurl gui selector da percent-decode thang xuong
socket.

result: **BREAKTHROUGH** - doi het lop cong cu sau ~350 request mu quang. Bai hoc: kenh
loi cua ung dung la tai lieu mo ta implementation mien phi.

## H13 - "gopher smuggle mot request HTTP tho"

`feed=gopher://127.0.0.1:8000/_GET%20/health%20HTTP/1.1%0d%0aHost:%20127.0.0.1%0d%0a%0d%0a`

Tape tra ve **toan bo response tho, gom ca header**:

```
HTTP/1.1 200 OK
Server: Werkzeug/3.1.8 Python/3.13.7
Content-Type: text/plain; charset=utf-8
Content-Length: 3

ok
```

Ca `_` lan `x` lam ky tu selector dau deu hoat dong. Tu do `POST /report` chay duoc
(`bytes=11230`, JSON co `document`, `bytes`, `encoding`, `data`).

result: **CONFIRMED** - GET/POST khong con la rao can. Dong nghia buc tuong metadata cung
sap: them `Metadata-Flavor: Google` vao request la doc duoc ca cay `v1/` (da kiem chung;
ben trong chi la metadata GCP chuan, khong co co -> dung la infra dung chung).

## H14 - "iframe file:// co render text khong?"

`<iframe src="file:///etc/passwd">` -> PDF 2537 byte nhung **0 text operator** (chi co
vector ops). Qt fetch duoc file (vi `file:///ctf/flag.txt` tra `ContentNotFoundError`,
chung to no that su doc) nhung khong ve text/plain trong subframe.

`<meta refresh -> file://>` va `location='file://'` -> `render failed: ... unknown error`.

result: DEAD cho huong render, nhung **con song cho huong doc bang script**.

## H15 - "script chay duoc, va /Title la kenh plaintext"

`<script>document.title="JSWORKS123"</script>` -> PDF `/Title` UTF-16BE = `JSWORKS123`.
**JavaScript chay.** `/Title` la plaintext, khong can giai font.

Sau do: XHR **dong bo** toi `file://` **thanh cong** (`document.title="OK:"+responseText`
tra ve dung `d89c16037bd5` = noi dung `/etc/hostname`), trong khi XHR toi `http://` bi
`NETWORK_ERR` -> dung y nghia default-allow local file access cua wkhtmltopdf 0.12.5.

result: **CONFIRMED** - day la duong doc file cuoi cung.

## H16 - loi harness thu hai (dang le da tiet kiem 5 phut)

5 case JS dau tien deu tra `/Title` mac dinh, khien toi tuong script khong chay voi
`try/catch`. Nguyen nhan: body la **form-urlencoded**, nen moi dau `+` trong
`"OK:"+x.responseText` bi decode thanh **space** -> JS sai cu phap, khong chay. Sua bang
`quote(content, safe="")` thi ca 5 case sang ro.

result: bai hoc cu lap lai: truoc khi ket luan "nan nhan khong lam gi", kiem tra encoding
 cua chinh tool.

## Duong co that

`/proc/self/cwd` -> `ContentOperationNotPermittedError`; `/ctf/flag.txt`, `/flag`,
`/app/flag.txt`, `/opt/flag.txt` -> `ContentNotFoundError`; **`/flag.txt` -> ra co**.

```
sun{s1x_m0r3_w33ks_0f_g0ph3r_ssrf}
```

`s1x_m0r3_w33ks_0f_g0ph3r_ssrf` = "six more weeks of gopher ssrf" - chinh chuoi co xac
nhan gopher la loi giai tac gia dinh.

## Thu ty khai thac

1. Doc `<!-- ops: ... feed=<url> -->` -> SSRF.
2. Doc `<p class="fault">` -> biet client la libcurl -> thu `gopher://`.
3. Gopher -> POST `/report` -> biet wkhtmltopdf that va render chay.
4. `/Title` qua `document.title` -> biet JS bat.
5. XHR dong bo `file://` -> doc `/flag.txt`.

