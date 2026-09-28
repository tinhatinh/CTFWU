#!/usr/bin/env python
"""Systematic ingredient testing for CookieCorp."""
import http.cookiejar
import json
import time
import urllib.request
import urllib.error

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import sys

HOST = "tomorrow.web.2026.sunshinectf.games"
SITE = f"https://{HOST}"

def login(username, password):
    cj = http.cookiejar.CookieJar()
    req = urllib.request.Request(SITE + "/login", data=json.dumps({"username": username, "password": password}).encode(), headers={"Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    try:
        with opener.open(req, timeout=30) as r:
            return cj
    except urllib.error.HTTPError as e:
        print(f"Login failed: {e.code}")
        return None


def submit_test(ing_name, ing_value, cj):
    """Submit a single ingredient and check response."""
    recipe_data = {"title": f"Test {ing_name}", "ingredients": [{"name": ing_name, "value": ing_value}]}
    req = urllib.request.Request(SITE + "/api/recipe", data=json.dumps(recipe_data).encode(), headers={"Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    try:
        with opener.open(req, timeout=30) as r:
            resp = json.loads(r.read())
            rid = resp.get("id")
            
            # Submit immediately
            req2 = urllib.request.Request(SITE + f"/api/recipe/{rid}/submit", method="POST")
            opener2 = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
            with opener2.open(req2, timeout=30) as r2:
                sub_resp = r2.read().decode()
                return ing_name, sub_resp
    except urllib.error.HTTPError as e:
        return ing_name, str(e.code) + " " + e.read().decode()[:100]


if __name__ == "__main__":
    cj = login("newbaker", "testpass123")
    if not cj:
        sys.exit(1)
    
    # Test suspicious ingredients
    suspects = [
        "flag", "golden_seal", "golden", "chief", "secret_flag", "solar_flavor",
        "magic_ingredient", "prime_element", "quantum_cookie", "atomic_sprinkles",
        "moon_sugar", "star_dust", "nebula_powder", "comet_tail", "black_hole",
    ]
    
    for ing in suspects:
        name, response = submit_test(ing, "use", cj)
        print(f"[{name}] {response}")
        time.sleep(2)  # Respect rate limits
