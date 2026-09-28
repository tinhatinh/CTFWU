"""Burst structure of the exfil audio: locate bursts, then read the tone sequence inside them."""

import sys
import wave
from collections import Counter

import numpy as np

with wave.Wave_read(sys.argv[1]) as w:
    sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64) / 32768

# --- 1. locate bursts via short-time energy in the 600-3000 Hz band
def bandpass(sig, lo, hi):
    n = len(sig)
    S = np.fft.rfft(sig)
    f = np.fft.rfftfreq(n, 1 / sr)
    S[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(S, n)

env = np.abs(bandpass(x, 600, 3000))
win = int(0.02 * sr)
nb = len(env) // win
e = np.array([env[i * win:(i + 1) * win].mean() for i in range(nb)])
thr = e.max() * 0.15
on = e > thr

bursts, i = [], 0
while i < nb:
    if on[i]:
        j = i
        while j < nb and on[j]:
            j += 1
        if (j - i) * 0.02 > 0.15:
            bursts.append((i * win / sr, j * win / sr))
        i = j
    else:
        i += 1

print(f"[*] {len(bursts)} burst(s), sr={sr}")
for k, (a, b) in enumerate(bursts[:14]):
    print(f"    burst {k:2d}: {a:7.3f} - {b:7.3f} s  ({(b-a)*1000:6.1f} ms)")

# --- 2. inside each burst: dominant tone(s) per frame
FRAME = int(0.020 * sr)
HOPF = int(0.020 * sr)
alphabet = Counter()
seq = []

for k, (a, b) in enumerate(bursts):
    s0, s1 = int(a * sr), int(b * sr)
    seg = x[s0:s1]
    frames = []
    for p in range(0, len(seg) - FRAME, HOPF):
        f = np.abs(np.fft.rfft(seg[p:p + FRAME] * np.hanning(FRAME)))
        fr = np.fft.rfftfreq(FRAME, 1 / sr)
        m = (fr > 500) & (fr < 3200)
        f2, fr2 = f[m], fr[m]
        peaks = []
        for idx in np.argsort(f2)[::-1]:
            hz = int(round(fr2[idx] / 25) * 25)
            if f2[idx] < f2.max() * 0.25:
                break
            if any(abs(hz - q) < 100 for q, _ in peaks):
                continue
            peaks.append((hz, float(f2[idx])))
        peaks.sort()
        frames.append(peaks)
        for hz, _ in peaks:
            alphabet[hz] += 1
    seq.append(frames)

print(f"\n[2] frequency alphabet across all bursts (rounded to 25 Hz):")
print("   ", sorted(alphabet.items(), key=lambda kv: -kv[1])[:30])

print(f"\n[3] per-burst frame detail (first 3 bursts):")
for k in range(min(3, len(seq))):
    print(f"  --- burst {k} ---")
    for fi, peaks in enumerate(seq[k][:50]):
        print(f"    t={fi*20:4d}ms  " + "  ".join(f"{hz}Hz" for hz, _ in peaks))
