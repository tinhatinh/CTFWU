"""Breadth-crawl cùng origin, chỉ theo link/asset xuất hiện trong HTML đã tải.

Không đoán path, không brute-force: mỗi URL phải được tham chiếu bởi một trang
đã lấy từ hàng đợi (bắt đầu từ seed).
"""
import os
import re
import sys
import time
import urllib.parse

import requests

BASE = sys.argv[1].rstrip("/")
OUT = sys.argv[2] if len(sys.argv) > 2 else "analysis/site"
SEEDS = sys.argv[3:] or ["/"]

ALLOW_EXT = (".html", ".js", ".css", ".json", "", ".txt", ".svg", ".wav", ".png", ".jpg")
LINK_RE = re.compile(r"""(?:href|src)\s*=\s*["']([^"']+)["']""", re.I)
PATH_RE = re.compile(r"""["'](/(?:api|studio|public|render|export|download|uploads?|files?|assets)[^"'()\s]*)["']""", re.I)

os.makedirs(OUT, exist_ok=True)
host = urllib.parse.urlparse(BASE).netloc
seen, queue = set(), list(SEEDS)
fetched = []

while queue:
    path = queue.pop(0)
    if path in seen:
        continue
    seen.add(path)
    if len(seen) > 60:
        break
    url = BASE + path
    try:
        r = requests.get(url, timeout=20, allow_redirects=True)
    except Exception as e:
        print("ERR %s -> %r" % (path, e))
        continue
    ctype = r.headers.get("content-type", "")
    ext = os.path.splitext(urllib.parse.urlparse(path).path)[1].lower()
    if not r.ok or (ext not in ALLOW_EXT and "html" not in ctype and "javascript" not in ctype
                    and "css" not in ctype and "json" not in ctype and "text" not in ctype):
        print("skip %d %s (%s)" % (r.status_code, path, ctype))
        continue
    name = re.sub(r"[^a-zA-Z0-9._-]", "_", path.strip("/") or "index")[:120] or "index"
    fn = os.path.join(OUT, ("%s.%s" % (name, ext.lstrip(".") or "html")))
    with open(fn, "wb") as fh:
        fh.write(r.content)
    fetched.append((path, r.status_code, len(r.content), fn))
    print("%3d %8d  %s  -> %s" % (r.status_code, len(r.content), path, fn))
    if "text/html" in ctype or path.endswith((".js", ".css", ".json")):
        text = r.text
        for m in LINK_RE.findall(text) + PATH_RE.findall(text):
            if m.startswith("http") and urllib.parse.urlparse(m).netloc != host:
                continue
            p = m if m.startswith("/") else "/" + urllib.parse.urlparse(m).path
            p = p.split("#")[0]
            if p and p not in seen and urllib.parse.urlparse(p).path.endswith(ALLOW_EXT):
                queue.append(p)
    time.sleep(0.2)

print("\n%d files saved to %s" % (len(fetched), OUT))
