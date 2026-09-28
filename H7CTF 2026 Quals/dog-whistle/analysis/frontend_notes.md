# Aria front-end DSP — transcription of `unpacked/aria` (.text)

Stripped PIE ELF. `.text` = vma 0x1180..0x29a9. `.rodata` vma 0x3000 = file offset 0x3000
(so `# 32xx` comments are directly readable from the file). `.data` vma 0x5000 = offset 0x4000.
`.bss` vma 0x5020..0x5180 (NOBITS). **The EQ band table (0x5060) and the band count (0x5040)
live in .bss — they are runtime state, not file contents.**

Call chain in `main` (0x13e0..0x15f7), buffer `[rbp-0x160]` = `double *x`, `[rbp-0x158]` = `size_t n`:

```
1422  0x1600  base64 decode  -> [rbp-0x170] buf, [rbp-0x168] len   (malloc(len/4*3+4))
1463  0x1710  WAV parse + 24-bit -> double, in place into malloc(n) array
              -> [rbp-0x160] = x, [rbp-0x158] = n   (0 = ok, -1 = reject)
148a  0x1940  eq_apply(x, n)                        IN PLACE, no return value
149d  0x2550  safety_check(x, n) -> eax!=0 => "SAFETY LOCKOUT..." + "capture quarantined"
14bc  0x1f70  transducer(x, n)                      IN PLACE, no return value
14eb  malloc( (n/6)*8 + 32 )                        (n*0xaaaaaaaaaaaaaaab >> 64 >> 2 = n/6)
1504  0x1e30  antialias_decimate(x, n, out) -> rax = out_n, then free(x)
1536  0x2070  demod(out, out_n, &payload, &len) -> eax==0 => frame recovered
15bd  0x2790  dispatch(payload, len)
```

## Constants (.rodata) — resolved

| vma | value | used at |
|---|---|---|
| 0x32b8 | `2**-23` = 1.1920928955078125e-07 | 0x1876 (in 0x1710) — 24-bit → double scale |
| 0x32c0 | 1.0 | 0x1a53, 0x1b38/40/48, 0x1b7d, 0x1c04 (0x1940) |
| 0x32c8 | 40.0 | 0x19c5 `gain/40` |
| 0x32d0 | 10.0 | 0x19bd `pow(10, …)` |
| 0x32d8 | 2π = 6.283185307179586 | 0x19e8 (0x1940), 0x21b9 (0x2070) |
| 0x32e0 | 96000.0 | 0x19f6 — EQ sample rate |
| 0x32e8 | −2.0 | 0x1a5b, 0x1b30, 0x1bbf, 0x1c14 |
| 0x32f0 | 4.0 | 0x1f86, 0x2019 (0x1f70 only) |
| 0x32f8 | 0.05 | 0x1f8e, 0x2026 |
| 0x3300 | 0.98 | 0x1f9c, 0x202e |
| 0x3308 | 0.005 | 0x1fa4, 0x2046 |
| 0x3310 | 0.9510565162951535 = cos(2π·800/16000) | 0x20d5 — Goertzel seed for k=0 |
| 0x3318 | −1.0 | 0x20e0 — running-max power initialiser |
| 0x3320 / 0x3328 / 0x3330 | 80.0 / 800.0 / 16000.0 | 0x21a9 / 0x21b1 / 0x21c1 — modem tone law, codec fs |
| 0x3338 | 0.0 | unreferenced |
| 0x3340..0x33b7 | 3 × {b0,b1,b2,a1,a2} | 0x1e6b (0x1e30 only) |
| 0x33c0/0x33c8 | (1.0, 0.0) | 0x2727, unrelated ctor |

**0x2550 itself references none of the 0x32b8.. doubles** (see §4).

## 1. `0x1940` — parametric EQ / biquad cascade

