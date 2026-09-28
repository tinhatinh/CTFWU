#!/usr/bin/env python
"""Radio Silence (H7TEX hardware) -- decode an unknown single RF burst.

capture.cf32 : interleaved float32 LE I/Q @ 1 MHz, 49193 samples.
Found by analysis (see analysis/notes inside writeup):
  * envelope is constant over samples 2909..46109 -> not OOK, it is 2-FSK
  * the burst has exactly two tones: +35.0 kHz and +85.0 kHz (centre 60 kHz,
    deviation 25 kHz)
  * transitions in the FM discriminator cluster on a 100-sample grid -> 10 kBaud,
    43200/100 = 432 symbols
Decoding = majority-vote each 100-sample slot, map high tone -> bit, 8 bits/byte MSB-first.

usage: python solve_rf.py capture.cf32
"""
import re
import sys
import numpy as np

FS = 1e6
FILE = sys.argv[1] if len(sys.argv) > 1 else "files/capture.cf32"
SPP = 100                    # samples per symbol @ 1 Msps == 10 kBaud
FLAG_RE = re.compile(rb"H7CTF\{[^{}]*\}")

raw = np.fromfile(FILE, dtype="<f4")
iq = raw[0::2] + 1j * raw[1::2]
mag = np.abs(iq)

# burst gate: anything above the noise floor found in the first 200 samples
noise = np.median(mag[:200])
on = mag > max(0.35 * mag.max(), 4 * noise)
edges = np.flatnonzero(np.diff(on.astype(np.int8)))
start, end = int(edges[0]) + 1, int(edges[-1]) + 1
burst = iq[start:end]

phase = np.unwrap(np.angle(burst))
disc = (phase[1:] - phase[:-1]) * FS / (2 * np.pi)
sm = np.convolve(disc, np.ones(8) / 8, mode="valid")
f_lo, f_hi = np.percentile(sm[sm < np.median(sm)], 50), np.percentile(sm[sm > np.median(sm)], 50)
thr = (f_lo + f_hi) / 2

states = (sm > thr).astype(np.int8)
n = (end - start) // SPP        # 43200/100 = 432 symbols, whole bytes
L = len(states)
slots = np.array([states[min(i * SPP + 10, L):min((i + 1) * SPP - 10, L)] for i in range(n)])
frac = slots.mean(axis=1)
margin = np.abs(frac - 0.5)
bits = (frac > 0.5).astype(np.uint8)

frame = np.packbits(bits)            # MSB-first, numpy default
text = frame.tobytes()

print("[*] burst       samples %d..%d  (%d us, %d symbols @ %.1f kBaud)"
      % (start, end, end - start, n, FS / SPP / 1e3))
print("[*] tones       %.2f kHz / %.2f kHz  (decision %.2f kHz)" % (f_lo / 1e3, f_hi / 1e3, thr / 1e3))
print("[*] decisions   min margin %.3f, %d/%d slots below 0.05 margin"
      % (margin.min(), int((margin < 0.05).sum()), n))
print("[*] raw frame   %s" % text.hex())
print("[*] as ascii    %r" % text)
tail = bits[n // 8 * 8:]
print("[*] leftover    %d bits after the last whole byte: %s" % (len(tail), "".join(map(str, tail))))

m = FLAG_RE.search(text)
if not m:
    sys.exit("[-] no H7CTF{...} in the decoded frame")
flag = m.group()
print("[+] FLAG: %s" % flag.decode())
open("flag.txt", "wb").write(flag)
