import sys, math, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------- 0x1940 EQ ---
# Literal transcription of the straight-line coefficient code, xmm0..xmm9 -> r[0..9]
FS = 96000.0

def coeffs(type_, f0, Q, gain_db):
    # 19bd: A = pow(10, gain_db/40)
    A = math.pow(10.0, gain_db / 40.0)
    # 19e8: w0 = 2*pi*f0/FS ; sincos -> r[0]=sin, r[6]=cos
    w0 = 2.0 * math.pi * f0 / FS
    s, c = math.sin(w0), math.cos(w0)
    r = [0.0] * 10
    r[0] = s
    r[6] = c
    r[1] = A
    r[2] = Q
    r[2] = r[2] + r[0]      # 1a23  2Q
    r[0] = r[0] / r[2]      # 1a2f  alpha = sin/(2Q)
    if type_ == 1:          # notch, branch at 1a33 (skips 1a39)
        r[6] = r[6] * -2.0  # 1b30
        r[1] = 1.0          # 1b38
        r[5] = 1.0          # 1b40
        r[7] = 1.0          # 1b48
        r[1] = r[1] + r[0]  # 1b50  a0 = 1+alpha
        r[5] = r[5] - r[0]  # 1b54  a2 = 1-alpha
        r[9] = r[7]         # 1b58  b0 = 1
        r[8] = r[6]         # 1b5d  b1 = -2cos
        # -> 1a8a
        r[9] /= r[1]; r[8] /= r[1]; r[7] /= r[1]; r[6] /= r[1]; r[5] /= r[1]
        return r[9], r[8], r[7], r[6], r[5]
    r[2] = r[1]             # 1a39  xmm2 = A
    if type_ == 0:          # peak, fall-through 1a4f
        r[2] = r[2] * r[0]  # 1a4f  A*alpha
        r[5] = 1.0          # 1a53
        r[6] = r[6] * -2.0  # 1a5b  -2cos
        r[7] = r[5]         # 1a63
        r[9] = r[2]         # 1a67
        r[7] = r[7] - r[2]  # 1a6c  1-A*alpha
        r[9] = r[9] + r[5]  # 1a70  1+A*alpha
        r[8] = r[6]         # 1a75  b1 = -2cos
        r[0] = r[0] / r[1]  # 1a7a  alpha/A
        r[1] = r[0] + r[5]  # 1a82  a0 = 1+alpha/A
        r[5] = r[5] - r[0]  # 1a86  a2 = 1-alpha/A
        # fall-through to 1a8a
        r[9] /= r[1]; r[8] /= r[1]; r[7] /= r[1]; r[6] /= r[1]; r[5] /= r[1]
        return r[9], r[8], r[7], r[6], r[5]
    elif type_ == 2:        # lowshelf, 1b70
        r[2] = math.sqrt(r[2])            # sqrt(A)
        r[5] = r[1]                       # A
        r[3] = 1.0
        r[8] = r[1]                       # A
        r[8] = r[8] + r[1]                # 2A
        r[5] = r[5] + r[3]                # A+1
        r[2] = r[2] + r[2]                # 2*sqrt(A)
        r[7] = r[5]                       # A+1
        r[0] = r[0] * r[2]                # 2*sqrt(A)*alpha  ("sa")
        r[2] = r[1]                       # A
        r[2] = r[2] - r[3]                # A-1
        r[3] = r[6]                       # cos
        r[6] = r[6] * r[5]                # cos*(A+1)
        r[3] = r[3] * r[2]                # cos*(A-1)
        r[4] = r[2]                       # A-1
        r[9] = r[0]                       # sa
        r[4] = r[4] - r[6]                # (A-1)-(A+1)cos
        r[6] = r[6] + r[2]                # (A-1)+(A+1)cos
        r[6] = r[6] * -2.0                # a1 num
        r[7] = r[7] - r[3]                # (A+1)-(A-1)cos   P
        r[5] = r[5] + r[3]                # (A+1)+(A-1)cos   Qs
        r[8] = r[8] * r[4]                # 2A*[(A-1)-(A+1)cos]  b1
        r[9] = r[9] + r[7]                # sa + P
        r[7] = r[7] - r[0]                # P - sa
        r[9] = r[9] * r[1]                # b0 = A(P+sa)
        r[7] = r[7] * r[1]                # b2 = A(P-sa)
        r[1] = r[0]                       # sa
        r[1] = r[1] + r[5]                # a0 = Qs + sa
        r[5] = r[5] - r[0]                # a2 = Qs - sa
        r[9] /= r[1]; r[8] /= r[1]; r[7] /= r[1]; r[6] /= r[1]; r[5] /= r[1]   # 1a8a
        return r[9], r[8], r[7], r[6], r[5]
    elif type_ == 3:        # highshelf, 1c00
        r[2] = math.sqrt(r[2])            # sqrt(A)
        r[3] = 1.0
        r[5] = r[1]                       # A
        r[4] = r[6]                       # cos
        r[8] = -2.0
        r[5] = r[5] + r[3]                # A+1
        r[2] = r[2] + r[2]                # 2sqrtA
        r[8] = r[8] * r[1]                # -2A
        r[6] = r[6] * r[5]                # cos*(A+1)
        r[7] = r[5]                       # A+1
        r[0] = r[0] * r[2]                # sa = 2sqrtA*alpha
        r[2] = r[1]                       # A
        r[2] = r[2] - r[3]                # A-1
        r[4] = r[4] * r[2]                # cos*(A-1)
        r[3] = r[6]                       # cos*(A+1)
        r[6] = r[2]                       # A-1
        r[6] = r[6] + r[3]                # (A-1)+(A+1)cos
        r[9] = r[0]                       # sa
        r[8] = r[8] * r[6]                # b1 = -2A[(A-1)+(A+1)cos]
        r[6] = r[2]                       # A-1
        r[7] = r[7] + r[4]                # (A+1)+(A-1)cos  Ph
        r[5] = r[5] - r[4]                # (A+1)-(A-1)cos  Qh
        r[6] = r[6] - r[3]                # (A-1)-(A+1)cos
        r[9] = r[9] + r[7]                # sa + Ph
        r[7] = r[7] - r[0]                # Ph - sa
        r[6] = r[6] + r[6]                # 2[(A-1)-(A+1)cos]   a1
        r[9] = r[9] * r[1]                # b0 = A(Ph+sa)
        r[7] = r[7] * r[1]                # b2 = A(Ph-sa)
        r[1] = r[0]                       # sa
        r[1] = r[1] + r[5]                # a0 = Qh + sa
        r[5] = r[5] - r[0]                # a2 = Qh - sa
        r[9] /= r[1]; r[8] /= r[1]; r[7] /= r[1]; r[6] /= r[1]; r[5] /= r[1]   # 1a8a
        return r[9], r[8], r[7], r[6], r[5]
    raise ValueError(type_)

