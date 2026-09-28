"""Gọi /api/render với slug/theme tuỳ ý, in tóm tắt raw JSON.

Dùng: python analysis/probe2.py <base>            -> chạy danh sách mặc định
      python analysis/probe2.py <base> --json f.json   -> đọc payload từ file
"""
import json
import os
import re
import sys

import requests

BASE = sys.argv[1].rstrip("/")
JAR = "analysis/cookies.json"


def load():
    s = requests.Session()
    if os.path.exists(JAR):
        s.cookies.update(json.load(open(JAR)))
    r = s.get(BASE + "/studio", timeout=30)
    m = re.search(r'Workspace <span class="mono">([0-9a-f]+)</span>', r.text)
    return s, (m.group(1) if m else None)


def upload(s):
    import wave, struct, math
    path = "analysis/clip.wav"
    if not os.path.exists(path):
        with wave.open(path, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000)
            w.writeframes(b"".join(struct.pack("<h", int(12000*math.sin(2*math.pi*220*t/8000)))
                                   for t in range(2*8000)))
    with open(path, "rb") as fh:
        return s.post(BASE + "/studio/upload", files={"clip": ("clip.wav", fh, "audio/wav")},
                      timeout=60).status_code


def render(s, slug="audiogram", theme="midnight"):
    r = s.post(BASE + "/api/render", json={"slug": slug, "theme": theme}, timeout=120)
    try:
        d = r.json()
    except Exception:
        return {"_http": r.status_code, "_raw": r.text[:2000]}
    err = d.get("errors")
    if err and len(err) > 1200:
        head = err.split("\n")[0]
        tail = err[-900:]
        d["errors"] = head + "\n   ...[lược]...\n" + tail
    return d


def brief(tag, d):
    print("\n===== %s =====" % tag)
    print(json.dumps(d, indent=2)[:2500])


CASES = [
    ("quote-open", {"slug": "x'"}),
    ("quote-break-id", {"slug": "x' && id && 'y"}),
    ("newline-id", {"slug": "x\nid\n"}),
    ("space-option", {"slug": "x -h"}),
    ("double-quote-break", {'slug': 'x" && id && "y'}),
    ("theme-color-inject", {"slug": "t1", "theme": "0x00ff00:s=200x200"}),
    ("theme-filter-inject", {"slug": "t2", "theme": "midnight,drawtext=text=HELLO:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"}),
    ("theme-array", {"slug": "t3", "theme": "nope"}),
]

if __name__ == "__main__":
    s, ws = load()
    print("[*] workspace=%s upload=%d" % (ws, upload(s)))
    if "--json" in sys.argv:
        cases = json.load(open(sys.argv[sys.argv.index("--json") + 1]))
    else:
        cases = CASES
    for tag, p in cases:
        p.setdefault("slug", "audiogram")
        p.setdefault("theme", "midnight")
        try:
            brief(tag, render(s, p["slug"], p["theme"]))
        except Exception as e:
            print("[%s] EXC %r" % (tag, e))
        json.dump(dict(s.cookies), open(JAR, "w"))
