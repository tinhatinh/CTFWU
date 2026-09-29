import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PT = {n: open("analysis/%s.pt" % n, "rb").read() for n in
      ("sample1", "sample2", "sample3", "team")}


def txt(b):
    return "".join(chr(c) if 32 <= c < 127 else ("@" if c == 0 else ("<%02x>" % c))
                   for c in b)


print("== byte histogram of control/high bytes per file")
for n, p in PT.items():
    ctl = {}
    for i, c in enumerate(p):
        if c < 0x20 or c >= 0x7f:
            ctl.setdefault(c, []).append(i)
    print(n, " ".join("%02x:%d" % (c, len(v)) for c, v in sorted(ctl.items())))

print()
print("== team contexts for every control/high byte occurrence")
p = PT["team"]
for i, c in enumerate(p):
    if c < 0x20 or c >= 0x7f:
        print(" %04x %02x  %s" % (i, c, txt(p[max(0, i - 10):i] + b"#" + p[i + 1:i + 11])))
