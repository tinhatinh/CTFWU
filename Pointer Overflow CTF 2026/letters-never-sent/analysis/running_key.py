import re

CT = "PXYWN{2.612.QNTOXCK6E7DKGMKC.WK4KK6MPPPRJGOFZZI66EISSED}"
L = [c for c in CT if c.isalpha()]
C = [ord(c) - 65 for c in L]
bf = lambda c, k: (k - c) % 26
KEY = [ord(c) - 65 for c in "ELAPSE"]

LETTER = """To Admiral Sir Francis Beaufort, K.C.B.
Hydrographer to the Navy
My dear Admiral,
I write to you in confidence, as one who has long admired
the elegance of your method - that reciprocal tableau which bears your name and which I have employed these many years in matters requiring discretion.
The matter I wish to convey is delicate. There are those
who believe the boundary between the living and the departed
is not the fixed wall we imagine, but a membrane - permeable,
responsive to the correct frequency of inquiry. I have reason
to believe they are correct.
I ask only that you examine what I have enclosed, and that
you guard it accordingly.
Your faithful correspondent,
H. Aldous Whitmore
Fellow, Liminal Society for Spectral Fellowship
November, 1887"""

run = re.sub(r"[^A-Za-z]", "", LETTER).upper()
print("running-key text letters:", len(run))
for pat in ("ELAPS", "ELAPSE", "ELE", "ELA"):
    hits = [m.start() for m in re.finditer(pat, run)]
    print(f"  '{pat}' at {hits[:10]}")

# (a) progressive shift per dot-separated segment
segs = []
i = 0
body = CT[5:-1]
print("\n(a) per-segment progressive Beaufort")
parts = body.split(".")
for shift, _ in [(0, 0)]:
    out = []
    pos = 0
    for si, seg in enumerate(parts):
        for ch in seg:
            if ch.isalpha():
                out.append(chr(bf(ord(ch) - 65, (KEY[(pos) % 6] + si)) % 26 + 65))
                pos += 1
            else:
                out.append(ch)
        out.append(".")
    print("  ", "".join(out))

# (b) running key from the letter at every offset
print("\n(b) running key = letter text, offsets where prefix decodes to POCTF")
for off in range(len(run) - len(C)):
    if all(bf(C[i], ord(run[off + i]) - 65) == [15, 14, 2, 19, 5][i] for i in range(5)):
        pt = "".join(chr(bf(C[i], ord(run[off + i]) - 65) + 65) for i in range(len(C)))
        print("   offset", off, "->", pt)

# (c) running key = letter text read backwards
rev = run[::-1]
print("\n(c) reversed running key")
for off in range(len(rev) - len(C)):
    if all(bf(C[i], ord(rev[off + i]) - 65) == [15, 14, 2, 19, 5][i] for i in range(5)):
        pt = "".join(chr(bf(C[i], ord(rev[off + i]) - 65) + 65) for i in range(len(C)))
        print("   offset", off, "->", pt)
print("   (none printed above = no match)")
