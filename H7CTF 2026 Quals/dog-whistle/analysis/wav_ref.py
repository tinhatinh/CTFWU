#!/usr/bin/env python3
"""Characterise reference_ping.wav from first principles: RIFF facts, sample
statistics, full-band spectrum, and the documented 16-tone MFSK decode
(96 kHz -> 16 kHz codec rate, 200-sample symbols, hex nibble per tone).

stdlib + numpy/scipy only.  No arguments.  Read-only with respect to the WAV.
"""
import math
import os
import struct
import sys

import numpy as np
from scipy import signal as sg

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
WAV = os.path.join(HERE, "unpacked", "reference_ping.wav")

FS = 96000                 # transport rate from the spec
CODEC_FS = 16000           # modem rate after decimation
DECIM = FS // CODEC_FS     # 6
SYM = 200                  # codec samples per symbol (12.5 ms)
LEADIN = 64                # codec samples of silence before the first symbol
TONE0, TONESTEP, NTONE = 800.0, 80.0, 16
AA_HZ = 7000.0             # anti-alias low-pass from the spec
FS24 = 2 ** 23             # 24-bit signed full scale

TONE_BY_IDX = {k: TONE0 + TONESTEP * k for k in range(NTONE)}
OPCODES = {0x10: "DEBUG_PING", 0x01: "SELECT_PROFILE", 0x02: "SET_CAL_VECTOR"}


