import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PATH = sys.argv[1] if len(sys.argv) > 1 else "files/team.sav"
KEY = bytes.fromhex(sys.argv[2]) if len(sys.argv) > 2 else bytes.fromhex("1337df4e77c16cc7")
STEP = int(sys.argv[3]) if len(sys.argv) > 3 else 32

body = open(PATH, "rb").read()[12:]
off = int(sys.argv[4]) if len(sys.argv) > 4 else 0
plain = bytes(x ^ KEY[(i + off) % len(KEY)] for i, x in enumerate(body))


def render(c):
    if 32 <= c < 127:
        return chr(c)
    if c == 0:
        return "|"
    if c < 32:
        return "."
    return "<%02x>" % c


for i in range(0, len(plain), STEP):
    chunk = plain[i:i + STEP]
    print("%04x  %s" % (i + 12, chunk.hex(" ")))
    print("      |%s|" % "".join(render(c) for c in chunk))
