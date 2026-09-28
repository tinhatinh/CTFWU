"""Spectral survey of the captured room audio: where is the hidden carrier?"""

import sys
import wave

import numpy as np

with wave.Wave_read(sys.argv[1]) as w:
    sr = w.getframerate()
    ch = w.getnchannels()
    sw = w.getsampwidth()
    raw = w.readframes(w.getnframes())

assert sw == 2
x = np.frombuffer(raw, dtype="<i2").astype(np.float64)
if ch > 1:
    x = x.reshape(-1, ch).mean(axis=1)
n = len(x)
print(f"[*] {n/sr:.2f} s, sr={sr}, ch={ch}, nyquist={sr/2:.0f} Hz")

WIN, HOP = 4096, 2048
win = np.hanning(WIN)
frames = 1 + (n - WIN) // HOP
spec = np.empty((frames, WIN // 2 + 1))
for i in range(frames):
    seg = x[i * HOP: i * HOP + WIN] * win
    spec[i] = np.abs(np.fft.rfft(seg))

freqs = np.fft.rfftfreq(WIN, 1 / sr)
mean = spec.mean(axis=0)

print("\n[1] band energy (dB relative to total):")
tot = mean.sum()
for lo, hi in ((0, 300), (300, 1000), (1000, 3000), (3000, 6000), (6000, 10000),
               (10000, 14000), (14000, 17000), (17000, 19000), (19000, 21000), (21000, 24000)):
    m = (freqs >= lo) & (freqs < hi)
    e = mean[m].sum()
    print(f"    {lo:>5}-{hi:<5} Hz  {20*np.log10(e/tot+1e-12):7.2f} dB  {'#'*int(max(0,(20*np.log10(e/tot+1e-12))+45))}")

print("\n[2] top 18 single-frequency peaks overall:")
order = np.argsort(mean)[::-1]
seen = []
for k in order:
    f = freqs[k]
    if any(abs(f - s) < 40 for s in seen):
        continue
    seen.append(f)
    tm = mean[k]
    # temporal duty cycle: fraction of frames where this bin is above 6 dB of its median
    col = spec[:, k]
    duty = float((col > 2 * np.median(col)).mean())
    print(f"    {f:8.1f} Hz  mag={tm:10.1f}  duty={duty:5.2f}")
    if len(seen) >= 18:
        break

print("\n[3] ultrasonic (>17 kHz) peak list, with duty cycle:")
ultra = np.where(freqs > 17000)[0]
peaks = ultra[np.argsort(mean[ultra])[::-1][:25]]
for k in sorted(peaks, key=lambda k: -mean[k]):
    col = spec[:, k]
    duty = float((col > 2 * np.median(col)).mean())
    print(f"    {freqs[k]:8.1f} Hz  mean={mean[k]:9.1f}  max={col.max():9.1f}  duty={duty:5.2f}")

spec.tofile(sys.argv[2] + ".spec.f64")
np.savez(sys.argv[2] + ".npz", freqs=freqs, mean=mean, spec=spec[:500], sr=sr)
print(f"\n[+] saved {sys.argv[2]}.npz")
