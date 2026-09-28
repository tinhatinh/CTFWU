"""Giải điều chế OOK từ capture.cf32 (I/Q float32 LE, fs=1 MHz).

In ra: số burst, histogram độ rộng xung, và chuỗi bit đã giải mã cho mỗi lần bấm.
"""
import sys

import numpy as np

FS = 1_000_000
path = sys.argv[1] if len(sys.argv) > 1 else "analysis/capture.cf32"

raw = np.fromfile(path, dtype="<f4")
iq = raw.reshape(-1, 2)
env = iq[:, 0] ** 2 + iq[:, 1] ** 2

# làm mượt theo cửa sổ ~20 us để san bằng ripple trong một chip
k = FS // 50_000
sm = np.convolve(env, np.ones(k) / k, mode="same")

lo, hi = np.percentile(sm, 1), sm.max()
thr = lo + 0.35 * (hi - lo)
on = sm > thr

# chia burst: im lặng > 5 ms
edges = np.flatnonzero(np.diff(on.astype(np.int8)))
trans = list(zip(edges[::2], edges[1::2]))          # (cạnh lên, cạnh xuống)
idx = np.flatnonzero(np.diff(on.astype(np.int8)))
if on[0]:
    idx = np.r_[0, idx]
if on[-1]:
    idx = np.r_[idx, len(on)]
# gom các segment liên tiếp, tách burst theo khoảng lặng dài
segs = [(idx[i], idx[i + 1]) for i in range(0, len(idx) - 1, 2) if idx[i + 1] > idx[i]]
gaps = [(segs[i + 1][0] - segs[i][1]) for i in range(len(segs) - 1)]
SIL = FS // 200                                     # 5 ms
presses, cur = [], [segs[0]]
for i, g in enumerate(gaps):
    if g > SIL:
        presses.append(cur)
        cur = []
    cur.append(segs[i + 1])
presses.append(cur)
presses = [p for p in presses if sum(b - a for a, b in p) > FS // 200]

print("[*] env: lo=%.3e thr=%.3e hi=%.3e | %d burst | %d press" % (lo, thr, hi, len(segs), len(presses)))

for pi, press in enumerate(presses):
    # dựng chuỗi run-length (độ rộng cao/thấp liên tiếp, tính theo sample)
    runs = []
    base = press[0][0]
    timeline = np.zeros(press[-1][1] - base, dtype=np.int8)
    for a, b in press:
        timeline[a - base:b - base] = 1
    state, pos = 0, 0
    for i, v in enumerate(timeline):
        if v != state:
            runs.append((state, i - pos))
            pos, state = i, v
    runs.append((state, len(timeline) - pos))
    lens = [r[1] for r in runs if r[1] > 20]
    if not lens:
        continue
    T = min(lens)
    hist = {}
    for L in lens:
        hist[round(L / T)] = hist.get(round(L / T), 0) + 1
    print("\n[press %d] duration=%d us  T=%d us  run-histo(xT)=%s"
          % (pi, len(timeline), T, dict(sorted(hist.items()))))
    # giải mã PWM: cặp (high, low) kế tiếp = 1 symbol
    bits = ""
    i = 0
    pairs = []
    while i + 1 < len(runs):
        (s1, l1), (s2, l2) = runs[i], runs[i + 1]
        if s1 == 1 and s2 == 0:
            pairs.append((l1, l2))
            i += 2
        else:
            i += 1
    for h, l in pairs:
        if h < l:
            bits += "1"
        elif l < h:
            bits += "0"
    print("  pairs=%d bits=%s" % (len(pairs), bits))
    print("  nibbles:", " ".join(bits[j:j + 4] for j in range(0, min(len(bits), 200), 4)))
