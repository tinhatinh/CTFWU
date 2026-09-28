"""Open Sesame — OOK/Manchester 48 bit: suy ra quy luật rolling code rồi POST /unlock.

Chuỗi:
  capture.cf32 (I/Q float32 LE, fs=1 MHz)
    -> envelope, ngưỡng OOK, tách 8 press theo khoảng lặng
    -> mỗi press 48 bit, symbol = H1L2 (bit 0) / H2L1 (bit 1), T ~ 303 us
  48 bit = 32 bit cố định + 12 bit counter (+0x30 mỗi lần bấm) + 4 bit checksum
  checksum = (tổng 11 nibble đầu) mod 16

Dùng: python solve.py <base-url> [capture.cf32] [--submit]
"""
import json
import re
import sys
import urllib.request

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
FS = 1_000_000


def bits_from_iq(path):
    raw = np.fromfile(path, dtype="<f4").reshape(-1, 2)
    w = FS // 50_000
    sm = np.convolve(raw[:, 0] ** 2 + raw[:, 1] ** 2, np.ones(w) / w, mode="same")
    lo, hi = np.percentile(sm, 1), sm.max()
    on = sm > lo + 0.35 * (hi - lo)

    idx = np.flatnonzero(np.diff(on.astype(np.int8)))
    if on[0]:
        idx = np.r_[0, idx]
    if on[-1]:
        idx = np.r_[idx, len(on)]
    segs = [(idx[i], idx[i + 1]) for i in range(0, len(idx) - 1, 2)]

    presses, cur = [], [segs[0]]
    for i in range(len(segs) - 1):
        if segs[i + 1][0] - segs[i][1] > FS * 0.0015:      # > 1.5 ms im lặng
            presses.append(cur)
            cur = []
        cur.append(segs[i + 1])
    presses.append(cur)

    codes = []
    for p in presses:
        base = p[0][0]
        tl = np.zeros(p[-1][1] - base, dtype=np.int8)
        for a, b in p:
            tl[a - base:b - base] = 1
        runs, state, pos = [], 0, 0
        for i, v in enumerate(tl):
            if v != state:
                runs.append((state, i - pos))
                pos, state = i, v
        runs.append((state, len(tl) - pos))
        runs = [r for r in runs if r[1] > 30]
        T = min(r[1] for r in runs)

        bits, i = "", 0
        while i + 1 < len(runs):
            (s1, l1), (s2, l2) = runs[i], runs[i + 1]
            if s1 == 1 and s2 == 0:
                bits += "1" if (l1 - l2) > 0 else "0"
                i += 2
            else:
                i += 1
        codes.append(bits[:48])
    return codes


def checksum(frame_hex):
    return sum(int(c, 16) for c in frame_hex[:11]) % 16


def main():
    base = sys.argv[1].rstrip("/")
    cap = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "analysis/capture.cf32"

    codes = bits_from_iq(cap)
    frames = [hex(int(c, 2))[2:].rjust(12, "0") for c in codes if len(c) == 48]
    print("[*] %d press giải mã được:" % len(frames))
    for f in frames:
        nib = [int(x, 16) for x in f]
        print("    %s   counter=0x%s  crc=%x  (kiểm tra crc=%x)"
              % (f, f[8:11], nib[11], sum(nib[:11]) % 16))

    fixed = frames[0][:8]
    assert all(f[:8] == fixed for f in frames), "32 bit đầu không cố định"
    ctr = [int(f[8:11], 16) for f in frames]
    steps = {b - a for a, b in zip(ctr, ctr[1:])}
    print("\n[*] 32 bit cố định = %s | counter %s, bước %s" % (fixed, hex(ctr[0]), steps))
    assert steps == {0x30}, "counter không tăng đều 0x30: %s" % steps
    for f in frames:
        assert checksum(f) == int(f[11], 16), "mô hình crc sai ở %s" % f
    print("[*] mô hình khớp: crc = (tổng 11 nibble đầu) mod 16")

    nxt = (ctr[-1] + 0x30) & 0xFFF
    body = fixed + "%03x" % nxt
    body += "%x" % checksum(body)
    print("[+] code dự đoán cho lần bấm tiếp theo: %s" % body)

    if "--submit" not in sys.argv:
        print("[*] thêm --submit để POST /unlock")
        return 0
    req = urllib.request.Request(base + "/unlock",
                                 data=json.dumps({"code": body}).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        txt = r.read().decode(errors="replace")
    print("[*] /unlock -> %d\n%s" % (r.status, txt))
    m = re.search(r"H7CTF\{[^}\s\"']*\}", txt)
    if m:
        open("flag.txt", "w", encoding="utf-8").write(m.group(0) + "\n")
        print("[+] FLAG: %s" % m.group(0))
        return 0
    print("[-] không thấy flag trong phản hồi")
    return 1


if __name__ == "__main__":
    sys.exit(main())
