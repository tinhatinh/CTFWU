#!/usr/bin/env python
"""Ghost on the Bus: decode the 8-channel NoiseGate boot capture (capture.vcd).

Channels: UART_TX, SCL/SDA (I2C), SPI_CLK/MOSI/MISO/CS, AUX.
Bit rates are measured from the file, not assumed:
  UART  bit = 8500 ns   (2 MHz logic -> 17 samples/bit)
  I2C   SCL period = 12500 ns (80 kHz)
  SPI   CLK period = 2000 ns (500 kHz), CPOL=0 (idle low), CS active low
"""
import collections
import sys

VCD = sys.argv[1] if len(sys.argv) > 1 else "files/capture.vcd"


def load(path):
    ids, ev, t = {}, collections.defaultdict(list), 0
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            t = int(line[1:])
        elif line.startswith("$var"):
            p = line.split()
            ids[p[3]] = p[4]
        elif line[0] in "01":
            ev[line[1:]].append((t, line[0]))
    return ids, ev, t


ids, ev, TEND = load(VCD)
CH = {name: sym for sym, name in ids.items()}


def level(sym, tt, at_or_before=True):
    v = "1"
    for t, val in ev[sym]:
        if (t <= tt) if at_or_before else (t < tt):
            v = val
        else:
            break
    return v


# ---------------------------------------------------------------- UART
def uart(sym, bit=8500, nbits=8, stop=1):
    e = ev[sym]
    out, i, spans = [], 0, []
    while i < len(e):
        if e[i][1] == "0" and (i == 0 or e[i - 1][1] == "1"):
            st = e[i][0]
            if st + bit * (nbits + 1) > TEND:
                break
            val = 0
            for b in range(nbits):
                val |= (1 if level(sym, st + bit * (1.5 + b)) == "1" else 0) << b
            stopbit = level(sym, st + bit * (nbits + 0.5))
            out.append(val)
            spans.append((st, st + bit * (nbits + stop)))
            frame_end = st + bit * (nbits + stop)
            while i < len(e) and e[i][0] < frame_end:
                i += 1
            continue
        i += 1
    return out, spans


# ---------------------------------------------------------------- I2C
def i2c(scl, sda):
    S, P = CH[scl], CH[sda]
    # merge edges, walk in time
    edges = sorted([(t, "C", v) for t, v in ev[S]] + [(t, "D", v) for t, v in ev[P]])
    scl_l = level(S, -1)
    sda_l = level(D := P, -1)
    bits, res, trans, cur = [], [], [], []
    last = -10 ** 18
    for t, kind, v in edges:
        if kind == "D":
            if scl_l == "1" and v != sda_l:
                if v == "0":
                    res.append(("START", t))
                    cur = []
                else:
                    res.append(("STOP", t))
                    if len(cur) % 9 == 0:
                        pass
            sda_l = v
        else:
            if v == "1" and sda_l != (level(P, t - 1) if t > last else sda_l):
                pass
            if v == "1" and scl_l == "0":       # rising edge: sample SDA
                bits.append(1 if sda_l == "1" else 0)
                res.append(("SAMP", t))
            scl_l = v
    # simpler and robust: sample SDA a bit after every SCL rising edge
    bits, times = [], []
    for t, v in ev[S]:
        if v == "1":
            bits.append(1 if level(P, t + 300) == "1" else 0)
            times.append(t)
    # conditions
    conds = []
    for t, v in ev[P]:
        if level(S, t - 1) == "1" and level(S, t + 1) == "1":
            conds.append(("START" if v == "0" else "STOP", t))
    return bits, times, conds


def group_i2c(bits, times, conds):
    """Split bitstream into bytes (9 bits incl. ACK), annotating START/STOP."""
    frames, cur, byteidx = [], [], 0
    marks = sorted(conds)
    mi = 0
    seq = []
    for b, t in zip(bits, times):
        while mi < len(marks) and marks[mi][1] < t:
            seq.append(marks[mi])
            mi += 1
        seq.append(("bit", b, t))
    while mi < len(marks):
        seq.append(marks[mi])
        mi += 1
    out, buf, addrmode = [], [], None
    items = [x for x in seq if x[0] in ("START", "STOP")]
    for b, t in zip(bits, times):
        pass
    # walk seq collecting bits between STARTs
    frame = {"bits": [], "start": None, "stop": None}
    res = []
    for entry in seq:
        if entry[0] == "START":
            if frame["bits"]:
                res.append(frame)
            frame = {"bits": [], "start": entry[1], "stop": None}
        elif entry[0] == "STOP":
            frame["stop"] = entry[1]
            if frame["bits"]:
                res.append(frame)
                frame = {"bits": [], "start": None, "stop": None}
        else:
            frame["bits"].append(entry[1])
    if frame["bits"]:
        res.append(frame)
    for fr in res:
        bs = fr["bits"]
        bl = []
        for i in range(0, len(bs) - 8, 9):
            v = 0
            for k in range(8):
                v = (v << 1) | bs[i + k]
            ack = bs[i + 8] if i + 8 < len(bs) else None
            bl.append((v, ack))
        fr["bytes"] = bl
    return res


# ---------------------------------------------------------------- SPI
def spi(cs, clk, mosi, miso, sample_on="rising"):
    CS, CK, MO, MI = CH[cs], CH[clk], CH[mosi], CH[miso]
    # CS windows
    windows = []
    e = ev[CS]
    i = 0
    while i < len(e) - 1:
        if e[i][1] == "0":
            windows.append((e[i][0], e[i + 1][0] if e[i + 1][1] == "1" else TEND))
        i += 1
    res = []
    for lo, hi in windows:
        edges = [(t, v) for t, v in ev[CK] if lo <= t <= hi]
        want = "1" if sample_on == "rising" else "0"
        samp = [t for t, v in edges if v == want]
        m = [int(level(MO, t + 60)) for t in samp]
        mi = [int(level(MI, t + 60)) for t in samp]
        def tobytes(bits):
            return bytes(sum(bits[i:i + 8]) << (7 - k) for i in range(0, len(bits) - 7, 8)
                         for k in [0]) if False else bytes(
                int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits) - 7, 8))
        res.append((lo, hi, len(samp), tobytes(m), tobytes(mi)))
    return res


if __name__ == "__main__":
    print("=== UART_TX @117647 8N1 (bit=8500ns) ===")
    data, spans = uart(CH["UART_TX"])
    txt = bytes(data).decode("latin-1")
    print("bytes=%d" % len(data))
    print(txt)

    print("\n=== I2C ===")
    bits, times, conds = i2c("SCL", "SDA")
    frames = group_i2c(bits, times, conds)
    print("SCL rising samples=%d  conditions=%s" % (len(bits), collections.Counter(c[0] for c in conds)))
    for fr in frames:
        line = "t=%9d  %s" % (fr["start"] or -1,
                              " ".join("%02x%s" % (v, "-" if a == 0 else "+") for v, a in fr["bytes"]))
        print(line, " STOP" if fr["stop"] else "")

    print("\n=== SPI (500 kHz, CPOL=0) ===")
    for son in ("rising", "falling"):
        for lo, hi, n, mo, mi in spi("SPI_CS", "SPI_CLK", "SPI_MOSI", "SPI_MISO", son):
            print(" %s  CS %d..%d ns  clocks=%d" % (son, lo, hi, n))
            print("   MOSI(%d): %s" % (len(mo), mo[:64].hex()))
            print("   MISO(%d): %s" % (len(mi), mi[:64].hex()))
            print("   MISO ascii: %r" % mi[:80])
        break
