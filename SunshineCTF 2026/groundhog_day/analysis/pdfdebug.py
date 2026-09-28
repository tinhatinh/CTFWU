#!/usr/bin/env python3
"""Debug the PDF text extractor against a string whose answer is known.

Renders <h1>HELLOFLAGTEST</h1>, so any correct extractor must give back HELLOFLAGTEST.
Prints the raw text operators and the whole ToUnicode CMap so the glyph-id mapping can
be fixed rather than guessed.
"""
import base64
import re
import sys

import pdfdump


def w(s):
    sys.stdout.buffer.write((str(s) + "\n").encode("utf-8", "replace"))
    sys.stdout.flush()


obj = pdfdump.report("<h1>HELLOFLAGTEST</h1>")
pdf = base64.b64decode(obj["data"])
open("../files/sanity.pdf", "wb").write(pdf)
w("pdf=%d" % len(pdf))
for i, s in enumerate(pdfdump.streams(pdf)):
    w("--- stream %d (%d bytes) ---" % (i, len(s)))
    if b"Tj" in s or b"TJ" in s or b"beginbfchar" in s or b"beginbfrange" in s:
        w(repr(s[:900]))
    else:
        w(repr(s[:160]))
w("=== objects with /ToUnicode ===")
for m in re.finditer(rb"<<[^<]{0,400}?/ToUnicode[^>]{0,120}>>", pdf, re.S):
    w(repr(m.group(0)[:200]))