`void eq_apply(double *x /*rdi*/, size_t n /*rsi*/)`. Lazy config load:
`edx = (int32)[0x5010]`; if `edx < 0` (`.data` init = −1) → 0x1c8f sets `[0x5010]=1`,
`[0x5040]=0`, `fopen(getenv("EQ_CFG") ?: "eq.cfg")`, then parses with
`sscanf(line,"%31s %lf %lf %lf", &type_str, &f0, &Q, &gain_db)` (0x1d47), requiring 4 fields.
Lines starting with `#` (0x23) or `\n` are skipped. `.bss` state:

```
0x5010  int32  .data  lazy-load sentinel: -1 not loaded, 1 loaded  (NOT a count)
0x5040  int32  .bss   n_bands, incremented per accepted line, `cmp ebx,7 / jg` => max 8 bands
0x5060  band table, stride 0x20, 8 entries = 0x5060..0x5160 (exactly abutting the 0x5160 globals)
        +0x00 int32 type   (0x5064 pad)
        +0x08 double f0
        +0x10 double Q
        +0x18 double gain_db
type: 0=peak 1=notch 2=lowshelf 3=highshelf (strcmp chain 0x1d51..0x1e1a; an
      unrecognised type string falls through 0x1d93 `xor ecx,ecx` => stored as 0 = peak)
```

Band loop 0x19a0..0x1b03 iterates bands in file order `i = 0 .. n_bands-1`.
Skip test (0x19a0): `if (gain_db == 0.0 && type == 0) continue;` — only *peak* at 0 dB is
skipped (NaN gain is not skipped, `jp` at 0x19ae goes to the design path).

Per band, 0x19bd/0x19e8:

```
A  = pow(10.0, gain_db / 40.0)                       (pow@plt 0x19cd)
w0 = 2*pi*f0 / 96000.0                               (sincos@plt 0x19fe, xmm0=x,
                                                         rdi=&sin, rsi=&cos)
alpha = sin(w0) / (2*Q)                              (0x1a23, 0x1a2f)
```

All four paths converge on `0x1a8a` and divide b0,b1,b2,a1,a2 by a0 (0x1a8f,0x1a9f,0x1aa4,
0x1aa8,0x1aac). With `sa = 2*sqrt(A)*alpha`:

```
peak (0x1a4f fall-through, a0 = 1 + alpha/A):
  b0 = (1 + A*alpha)/a0   b1 = -2cos(w0)/a0   b2 = (1 - A*alpha)/a0
  a1 = -2cos(w0)/a0       a2 = (1 - alpha/A)/a0
notch (0x1b30, A discarded, a0 = 1 + alpha):
  b0 = 1/a0   b1 = -2cos(w0)/a0   b2 = 1/a0   a1 = -2cos(w0)/a0   a2 = (1-alpha)/a0
lowshelf (0x1b70):
  P = (A+1) - (A-1)cos(w0)        Qs = (A+1) + (A-1)cos(w0)       a0 = Qs + sa
  b0 = A*(P + sa)/a0   b2 = A*(P - sa)/a0   b1 = 2A*[(A-1) - (A+1)cos(w0)]/a0
  a1 = -2*[(A-1) + (A+1)cos(w0)]/a0          a2 = (Qs - sa)/a0
highshelf (0x1c00):
  Ph = (A+1) + (A-1)cos(w0)       Qh = (A+1) - (A-1)cos(w0)       a0 = Qh + sa
  b0 = A*(Ph + sa)/a0  b1 = -2A*[(A-1)+(A+1)cos(w0)]/a0  b2 = A*(Ph - sa)/a0
  a1 = 2*[(A-1) - (A+1)cos(w0)]/a0           a2 = (Qh - sa)/a0
```

