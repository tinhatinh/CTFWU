"""Client nho cho Echo Chamber (FastAPI/uvicorn), gi cookie trong 1 phien."""
import json
import ssl
import sys
import urllib.error
import urllib.request

BASE = "https://web-3285347d50d467ba.web.h7tex.com"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
COOKIE = {}


def req(method, path, body=None, raw=False):
    url = BASE + path
    data = None
    hdr = {"User-Agent": "Mozilla/5.0", "Accept": "application/json",
           "Content-Type": "application/json"}
    if body is not None:
        data = json.dumps(body).encode() if not isinstance(body, bytes) else body
    if COOKIE:
        hdr["Cookie"] = "; ".join("%s=%s" % kv for kv in COOKIE.items())
    r = urllib.request.Request(url, data=data, headers=hdr, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=90, context=CTX)
        code, payload, head = resp.status, resp.read(), resp.headers
    except urllib.error.HTTPError as e:
        code, payload, head = e.code, e.read(), e.headers
    for c in (head.get_all("set-cookie") or []):
        kv = c.split(";")[0]
        if "=" in kv:
            k, v = kv.split("=", 1)
            (COOKIE.__setitem__(k, v) if v else COOKIE.pop(k, None))
    if raw:
        return code, payload
    try:
        return code, json.loads(payload)
    except Exception:
        return code, payload.decode("utf-8", "replace")


def show(method, path, body=None):
    code, out = req(method, path, body)
    print("### %s %s -> %s" % (method, path, code))
    print(json.dumps(out, indent=1)[:6000] if not isinstance(out, str) else out[:3000])
    return code, out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    m = sys.argv[1] if len(sys.argv) > 1 else "GET"
    p = sys.argv[2] if len(sys.argv) > 2 else "/api/incidents/INC-7421"
    b = json.loads(sys.argv[3]) if len(sys.argv) > 3 else None
    show(m, p, b)