def H(b0, b1, b2, a1, a2, f, fs=FS):
    w = 2 * math.pi * f / fs
    z = complex(math.cos(w), -math.sin(w))
    return (b0 + b1*z + b2*z*z) / (1 + a1*z + a2*z*z)

print("=== 0x1940 coefficient formulas, closed form check (f0=1000,Q=0.7,gain=+6) ===")
for t, name in enumerate(["peak", "notch", "lowshelf", "highshelf"]):
    b0, b1, b2, a1, a2 = coeffs(t, 1000.0, 0.7, 6.0)
    print(f"{name:10s} b0={b0:+.12f} b1={b1:+.12f} b2={b2:+.12f} a1={a1:+.12f} a2={a2:+.12f}")

print()
print("=== shelf identity tests ===")
for t, name in [(2, "lowshelf"), (3, "highshelf")]:
    for g in [0.0, 6.0, -6.0]:
        b = coeffs(t, 3000.0, 0.7, g)
        flat = max(abs(H(*b, f)[0] - 1.0) if False else abs(20*math.log10(abs(H(*b, f))) - (0.0 if g == 0 else 0.0))
                   for f in [10, 50, 200, 800, 3000, 12000, 40000, 47000]) if g == 0 else None
        lo = 20*math.log10(abs(H(*b, 10.0)))
        hi = 20*math.log10(abs(H(*b, 47000.0)))
        mid = 20*math.log10(abs(H(*b, 3000.0)))
        pol = None
        print(f"{name} f0=3000 gain={g:+5.1f} dB | @10Hz={lo:+7.3f} @3000={mid:+7.3f} @47k={hi:+7.3f}"
              + (f"  max|H|-1={flat:.2e}" if flat is not None else ""))

print()
print("=== peak/notch identity ===")
b = coeffs(0, 1000, 0.7, 6.0)
print("peak +6dB @f0 (should be +6):", round(20*math.log10(abs(H(*b, 1000.0))), 6),
      " @10Hz (0):", round(20*math.log10(abs(H(*b, 10.0))), 6),
      " @47k (0):", round(20*math.log10(abs(H(*b, 47000.0))), 6))
b = coeffs(1, 1000, 0.7, 0.0)
print("notch @f0 (should be ~ -inf):", round(20*math.log10(abs(H(*b, 1000.0)) + 1e-300), 4),
      " @10Hz:", round(20*math.log10(abs(H(*b, 10.0))), 6), " @47k:", round(20*math.log10(abs(H(*b, 47000.0))), 6))

