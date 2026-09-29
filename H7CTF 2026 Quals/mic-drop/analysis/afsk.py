"""Bell-202 style AFSK demodulator: mark/space envelopes, baud estimation, 8N1 decode."""

import sys
import wave
from collections import Counter

import numpy as np

with wave.Wave_read(sys.argv[1]) as w:
    sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64) / 32768

MARK, SPACE = float(sys.argv[2]) if len(sys.argv) > 2 else 1200.0, float(sys.argv[3]) if len(sys.argv) > 3 else 2200.0
BW = 120.0


def tone_env(sig, f0):
    """Complex-envelope magnitude of a narrow band around f0 (FFT domain)."""
    n = len(sig)
    S = np.fft.rfft(sig)
    fr = np.fft.rfftfreq(n, 1 / sr)
    S[(fr < f0 - BW) | (fr > f0 + BW)] = 0
    return np.abs(np.fft.irfft(S, n))


def band_bits(sig, mark, space, baud):
    """Sample the mark/space comparison once per bit, return hard bits."""
    em, es = tone_env(sig, mark), tone_env(sig, space)
    spb = sr / baud
    nbits = int(len(sig) / spb) - 2
    out = np.empty(nbits, dtype=np.uint8)
    for i in range(nbits):
        a, b = int((i + 0.5) * spb), int((i + 1.5) * spb)
        out[i] = 1 if em[a:b].mean() > es[a:b].mean() else 0
    return out


def decode(bits, start=0, databits=8, parity=None, lsbfixed=True):
    chars, i, bad = [], start, 0
    while i + 1 + databits <= len(bits):
        if bits[i] != 0:                      # start bit
            i += 1
            continue
        val = 0
        for k in range(databits):
            b = bits[i + 1 + k]
            val |= (b << k) if lsbfixed else (b << (databits - 1 - k))
        i += 1 + databits
        if parity == "even" and i <= len(bits):
            i += 1
        chars.append(val)
    return bytes(chars)


def printable_score(bs):
    return sum(1 for c in bs if 32 <= c < 127) / max(1, len(bs))


print(f"[*] sr={sr} mark={MARK} space={SPACE}")

# 1. find the active bursts (same energy detector as bursts.py)
env = tone_env(x, MARK) + tone_env(x, SPACE)
win = int(0.02 * sr)
nb = len(env) // win
e = np.array([env[i * win:(i + 1) * win].mean() for i in range(nb)])
on = e > e.max() * 0.15
runs, i = [], 0
while i < nb:
    if on[i]:
        j = i
        while j < nb and on[j]:
            j += 1
        runs.append((i * win, j * win))
        i = j
    else:
        i += 1
print(f"[*] {len(runs)} active region(s); longest = "
      f"{max((b-a)/sr for a,b in runs):.2f} s")

# 2. baud estimation: transition density of the mark>space decision at fine resolution
a, b = max(runs, key=lambda r: r[1] - r[0])
seg = x[a:b]
best = None
for baud in (300, 600, 1200, 1800, 2400):
    bits = band_bits(seg, MARK, SPACE, baud)
    trans = int(np.count_nonzero(np.diff(bits)))
    print(f"    baud {baud:4d}: {len(bits)} bits, {trans} transitions, "
          f"trans/bit={trans/len(bits):.3f}")
    if best is None or 0.18 < trans / len(bits) < 0.5:
        best = baud

# 3. decode at each candidate baud, keep the most text-like result
print("\n[*] decode attempts:")
results = []
for baud in (300, 600, 1200, 1800, 2400):
    for region in runs:
        s0, s1 = region
        seg = x[s0:s1]
        if len(seg) < sr * 0.2:
            continue
        bits = band_bits(seg, MARK, SPACE, baud)
        for start in range(0, 8):
            for lsbfixed in (True, False):
                txt = decode(bits, start, 8, None, lsbfixed)
                sc = printable_score(txt)
                if sc > 0.9 and len(txt) > 8:
                    results.append((sc, len(txt), baud, start, lsbfixed, txt))
results.sort(key=lambda r: (-r[1], -r[0]))
for sc, ln, baud, start, lsb, txt in results[:6]:
    print(f"    baud={baud} phase={start} lsb={lsb} printable={sc:.2f} len={ln}")
    print(f"      {txt[:160]!r}")
if not results:
    print("    no high-printability decode yet - inspect raw bit stream instead")
    bits = band_bits(x[runs[0][0]:runs[0][1]], MARK, SPACE, 1200)
    print("    first 120 bits @1200:", "".join(map(str, bits[:120])))
