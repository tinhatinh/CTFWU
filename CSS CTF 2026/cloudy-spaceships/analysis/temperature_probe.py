"""Do hai thu: con so co phan biet ten tau khong, va no quan he voi body ra sao.

Chay: python analysis/temperature_probe.py
"""

import base64
import json
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://34.116.80.78:9143"


def temp(resolver, ship="Cassini"):
    hdr = "X" + base64.b64encode(json.dumps({"resolver": resolver}).encode()).decode()
    url = f"{BASE}/api/v1/ship/{urllib.parse.quote(ship)}/temperature"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"X-Resolver": hdr}), timeout=45) as r:
            return r.read().decode().strip()
    except urllib.error.HTTPError as e:
        return f"HTTP{e.code}"


def local_len(url):
    req = urllib.request.Request(url, headers={"user-agent": "node-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        data = r.read()
    return len(data)


RESOLVER = "https://example.com/"
print("cung resolver, 5 ten tau cua board:")
for ship in ["Voyager 1", "Cassini", "New Horizons", "Juno", "Galileo"]:
    print(f"  {ship:14}: {temp(RESOLVER, ship)}")
print("ten tau khong co tren board:", temp(RESOLVER, "Zhiping"))
print("ten tau try path traversal :", temp(RESOLVER, "../../../etc/passwd"))

print("\nso sanh kich thuoc body tai local voi con so tra ve:")
for url in ["https://example.com/", "http://1.1.1.1/", "https://en.wikipedia.org/wiki/Space_weather"]:
    n = local_len(url)
    print(f"  {url:46} local={n:>7} B  server={temp(url):>8}  len/10 = {n / 10}")