print()
print("=== shipped eq.cfg cascade (all gains 0.0) ===")
cfg = [l.split() for l in open("unpacked/eq.cfg") if l.strip()]
TY = {"peak": 0, "notch": 1, "lowshelf": 2, "highshelf": 3}
stages = [coeffs(TY[t], float(f), float(q), float(g)) for t, f, q, g in cfg]
for f in [20, 100, 250, 500, 1000, 2000, 3000, 4000, 7000, 8000, 12000, 20000, 30000, 47000]:
    m = 1.0
    for s in stages:
        m *= abs(H(*s, f))
    print(f"  {f:6d} Hz  {20*math.log10(m):+8.4f} dB")

# ------------------------------------------------- 0x1e30 anti-alias filter ---
d = open("unpacked/aria", "rb").read()
SOS = [struct.unpack("<5d", d[0x3340 + i*0x28: 0x3368 + i*0x28]) for i in range(3)]
print()
print("=== 0x3340 SOS table (3 x {b0,b1,b2,a1,a2}) ===")
for i, s in enumerate(SOS):
    print(f"  sec{i} @0x{0x3340+i*0x28:04x}: " + " ".join(f"{v:+.12e}" for v in s))
def casc(f, fs=96000.0):
    m = 1.0
    for b0, b1, b2, a1, a2 in SOS:
        m *= H(b0, b1, b2, a1, a2, f, fs)
    return m
print("  DC gain:", round(abs(casc(0.0)), 12), " Nyquist:", f"{abs(casc(48000.0)):.3e}")
print("  response (dB):")
for f in [100, 1000, 3000, 5000, 6000, 6500, 7000, 7500, 8000, 10000, 13333, 16000, 20000, 40000]:
    print(f"    {f:6d} Hz {20*math.log10(max(abs(casc(f)),1e-300)):+9.3f} dB")

# reference 6th-order Butterworth, bilinear at 96k, to identify cutoff
def butter_lp(n, fc, fs):
    w = 2*math.tan(math.pi*fc/fs)/2.0*2  # prewarp: Wc = 2*fs*tan(pi*fc/fs) /2 ... use standard
    Wc = 2*fs*math.tan(math.pi*fc/fs)
    # build analog poles, then bilinear each biquad
    secs = []
    k = 0
    import cmath
    poles = []
    for i in range(n):
        th = math.pi/2 + (2*i+1)*math.pi/(2*n)
        poles.append(Wc*cmath.exp(1j*th))
    used = [False]*n
    for i in range(n):
        if used[i]:
            continue
        used[i] = True
        p = poles[i]
        if abs(p.imag) > 1e-9:
            j = [q for q in range(n) if not used[q] and abs(poles[q]-p.conjugate()) < 1e-9][0]
            used[j] = True
            a1 = -2*p.real/ (1.0)  # placeholder
        # do it numerically instead (below)
    return secs

# numeric identification of fc from the actual SOS: match -3dB point by scan
def find_m3():
    lo, hi = 1000.0, 20000.0
    for _ in range(80):
        mid = (lo+hi)/2
        if abs(casc(mid)) > 10**(-3/20):
            lo = mid
        else:
            hi = mid
    return (lo+hi)/2
print("  -3 dB cutoff = %.3f Hz (Nyquist-relative %.6f)" % (find_m3(), find_m3()/48000))

# --------------------------------------------- 0x1f70 transducer response ---
def shape(x):
    u = 4.0*x
    return 0.98*u + 0.05*u*u + 0.005*u*u*u
print()
print("=== 0x1f70 y = 0.98u+0.05u^2+0.005u^3, u = 4x ===")
print("  small-signal gain dy/dx|0 =", round((shape(1e-9)-shape(-1e-9))/2e-9, 9),
      "= %.4f dB" % (20*math.log10(0.98*4)))
for x in [-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0]:
    print(f"    x={x:+.3f} -> {shape(x):+9.6f}")
print("  range on [-1,1]: min %.6f max %.6f" % (min(shape(x/1e5) for x in range(-100001,100002)),
                                                 max(shape(x/1e5) for x in range(-100001,100002))))

# ---------------------------------------------------- 0x2070 Goertzel tone ---
print()
print("=== 0x3310 constant = 2*cos(w) seed for k=0 ===")
print("  0.9510565162951535*2 =", 2*0.9510565162951535,
      " 2cos(2pi*800/16000) =", 2*math.cos(2*math.pi*800/16000))
print("  tones:", [800+80*k for k in range(16)], "Hz; all inside 300..3400:",
      all(300 <= 800+80*k <= 3400 for k in range(16)))

# --------------------------------------------- extra: identities & stability --
import cmath
def poles(a1, a2):
    return [z for z in ((-a1 + cmath.sqrt(a1*a1 - 4*a2))/2, (-a1 - cmath.sqrt(a1*a1 - 4*a2))/2)]
