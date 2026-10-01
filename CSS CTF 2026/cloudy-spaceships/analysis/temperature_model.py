"""Nhan try buoc da loai: try model con so nhiet do tu body cua trang duoc fetch.

Ket luan cua chinh no: khong model duoc, vi body ma server nhan duoc khac body ma
ta tai duoc (UA khac, Wikipedia tra compressed/gzip khac byte) va con so doi theo
noi dung chu khong phai theo ten tau. De lai file nay de lan sau khoi thu lai.

Chay: python analysis/temperature_model.py
"""

import base64
import hashlib
import json
import urllib.request

BASE = "http://34.116.80.78:9143"
OBSERVED = {
    "https://en.wikipedia.org/wiki/Space_weather": 3604.5,
    "https://example.com/": 71.3,
    "http://1.1.1.1/": 5661.4,
}


def temperature(resolver):
    hdr = "X" + base64.b64encode(json.dumps({"resolver": resolver}).encode()).decode()
    req = urllib.request.Request(f"{BASE}/api/v1/ship/Cassini/temperature")
    req.add_header("X-Resolver", hdr)
    with urllib.request.urlopen(req, timeout=40) as r:
        return float(r.read().decode())


def fetch(url):
    req = urllib.request.Request(url, headers={"user-agent": "node-fetch/1.0 "})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


for url, expected in OBSERVED.items():
    got = temperature(url)
    body = fetch(url)
    digests = {}
    for name in ("md5", "sha1", "sha256", "sha512"):
        raw = getattr(hashlib, name)(body).digest()
        ints = [raw[i : i + 4].hex() for i in range(0, len(raw) - 3)]
        digests[name] = ints
    target = round(got * 10)
    hit = [
        f"{name}:{h}"
        for name, words in digests.items()
        for h in words
        for cand in (int(h, 16) % 600000, int(h, 16) % 720)
        if cand == target or cand == round(expected * 10)
    ]
    print(
        f"{url[:44]:46} server={got:<7} local_body={len(body)}B "
        f"doi_truc_tiep={got == expected} khoi_hop_le={hit or 'khong'}"
    )

print(
    "\nKet luan: con so phu thuoc noi dung server doc duoc, ma ta khong tai duoc\n"
    "dung byte do, nen moi phep model deu vo nghia. Gia tri cua primitive nam o\n"
    "request di ra, khong phai o con so nay."
)