These are the RBJ/Audio-EQ-Cookbook formulas with `alpha = sin(w0)/(2Q)` used for *both*
peak and shelves (i.e. the Q-parameterised shelf variant, not the `S`-parameterised one;
`shelf slope` is not read from the config). Verified (`_model.py`, `_verify.py`):
peak at f0 = +6.000000 dB exactly for (1000, 0.7, +6); notch → |H(f0)| < 1e-300;
`gain_db == 0` shelves give `b == a` bit-for-bit (max ||H|−1| = 0.0) so they are exactly flat;
lowshelf asymptotic gain matches `gain_db` to 1.5e-2 dB, highshelf to 7.5e-5 dB; all sections
stable over f0∈[50,20000], Q∈[0.4,4], gain∈[−12,12].
The shipped `eq.cfg` (8 bands, all `gain_db = 0.0`) is therefore an **exact identity**
(cascade = 0.000e+00 dB at 1 Hz … 47 kHz).

**Application — Direct Form II, cascade, in place, zero state.** The sample loop 0x1ab0..0x1afa
(`xmm0` = s0, `xmm3` = s1, both zeroed at 0x1a94/0x1a9b):

```
y[n]   = b0*x[n] + s0            -> stored back over x[n] (0x1ad6 movsd [rax-8],xmm1)
s0     = b1*x[n] - a1*y[n] + s1
s1     = b2*x[n] - a2*y[n]
```

i.e. H(z) = (b0 + b1 z⁻¹ + b2 z⁻²)/(1 + a1 z⁻¹ + a2 z⁻²). Not DF-I (DF-I would keep x[n−1],
x[n−2] as the states; these hold the filtered/feedback combination). Initial state is zero
and is **re-zeroed for every band**. Loop order = outer loop over bands, inner full pass over
all n samples; band i's output is band i+1's input, in the same buffer. `n == 0` skips the
sample loop (0x1a8a `test r12,r12`) but the coefficients are still computed. The biquad sample
loops in **0x1940 and 0x1e30 are scalar** (`mulsd/addsd/subsd`, 1 sample/iteration — no SIMD
despite the SSE registers); only 0x1f70 is vectorised 2 doubles wide, and only 0x1e30's
`memcpy` and 0x2070's checksum use packed SSE (`movdqu/pxor`).

## 2. `0x1e30` — 7 kHz anti-alias LPF + decimate ×6  (not the 24-bit conversion)

`double *antialias_decimate(double *x /*rdi*/, size_t n /*rsi*/, double *out /*rdx*/)`.
Returns the output sample count in `rax` (`0x1f3e`/`0x1f40`; 0 if `malloc` failed or n==0).

```
1e4c  tmp = malloc(n*8); memcpy(tmp, x, n*8)            (input never modified)
1e6b  rcx = 0x3340 ; rsi = 0x33b8 (= rcx + 0x78)        3 sections, stride 0x28
      for each section (0x1e86..0x1f03), scalar DF-II, same recursion as §1,
      s0 = s1 = 0 per section (0x1e86 pxor, 0x1ea2), in place over tmp[0..n):
1f20  for (i = 0, j = 0; i < n; i += 6, j++)  out[j] = tmp[i]        DECIMATE BY 6
1f39  free(tmp); return j = ceil(n/6)
```

Decimation factor 6 = 96000/16000. **Picks every 6th sample starting at index 0 — no
group-delay/phase compensation**, so the 6th-order filter's delay shows up as a fractional
delay in the 16 kHz stream.

Coefficient table (order `{b0,b1,b2,a1,a2}`; all three numerators are `b0·[1,2,1]`,
i.e. 6 transmission zeros at z = −1):

```
0x3340 sec0: +6.565838017394151e-05 +1.3131676034788302e-04 +6.565838017394151e-05
             -1.2568124819759159    +0.4013275504706693
0x3368 sec1: +1.0 +2.0 +1.0 -1.3664078166641995 +0.5235247470327964
0x3390 sec2: +1.0 +2.0 +1.0 -1.6095014479758285 +0.7945705933991384
```

