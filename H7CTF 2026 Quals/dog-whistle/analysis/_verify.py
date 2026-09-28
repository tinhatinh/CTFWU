import sys, math, struct, cmath, wave
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

d = open("unpacked/aria", "rb").read()
SOS = [list(struct.unpack("<5d", d[0x3340 + i*0x28: 0x3368 + i*0x28])) for i in range(3)]

def H(b0, b1, b2, a1, a2, f, fs=96000.0):
    w = 2*math.pi*f/fs
    z = complex(math.cos(w), -math.sin(w))
    return (b0 + b1*z + b2*z*z) / (1 + a1*z + a2*z*z)

# ---- (a) is the SOS set the 3 conjugate-pole pairs of butter(6, 7000/48000)? --
fs, fc = 96000.0, 7000.0
Wc = 2*fs*math.tan(math.pi*fc/fs)
poles = [Wc*cmath.exp(1j*(math.pi/2 + (2*i+1)*math.pi/12)) for i in range(6)]
pairs = []
used = [False]*6
for i in range(6):
    if used[i]: continue
    for j in range(i+1, 6):
        if not used[j] and abs(poles[i] - poles[j].conjugate()) < 1e-9:
            used[i] = used[j] = True
            pairs.append((poles[i], poles[j])); break
ref_a = []
for p, pc in pairs:
    A0, A1, A2 = 1.0, -2*p.real, abs(p)**2
    a0 = 4*fs*fs + 2*fs*A1 + A2
    ref_a.append((( -8*fs*fs + 2*A2)/a0, (4*fs*fs - 2*fs*A1 + A2)/a0))
print("=== butter(6, fc=7000Hz @ fs=96000) analog-pole bilinear a1,a2 vs binary table ===")
for i, (b0, b1, b2, a1, a2) in enumerate(SOS):
    best = min(ref_a, key=lambda r: abs(r[0]-a1)+abs(r[1]-a2))
    print(f"  sec{i} binary a1={a1:+.12f} a2={a2:+.12f} | ref a1={best[0]:+.12f} a2={best[1]:+.12f}"
          f" | match={abs(best[0]-a1)+abs(best[1]-a2):.2e}")
    print(f"        b = [{b0:+.6e}, {b1:+.6e}, {b2:+.6e}]  b1/b0={b1/b0:.6f} b2/b0={b2/b0:.6f}")

# ---- (b) full front-end model, applied to the shipped reference_ping.wav ------
TY = {"peak": 0, "notch": 1, "lowshelf": 2, "highshelf": 3}
def coeffs(t, f0, Q, g):
    A = math.pow(10.0, g/40.0); w0 = 2*math.pi*f0/fs
    s, c = math.sin(w0), math.cos(w0); al = s/(2*Q)
    if t == 0:
        return [(1+A*al)/(1+al/A), -2*c/(1+al/A), (1-A*al)/(1+al/A), -2*c/(1+al/A), (1-al/A)/(1+al/A)]
    if t == 1:
        return [1/(1+al), -2*c/(1+al), 1/(1+al), -2*c/(1+al), (1-al)/(1+al)]
    sa = 2*math.sqrt(A)*al
    if t == 2:
        P = (A+1)-(A-1)*c; Qs = (A+1)+(A-1)*c; a0 = Qs+sa
        return [A*(P+sa)/a0, 2*A*((A-1)-(A+1)*c)/a0, A*(P-sa)/a0, -2*((A-1)+(A+1)*c)/a0, (Qs-sa)/a0]
    P = (A+1)+(A-1)*c; Qh = (A+1)-(A-1)*c; a0 = Qh+sa
    return [A*(P+sa)/a0, -2*A*((A-1)+(A+1)*c)/a0, A*(P-sa)/a0, 2*((A-1)-(A+1)*c)/a0, (Qh-sa)/a0]

def biquad_df2(x, b):
    s0 = s1 = 0.0
    y = [0.0]*len(x)
    for n, v in enumerate(x):
        t = b[0]*v + s0
        s0 = b[1]*v - b[3]*t + s1
        s1 = b[2]*v - b[4]*t
        y[n] = t
    return y

def eq(x, cfg):
    for t, f0, Q, g in cfg:
        if g == 0.0 and t == 0:
            continue                      # 19aa: peak with 0 dB is skipped
        x = biquad_df2(x, coeffs(t, f0, Q, g))
    return x

def shape(x):                          # 0x1f70
    return [0.98*(4*v) + 0.05*(4*v)**2 + 0.005*(4*v)**3 for v in x]

def aa_decimate(x):                   # 0x1e30
    for sec in SOS:
        x = biquad_df2(x, sec)
    return x[::6]

cfg = [(TY[l.split()[0]], float(l.split()[1]), float(l.split()[2]), float(l.split()[3]))
       for l in open("unpacked/eq.cfg") if l.strip()]
print("\n=== eq.cfg parsed by model: %d bands (binary caps at 8) ===" % len(cfg))

w = wave.open("unpacked/reference_ping.wav", "rb")
n, ch, sw, rate = w.getnframes(), w.getnchannels(), w.getsampwidth(), w.getframerate()
raw = w.readframes(n)
print("  wav: frames=%d ch=%d samplewidth=%d rate=%d" % (n, ch, sw, rate))
x = []
for i in range(n):
    v = raw[3*i] | (raw[3*i+1] << 8) | (raw[3*i+2] << 16)
    if v & 0x800000: v |= 0xFF000000
    x.append(struct.unpack("<i", struct.pack("<I", v & 0xFFFFFFFF))[0] * 2**-23)
print("  0x1710 model: N=%d samples, peak |x| = %.6f" % (len(x), max(abs(v) for v in x)))

e = eq(x, cfg)
print("  after 0x1940 (flat profile): max|diff| = %.3e  (expect 0)" % max(abs(a-b) for a, b in zip(e, x)))
sh = shape(e)
out = aa_decimate(sh)
print("  after 0x1f70: peak %.4f  -> 0x1e30 out len = %d (ceil(%d/6)=%d)"
      % (max(abs(v) for v in sh), len(out), len(sh), -(-len(sh)//6)))

def tone_at(f, sig, fs_):
    N = len(sig); k = 2*math.pi*f/fs_
    c = sum(v*math.cos(k*i) for i, v in enumerate(sig))
    s = sum(v*math.sin(k*i) for i, v in enumerate(sig))
    return 20*math.log10(math.hypot(c, s)/N + 1e-30)
for f in [800, 1000, 1600, 2000, 7000, 12000, 20000, 40000]:
    print("    f=%6d Hz  96k-domain %8.2f dB -> 16k-domain(DT of out) %8.2f dB"
          % (f, tone_at(f, sh, 96000.0), tone_at(f, out, 16000.0)))

# aliasing sanity: a 9 kHz tone must be attenuated by the LPF before decimation
import random
for f in [7500, 9000, 11000, 15000, 24000]:
    t = [math.sin(2*math.pi*f*i/96000.0) for i in range(9600)]
    print("    pure %6d Hz sine: LPF+decimate residual = %8.2f dB (alias would land at %6.1f Hz)"
          % (f, tone_at(f, aa_decimate(shape(t)), 16000.0), abs(round(f/16000.0)*16000.0-f)))
