#!/usr/bin/env python
"""CookieCorp (SunshineCTF 2026, web 479đ) - full initial enumeration.

Target: tomorrow.web.2026.sunshinectf.games
Server: nginx + Express
Known endpoints: GET /, POST /register, POST /login
Goal: find batch submission endpoint for Quality Inspector flow.
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
    # Test registration and login
    print("[1] Registration tests:")
    for user, pw in [("d", "a"), ("demo_baker", "test123"), ("valid_user", "longpassword")]:
        status, body = post("/register", {"username": user, "password": pw})
        print(f"    {user}/{pw}: {status} {body[:80]}")

    # Query parameter testing
    print("\n[2] Query param injection on /:")
    params = ["?submit", "?batch", "?bake", "?ingredient", "?cookie", "?json", "?data"]
    for p in params:
        status, _ = get(p)
        print(f"    /{p.strip()}: {status}")

    # Route enumeration
    print("\n[3] Batch/submit route probes:")
    candidates = [
        "/api/submit", "/api/batch", "/api/bake", "/batch", "/batch/submit", "/batch/create",
        "/cookie/submit", "/cookie/batch", "/bake/submit", "/fabricate", "/inspect/cookie",
        "/quality/inspect", "/review/batch", "/check/batch", "/validate/batch",
    ]
    for path in candidates:
        status, _ = post(path, {"batch_id": "x", "ingredients": []})
        if status != 404:
            print(f"    {path}: {status} (non-404!)")

    # HTTP methods
    print("\n[4] Alternative HTTP methods on /submit:")
    for verb in ["GET", "PUT", "PATCH", "DELETE"]:
        req = urllib.request.Request(SITE + "/submit", method=verb)
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                print(f"    {verb} /submit: {r.status}")
        except urllib.error.HTTPError as e:
            print(f"    {verb} /submit: {e.code}")