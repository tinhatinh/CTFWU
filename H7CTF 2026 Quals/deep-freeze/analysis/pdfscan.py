import re
import sys

path = sys.argv[1]
d = open(path, "rb").read()
print(f"region size: {len(d)}")

hits = [m.start() for m in re.finditer(rb"%PDF-", d)]
print("'%PDF-' at:", [f"+0x{x:x}" for x in hits] or "none")

for m in re.finditer(rb"Recovery token", d):
    ctx = re.sub(rb"[^\x20-\x7e]", b".", d[m.start(): m.start() + 90]).decode()
    print(f"  token at +0x{m.start():x}: {ctx}")

for k in (b"AES", b"MODE_", b"Cipher", b"sha256", b"key", b"Fernet", b"ChaCha", b"iv", b"nonce"):
    n = d.count(k)
    if n:
        print(f"  hint {k!r}: {n}")

if hits:
    i = hits[0]
    j = d.find(b"%%EOF", i)
    end = j + 5 if j > 0 else len(d)
    out = path.rsplit("/", 1)[-1].replace(".bin", "") + ".pdf"
    open(out, "wb").write(d[i:end])
    print(f"[+] wrote {out} ({end - i} bytes)")
else:
    print("[*] no PDF header in this region; show printable runs instead:")
    for s in re.findall(rb"[\x20-\x7e]{12,}", d)[:40]:
        print("   ", s.decode()[:150])
