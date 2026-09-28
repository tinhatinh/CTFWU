"""Client cho Tapedeck Studio: upload clip, gọi /api/render, in raw JSON.

Dùng:
    python analysis/client.py <instance-base-url> [slug-payload ...]
Không có slug-payload thì chạy một lần với slug thường để lấy baseline.
"""
import json
import os
import sys
import wave

import requests

BASE = sys.argv[1].rstrip("/")
JAR = "analysis/cookies.json"
SLUGS = sys.argv[2:] or ["audiogram"]


def make_wav(path, seconds=2, rate=8000):
    import math
    import struct as st

    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        frames = b"".join(
            st.pack("<h", int(12000 * math.sin(2 * math.pi * 220 * t / rate)))
            for t in range(seconds * rate)
        )
        w.writeframes(frames)
    return path


def load_session():
    s = requests.Session()
    if os.path.exists(JAR):
        with open(JAR) as fh:
            s.cookies.update(json.load(fh))
    return s


def save_session(s):
    with open(JAR, "w") as fh:
        json.dump(dict(s.cookies), fh)


def main():
    s = load_session()
    r = s.get(BASE + "/studio", timeout=30)
    r.raise_for_status()
    ws = [w for w in s.cookies]
    print("[*] cookies: %s" % [(c.name, c.value[:16]) for c in ws])
    import re
    m = re.search(r"Workspace <span class=\"mono\">([0-9a-f]+)</span>", r.text)
    print("[*] workspace = %s" % (m.group(1) if m else "?"))
    save_session(s)

    wav = make_wav("analysis/clip.wav")
    with open(wav, "rb") as fh:
        up = s.post(BASE + "/studio/upload",
                    files={"clip": ("clip.wav", fh, "audio/wav")},
                    timeout=60, allow_redirects=True)
    print("[*] upload -> %d, %d bytes" % (up.status_code, len(up.content)))
    if "error" in up.text.lower() or up.status_code >= 400:
        frag = re.search(r'<div class="panel">.*?</div>', up.text, re.S)
        print("    upload page snippet:", (frag.group(0)[:400] if frag else ""))
    save_session(s)

    for slug in SLUGS:
        payload = {"slug": slug, "theme": "midnight"}
        rr = s.post(BASE + "/api/render", json=payload, timeout=90)
        print("\n===== slug=%r -> HTTP %d =====" % (slug, rr.status_code))
        print("content-type: %s" % rr.headers.get("content-type"))
        body = rr.text
        try:
            print(json.dumps(rr.json(), indent=2)[:6000])
        except Exception:
            print(body[:4000])
        save_session(s)


if __name__ == "__main__":
    main()
