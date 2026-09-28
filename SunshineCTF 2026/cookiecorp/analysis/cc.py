#!/usr/bin/env python3
"""CookieCorp client.

Re-built from scratch for this session because the previous workspace's tooling is not
here. Deliberately uses only stdlib and always measures response time, because the
untested class this session is the database layer: the last run proved the app is
Express + a real DB (case-insensitive username uniqueness, bcrypt on found rows only,
login not rate-limited at all) but never sent a single SQL metacharacter.

Every helper returns (status, json-or-text, elapsed) so time-based inference is
possible without a second pass.
"""
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://tomorrow.web.2026.sunshinectf.games"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


class Client:
    def __init__(self, cookies=None):
        self.jar = dict(cookies or {})

    def req(self, method, path, body=None, headers=None, timeout=40):
        data = None
        hdrs = {"User-Agent": UA, "Accept": "application/json, text/html"}
        if body is not None:
            data = json.dumps(body).encode()
            hdrs["Content-Type"] = "application/json"
        if self.jar:
            hdrs["Cookie"] = "; ".join("%s=%s" % kv for kv in self.jar.items())
        hdrs.update(headers or {})
        req = urllib.request.Request(BASE + path, data=data, headers=hdrs, method=method)
        t0 = time.time()
        try:
            r = urllib.request.urlopen(req, timeout=timeout)
            code, raw = r.status, r.read()
            setc = r.headers.get_all("Set-Cookie") or []
        except urllib.error.HTTPError as e:
            code, raw = e.code, e.read()
            setc = e.headers.get_all("Set-Cookie") or []
        except Exception as ex:
            return None, repr(ex), time.time() - t0
        dt = time.time() - t0
        for c in setc:
            name, _, val = c.split(";")[0].partition("=")
            self.jar[name.strip()] = val.strip()
        text = raw.decode("utf-8", "replace")
        try:
            return code, json.loads(text), dt
        except Exception:
            return code, text, dt

    def get(self, path, **kw):
        return self.req("GET", path, **kw)

    def post(self, path, body, **kw):
        return self.req("POST", path, body=body, **kw)


def gold(page):
    """Every rendering of a golden seal we have ever seen, plus the flag itself."""
    out = []
    if isinstance(page, str):
        out += re.findall(r"sun\{[^{}\r\n]{1,160}\}", page)
        if re.search(r"class=[\"']?flag", page):
            out.append("<div class=flag present>")
        if re.search(r"seal[- ]?gold|golden", page, re.I):
            out.append("gold-class present")
    return out


def register(user, pwd):
    c = Client()
    return c, c.post("/register", {"username": user, "password": pwd})


def new_baker(prefix="bk"):
    import random
    u = "%s%04d" % (prefix, random.randrange(1000, 9999))
    c, r = register(u, "Passw0rd!")
    if r[0] not in (200, 201):
        return u, None, r
    c.post("/login", {"username": u, "password": "Passw0rd!"})
    return u, c, r


def save(c, title, ingredients):
    return c.post("/api/recipe", {"title": title, "ingredients": ingredients})


def submit(c, rid):
    return c.post("/api/recipe/%s/submit" % rid, {})


def seal(c, rid, level="gold"):
    return c.post("/api/seal", {"id": rid, "level": level})


def page_of(c, rid, kind="review"):
    return c.get("/%s/%s" % (kind, rid))


if __name__ == "__main__":
    import sys

    def w(s):
        sys.stdout.buffer.write((str(s) + "\n").encode("utf-8", "replace"))
        sys.stdout.flush()

    u, c, r = new_baker()
    w("register %s -> %s" % (u, r[:2] if r else None))
    if not c:
        sys.exit(1)
    w("cookies: %s" % sorted(c.jar))
    code, dash, dt = c.get("/dashboard")
    w("dashboard %s %.2fs len=%s" % (code, dt, len(dash) if isinstance(dash, str) else dash))
    code, rec, dt = save(c, "test batch", [{"name": "flour", "value": "1 cup"},
                                           {"name": "sugar", "value": "2 tbsp"}])
    w("save recipe -> %s %s" % (code, str(rec)[:300]))