print()
print("=== shelf asymptotic-gain identities (binary's own formulas) ===")
worst = {}
for t, name, edge in [(2, "lowshelf", "DC"), (3, "highshelf", "Nyq")]:
    worst[name] = 0.0
    for f0 in [50, 120, 300, 1000, 3000, 8000, 12000, 20000]:
        for Q in [0.4, 0.707, 1.0, 2.0, 4.0]:
            for g in [-12.0, -6.0, -1.0, 0.0, 1.0, 6.0, 12.0]:
                b = coeffs(t, f0, Q, g)
                if max(abs(z) for z in poles(b[3], b[4])) >= 1.0:
                    print("  UNSTABLE", name, f0, Q, g, b)
                meas = 20*math.log10(abs(H(*b, 0.5 if t == 2 else 47900.0)))
                err = abs(meas - g)
                worst[name] = max(worst[name], err)
    print(f"  {name}: max |asymptotic gain - gain_dB| = {worst[name]:.3e} dB"
          f"  (edge={edge})")
b0 = coeffs(2, 1000, 0.7, 0.0); b1 = coeffs(3, 1000, 0.7, 0.0)
print("  0 dB shelf flatness: lowshelf max||H|-1| =",
      max(abs(abs(H(*b0, f))-1) for f in [1,10,100,500,1000,5000,20000,47000]),
      " highshelf:", max(abs(abs(H(*b1, f))-1) for f in [1,10,100,500,1000,5000,20000,47000]))
print()
print("=== shipped eq.cfg: exact flatness (b==a per band) ===")
for (t, f, q, g), name in zip([(TY[c[0]], float(c[1]), float(c[2]), float(c[3])) for c in cfg],
                              [c[0] for c in cfg]):
    b = coeffs(t, f, q, g)
    print(f"  {name:10s} f0={f:>9} gain={g:>5} -> b0-a0={b[0]-1:+.3e} b1-a1={b[1]-b[3]:+.3e} b2-a2={b[2]-b[4]:+.3e}")
m = 1.0
for f in [1, 10, 100, 1000, 7000, 20000, 47000]:
    m = 1.0
    for c in cfg:
        s = coeffs(TY[c[0]], float(c[1]), float(c[2]), float(c[3]))
        m *= abs(H(*s, f))
    print(f"  cascade @{f:>6d} Hz = {20*math.log10(m):+.3e} dB")

print()
print("=== 6th-order Butterworth reference (bilinear, fc=7000, fs=96000) ===")
def bw_sos(n, fc, fs):
    Wc = 2*fs*math.tan(math.pi*fc/fs)
    zp = []
    for i in range(n):
        th = math.pi/2 + (2*i+1)*math.pi/(2*n)
        zp.append(Wc*cmath.exp(1j*th))
    secs = []
    pairs = []
    used = [False]*n
    for i in range(n):
        if used[i]: continue
        used[i] = True
        if i+1 < n and not used[i+1] and abs(zp[i+1]-zp[i].conjugate()) < 1e-6:
            used[i+1] = True
            pairs.append((zp[i], zp[i+1]))
        else:
            pairs.append((zp[i], None))
    for pr in pairs:
        if pr[1] is None:
            p = pr[0]
            b1c, b2c, a1c, a2c = None, None, None, None
            continue
        p, pc = pr
        # analog section: 1/((s-p)(s-pc)) = 1/(s^2 - 2Re(p) s + |p|^2)
        A0, A1, A2 = 1.0, -2*p.real, abs(p)**2
        # bilinear: s = 2fs (1-z)/(1+z) ; numerator Wc^2 (1+z)^2 style
        K = Wc**2
        a0 = A0*4*fs*fs + A1*2*fs + A2
        a1 = -2*A0*4*fs*fs + 2*A2
        a2 = A0*4*fs*fs - A1*2*fs + A2
        bb0, bb1, bb2 = K/a0, 2*K/a0, K/a0
        secs.append((bb0, bb1, bb2, a1/a0, a2/a0))
    return secs
ref = bw_sos(6, 7000.0, 96000.0)
for i, s in enumerate(ref):
    print(f"  ref sec{i}: " + " ".join(f"{v:+.12e}" for v in s))
def casc2(sos, f, fs=96000.0):
    m = 1.0
    for b0, b1, b2, a1, a2 in sos:
        m *= H(b0, b1, b2, a1, a2, f, fs)
    return m
print("  gain-matched product vs binary SOS (dB diff):")
gm = 1.0
for s in SOS: gm *= H(*s, 0.0)[0] if False else abs(H(*s, 0.0))
gr = 1.0
for s in ref: gr *= abs(H(*s, 0.0))
scale = gr/gm
for f in [100, 3000, 6000, 7000, 8000, 12000, 20000, 40000]:
    a = 20*math.log10(abs(casc(f)))
    b = 20*math.log10(abs(casc2(ref, f)))
    print(f"    {f:6d} Hz  binary {a:+9.4f}  ref {b:+9.4f}  diff {a-b:+9.6f}")
