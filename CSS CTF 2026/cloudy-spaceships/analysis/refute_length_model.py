"""Do nhanh loi 500: loopback co that bi chan, hay chi la fetch that bai?

ba port duoi day khong co HTTP server nao nghe; neu 500 sinh ra tu mot bộ lọc
URL thi ba port cho ba ket qua khac nhau theo chuoi, con neu la nhanh "fetch
loi" thi chung cho cung mot trang.

Chay: python analysis/refute_length_model.py
"""

import base64
import json
import urllib.error
import urllib.request

BASE = "http://34.116.80.78:9143"


def temp(resolver, ship="Cassini"):
    hdr = "X" + base64.b64encode(json.dumps({"resolver": resolver}).encode()).decode()
    req = urllib.request.Request(f"{BASE}/api/v1/ship/{ship}/temperature", headers={"X-Resolver": hdr})
    try:
        with urllib.request.urlopen(req, timeout=50) as r:
            return f"HTTP{r.status} body={r.read().decode().strip()!r}"
    except urllib.error.HTTPError as e:
        return f"HTTP{e.code}"
    except Exception as e:
        return f"err {type(e).__name__}"


print("refute: so = len(body)/10 ?")
for port in (1, 9, 65500):
    u = f"http://127.0.0.1:{port}/"
    print(f"  {u:26}: {temp(u)}   (no HTTP server on this port)")
print("  => 500 o day la nhanh 'fetch that bai', cung trang voi file:// va [::1]")
print("  => nen cac con so metadata_probe.py la do body that, khong phai loi bi chan")
