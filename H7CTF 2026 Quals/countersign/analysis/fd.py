"""In ra tu disassembly theo vma: python fd.py <start> <end>"""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
lo = int(sys.argv[1], 16)
hi = int(sys.argv[2], 16) if len(sys.argv) > 2 else 1 << 40
pat = re.compile(r"^\s+([0-9a-f]+):\t(.*)$")
for line in open("cs.asm", encoding="utf-8", errors="replace"):
    m = pat.match(line)
    if not m:
        continue
    a = int(m.group(1), 16)
    if lo <= a <= hi:
        print("%05x\t%s" % (a, m.group(2).replace("\t", " ").strip()))
    if a > hi:
        break
