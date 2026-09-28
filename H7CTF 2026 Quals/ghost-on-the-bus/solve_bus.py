#!/usr/bin/env python
"""Ghost on the Bus (H7TEX hardware) -- recover the NoiseGate provisioning key.

capture.vcd is an 8-channel logic capture of the board booting:
  UART_TX, SCL, SDA, SPI_CLK, SPI_MOSI, SPI_MISO, SPI_CS, AUX

The UART console log states the recipe, the buses carry the operands:
  [prov]   part A <- SPI flash READ(0x03) @ 0x001A00, 43 bytes
  [prov]   part B <- I2C EEPROM 0x50 (read), 43 bytes
  [prov]   provisioning_key = part_A XOR part_B

Bit timing is measured from the file: UART 8500 ns/bit (2 MHz logic, 17 samples),
I2C SCL 80 kHz, SPI 500 kHz CPOL=0 (idle low) sampled on the rising edge, CS low
for one 376-clock transaction.

usage: python solve_bus.py [capture.vcd]
"""
import collections
import re
import sys

VCD = sys.argv[1] if len(sys.argv) > 1 else "files/capture.vcd"
UART_BIT = 8500
FLAG_RE = re.compile(rb"H7CTF\{[^{}]*\}")

ids, ev, TEND = {}, collections.defaultdict(list), 0
for line in open(VCD):
    line = line.strip()
    if not line:
        continue
    if line.startswith("#"):
        TEND = int(line[1:])
    elif line.startswith("$var"):
        p = line.split()
        ids[p[3]] = p[4]
    elif line[0] in "01":
        ev[line[1:]].append((TEND, line[0]))
CH = {name: sym for sym, name in ids.items()}


def level(sym, t):
    """Value of `sym` at time t (last change at or before t)."""
    v = "1"
    for tt, val in ev[sym]:
        if tt <= t:
            v = val
        else:
            break
    return v


def uart_tx(name="UART_TX", bit=UART_BIT):
    s = CH[name]
    e = ev[s]
    out, i = [], 0
    while i < len(e):
        if e[i][1] == "0" and (i == 0 or e[i - 1][1] == "1"):
            st = e[i][0]
            val = 0
            for b in range(8):
                val |= (1 if level(s, st + bit * (1.5 + b)) == "1" else 0) << b
            stop_ok = level(s, st + bit * 9.5) == "1"
            out.append((val, stop_ok, st))
            fe = st + bit * 10
            while i < len(e) and e[i][0] < fe:
                i += 1
            continue
        i += 1
    return out


def i2c_transfers(scl="SCL", sda="SDA"):
    S, D = CH[scl], CH[sda]
    # START / STOP: SDA moves while SCL is held high (t==0 is the VCD init, skip it)
    conds = [(t, 0, "START" if v == "0" else "STOP", None)
             for t, v in ev[D] if t > 0 and level(S, t - 1) == "1"]
    # one data bit per SCL rising edge, SDA sampled just after the edge
    samples = [(t, 1, "BIT", 1 if level(D, t + 300) == "1" else 0)
               for t, v in ev[S] if v == "1" and t > 0]     # t==0 is the VCD init
    seq = sorted(conds + samples)
    groups, frame = [], None
    for t, _rank, kind, payload in seq:
        if kind == "START":
            if frame and frame["bits"]:
                groups.append(frame)
            frame = {"bits": [], "start": t, "stop": None}
        elif kind == "STOP":
            if frame is not None:
                frame["stop"] = t
                if frame["bits"]:
                    groups.append(frame)
                    frame = None
        elif frame is not None:
            frame["bits"].append(payload)
        else:
            frame = {"bits": [payload], "start": None, "stop": None}
    if frame and frame["bits"]:
        groups.append(frame)
    for g in groups:
        bs, g["bytes"] = g["bits"], []
        for i in range(0, len(bs) - 8, 9):
            g["bytes"].append((int("".join(map(str, bs[i:i + 8])), 2), bs[i + 8]))
    return groups


def spi_transaction(cs="SPI_CS", clk="SPI_CLK", mosi="SPI_MOSI", miso="SPI_MISO"):
    CS, CK, MO, MI = CH[cs], CH[clk], CH[mosi], CH[miso]
    e = ev[CS]
    win = None
    for i in range(len(e) - 1):
        if e[i][1] == "0":
            win = (e[i][0], e[i + 1][0])
    edges = [(t, v) for t, v in ev[CK] if win[0] <= t <= win[1] and v == "1"]

    def grab(sym):
        b = [level(sym, t + 60) for t, _ in edges]
        return bytes(int("".join(b[i:i + 8]), 2) for i in range(0, len(b) - 7, 8))

    return win, len(edges), grab(MO), grab(MI)


def main():
    print("=== UART_TX  (%d bitsamples) ===" % UART_BIT)
    chars = uart_tx()
    bad = [c for c in chars if not c[1]]
    log = bytes(c[0] for c in chars)
    sys.stdout.write(log.decode("latin-1"))
    print("[*] %d characters, %d with a bad stop bit" % (len(chars), len(bad)))

    print("\n=== SPI flash ===")
    win, nclk, mo, mi = spi_transaction()
    print("[*] CS low %d..%d ns, %d clocks -> %d bytes out / %d bytes in"
          % (win[0], win[1], nclk, len(mo), len(mi)))
    print("[*] MOSI: %s   (opcode 0x03 = READ, addr %s)" % (mo[:4].hex(), mo[1:4].hex()))
    part_a = mi[4:]
    print("[*] part A (%d bytes) = %s" % (len(part_a), part_a.hex()))

    print("\n=== I2C ===")
    part_b = None
    for g in i2c_transfers():
        bs = g["bytes"]
        if not bs:
            continue
        print("[*] frame t=%s..%s  %d bytes: %s"
              % (g["start"], g["stop"], len(bs), " ".join(
                  "%02x%s" % (v, " ACK" if a == 0 else " NACK") for v, a in bs)))
        slave, rw = bs[0][0] >> 1, bs[0][0] & 1
        print("[*] slave 0x%02x %s -> %d data bytes" % (slave, "read" if rw else "write", len(bs) - 1))
        if slave == 0x50 and rw == 1:
            part_b = bytes(v for v, _ in bs[1:])
            print("[*] part B (%d bytes) = %s" % (len(part_b), part_b.hex()))
    if part_b is None:
        sys.exit("[-] no I2C read frame from EEPROM 0x50")

    if len(part_a) != len(part_b):
        sys.exit("[-] part lengths differ: %d vs %d" % (len(part_a), len(part_b)))
    key = bytes(x ^ y for x, y in zip(part_a, part_b))
    print("\n=== provisioning_key = part_A XOR part_B ===")
    print("[*] %r" % key)
    m = FLAG_RE.search(key)
    if not m:
        sys.exit("[-] no H7CTF{...} in the XOR result")
    print("[+] FLAG: %s" % m.group().decode())
    open("flag.txt", "wb").write(m.group())


if __name__ == "__main__":
    main()
