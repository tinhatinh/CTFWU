CT = "PXYWN{2.612.QNTOXCK6E7DKGMKC.WK4KK6MPPPRJGOFZZI66EISSED}"
KEY = "ELAPSE"
K = [ord(c) - 65 for c in KEY]
bf = lambda c, k: (k - c) % 26

VARIANTS = {
    "letters-only": lambda ch: ch.isalpha(),
    "letters+digits": lambda ch: ch.isalnum(),
    "letters+dots": lambda ch: ch.isalpha() or ch == ".",
    "letters+digits+dots": lambda ch: ch.isalnum() or ch == ".",
    "everything-in-braces": lambda ch: True,
}

for name, advance in VARIANTS.items():
    out, ki = [], 0
    for ch in CT:
        if ch == "{" or ch == "}":
            out.append(ch)
            if name == "everything-in-braces":
                ki += 1
            continue
        if advance(ch):
            if ch.isalpha():
                out.append(chr(bf(ord(ch) - 65, K[ki % 6]) + 65))
            else:
                out.append(ch)
            ki += 1
        else:
            out.append(ch)
    print(f"{name:22s} ki_end={ki:3d}: {''.join(out)}")

# also: key index = absolute position in CT mod 6, letters decrypted, others preserved
out = []
for i, ch in enumerate(CT):
    out.append(chr(bf(ord(ch) - 65, K[i % 6]) + 65) if ch.isalpha() else ch)
print(f"{'abs-position':22s}: {''.join(out)}")

# and: skip braces/digits/dots but start key at index 5 for the body (prefix consumed 5)
body = [c for c in CT if c.isalpha()][5:]
out = list(CT)
j = 0
for i, ch in enumerate(CT):
    if ch.isalpha() and i > 4:
        out[i] = chr(bf(ord(ch) - 65, K[j % 6]) + 65)
        j += 1
print(f"{'body-key-from-0':22s}: {''.join(out)}")