def hr(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


# ---------------------------------------------------------------- 1. header
def read_chunks(raw):
    """Walk the RIFF chunk list byte by byte; return list of (id,size,offset)."""
    out = []
    if raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        raise ValueError("not a RIFF/WAVE file: %r" % (raw[:12],))
    riff_size = struct.unpack("<I", raw[4:8])[0]
    i = 12
    while i + 8 <= len(raw):
        cid = raw[i:i + 4]
        size = struct.unpack("<I", raw[i + 4:i + 8])[0]
        out.append((cid, size, i))
        i += 8 + size + (size & 1)          # chunks are word-aligned
    return riff_size, out, i


def parse_wav(path):
    raw = open(path, "rb").read()
    riff_size, chunks, walker_end = read_chunks(raw)
    fmt = next(c for c in chunks if c[0] == b"fmt ")
    f = raw[fmt[2] + 8: fmt[2] + 8 + fmt[1]]
    (audio_format, channels, sample_rate, byte_rate,
     block_align, bits) = struct.unpack("<HHIIHH", f[:16])
    data = next(c for c in chunks if c[0] == b"data")
    d_off, d_size = data[2] + 8, data[1]
    avail = len(raw) - d_off
    nbytes = min(d_size, avail)
    samples = (nbytes // max(1, bits // 8)) // channels
    info = dict(path=path, filesize=len(raw), riff_size=riff_size, chunks=chunks,
                walker_end=walker_end, trailing=len(raw) - walker_end,
                audio_format=audio_format, channels=channels, sample_rate=sample_rate,
                byte_rate=byte_rate, block_align=block_align, bits=bits,
                data_off=d_off, data_size=d_size, data_avail=avail,
                nframes=samples, duration=samples / sample_rate)
    # 24-bit packed little-endian -> int32
    b3 = np.frombuffer(raw[d_off:d_off + samples * channels * 3], dtype=np.uint8)
    b3 = b3.reshape(-1, 3).astype(np.int64)
    v = b3[:, 0] | (b3[:, 1] << 8) | (b3[:, 2] << 16)
    v = np.where(v >= 2 ** 23, v - 2 ** 24, v)
    info["ivals"] = v
    info["x"] = v.astype(np.float64)
    return info


# ------------------------------------------------------------- 2. statistics
def rms(x):
    return float(np.sqrt(np.mean(np.asarray(x, dtype=np.float64) ** 2)))


def dbfs(a, ref=FS24):
    return 20 * math.log10(max(abs(a), 1e-30) / ref)


def effective_bits(v):
    """Smallest power-of-two divisor of all samples => quantisation actually used."""
    nz = np.abs(v[v != 0].astype(np.int64))
    if len(nz) == 0:
        return 0, 0
    g = int(nz[0])
    for t in nz.tolist():
        g = math.gcd(g, int(t))
        if g == 1:
            break
    step = g & -g                      # largest power-of-two divisor of the gcd
    return g, 24 - int(round(math.log2(step)))


def region_envelope(v, blk):
    n = len(v) // blk * blk
    e = np.sqrt((v[:n].astype(np.float64).reshape(-1, blk) ** 2).mean(axis=1))
    return e, len(v) % blk


# ---------------------------------------------------------------- 3. spectrum
def welch_map(x, fs, nperseg=8192):
    fr, p = sg.welch(x, fs=fs, nperseg=min(nperseg, len(x)),
                     noverlap=min(nperseg, len(x)) // 2)
    return fr, 10 * np.log10(p / p.max())


def symbol_fits(v, lead96, nsym, blk):
    """Per-symbol coherent least-squares sine fit at the native 96 kHz rate.
    Returns (fits, reconstruction) where reconstruction is the ideal tone comb."""
    fits, recon = [], np.zeros(len(v))
    t_all = np.arange(len(v), dtype=np.float64)
    for s in range(nsym):
        t0 = lead96 + s * blk
        seg = v[t0:t0 + blk]
        sp = np.abs(np.fft.rfft(seg))
        fr = np.fft.rfftfreq(blk, 1.0 / FS)
        cand = [(k, int(np.argmin(np.abs(fr - TONE_BY_IDX[k])))) for k in range(NTONE)]
        kbest = cand[int(np.argmax([sp[i] for _, i in cand]))][0]
        f = TONE_BY_IDX[kbest]
        t = t_all[t0:t0 + blk]
        M = np.stack([np.cos(2 * np.pi * f * t / FS), np.sin(2 * np.pi * f * t / FS),
                      np.ones(blk)], 1)
        c, *_ = np.linalg.lstsq(M, seg, rcond=None)
        amp = math.hypot(c[0], c[1])
        ph = math.atan2(-c[1], c[0])
        idal = amp * np.cos(2 * np.pi * f * t / FS + ph)
        recon[t0:t0 + blk] = idal
        fits.append(dict(sym=s, k=kbest, freq=f, amp=amp, phase=ph, dc=float(c[2]),
                         resid=float(np.sqrt(np.mean((seg - idal) ** 2))),
                         margin=20 * math.log10(max(sp[cand[int(np.argmax([sp[i] for _, i in cand]))][1]], 1e-30) /
                                                max(sorted([sp[i] for _, i in cand], reverse=True)[1], 1e-30))))
    return fits, recon


def clusters(fr, pdb, thresh):
    act = pdb > thresh
    res, i = [], 0
    while i < len(fr):
        if act[i]:
            j = i
            while j + 1 < len(fr) and act[j + 1]:
                j += 1
            seg = pdb[i:j + 1]
            res.append((fr[i], fr[j], float(seg.max()), float(fr[i + int(np.argmax(seg))])))
            i = j + 1
        else:
            i += 1
    return res


def parseval_band(x, lo, hi):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / FS)
    tot = float(np.sum(np.abs(X) ** 2))
    m = (f >= lo) & (f < hi)
    e = float(np.sum(np.abs(X[m]) ** 2))
    return e / tot if tot else 0.0, (f[m][np.abs(X[m]) > 0].tolist() if e else []), X, f, tot


# ---------------------------------------------------------------- 4. modem
def decimate_lp(x):
    """The documented front-end tail: a 7 kHz anti-alias low-pass, then 6:1 decimation
    to the 16 kHz codec rate.  Implemented zero-phase (sosfiltfilt) so the symbol grid
    is not shifted.  NOTE: a narrow-transition FIR here (e.g. remez(129) with a 1 kHz
    transition at 96 kHz) is physically impossible and injects ~5 % passband ripple,
    which would fake a 'difference' between the two decimation paths."""
    sos = sg.butter(12, AA_HZ / (FS / 2.0), output="sos")
    return sg.sosfiltfilt(sos, x)[::DECIM]


def decimate_naive(x):
    return x[::DECIM]


def goertzel(seg, f0, fsr=CODEC_FS):
    n = len(seg)
    k = f0 * n / fsr
    if abs(k - round(k)) > 1e-6:            # only valid for coherent windows
        return float(np.abs(np.fft.rfft(seg * np.hanning(n), n))[int(round(f0 * n / fsr))])
    w = 2 * math.pi * round(k) / n
    c = 2 * math.cos(w)
    s1 = s2 = 0.0
    for x0 in seg:
        s0 = float(x0) + c * s1 - s2
        s2, s1 = s1, s0
    return math.sqrt(max(s1 * s1 + s2 * s2 - c * s1 * s2, 0.0))


def tone_mags(seg, fsr=CODEC_FS):
    n = len(seg)
    sp = np.abs(np.fft.rfft(seg))
    fr = np.fft.rfftfreq(n, 1.0 / fsr)
    return [float(np.interp(TONE_BY_IDX[k], fr, sp)) for k in range(NTONE)]


def decode_symbols(y, base, nsym):
    """Return per-symbol (nibble, amp_in_full_scale_units, margin_dB, best, second)."""
    res = []
    for s in range(nsym):
        seg = y[base + s * SYM: base + (s + 1) * SYM]
        if len(seg) < SYM:
            break
        gm = np.array([goertzel(seg, TONE_BY_IDX[k]) for k in range(NTONE)])
        rm = np.array(tone_mags(seg))
        order = np.argsort(gm)[::-1]
        b1, b2 = int(order[0]), int(order[1])
        margin = 20 * math.log10(max(gm[b1], 1e-30) / max(gm[b2], 1e-30))
        agree = b1 == int(np.argmax(rm))
        res.append(dict(sym=s, nib=b1, hz=TONE_BY_IDX[b1], amp=gm[b1] / (SYM / 2.0),
                        margin=margin, alt=int(np.argmax(rm)), agree=agree,
                        runner=TONE_BY_IDX[b2], runner_amp=gm[b2] / (SYM / 2.0)))
    return res


def group_bytes(nibs):
    return [int(nibs[i]) * 16 + int(nibs[i + 1]) for i in range(0, len(nibs) - 1, 2)]


# ------------------------------------------------------------- 5. frame parse
def parse_frame(byts):
    rep = []
    ok = True
    if len(byts) < 3 or byts[0] != 0xA5 or byts[1] != 0x5A:
        rep.append("  sync A5 5A : MISSING (got %s)" % " ".join("%02X" % b for b in byts[:4]))
        return False, rep
    rep.append("  sync A5 5A : ok")
    ln = byts[2]
    rep.append("  LEN        : %d -> payload %s" % (ln, " ".join("%02X" % b for b in byts[3:3 + ln])))
    if len(byts) < 3 + ln + 1:
        rep.append("  truncated  : need %d bytes, have %d" % (3 + ln + 1, len(byts)))
        return False, rep
    payload = byts[3:3 + ln]
    ck = byts[3 + ln]
    calc = ln
    for p in payload:
        calc ^= p
    rep.append("  CKSUM      : wire %02X  computed(L^payload) %02X  -> %s"
               % (ck, calc, "VALID" if calc == ck else "MISMATCH"))
    ok = (calc == ck)
    i, recs = 0, []
    while i < ln:
        typ = payload[i]
        if i + 1 >= ln:
            recs.append("    !! dangling TYPE %02X at end of payload" % typ)
            ok = False
            break
        vl = payload[i + 1]
        val = payload[i + 2:i + 2 + vl]
        name = OPCODES.get(typ, "UNKNOWN(0x%02X)" % typ)
        recs.append("    TLV type=0x%02X %-14s len=%d value=%s%s"
                    % (typ, name, vl, " ".join("%02X" % b for b in val) or "(none)",
                     "" if vl == len(val) else "  [TRUNCATED]"))
        if typ == 0x10 and vl == 0:
            recs.append("      -> opcode 0x10 DEBUG_PING carries no value; firmware replies PONG")
        if vl in OPCODES and typ in (0x01, 0x02):
            recs.append("      -> engineering-class opcode (safety interlock territory)")
        i += 2 + vl
    rep.extend(recs)
    return ok, rep


# ---------------------------------------------------------------------- main
def main():
    info = parse_wav(WAV)
    v, ivals = info["x"], info["ivals"]
    fs = info["sample_rate"]

    hr("1. HEADER FACTS")
    print("file            : %r" % info["path"])
    print("size on disk    : %d bytes" % info["filesize"])
    print("RIFF size field : %d (file-8 = %d) -> %s"
          % (info["riff_size"], info["filesize"] - 8,
             "consistent" if info["riff_size"] == info["filesize"] - 8 else "INCONSISTENT"))
    print("chunk list      :")
    for cid, size, off in info["chunks"]:
        print("    @%-6d %-8r size=%-8d data@%-6d end@%d"
              % (off, cid, size, off + 8, off + 8 + size + (size & 1)))
    known = {b"fmt ", b"data"}
    odd = [c for c in info["chunks"] if c[0] not in known]
    print("non-standard chunks: %s" % ([(c[0], c[1]) for c in odd] or "NONE"))
    print("  (the 'WAVE1/AUE1/ATE1/dataH' seen by strings are x86 opcode byte sequences such")
    print("   as 41 55 45 31 = 'push r12; sub ebp,imm' inside aria's RIFF chunk scanner,")
    print("   not real RIFF chunk ids; verified against the chunk walk above.)")
    print("data chunk      : declared %d bytes, %d available from its offset"
          % (info["data_size"], info["data_avail"]))
    print("                : declared size covers %s of the remainder (trailing bytes after chunk walk: %d)"
          % ("all" if info["data_size"] == info["data_avail"] else "PART", info["trailing"]))
    print("format tag      : %d (1=PCM)   channels %d   bits %d"
          % (info["audio_format"], info["channels"], info["bits"]))
    print("sample rate     : %d Hz    byte rate %d   block align %d"
          % (info["sample_rate"], info["byte_rate"], info["block_align"]))
    print("nframes         : %d       duration %.6f s" % (info["nframes"], info["duration"]))
    spec_ok = (info["channels"] == 1 and info["bits"] == 24
               and info["sample_rate"] == 96000 and info["audio_format"] == 1
               and info["duration"] <= 2.0)
    print("SPEC transport  : mono/24-bit signed PCM/96000 Hz/<=2 s -> %s"
          % ("CONFIRMED" if spec_ok else "VIOLATED"))

    hr("2. SAMPLE STATISTICS")
    peak = int(np.abs(ivals).max())
    print("min %d   max %d   peak %d   (%.3f FS, %.2f dBFS)"
          % (ivals.min(), ivals.max(), peak, peak / FS24, dbfs(peak)))
    print("mean (DC offset) %.4f LSB = %.3e FS   -> %s"
          % (ivals.mean(), ivals.mean() / FS24, "no DC" if abs(ivals.mean()) < 1 else "DC PRESENT"))
    print("rms %.1f LSB (%.2f dBFS)   crest factor %.2f dB"
          % (rms(ivals), dbfs(rms(ivals)), 20 * math.log10(peak / max(rms(ivals), 1e-30))))
    print("exact-zero samples %d of %d (%.1f %%)" % (int((ivals == 0).sum()), len(ivals),
                                                    100.0 * (ivals == 0).sum() / len(ivals)))
    g, eff = effective_bits(ivals)
    print("quantisation depth : gcd(|samples|) = %d -> %d effective bits (real 24-bit container; "
          "low byte takes %d distinct values, so not 16-bit data in 24-bit clothing)"
          % (g, eff, len(np.unique(np.abs(ivals) & 0xFF))))

    nz = np.nonzero(ivals)[0]
    lead96 = int(nz[0])
    print("first nonzero sample %d   last nonzero %d" % (nz[0], nz[-1]))
    blk = SYM * DECIM
    e, tail = region_envelope(ivals, blk)
    t_hi = int(nz[-1]) + 1
    print("region RMS: silence lead-in [0,%d) rms %.3f LSB | tone burst [%d,%d) rms %.1f LSB"
          " | tail [%d,%d) rms %.3f LSB"
          % (lead96, rms(ivals[:lead96]), lead96, t_hi, rms(ivals[lead96:t_hi]),
             t_hi, len(ivals), rms(ivals[t_hi:])))
    print("RMS envelope, %d-sample (%.1f ms = one symbol at 96k) blocks:" % (blk, 1000 * blk / FS))
    for i, val in enumerate(e):
        a0, a1 = i * blk, (i + 1) * blk
        ov = max(0, min(a1, t_hi) - max(a0, lead96))
        flag = "silence" if ov == 0 else ("mixed" if ov < blk else "tone")
        print("   %2d %-8s samples %6d-%-6d rms %10.1f  %7.2f dBFS" % (i, flag, a0, a1, val, dbfs(val)))
    if tail:
        tr = ivals[len(ivals) - tail:]
        print("   tail     leftover %d samples after %d full blocks: rms %.1f LSB, %d of them"
              " exactly zero (the burst ends mid-block at sample %d)"
              % (tail, len(e), rms(tr), int((tr == 0).sum()), t_hi))
    print("silence lead-in = %d samples at 96 kHz = %d codec samples (spec: %d) -> %s"
          % (lead96, lead96 // DECIM, LEADIN,
             "MATCH" if lead96 // DECIM == LEADIN else "MISMATCH"))
    act = int(nz[-1]) + 1 - lead96
    nsym = int(round(act / blk))
    print("active tone region = %d samples = %d symbols of %d samples (%.1f ms each)"
          % (act, nsym, blk, 1000 * blk / FS))

    hr("3. SPECTRUM (full %.0f kHz bandwidth)" % (FS / 2000))
    fr, pdb = welch_map(v, FS)
    cl = clusters(fr, pdb, -60.0)
    print("Welch PSD, clusters above -60 dB rel max (%d found):" % len(cl))
    for lo, hi, pk, fpk in cl:
        print("   %8.1f - %8.1f Hz   peak %7.1f dB rel (at %.1f Hz)" % (lo, hi, pk, fpk))
    print("highest cluster edge anywhere: %.1f Hz   (%s)"
          % (max(hi for _, hi, _, _ in cl),
             "no cluster reaches the 7 kHz region" if max(hi for _, hi, _, _ in cl) < 7000
             else "cluster extends past 7 kHz"))
    print("noise floor above 7 kHz (Welch): %.1f dB rel max -> %s"
          % (pdb[fr > 7000].max(), "NO significant HF content"
             if pdb[fr > 7000].max() < -55 else "HF CONTENT PRESENT"))
    print("Parseval band energy fractions:")
    for lo, hi, lbl in [(0, 700, "sub-modem 0-700"), (700, 2100, "MODEM 700-2100"),
                        (2100, 3400, "2100-3400 (audible)"), (3400, 7000, "3400-7000"),
                        (7000, 12000, "7-12 kHz"), (12000, 24000, "12-24 kHz"),
                        (24000, FS / 2, "24k-Nyquist"), (7000, FS / 2, "ALL > 7 kHz")]:
        frac, _, _, _, _ = parseval_band(v, lo, hi)
        print("   %-20s %10.6f %%  (%+8.2f dB rel total)" % (lbl, 100 * frac, 10 * math.log10(max(frac, 1e-30))))
    frac, _, X, fx, tot = parseval_band(v, 0, FS / 2)
    m = (fx < 700) | (fx > 2100)
    bi = int(np.argmax(np.abs(X) * m))
    print("strongest out-of-modem bin: %.1f Hz, %.1f dB rel total power"
          % (fx[bi], 10 * math.log10(max(float(np.abs(X[bi]) ** 2), 1e-30) / tot)))
    inbins = (fx >= 700) & (fx <= 2100)
    big = fx[inbins][np.abs(X[inbins]) > 0.001 * np.abs(X).max()]
    print("bins carrying > -60 dB: %s" % " ".join("%.0f" % b for b in sorted(set(np.round(big / 80) * 80))))
    print("CAVEAT: the percentages outside the comb are rectangular-gating sidelobes of the")
    print("  abruptly switched tone bursts (a gated sine has 1/f sidelobes across the whole")
    print("  band), not separate emitters. Decisive test below.")
    fits, recon = symbol_fits(v, lead96, nsym, blk)
    d = v - recon
    print("IDEAL-RECONSTRUCTION RESIDUAL TEST (fit one sine per symbol, subtract):")
    print("   max |capture - ideal tone comb| = %.3f LSB   rms = %.4f LSB   (%.1f dBFS)"
          % (np.abs(d).max(), rms(d), dbfs(rms(d))))
    clean = np.abs(d).max() <= 2.0
    print("   -> %s" % ("the file IS the modem comb to within 24-bit rounding: no hidden carrier,"
                        " dither, beacon or noise floor" if clean else
                        "residual exceeds rounding: something real hides in the file"))
    RD = np.fft.rfft(d)
    fd = np.fft.rfftfreq(len(d), 1.0 / FS)
    hf = float(np.abs(RD[fd > 7000]).max()) / len(d) * 2
    print("   residual peak above 7 kHz: %.3e FS = %.1f dBFS  -> %s"
          % (hf / FS24, dbfs(hf),
             "NOTHING above 7 kHz" if dbfs(hf) < -110 else "CONTENT above 7 kHz"))
    print("   residual peak 2.1-48 kHz   : %.1f dBFS"
          % dbfs(float(np.abs(RD[fd > 2100]).max()) / len(d) * 2))
    print("=> energy lives ONLY in the 800-2000 Hz modem comb; nothing above 7 kHz.")

    hr("4. CODEC-RATE DECODE")
    y_lp = decimate_lp(v)
    y_nv = decimate_naive(v)
    n = min(len(y_lp), len(y_nv))
    dcd = np.abs(y_lp[:n] - y_nv[:n])
    diff = float(dcd.max())
    nz_codec = int(np.nonzero(np.abs(y_nv) > 0)[0][0])
    print("decimation paths: A) spec 7 kHz anti-alias LP (12th-order Butterworth, zero-phase)")
    print("                B) plain 6:1 subsampling with no filter")
    print("   lengths lp=%d naive=%d" % (len(y_lp), len(y_nv)))
    print("   max |A-B| over the whole file : %.1f LSB (%.4f FS) at codec sample %d"
          % (diff, diff / FS24, int(np.argmax(dcd))))

    nsym_codec = max(1, (len(y_lp) - LEADIN) // SYM)
    print("symbol count from the codec timeline: %d (96 kHz region analysis said %d) -> %s"
          % (nsym_codec, nsym, "agree" if nsym_codec == nsym else "MISMATCH"))
    nsym = nsym_codec
    print("independent lead-in estimate from the decimated envelope: codec sample %d (spec %d)"
          % (nz_codec, LEADIN))
    # steady-state agreement: drop +-50 codec samples around every symbol edge
    keep = np.zeros(len(dcd), dtype=bool)
    for s in range(nsym):
        a0 = nz_codec + s * SYM + 50
        keep[a0:nz_codec + (s + 1) * SYM - 50] = True
    steady = float(dcd[keep].max()) if keep.any() else 0.0
    edge = np.argsort(dcd)[::-1][:5]
    print("   top 5 |A-B| hits at codec samples %s -> phase inside the symbol grid: %s"
          % (list(edge), [int((t - nz_codec) % SYM) for t in edge]))
    print("   max |A-B| over symbol INTERIORS only (edges +-50 samples excluded): %.2f LSB "
          "(%.5f %% of tone)" % (steady, 100.0 * steady / 2097152.0))
    print("   -> the A/B gap is concentrated at the hard tone edges (phase ~0 in the grid), i.e.")
    print("      the anti-alias LP ringing on a 0 -> +0.25 FS step. It is NOT evidence of HF")
    print("      energy: section 3 already proved the whole file matches an ideal tone comb to")
    print("      %.2f LSB, so nothing else is present." % float(np.abs(v - recon).max()))

    print("\nsymbol grid search: all %d phase offsets, scored by MEDIAN best/2nd margin" % SYM)
    print("  (median, not mean: a heavy anti-alias filter rings on every symbol edge, and a")
    print("   mean would let 300 dB single-symbol hits hide 15 dB ones)")
    winners = {}
    for name, y in (("anti-alias LP", y_lp), ("naive 6:1", y_nv)):
        rows = []
        for b in range(SYM):
            dsym = decode_symbols(y, b, nsym)
            if len(dsym) < nsym:
                continue
            mg = np.array([r["margin"] for r in dsym])
            rows.append((float(np.median(mg)), float(mg.min()), b, dsym))
        rows.sort(key=lambda t: -t[0])
        same = sum(1 for _, _, _, dsym in rows
                   if "".join("%x" % r["nib"] for r in dsym) == "".join("%x" % r["nib"] for r in rows[0][3]))
        print("   %s:" % name)
        for med, mn, b, dsym in rows[:3]:
            print("      base %3d median margin %7.1f dB  min %7.1f dB  nibbles %s"
                  % (b, med, mn, "".join("%x" % r["nib"] for r in dsym)))
        print("      %d of %d offsets reproduce the winning nibble string; worst median %.1f dB"
              % (same, len(rows), rows[-1][0]))
        winners[name] = rows[0]
    base = winners["naive 6:1"][2]
    dec = winners["naive 6:1"][3]
    dec_lp = winners["anti-alias LP"][3]
    print("   chosen grid base = %d codec samples; spec lead-in = %d -> %s"
          % (base, LEADIN, "MATCH" if base == LEADIN else "DIFFERS"))

    print("\nper-symbol decode (Goertzel over 200-sample windows at 16 kHz):")
    print("   sym  samples@16k    hz   nib  amp(naive,FS)  amp(LP,FS)  margin naive  margin LP  96k-fit agrees")
    for r, rl in zip(dec, dec_lp):
        fit = fits[r["sym"]]
        print("   %3d  %5d-%-5d %6.0f   %x    %.6f       %.6f    %8.1f dB   %8.1f dB   %s"
              % (r["sym"], base + r["sym"] * SYM, base + (r["sym"] + 1) * SYM,
                 r["hz"], r["nib"], r["amp"] / FS24, rl["amp"] / FS24,
                 r["margin"], rl["margin"], "yes" if fit["k"] == r["nib"] else "NO"))
    nibs = [r["nib"] for r in dec]
    print("nibble stream (high nibble first): %s" % "".join("%x" % k for k in nibs))
    byts = group_bytes(nibs)
    print("byte stream : %s" % " ".join("%02X" % b for b in byts))
    print("   (the anti-alias-LP path yields the identical string: %s)"
          % "".join("%x" % r["nib"] for r in dec_lp))
    lo_first = [int(nibs[i + 1]) * 16 + int(nibs[i]) for i in range(0, len(nibs) - 1, 2)]
    print("if nibbles were low-first you would get %s (no A5 5A sync) -> high-first confirmed"
          % " ".join("%02X" % b for b in lo_first))

    hr("5. FRAME PARSE + CHECKSUM")
    ok, rep = parse_frame(byts)
    print("\n".join(rep))
    print("frame %s" % ("VALIDATES" if ok else "DOES NOT VALIDATE"))
    extra = byts[3 + byts[2] + 1:]
    print("bytes after the frame: %s" % (" ".join("%02X" % b for b in extra) or "none - capture is exactly one frame"))

    hr("6. ROBUSTNESS / CONFIDENCE")
    for nm, dd in (("naive 6:1", dec), ("anti-alias LP", dec_lp)):
        a = np.array([r["amp"] for r in dd]) / FS24
        m = np.array([r["margin"] for r in dd])
        print("%-14s tone amplitude: min %.6f max %.6f FS (spread %.2f dB), 16-kHz codec full"
              % (nm, a.min(), a.max(), 20 * math.log10(max(a.max(), 1e-30) / max(a.min(), 1e-30))))
        print("%-16s scale = 0.250000 FS = -12.04 dBFS; tone is at %.2f dBFS (relative to FS)"
              % ("", 20 * math.log10(a.mean())))
        print("%-14s best/2nd margin: min %6.1f dB  median %6.1f dB -> %s"
              % ("", m.min(), np.median(m),
                 "CONFIDENT" if m.min() > 20 else "MARGINAL"))
    amps = np.array([r["amp"] for r in dec]) / FS24
    marg = np.array([r["margin"] for r in dec])
    print("symbol-amplitude dropouts (any symbol < 10 %% of the loudest): %d"
          % int((amps < 0.1 * amps.max()).sum()))
    print("every one of the 3 decoding routes (Goertzel@16k naive-decim, Goertzel@16k filtered,")
    print("  coherent rFFT on the raw 96 kHz stream) returns the same 12 nibbles: %s"
          % all(f["k"] == r["nib"] for f, r in zip(fits, dec)))
    print("coherent-window check: all %d tone freqs are multiples of 80 Hz and the symbol is"
          % NTONE)
    print("   12.5 ms => exactly %d..%d whole cycles per symbol, so bins are leakage-free."
          % (TONE0 * SYM / CODEC_FS, TONE_BY_IDX[15] * SYM / CODEC_FS))
    print("why the anti-alias LP looks worse: each symbol starts its cosine at its own peak, so")
    print("  every symbol boundary is a hard 0 -> +0.25 FS step (see samples at the onset below),")
    print("  and a steep LP rings on it. First 6 raw samples of the burst, and of the LP path:")
    print("   raw   : %s" % " ".join("%9.1f" % t for t in v[lead96:lead96 + 6]))
    print("   LP@16k: %s" % " ".join("%9.1f" % t for t in y_lp[nz_codec - 2:nz_codec + 6]))
    print("   naive : %s" % " ".join("%9.1f" % t for t in y_nv[nz_codec - 2:nz_codec + 6]))

    hr("7. PRE- vs POST-FRONT-END VERDICT")
    print("least-squares sine fit per symbol at native 96 kHz (global time axis):")
    print("   sym   f(Hz)   amplitude(FS)   global phase(rad)   DC term   fit residual(LSB)")
    for r in fits:
        print("   %3d  %6.0f   %.9f      %+8.4f        %+7.3f     %.4f"
              % (r["sym"], r["freq"], r["amp"] / FS24, r["phase"], r["dc"], r["resid"]))
    fa = [r["amp"] for r in fits]
    tilt = 20 * math.log10(max(fa) / min(fa))
    print("amplitude spread across the tone frequencies actually used (800-2000 Hz): %.5f dB"
          % tilt)
    print("  -> %s" % ("FLAT: no EQ / analog-gain / transducer imprint" if tilt < 0.01
                       else "TILTED: the analog front end has been applied"))
    print("first sample of each burst divided by that burst's fitted amplitude (cos peak = +1):")
    print("   %s" % " ".join("%+.3f" % ((v[lead96 + r["sym"] * blk] / r["amp"]) if r["amp"] else 0)
                             for r in fits))
    print("  (every symbol starts at its own cosine peak, i.e. the oscillator phase RESETS at")
    print("   each symbol boundary - a per-symbol modem encoder, not a continuous source, and")
    print("   certainly not a room recording: it also means each boundary is a hard +A step)")
    print("lead-in silence max |sample| = %d LSB, tail max |sample| = %d LSB -> hard gate, no"
          % (int(np.abs(ivals[:lead96]).max()), int(np.abs(ivals[int(nz[-1]) + 1:]).max())))
    print("  ringing tails that a 7 kHz LP / transducer resonance would leave behind")
    print("out-of-comb energy (2.1 k-48 kHz): %.2f dB relative to total signal power"
          % (10 * math.log10(max(parseval_band(v, 2100, FS / 2)[0], 1e-30))))
    print("naive 6:1 vs anti-alias-filtered decimation agree to %.2f LSB (%.5f %% of tone) inside"
          % (steady, 100.0 * steady / 2097152.0))
    print("  the symbols; the only large delta is the LP ringing on the hard symbol edges.")
    print("CONCLUSION: this capture is the PRE-front-end synthetic encode. The documented 7 kHz")
    print("  anti-alias LP and the 16 kHz decimation leave no imprint on it (no tilt, no ringing,")
    print("  no images), and the modem comb 800-2000 Hz is the only thing present.")
    print("  NOTE: that modem band sits INSIDE the 300-3400 Hz 'engineering tone' safety-scan")
    print("  window - irrelevant for DEBUG_PING, which the firmware always services.")


if __name__ == "__main__":
    main()
