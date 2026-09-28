#!/usr/bin/env python3
"""Enumerate the router with POST, which the previous run may not have done per-route.

Unmatched paths answer Express's `Cannot POST /x` (~149 bytes). Anything that answers
403 (a handler that ran and refused), 400/401 (a handler that parsed a body), 405 or a
different length is a *real* route. Probing with POST matters because the only route we
care about, /api/seal, is POST-only: a GET sweep cannot tell "404" from "POST-only".
"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from cc import Client, new_baker, BASE, UA

CANDIDATES = [
    "/api/seal", "/api/seal/chief", "/api/seal/golden", "/api/seal/gold",
    "/api/chief/seal", "/api/chief", "/api/golden", "/api/gold",
    "/api/inspect", "/api/inspection", "/api/inspection/seal", "/api/review",
    "/api/seal/chief", "/api/staff/seal", "/api/admin/seal", "/api/seal/level",
    "/internal/seal", "/internal/api/seal", "/api/internal/seal", "/chief/seal",
    "/seal", "/api/seals", "/api/recipe/seal", "/api/recipe/batch/seal",
    "/api/recipe/:id/seal", "/api/worker/seal", "/api/bot/seal",
    "/api/recipe/%ID%/seal", "/api/recipe/%ID%/review", "/api/recipe/%ID%/approve",
    "/api/recipe/%ID%/escalate", "/api/recipe/%ID%/chief", "/api/recipe/%ID%/recheck",
    "/api/recipe/%ID%/rescore", "/api/recipe/%ID%/resubmit", "/api/recipe/%ID%/requeue",
    "/api/recipe/%ID%/unseal", "/api/recipe/%ID%/status",
    "/api/seal/%ID%", "/api/queue", "/api/queue/claim", "/api/jobs", "/api/jobs/claim",
    "/api/mixer", "/api/fabricate", "/api/ingredients", "/api/user", "/api/users",
    "/api/profile", "/api/role", "/api/whoami", "/api/session", "/api/badge",
    "/api/login", "/api/register", "/api/admin", "/admin", "/console", "/inspect",
    "/inspector", "/review", "/queue", "/worker", "/robots.txt", "/sitemap.xml",
    "/.well-known/ai.txt", "/healthz", "/health", "/metrics", "/debug", "/api",
    "/api/version", "/api/config", "/api/status", "/favicon.ico", "/uploads",
]


def post_raw(path, body=None, cookie=None):
    data = json.dumps(body).encode() if body is not None else b"{}"
    h = {"User-Agent": UA, "Content-Type": "application/json"}
    if cookie:
        h["Cookie"] = cookie
    req = urllib.request.Request(BASE + path, data=data, headers=h, method="POST")
    try:
        r = urllib.request.urlopen(req, timeout=20)
        return r.status, len(r.headers.get("Content-Length") or "") and int(r.headers["Content-Length"]), r.read()[:90]
    except urllib.error.HTTPError as e:
        cl = e.headers.get("Content-Length")
        return e.code, (int(cl) if cl and cl.isdigit() else -1), e.read()[:90]
    except Exception as ex:
        return None, -1, repr(ex)[:60]


def get_raw(path, cookie=None):
    h = {"User-Agent": UA}
    if cookie:
        h["Cookie"] = cookie
    req = urllib.request.Request(BASE + path, headers=h)
    try:
        r = urllib.request.urlopen(req, timeout=20)
        return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as ex:
        return None, repr(ex).encode()


if __name__ == "__main__":
    u, c, r = new_baker("rt")
    ck = "; ".join("%s=%s" % kv for kv in c.jar.items())
    code, rec, _ = c.post("/api/recipe", {"title": "router probe", "ingredients": [
        {"name": "flour", "value": "1"}]})
    rid = rec["id"]
    cands = [x.replace("%ID%", rid) for x in CANDIDATES]
    print("recipe", rid, flush=True)
    print("baseline unmatched POST:", post_raw("/definitely-not-a-route-zz"), flush=True)
    for p in cands:
        st, ln, body = post_raw(p, {}, ck)
        base = b"Cannot POST " + p.encode()
        if st != 404 or not body.startswith(b"<") is False:
            pass
        if not (st == 404 and (b"Cannot POST" in body or b"Not Found" in body)):
            print("  POST %-34s -> %s len=%s %r" % (p, st, ln, body[:70]), flush=True)
        time.sleep(0.12)
    print("--- GET sweep (looking for staff pages) ---", flush=True)
    for p in ["/chief", "/inspector", "/queue", "/admin", "/console", "/internal",
              "/worker", "/staff", "/seal", "/review", "/api/seal", "/api/queue",
              "/dashboard/staff", "/recipe", "/batches", "/leaderboard", "/hall",
              "/legendary", "/golden", "/robots.txt", "/sitemap.xml", "/.git/HEAD",
              "/.env", "/package.json", "/app.js", "/index.js", "/server.js"]:
        st, body = get_raw(p, ck)
        if st != 404:
            print("  GET  %-26s -> %s len=%s %r" % (p, st, len(body), body[:60]), flush=True)
        time.sleep(0.12)