Identity: this is the **6th-order Butterworth lowpass, fc = 7000 Hz, fs = 96000 Hz,
bilinear-transformed**, split into 3 biquads with the section gains redistributed (sec0 carries
the whole `b0` scale, sec1/sec2 left at `[1,2,1]`). All three `(a1,a2)` pairs match the
conjugate-pole bilinear reference to ≤ 6.7e-16 (`_verify.py`). Cascade |H(0)| = 1.0 exactly,
|H(Nyquist)| = 0 exactly, −3.010 dB at 6997.3 Hz, flat to +0.000 dB below 3 kHz,
−19.6 dB @10 kHz, −47.3 dB @16 kHz, −62.1 dB @20 kHz, −144.5 dB @40 kHz. Not a brick wall:
a 9000 Hz tone survives decimation at −7.5 dB and aliases to 7000 Hz; 15000 Hz → −36.8 dB
aliasing into 1000 Hz (the modem band).

`0x1710`, not this function, does the 24-bit → double conversion (0x1890..0x18d5):
`v = b0 | b1<<8 | b2<<16`; if `v & 0x800000` then `v |= 0xff000000` (sign-extend via int32);
`x = (int)v * 2**-23` (0x32b8). n = data_bytes/3; requires mono (`channels==1`), `bits==24`,
`rate==96000` (0x17700), data chunk > 2 bytes; if the data chunk exceeds 0x8ca02 (576002)
bytes it is clamped to 0x177000 bytes = 192000 samples (2 s) at 0x18f0.

## 3. `0x1f70` — analog gain + transducer response (memoryless polynomial, in place)

`void transducer(double *x /*rdi*/, size_t n /*rsi*/)`. n==0 → return; n==1 → tail path only
(0x2069). Vectorised 2 doubles/iteration (0x1fd0..0x200f, `n>>1` iterations), remainder handled
scalar at 0x2019..0x205e. Restated scalar maths — for every sample, in place:

```
u = 4.0 * x[n]                          (0x32f0)
x[n] = 0.98*u + 0.05*u^2 + 0.005*u^3    (0x3300, 0x32f8, 0x3308)
     = 3.92*x + 0.80*x^2 + 0.32*x^3
```

Small-signal gain 3.92 (= +11.8657 dB). No clipping, no saturation, no state, no filtering —
pure memoryless 3rd-order nonlinearity, asymmetric (even term) → even-harmonic distortion.
On x∈[−1,1] the output spans [−3.440, +5.040]; x=+0.25 → +1.035 (so the "flat" input of
`reference_ping.wav`, peak 0.25, is pushed to 1.035 — full scale is exceeded).
This is SPEC steps 2+3 combined; it contains no resampling.

## 4. `0x2550` — "SAFETY LOCKOUT" — it is NOT a spectral check

