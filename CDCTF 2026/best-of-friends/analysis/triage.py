r"""Triage cho CDCTF 2026 / Best of Friends.

    python analysis/triage.py

In ra: thong ke byte/pattern, ket qua quet Morse theo hai quy uoc, va ket qua
quet cac ham so hoc cua tung nhom (hai huong da loai).
"""
import collections
import os

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "..", "files", "bestfriends.txt"), encoding="utf-8") as fh:
    CIPHER = fh.read().strip()

groups = CIPHER.split()
stream = CIPHER.replace(" ", "")

print("[*] ciphertext (line 1, %d bytes)" % len(CIPHER))
print("    " + CIPHER)

print("\n[*] accounting")
print("    groups            : %d" % len(groups))
print("    separators        : %d" % (len(CIPHER) - len(stream)))
print("    symbols           : %d (slashes %d, backslashes %d)"
      % (len(stream), stream.count("/"), stream.count("\\")))
print("    distinct patterns : %d" % len(set(groups)))
print("    length histogram  : %s"
      % sorted(collections.Counter(len(g) for g in groups).items()))
print("    alphabet only   : %s (only /, backslash, space)"
      % (set(CIPHER) <= {"/", "\\", " "}))

print("\n[*] distinct patterns, ordered by length")
for pat in sorted(set(groups), key=lambda p: (len(p), p)):
    print("    %-5s len=%d  /=%d  \\=%d" % (pat, len(pat), pat.count("/"), pat.count("\\")))

MORSE = {
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E", "..-.": "F",
    "--.": "G", "....": "H", "..": "I", ".---": "J", "-.-": "K", ".-..": "L",
    "--": "M", "-.": "N", "---": "O", ".--.": "P", "--.-": "Q", ".-.": "R",
    "...": "S", "-": "T", "..-": "U", "...-": "V", ".--": "W", "-..-": "X",
    "-.--": "Y", "--..": "Z",
}

print("\n[*] morse scan (each group = one letter)")
for name, slash_is_dit in (("/ = dit, \\ = dah", True), ("\\ = dit, / = dah", False)):
    letters, bad = [], []
    for g in groups:
        code = "".join(("." if (c == "/") == slash_is_dit else "-") for c in g)
        letters.append(MORSE.get(code, "?"))
        if code not in MORSE:
            bad.append((g, code))
    ok = 100 * (len(groups) - len(bad)) // len(groups)
    print("    %s" % name)
    print("      letters    : %s" % "".join(letters))
    print("      unresolved : %s  (%d%% groups valid)" % (bad, ok))

print("\n[*] numeric reads of each group")
lens = [len(g) for g in groups]
ns = [g.count("/") for g in groups]
nb = [g.count("\\") for g in groups]
binv = [int(g.replace("/", "0").replace("\\", "1"), 2) for g in groups]


def a1z(xs):
    return "".join(chr(96 + x) for x in xs if 1 <= x <= 26)


print("    lengths      : %s" % lens)
print("      a1z26      : %s" % a1z(lens))
print("    count('/')   : %s" % ns)
print("      a1z26      : %s" % a1z(ns))
print("    count('\\')   : %s" % nb)
print("      a1z26      : %s" % a1z(nb))
print("    binary (/=0) : %s -> range %d..%d" % (binv, min(binv), max(binv)))
print("    (/,\\) tuples : %s" % list(zip(ns, nb)))
print("    stream bits  : %d -> %d bytes + %d bits leftover"
      % (len(stream), len(stream) // 8, len(stream) % 8))

print("\n[*] group lengths as run-lengths of an alternating bit stream")
for start in (0, 1):
    bits = "".join(str(start if i % 2 == 0 else 1 - start) * len(t)
                   for i, t in enumerate(groups))
    vals = [int(bits[i:i + 8], 2) for i in range(0, len(bits) - 7, 8)]
    printable = sum(1 for v in vals if 32 <= v < 127)
    print("    first bit %d: %s -> %d/%d bytes printable"
          % (start, " ".join("%02x" % v for v in vals), printable, len(vals)))

