"""Do bo loc scheme/loopback cua resolver va cach no phan ung voi input lac loi.

Chay: python analysis/resolver_probe.py [base_url]
"""

import base64
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://34.116.80.78:9143"
SHIP = "Cassini"


def build(resolver) -> str:
    """str -> header hop le; ('raw', s) -> gui thang s de do nhanh loi parse."""
    if isinstance(resolver, tuple):
        return resolver[1]
    return "X" + base64.b64encode(json.dumps({"resolver": resolver}).encode()).decode()


def call(header):
    url = f"{BASE}/api/v1/ship/{urllib.parse.quote(SHIP)}/temperature"
    req = urllib.request.Request(url)
    if header is not None:
        req.add_header("X-Resolver", header)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return f"HTTP {r.status} body={r.read().decode().strip()}"
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code} body={e.read().decode().strip()[:40]}"
    except Exception as e:
        return f"err {type(e).__name__}"


CASES = [
    ("thieu header", None),
    ("khong phai base64", ("raw", "notbase64")),
    ("base64 thieu key resolver", ("raw", base64.b64encode(b"{}").decode())),
    ("wikipedia Space_weather", "https://en.wikipedia.org/wiki/Space_weather"),
    ("example.com https", "https://example.com/"),
    ("example.com http", "http://example.com/"),
    ("1.1.1.1 http", "http://1.1.1.1/"),
    ("1.1.1.1 https", "https://1.1.1.1/"),
    ("8.8.8.8 (khong co HTTP)", "http://8.8.8.8/"),
    ("127.0.0.1", "http://127.0.0.1/"),
    ("localhost", "http://localhost/"),
    ("file:///etc/passwd", "file:///etc/passwd"),
]

for label, resolver in CASES:
    print(f"{label:32}: {call(build(resolver) if resolver is not None else None)}")
