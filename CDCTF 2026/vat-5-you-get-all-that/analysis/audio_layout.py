"""Kiem tra artifact audio co payload roi ra byte/ton khong, va dem utterance.
Chay: python analysis/audio_layout.py
"""
import subprocess
import wave
from pathlib import Path

import numpy as np

MP3 = Path("files/captured_cred_call.mp3")
WAV = Path("analysis/_tmp.wav")

print(subprocess.run(["ffprobe", "-hide_banner", "-i", str(MP3)],
                     capture_output=True, text=True).stderr.strip())
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(MP3),
                "-acodec", "pcm_s16le", "-ar", "48000", str(WAV)], check=True)
w = wave.open(str(WAV))
sr, n = w.getframerate(), w.getnframes()
x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768
w.close()
print(f"samples={n} dur={n/sr:.2f}s rms={np.sqrt((x*x).mean()):.4f} "
      f"peak={x.max():.4f}/{x.min():.4f}")

win, hop = int(sr * 0.01), int(sr * 0.005)
m = (len(x) - win) // hop
e = np.array([np.sqrt((x[i*hop:i*hop+win]**2).mean()) for i in range(m)])
thr = max(e.max() * 0.06, 0.004)
act = e > thr
segs, i = [], 0
while i < m:
    if act[i]:
        j = i
        while j + 1 < m and (act[j+1] or (j+4 < m and e[j+4] > thr)):
            j += 1
        segs.append((i * hop / sr, (j + 1) * hop / sr + 0.01))
        i = j + 1
    else:
        i += 1
big = [s for s in segs if s[1] - s[0] >= 0.2]
print(f"gate={thr:.4f} segs={len(segs)} (>=0.25s: {len(big)})")
for k, (a, b) in enumerate(big):
    print(f"  {k+1:2d} {a:6.2f} {b:6.2f} {b-a:5.2f}")

# profile RMS tung 1 s (do chieu dai bucket = sr sample, khong phai sr//f)
prof = [float(np.sqrt((x[i*sr:(i+1)*sr]**2).mean())) for i in range(int(n/sr))]
print("RMS tung 1 s:", [round(v, 4) for v in prof])
code = [s for s in big if s[0] >= 9.0]
print(f"utterance tu 9.0 s tro di = {len(code)} (intro 0-9 s, code words 9-25 s)")
print(f"tot do dai {sum(b-a for a,b in code):.2f} s / {len(code)} utterance")
WAV.unlink()
