#!/usr/bin/env python
"""CookieCorp (SunshineCTF 2026) - test auth flow and dashboard access."""
import http.cookiejar
import json
import urllib.request
import urllib.error
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HOST = "tomorrow.web.2026.sunshinectf.games"
SITE = f"https://{HOST}"


def get_cookiejar():
    return http.cookiejar.CookieJar()


def post_with_cookies(cj, path, data):
    req = urllib.request.Request(
        SITE + path,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
    )
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    try:
        r = opener.open(req, timeout=30)
        return r.status, r.read(), cj
    except urllib.error.HTTPError as e:
        return e.code, e.read(), cj


def get_with_cookies(cj, path):
    req = urllib.request.Request(SITE + path)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    try:
        r = opener.open(req, timeout=30)
        return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


if __name__ == "__main__":
    cj = get_cookiejar()

    # Step 1: Register
    status, body, cj = post_with_cookies(cj, "/register", {"username": "auth_test", "password": "testpass123"})
    print(f"[1] POST /register: {status} {body[:100]}")
    print(f"    Cookies: {[(c.name, c.value) for c in cj]}")

    # Step 2: Login
    status, body, cj = post_with_cookies(cj, "/login", {"username": "auth_test", "password": "testpass123"})
    print(f"\n[2] POST /login: {status} {body[:100]}")
    print(f"    Cookies: {[(c.name, c.value) for c in cj]}")

    # Step 3: Try dashboard
    status, body = get_with_cookies(cj, "/dashboard")
    print(f"\n[3] GET /dashboard (with cookies): {status}")
    print(f"    Body: {body[:500]}")

    # Step 4: Submit tests with cookies
    print("\n[4] Batch endpoints with cookies:")
    candidates = ["/submit", "/api/submit"]
    for p in candidates:
        status, _, cj = post_with_cookies(cj, p, {"batch_id": "x", "ingredients": []})
        print(f"    {p}: {status}")