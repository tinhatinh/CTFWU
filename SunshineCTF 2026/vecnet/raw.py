#!/usr/bin/env python
"""Raw HTTP on :8000 so headers are visible per-route."""
import base64, re, socket, ssl, sys
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HOST = "vec.web.2026.sunshinectf.games"
CFG = open("files/repo-history/c2/config.php", encoding="utf-8").read()
KEY = re.search(r"INTERNAL_API_KEY',\s*'([^']+)'", CFG).group(1)
USER = re.search(r"MAIL_ADMIN_USER',\s*'([^']+)'", CFG).group(1)
PW = re.search(r"MAIL_ADMIN_PASS',\s*'([^']+)'", CFG).group(1)
BASIC = base64.b64encode(("%s:%s" % (USER, PW)).encode()).decode()

def req(path, host, port, hdrs=(), tls=False, method="GET", body=None):
    s = socket.create_connection((HOST, port), timeout=20)
    if tls:
        s = ssl.wrap_socket(s, server_hostname=HOST)
    h = ["%s %s HTTP/1.1" % (method, path), "Host: %s:%d" % (host, port), "Connection: close",
         "Accept: */*", "User-Agent: curl/8"]
    h += list(hdrs)
    if body is not None:
        h.append("Content-Type: application/json")
        h.append("Content-Length: %d" % len(body))
    s.sendall(("\r\n".join(h) + "\r\n\r\n" + (body or "")).encode())
    d = b""
    while True:
        try:
            c = s.recv(65536)
        except Exception:
            break
        if not c: break
        d += c
        if len(d) > 200000: break
    s.close()
    return d

for path in ["/api/v2/heartbeat", "/api/v2/collections", "/api/v2/version"]:
    d = req(path, HOST, 8000, [("Authorization: Basic " + BASIC), ("X-API-Key: " + KEY)])
    print("### %-24s" % path)
    print(d.decode("utf-8", "replace")[:700])
    print()
