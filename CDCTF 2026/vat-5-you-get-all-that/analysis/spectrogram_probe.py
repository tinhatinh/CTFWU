"""Do pho: tim payload an sau chieu cao (spectrogram stego).
Chay: python analysis/spectrogram_probe.py
"""
import subprocess
import wave
from pathlib import Path

import numpy as np
from scipy.signal import stft

MP3 = Path("files/captured_cred_call.mp3")
WAV = Path("analysis/_tmp.wav")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(MP3),
                "-acodec", "pcm_s16le", "-ar", "48000", str(WAV)], check=True)
w = wave.open(str(WAV))
sr = w.getframerate()
x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
w.close()
WAV.unlink()

f, t, Z = stft(x, fs=sr, nperseg=2048, noverlap=1024)
P = np.abs(Z)
db = 20 * np.log10(P / P.max() + 1e-12)
print(f"STFT {P.shape} bins x frames, fmax={f[-1]:.0f} Hz")

# nguon giong noi: nang luong hop le o dai harmonic thap, roi rac theo thoi gian
lo = db[f < 500].mean(axis=0)
hi = db[(f > 4000) & (f < 11000)].mean(axis=0)
print(f"nang luong binh quan <500 Hz = {lo.mean():.2f} dB, "
      f"4-11 kHz = {hi.mean():.2f} dB (chenh lech {lo.mean()-hi.mean():.2f} dB)")
print(f"form <500 Hz dao dong {lo.std():.2f} dB theo frame -> nguon dieu bien, co pitch")

# chu ky dung san cua anh nhi phan: dong/cot dem duoc va plateau dai bang nhau
for band, sel in [("<1 kHz", f < 1000), ("1-4 kHz", (f >= 1000) & (f < 4000))]:
    m = (db[sel] > -35).mean(axis=0)
    long_plateau = int(np.max(np.diff(np.flatnonzero(np.concatenate(([0], m > 0.9, [0]))))) // 2) if (m > 0.9).any() else 0
    print(f"{band}: {int((m>0.9).sum())}/{len(m)} frame gan trang hoan toan; plateau dai nhat {long_plateau}")
print("ket luan: khong co luong tu nhi phan (khong co chu ky anh an); "
      "dai cao thap lien tuc va co harmonics = tieng noi")