`int safety_check(double *x /*rdi*/, size_t n /*rsi*/)`. **There are no frequency bins, no
300..3400 Hz window, no thresholds, and no tone-signature detector in this function.** It
references no `.rodata` double at all (only the magic constant 0xaaaaaaaaaaaaaaab). The
premise in the task brief (and in SPEC.md's "Safety interlock" section) does not describe the
code. What it actually does:

```
255a  m = n * 0xaaaaaaaaaaaaaaab >> 64 >> 2          = floor(n/6)
2582  buf = malloc(m*8 + 32)          ; malloc fail -> return 0 (0x2679)
25af  out_n = antialias_decimate(x, n, buf)           ; == 0x1e30, same as the real demod path
25cf  ret = demod(buf, out_n, &payload, &len)         ; == 0x2070
      payload at [rbp-0x150], int32 len at [rbp-0x154] (initialised 0 at 0x25c5)
25da  if (ret != 0) return 0;          ; frame NOT recovered => no lockout
2610  len = [rbp-0x154]
      if (len <= 1) return 0;
      i = 0
2656  loop:  t = payload[i]            ; TLV record TYPE
             if ((unsigned)(t - 1) <= 1) return 1;      ; t == 0x01 or 0x02  -> LOCKOUT
             i += payload[i+1] + 2                       ; skip TYPE, LEN, value
2652       if (i + 1 >= len) return 0;                    ; no full header left -> ok
```

So a "signature" is recognised as: **the capture demodulates into a valid frame
(0xA5 0x5A sync, LEN, XOR checksum all verified inside 0x2070) whose TLV record stream
contains a record of type 0x01 (SELECT_PROFILE) or 0x02 (SET_CAL_VECTOR).** Opcode value
inspection after decoding, not spectrum inspection. Reads are in-bounds: index validation
precedes each `payload[]` access.

Ordering consequence (from `main`): 0x2550 runs at 0x149d, i.e. on
`EQ(x)` → LPF+decimate → demod. The *real* demodulator at 0x1536 runs on
`EQ(x)` → `transducer()` → LPF+decimate. The interlock therefore tests a **different signal
than the one the decoder sees**: it omits the ×3.92 gain and the polynomial, which is exactly
the stage that can push |x| past full scale and change which tone wins each Goertzel window.

The oracle it delegates to, `0x2070` (needed to state "which bins"), in the **16 kHz** domain:

```
requires out_n >= 264 (0x108); symbol k window = samples[64 + 200k .. 264 + 200k)
  (0x20a9 r15 = x + 0x840 = +264 doubles; 0x20e8 rbx = r15 - 0x640 = +64; step 0xc8 = 200)
at most 600 symbols (0x258, 0x2202); needs > 7 symbols (0x2217 `cmp r12d,7 / jle` -> reject)
for each of 16 tones k = 0..15:
  f_k = 800 + 80*k Hz   (0x21a9/0x21b1)   w = 2*pi*f_k/16000  (0x21b9/0x21c1)  c = 2*cos(w)
  Goertzel (0x2144): s0 = c*s2 + x[n] - s1 ; s1 = s2 ; s2 = s0   (200 iterations)
  power = s_N^2 + s_{N-1}^2 - c*s_N*s_{N-1}                      (0x2162..0x217e)
  argmax over k, strictly-greater wins (0x2182 comisd / 0x218a cmova), seed -1.0 (0x3318)
  -> one nibble per symbol, packed high-nibble-first (0x2237..0x2248: (nib[2j]<<4)|nib[2j+1])
frame accept test: byte0==0xA5 (0x225b), byte1==0x5A (0x2268), byte2==LEN,
  LEN+3 < n_bytes (0x2282), XOR of LEN and the LEN payload bytes (0x22b5..0x2302) ==
  byte[3+LEN] (0x234c). Then memcpy(payload, frame+3, LEN) and *len_out = LEN.
  returns 0 = ok, -1 = reject.
```

**No energy threshold exists anywhere in 0x2070** — every 200-sample window yields some tone
index by argmax, including pure silence. So the interlock has no "is there a tone at all"
test; the only gates are sync/LEN/checksum, and the opcode test in 0x2550.
The 16 modem tones span 800..2000 Hz (all inside the claimed 300..3400 Hz window, and all
inside the 7 kHz LPF passband); nothing in the front end is specialised to 300 or 3400 Hz —
those two numbers appear nowhere in the binary as constants.

## Unknowns / not determined

- Whether the Q-parameterised shelf `alpha` and the `b1` signs are the intended Cookbook
  variant: the implementation is self-consistent (0 dB ⇒ exactly flat, correct asymptotic
  gains, stable), so this is only a naming-variant question, not a defect.
- The `0x2790` opcode handler and the `0x5160..0x5178` globals (capture budget / region list /
  the `FLAG` path at 0x26a0) were not transcribed — out of scope.
- Nothing observed at runtime: analysis is static + a Python model only (`_model.py`,
  `_verify.py` in this directory). The binary was never executed.
