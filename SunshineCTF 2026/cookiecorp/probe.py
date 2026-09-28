#!/usr/bin/env python
"""CookieCorp (SunshineCTF 2026, web 479đ) - initial probe.

Server: nginx + Express
Endpoints confirmed:
- GET / -> home page with login/register forms
- POST /register -> creates user, returns {"ok":true,"user":"...","role":"baker"}
- POST /login -> authenticates
- All other routes return 404 HTML errors

Next steps: explore cookie batch submission flow, Quality Inspector logic, Golden Seal mechanism.
"""
import json
import sys
import urllib.error
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HOST = "tomorrow.web.2026.sunshinectf.games"
SITE = f"https://{HOST}"


def post(path, data):
    """Send JSON POST request."""
    req = urllib.request.Request(
        SITE + path,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def get(path):
    """Send GET request."""
    try:
        with urllib.request.urlopen(SITE + path, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


if __name__ == "__main__":
    # Basic registration/login test
    status, body = post("/register", {"username": "probe_baker", "password": "x"})
    print(f"[1] POST /register: {status} {body[:150]}")

    status, body = post("/login", {"username": "probe_baker", "password": "x"})
    print(f"[2] POST /login: {status} {body[:150]}")

    # Check for alternative submission endpoints
    for path in ["/api/submit", "/api/cookie", "/inspect", "/quality", "/review"]:
        status, _ = post(path, {})
        print(f"[{path}] POST /{path}: {status}")
