#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Latency side-channel measurement against the authorised CTF instance
pwn.h7tex.com:43708  (variable-length "walk" hypothesis).

Pure measurement: we never look at the binary. We only time round trips.

Design notes
------------
* STRICTLY ONE SOCKET at a time (the service is single-connection).
* Timing window = right before sendall() .. immediately after the recv() that
  delivered the terminating '\n' (i.e. "last byte of the reply").  We return
  from the read the instant the newline shows up, so no fixed sleep is ever
  inside the measured window.  Pacing sleeps are applied AFTER the sample is
  taken, so they cannot contaminate the signal.
* Every reply is recorded verbatim (repr), so we can prove whether the server
  ever said something other than 'denied'.
* Connection identity is logged with every sample (instance state is per
  connection: fresh nonce / image / key), so a mid-run reconnect is visible
  and samples stay attributable.

Usage:
    python -u latency.py --smoke     # 3 commands, protocol/latency sanity
    python -u latency.py             # the full measurement series
"""

import ast
import binascii
import os
import random
import re
import socket
import statistics
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HOST = "pwn.h7tex.com"
PORT = 43708
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "latency_results.txt")

READ_TIMEOUT = 12.0        # hard per-read socket timeout (never block forever)
CMD_DEADLINE = 12.0        # wall-clock budget for one command's reply
PACE = 0.42                # nominal round trip; minimum spacing between sends
MAX_TRIES_SAME_CMD = 3     # stop after 3 identical failures on one command

ZERO24 = bytes(24)


# --------------------------------------------------------------------------- #
# transport
# --------------------------------------------------------------------------- #
class Fatal(Exception):
    pass


class Client:
    """One-connection line-protocol client with per-command latency timing."""

    def __init__(self, log, conn_index):
        self.log = log
        self.conn = conn_index
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(READ_TIMEOUT)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.buf = b""
        t0 = time.perf_counter()
        self.sock.connect((HOST, PORT))
        self.log("conn %d: connected to %s:%d in %.3fs" %
                 (conn_index, HOST, PORT, time.perf_counter() - t0))
        self.preamble = self.drain_preamble()

    def _read_line(self, what, wait=None):
        """Read until b'\\n' (returns as soon as the newline lands)."""
        deadline = time.perf_counter() + (CMD_DEADLINE if wait is None else wait)
        while True:
            i = self.buf.find(b"\n")
            if i >= 0:
                line = self.buf[:i]
                self.buf = self.buf[i + 1:]
                return line
            left = deadline - time.perf_counter()
            if left <= 0:
                raise socket.timeout("no newline for %s" % what)
            self.sock.settimeout(min(left, READ_TIMEOUT))
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("EOF from peer during %s (buffered=%r)"
                                      % (what, self.buf[:80]))
            self.buf += chunk

    def drain_preamble(self, quiet=1.5, overall=8.0):
        """Read every line the server pushes at connect, until the line stream
        goes quiet for `quiet` seconds.  Without this the replies are lagged by
        one line and the latency samples would be meaningless (measured on the
        smoke run: every read returned in <100 us because it was serving the
        *previous* command's already-buffered line)."""
        lines = []
        start = time.perf_counter()
        while True:
            left = start + overall - time.perf_counter()
            if left <= 0:
                break
            self.sock.settimeout(min(quiet, left))
            try:
                lines.append(self._read_line("preamble", wait=min(quiet, left))
                             .decode("latin-1"))
            except socket.timeout:
                break
            except (OSError, ConnectionError):
                raise
        if self.buf:
            lines.append("<unterminated:%r>" % self.buf)
            self.buf = b""
        return lines

    def cmd(self, text):
        """Send one command line; return (latency_seconds, reply_repr)."""
        t0 = time.perf_counter()
        self.sock.sendall(text.encode() + b"\n")
        try:
            line = self._read_line(text[:24])
        except (socket.timeout, OSError, ConnectionError):
            # connection state unknown -> caller must reconnect
            raise
        dt = time.perf_counter() - t0
        return dt, line.decode("latin-1")

    def close(self):
        try:
            self.sock.sendall(b"QUIT\n")
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass
        self.log("conn %d: closed" % self.conn)


def is_hex(s, nchars):
    if len(s) != nchars:
        return False
    try:
        binascii.unhexlify(s)
        return True
    except Exception:
        return False


class Harness:
    """Command sender with pacing, retry, reconnect and verbatim logging."""

    def __init__(self, logf):
        self.logf = logf
        self.conn_n = 0
        self.c = None
        self.nonce = None
        self._pace_at = 0.0
        self.samples = []          # dicts: conn,tag,kind,hex,lat,reply
        self.replies = {}          # reply text -> count (all commands)
        self.run_replies = {}      # reply text -> count (RUN only)
        self.reconnects = 0

    def log(self, msg):
        line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
        print(line, flush=True)
        self.logf.write(line + "\n")
        self.logf.flush()

    def connect(self):
        if self.c is not None:
            try:
                self.c.close()
            except Exception:
                pass
        self.conn_n += 1
        self.c = Client(self.log, self.conn_n)
        self.log("conn %d: preamble lines at connect = %r" %
                 (self.conn_n, self.c.preamble))
        self.logf.write("PREAMBLE conn=%d %r\n" % (self.conn_n, self.c.preamble))
        self.logf.flush()
        try:
            self.align()
        except (socket.timeout, OSError, ConnectionError) as e:
            raise Fatal("align failed on conn %d: %s: %r"
                        % (self.conn_n, type(e).__name__, e))

    def ensure(self):
        if self.c is None:
            self.connect()

    def align(self):
        """Alignment oracle: NONCE must answer with exactly 16 hex chars.
        If we are one line behind (server pushed extra lines we have not read)
        we get a stale line; drain and retry.  Returns the nonce."""
        for attempt in range(1, 6):
            dt, reply = self.c.cmd("NONCE")
            if is_hex(reply, 16):
                self.nonce = reply
                self.log("conn %d: ALIGNED on attempt %d  NONCE->%r in %.6fs"
                         % (self.c.conn, attempt, reply, dt))
                self.logf.write("ALIGN conn=%d attempt=%d nonce=%s probe_lat=%.6f\n"
                                % (self.c.conn, attempt, reply, dt))
                self.logf.flush()
                self._pace_at = time.perf_counter() + PACE
                return reply
            self.log("conn %d: alignment attempt %d got %r -> draining"
                     % (self.c.conn, attempt, reply))
            try:
                extra = self.c.drain_preamble(quiet=0.8, overall=3.0)
                self.log("conn %d: drained %r" % (self.c.conn, extra))
            except (socket.timeout, OSError, ConnectionError) as e:
                raise Fatal("alignment drain failed on conn %d: %r" % (self.c.conn, e))
        raise Fatal("could not align request/reply on conn %d" % self.conn_n)

    def next_send_at(self):
        return getattr(self, "_pace_at", 0.0)

    def send(self, text, tag, kind):
        """One measured command.  text is the raw line (no newline)."""
        self.ensure()
        fails = 0
        last_err = None
        while True:
            wait = self.next_send_at() - time.perf_counter()
            if wait > 0:
                time.sleep(wait)
            t_send = time.perf_counter()
            try:
                dt, reply = self.c.cmd(text)
            except (socket.timeout, OSError, ConnectionError) as e:
                fails += 1
                last_err = e
                self.log("FAIL(%d/%d) %s -> %s: %r" %
                         (fails, MAX_TRIES_SAME_CMD, tag, type(e).__name__, e))
                if fails >= MAX_TRIES_SAME_CMD:
                    raise Fatal("stopped: %d identical failures on command %r "
                                "(%r); last tag=%s" %
                                (fails, text[:40], last_err, tag))
                # dead socket -> rebuild, keep the series coherent by tag
                try:
                    self.c.close()
                except Exception:
                    pass
                self.c = None
                self.reconnects += 1
                self.log("reconnecting (attempt %d) ..." % fails)
                time.sleep(2.0)
                self.connect()
                continue
            self._pace_at = t_send + PACE
            self.replies[reply] = self.replies.get(reply, 0) + 1
            if kind == "RUN":
                self.run_replies[reply] = self.run_replies.get(reply, 0) + 1
            # payload only, so the log line never contains a space before `data=`
            if text.startswith("RUN "):
                hexpart = text[4:]
            elif text.startswith("MINT "):
                hexpart = text[5:]
            else:
                hexpart = text
            self.samples.append({
                "conn": self.c.conn, "tag": tag, "kind": kind,
                "hex": hexpart, "lat": dt, "reply": reply,
            })
            n = len(self.samples)
            disp = repr(reply) if len(reply) <= 90 else (
                repr(reply[:60])[:-1] + "+<%d more chars: image hex>" % (len(reply) - 60))
            self.logf.write("SAMPLE n=%d conn=%d kind=%s tag=%s lat=%.6f reply=%s "
                            "data=%s\n"
                            % (n, self.c.conn, kind, tag, dt, disp, hexpart))
            self.logf.flush()
            return dt, reply


# --------------------------------------------------------------------------- #
# input families
# --------------------------------------------------------------------------- #
def hx(b):
    return binascii.hexlify(b).decode()


def build_sweep(rng):
    """(~430) RUN inputs, each (tag_family, bytes24)."""
    items = []
    items.append(("all-zero", bytes(24)))
    items.append(("all-ff", bytes([0xff]) * 24))
    items.append(("all-01", bytes([0x01]) * 24))

    for off in range(24):                       # single 0x01
        b = bytearray(24)
        b[off] = 0x01
        items.append(("one01@%02d" % off, bytes(b)))
    for off in range(24):                       # single 0xff
        b = bytearray(24)
        b[off] = 0xff
        items.append(("oneff@%02d" % off, bytes(b)))

    for v in range(256):                        # constant fills
        items.append(("fill-%02x" % v, bytes([v]) * 24))

    for i in range(100):                        # random
        items.append(("rand-%03d" % i, bytes(rng.randrange(256) for _ in range(24))))

    # record structure: 2-byte LE id + 4 zero bytes + length byte + junk
    for j, (rid, ln) in enumerate([(0, 0), (1, 1), (1, 2), (1, 4), (1, 8), (1, 16),
                                   (2, 3), (2, 7), (2, 12), (3, 5), (3, 9), (3, 16),
                                   (7, 1), (7, 6), (16, 2), (16, 10), (100, 4),
                                   (100, 15), (255, 1), (255, 13), (256, 8),
                                   (1024, 2), (1024, 11), (65535, 16)]):
        b = bytearray(24)
        b[0:2] = rid.to_bytes(2, "little")
        b[2:6] = b"\x00\x00\x00\x00"
        b[6] = ln
        for k in range(7, 24):
            b[k] = 0x41 + (k % 26)
        items.append(("rec-%02d-id%d-len%d" % (j, rid, ln), bytes(b)))
    return items


def family(name):
    if name.startswith("fill-"):
        return "fill(256)"
    if name.startswith("one01@"):
        return "single-0x01"
    if name.startswith("oneff@"):
        return "single-0xff"
    if name.startswith("rand-"):
        return "random(100)"
    if name.startswith("rec-"):
        return "record-struct"
    return name


# --------------------------------------------------------------------------- #
# stats helpers
# --------------------------------------------------------------------------- #
def describe(xs):
    xs = list(xs)
    if not xs:
        return dict(n=0)
    d = {"n": len(xs), "min": min(xs), "max": max(xs),
         "median": statistics.median(xs), "mean": statistics.fmean(xs)}
    d["stdev"] = statistics.stdev(xs) if len(xs) > 1 else 0.0
    s = sorted(xs)
    d["mad"] = statistics.median([abs(v - d["median"]) for v in xs])
    d["p5"] = s[max(0, int(0.05 * (len(s) - 1)))]
    d["p95"] = s[min(len(s) - 1, int(0.95 * (len(s) - 1)))]
    return d


def fmt(d):
    if d.get("n", 0) == 0:
        return "n=0"
    return ("n=%-4d min=%8.6f  p5=%8.6f  median=%8.6f  mean=%8.6f  "
            "p95=%8.6f  max=%8.6f  stdev=%8.6f  MAD=%8.6f"
            % (d["n"], d["min"], d["p5"], d["median"], d["mean"],
               d["p95"], d["max"], d["stdev"], d["mad"]))


def hist(xs, bins=20):
    xs = list(xs)
    if len(xs) < 2:
        return ["(too few samples)"]
    lo, hi = min(xs), max(xs)
    if hi - lo < 1e-9:
        return ["all samples identical: %.6f" % lo]
    w = (hi - lo) / bins
    counts = [0] * bins
    for v in xs:
        k = min(bins - 1, int((v - lo) / w))
        counts[k] += 1
    mx = max(counts)
    out = []
    for i, c in enumerate(counts):
        out.append("  %8.5f-%8.5f  %-3d %s"
                   % (lo + i * w, lo + (i + 1) * w, c, "#" * int(60 * c / mx)))
    return out


def welch(a, b):
    """Welch t statistic + d.o.f. (pure python)."""
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return 0.0, 0
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    va, vb = statistics.variance(a), statistics.variance(b)
    se2 = va / na + vb / nb
    if se2 <= 0:
        return 0.0, na + nb - 2
    t = (ma - mb) / (se2 ** 0.5)
    df = (se2 ** 2) / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    return t, df


def normal_sf(z):
    """1-Phi(z) via erfc."""
    import math
    return 0.5 * math.erfc(z / math.sqrt(2))


# --------------------------------------------------------------------------- #
# phases
# --------------------------------------------------------------------------- #
def phase1(h):
    h.logf.write("\n" + "=" * 78 + "\nPHASE 1 - NOISE FLOOR CALIBRATION\n" + "=" * 78 + "\n")
    h.logf.flush()
    lat = {"RUN-zero": [], "NONCE": [], "MINT": []}
    for i in range(40):
        dt, r = h.send("RUN " + hx(ZERO24), "p1-run-zero-%02d" % i, "RUN")
        lat["RUN-zero"].append(dt)
    for i in range(20):
        dt, r = h.send("NONCE", "p1-nonce-%02d" % i, "NONCE")
        lat["NONCE"].append(dt)
    for i in range(20):
        dt, r = h.send("MINT 414243", "p1-mint-%02d" % i, "MINT")
        lat["MINT"].append(dt)

    stats = {}
    for k, xs in lat.items():
        d = describe(xs)
        stats[k] = d
        h.logf.write("  %-10s %s\n" % (k, fmt(d)))
    h.logf.write("\n  RUN-zero stdev/median = %.4f%%  ; spread(max-min) = %.6f s\n"
                 % (100 * stats["RUN-zero"]["stdev"] / stats["RUN-zero"]["median"],
                    stats["RUN-zero"]["max"] - stats["RUN-zero"]["min"]))
    for k in ("RUN-zero", "NONCE", "MINT"):
        h.logf.write("  hist %s:\n" % k + "\n".join(hist(lat[k], 12)) + "\n")
    # is there a uniform per-command pad?  NONCE/MINT do no "walk" at all.
    rn, nn, mn = (statistics.median(lat["RUN-zero"]), statistics.median(lat["NONCE"]),
                  statistics.median(lat["MINT"]))
    h.logf.write("  cross-command medians: RUN=%.6f NONCE=%.6f MINT=%.6f  "
                 "RUN-NONCE=%+.6f s (%.2f%%)\n"
                 % (rn, nn, mn, rn - nn, 100 * (rn - nn) / nn))
    tt, df = welch(lat["RUN-zero"], lat["NONCE"])
    h.logf.write("  RUN vs NONCE: Welch t=%+.2f -> %s\n"
                 % (tt, "RUN costs measurably more than a walk-free command"
                    if abs(tt) > 3 else
                    "RUN and the walk-free NONCE cost the SAME => the reply time is "
                    "dominated by a uniform per-command delay, not by walk depth"))
    h.logf.write("  distinct replies seen in phase1: %r\n"
                 % sorted(h.replies.keys()))
    h.logf.flush()
    return stats, lat


def phase2(h):
    h.logf.write("\n" + "=" * 78 + "\nPHASE 2 - BROAD SWEEP (one connection)\n" + "=" * 78 + "\n")
    h.logf.flush()
    rng = random.Random(0xC0FFEE)
    items = build_sweep(rng)
    h.log("phase2: %d RUN inputs queued" % len(items))
    t_start = time.perf_counter()
    base = []
    for idx, (tag, b) in enumerate(items):
        dt, r = h.send("RUN " + hx(b), "p2-" + tag, "RUN")
        base.append(dt)
        if idx and idx % 50 == 0:
            # drift probe: baseline re-measured inline, kept out of the sweep set
            h.send("RUN " + hx(ZERO24), "p2-driftprobe-%03d" % idx, "DRIFT")
            h.log("phase2 %d/%d done, %.0fs elapsed" % (idx + 1, len(items),
                                                        time.perf_counter() - t_start))
    h.log("phase2 finished in %.0fs" % (time.perf_counter() - t_start))
    return items


def report_phase2(h, stats):
    h.logf.write("\n" + "=" * 78 + "\nPHASE 2 ANALYSIS\n" + "=" * 78 + "\n")
    sweep = [s for s in h.samples if s["tag"].startswith("p2-") and s["kind"] == "RUN"]
    drift = [s for s in h.samples if s["kind"] == "DRIFT"]
    xs = [s["lat"] for s in sweep]
    d = describe(xs)
    h.logf.write("  sweep  %s\n" % fmt(d))
    floor = stats["RUN-zero"]
    h.logf.write("  floor  %s   (phase1, same connection=%s)\n"
                 % (fmt(floor), sorted({s['conn'] for s in sweep})))
    if len(sweep) < 3:
        h.logf.write("  !! sweep aborted before enough samples were taken; no analysis.\n")
        h.logf.flush()
        return [], d, drift
    h.logf.write("\n  histogram of sweep latencies (s):\n"
                 + "\n".join(hist(xs, 24)) + "\n")

    thr_hi = d["median"] + 3 * d["stdev"]
    thr_lo = d["median"] - 3 * d["stdev"]
    outliers = [s for s in sweep if s["lat"] > thr_hi or s["lat"] < thr_lo]
    h.logf.write("\n  outlier gates: > median+3sd = %.6f s ; < median-3sd = %.6f s\n"
                 % (thr_hi, thr_lo))
    h.logf.write("  outliers found: %d\n" % len(outliers))
    for s in sorted(outliers, key=lambda z: -z["lat"]):
        h.logf.write("    %-28s lat=%.6f reply=%r data=%s\n"
                     % (s["tag"], s["lat"], s["reply"], s["hex"]))

    # how far outside the *calibrated* floor is the whole sweep?
    fstd = floor["stdev"] or 1e-9
    zs = [(s["lat"] - floor["mean"]) / fstd for s in sweep]
    ordered_sweep = sorted(zs)
    h.logf.write("\n  sweep samples vs phase-1 RUN-zero floor, in floor-sigma units:\n")
    h.logf.write("    z min=%+.2f  p5=%+.2f  median=%+.2f  p95=%+.2f  max=%+.2f\n"
                 % (ordered_sweep[0],
                    ordered_sweep[max(0, int(.05 * (len(ordered_sweep) - 1)))],
                    statistics.median(zs),
                    ordered_sweep[min(len(ordered_sweep) - 1,
                                      int(.95 * (len(ordered_sweep) - 1)))],
                    ordered_sweep[-1]))
    t, df = welch(xs, [s["lat"] for s in h.samples if s["tag"].startswith("p1-run")])
    z = (statistics.fmean(xs) - floor["mean"]) / (floor["stdev"] / len(xs) ** 0.5) \
        if floor["stdev"] > 0 else 0.0
    h.logf.write("  sweep-vs-floor: Welch t=%+.2f (df~%.0f), mean-diff z=%+.2f "
                 "(two-sided p=%.3g)\n" % (t, df, z, 2 * normal_sf(abs(z))))

    # families
    fams = {}
    for s in sweep:
        fams.setdefault(family(s["tag"][3:]), []).append(s["lat"])
    h.logf.write("\n  per-family latency (sorted by mean, slowest first):\n")
    p1run = [s["lat"] for s in h.samples if s["tag"].startswith("p1-run")]
    gm, gs = d["median"], (d["stdev"] or 1e-9)
    rows = []
    for name, v in fams.items():
        dd = describe(v)
        if len(v) < 2 or floor["stdev"] <= 1e-9 or len(p1run) < 2:
            rows.append((name, dd, None, None, None))
            continue
        zm = (statistics.fmean(v) - floor["mean"]) / (floor["stdev"] / len(v) ** 0.5)
        zg = (statistics.fmean(v) - gm) / (gs / len(v) ** 0.5)
        tt, df = welch(v, p1run)
        rows.append((name, dd, zm, tt, zg))
    h.logf.write("    %-16s %5s %10s %10s %10s %8s %9s %s\n"
                 % ("family", "n", "median", "mean", "stdev", "z_floor", "z_grand",
                    "welch vs floor"))
    for name, dd, zm, tt, zg in sorted(rows, key=lambda r: -r[1].get("mean", 0.0)):
        if zm is None:
            h.logf.write("    %-16s %5d %10.6f %10.6f %10.6f %8s %9s %s\n"
                         % (name, dd["n"], dd["median"], dd["mean"], dd["stdev"],
                            "-", "-", "(too few samples)"))
            continue
        p = 2 * normal_sf(abs(zm))
        h.logf.write("    %-16s %5d %10.6f %10.6f %10.6f %+8.2f %+9.2f t=%+6.2f "
                     "p=%.3g%s\n"
                     % (name, dd["n"], dd["median"], dd["mean"], dd["stdev"],
                        zm, zg, tt, p,
                        "  <== passes Bonferroni"
                        if p < 0.05 / max(1, len([r for r in rows if r[2] is not None]))
                        else ""))
    ntest = max(1, len([r for r in rows if r[2] is not None]))
    zmax = max([abs(r[2]) for r in rows if r[2] is not None] or [0.0])
    h.logf.write("    families tested=%d ; |z| needed for Bonferroni p<0.05 = %.2f ; "
                 "largest observed |z_floor| = %.2f -> %s\n"
                 % (ntest, 2.81 if ntest > 1 else 1.96, zmax,
                    "NO input family is statistically distinguishable from the "
                    "noise floor" if zmax < (2.81 if ntest > 1 else 1.96) else
                    "at least one family crosses the corrected threshold"))
    # flatness across the session: block medians
    h.logf.write("\n  sweep split into blocks of 50 (in send order) - is latency flat "
                 "or drifting over the session?\n")
    for i in range(0, len(sweep), 50):
        blk = [s["lat"] for s in sweep[i:i + 50]]
        bd = describe(blk)
        h.logf.write("    block %3d-%3d n=%3d median=%8.6f mean=%8.6f stdev=%8.6f "
                     "min=%8.6f max=%8.6f\n"
                     % (i, i + len(blk) - 1, bd["n"], bd["median"], bd["mean"],
                        bd["stdev"], bd["min"], bd["max"]))

    # top/bottom 20
    ordered = sorted(sweep, key=lambda s: -s["lat"])
    h.logf.write("\n  20 SLOWEST RUN inputs:\n")
    h.logf.write("    %-30s %10s %-12s %s\n" % ("tag", "lat(s)", "conn", "24-byte input (hex)"))
    for s in ordered[:20]:
        h.logf.write("    %-30s %10.6f conn%-8d %s\n"
                     % (s["tag"], s["lat"], s["conn"], s["hex"]))
    h.logf.write("\n  20 FASTEST RUN inputs:\n")
    for s in ordered[-20:]:
        h.logf.write("    %-30s %10.6f conn%-8d %s\n"
                     % (s["tag"], s["lat"], s["conn"], s["hex"]))

    # drift over the sweep
    h.logf.write("\n  drift check (interleaved RUN-zero probes, in order; "
                 "@NNN = sweep index the probe was taken after):\n")
    if drift:
        pts = []
        for s in drift:
            try:
                at = int(s["tag"].rsplit("-", 1)[1])
            except ValueError:
                at = -1
            pts.append("%.6f@%d" % (s["lat"], at))
        h.logf.write("    " + "  ".join(pts) + "\n")
        half = max(1, len(drift) // 2)
        first = statistics.fmean([s["lat"] for s in drift[:half]])
        last = statistics.fmean([s["lat"] for s in drift[half:]])
        h.logf.write("    mean(first half)=%.6f mean(second half)=%.6f delta=%+.6f s"
                     "  (= %.2f%% of the baseline median)\n"
                     % (first, last, last - first,
                        100 * (last - first) / statistics.median(xs)))
    h.logf.flush()
    return outliers, d, drift


def phase4(h, outliers, floor):
    h.logf.write("\n" + "=" * 78 +
                 "\nPHASE 4 - REPEAT MEASUREMENT OF OUTLIERS, INTERLEAVED WITH BASELINE\n"
                 + "=" * 78 + "\n")
    if not outliers:
        h.logf.write("  phase2 produced no >median+/-3sd outlier: nothing to confirm.\n")
        h.logf.flush()
        return {}
    picked = {}
    for s in sorted(outliers, key=lambda z: -z["lat"])[:6]:
        picked[s["tag"]] = s["hex"]
    conf = {}
    for tag, hexs in picked.items():
        reps = []
        for i in range(10):
            dt, r = h.send("RUN " + hexs, "p4-%s-r%d" % (tag[3:], i), "P4CAND")
            reps.append(dt)
            h.send("RUN " + hx(ZERO24), "p4-baseline-after-%s-r%d" % (tag[3:], i),
                   "P4BASE")
        conf[tag] = (reps, hexs)
        d = describe(reps)
        h.logf.write("  %-30s %s\n" % (tag, fmt(d)))
    bl = [s["lat"] for s in h.samples if s["kind"] == "P4BASE"]
    d = describe(bl)
    h.logf.write("\n  interleaved baseline over the SAME window: %s\n" % fmt(d))
    h.logf.write("  phase-1 baseline (start of session):        %s\n" % fmt(floor))
    shift = d["mean"] - floor["mean"]
    h.logf.write("  session drift over phase-4 window: %+.6f s (%.2f%% of baseline)\n"
                 % (shift, 100 * shift / floor["mean"]))
    h.logf.write("\n  candidate vs the *interleaved* baseline of the same moment:\n")
    for tag, (reps, hexs) in conf.items():
        near = [s["lat"] for s in h.samples if s["kind"] == "P4BASE"
                and s["tag"].startswith("p4-baseline-after-" + tag[3:] + "-")]
        tt, df = welch(reps, near if len(near) > 1 else bl)
        dm = statistics.fmean(reps) - statistics.fmean(near or bl)
        h.logf.write("    %-30s mean=%8.6f  local-base=%8.6f  diff=%+9.6f s  t=%+6.2f\n"
                     % (tag, statistics.fmean(reps),
                        statistics.fmean(near or bl), dm, tt))
    h.logf.flush()
    return conf


def rec_input(rid, ln, junk=0x41):
    """2-byte LE id + 4 zero bytes + length byte + junk."""
    b = bytearray(24)
    b[0:2] = (rid & 0xffff).to_bytes(2, "little")
    b[2:6] = b"\x00\x00\x00\x00"
    b[6] = ln & 0xff
    for k in range(7, 24):
        b[k] = (junk + k) & 0xff
    return bytes(b)


def slope(xs, ys):
    """OLS slope of ys on xs; returns (slope, standard_error, r)."""
    n = len(xs)
    if n < 3:
        return 0.0, 0.0, 0.0
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0:
        return 0.0, 0.0, 0.0
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    a = my - b * mx
    s2 = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys)) / (n - 2)
    se = (s2 / sxx) ** 0.5
    r = (b * (sxx ** 0.5)) / (syy ** 0.5) if syy > 0 else 0.0
    return b, se, r


def phase5(h, stats, conf):
    """Step-cost calibration.  There is no reproducible slow/fast class from
    phases 2-4, so 'sweep within the class' is done on the two axes a variable
    -length walk would actually depend on: the declared length byte, and the
    offset of a non-zero byte."""
    h.logf.write("\n" + "=" * 78 +
                 "\nPHASE 5 - IS ANY SERVER-SIDE WORK VISIBLE IN THE REPLY TIME AT "
                 "ALL?  + PER-STEP (STAIRCASE) MEASUREMENTS\n" + "=" * 78 + "\n")

    # ---- 5.0 reproduce-check of the phase-4 candidates ---------------------
    bl = [s["lat"] for s in h.samples if s["kind"] == "P4BASE"]
    if bl and conf:
        mb = statistics.fmean(bl)
        for tag, (reps, hexs) in conf.items():
            tt, df = welch(reps, bl) if len(bl) > 1 else (0.0, 0)
            h.logf.write("  reproduce-check %-30s mean=%8.6f base=%8.6f "
                         "diff=%+9.6f t=%+6.2f p=%.3g%s\n"
                         % (tag, statistics.fmean(reps), mb,
                            statistics.fmean(reps) - mb, tt,
                            2 * normal_sf(abs(tt)),
                            "  <== REPRODUCES" if (abs(statistics.fmean(reps) - mb)
                                                   > 1e-3
                                                   and 2 * normal_sf(abs(tt)) < 1e-4)
                            else ""))

    # ---- 5A work-visibility calibration ------------------------------------
    h.logf.write("\n  5A. work-visibility calibration: interleave a command that "
                 "does NO walk (NONCE), two that differ only in how much DATA they "
                 "process (MINT 1 byte vs MINT 16 bytes), the RUN, and GET (which "
                 "streams the whole image).  10 rounds, round-robin, so drift "
                 "cannot masquerade as work.\n")
    labels = [("NONCE", "NONCE", "NONCE"),
              ("MINT-1B", "MINT 41", "MINT"),
              ("MINT-16B", "MINT " + "41" * 16, "MINT"),
              ("RUN-zero", "RUN " + hx(ZERO24), "RUN")]
    acc = {}
    for rep in range(10):
        for label, cmd, kind in labels:
            dt, r = h.send(cmd, "p5a-%s-r%02d" % (label, rep), "P5A:" + label)
            acc.setdefault(label, []).append(dt)
    gets = []
    for i in range(3):
        dt, r = h.send("GET", "p5a-get-%d" % i, "GET")
        gets.append(dt)
    h.logf.write("    %-10s %s\n" % ("label", "stats"))
    for label, _, _ in labels:
        h.logf.write("    %-10s %s\n" % (label, fmt(describe(acc[label]))))
    gd = describe(gets)
    h.logf.write("    %-10s %s   (GET streams the program image as hex)\n"
                 % ("GET", fmt(gd)))
    n1, n16 = statistics.median(acc["MINT-1B"]), statistics.median(acc["MINT-16B"])
    rn, nn = statistics.median(acc["RUN-zero"]), statistics.median(acc["NONCE"])
    h.logf.write("    MINT-16B minus MINT-1B (15 extra bytes of real work) = "
                 "%+9.6f s\n" % (n16 - n1))
    h.logf.write("    RUN minus NONCE  (one walk)                          = "
                 "%+9.6f s\n" % (rn - nn))
    tt, df = welch(acc["RUN-zero"], acc["NONCE"])
    diff = statistics.fmean(acc["RUN-zero"]) - statistics.fmean(acc["NONCE"])
    se = (((statistics.pvariance(acc["RUN-zero"]) / len(acc["RUN-zero"]))
           + (statistics.pvariance(acc["NONCE"]) / len(acc["NONCE"]))) ** 0.5)
    h.logf.write("    RUN-vs-NONCE mean diff = %+.6f s  95%% CI = [%+.6f, %+.6f]  "
                 "t=%+.2f (n=10 each)\n" % (diff, diff - 1.96 * se, diff + 1.96 * se, tt))

    # ---- 5B declared-length staircase --------------------------------------
    h.logf.write("\n  5B. per-step staircase on the walk's likely loop count: the "
                 "record's length byte L = 0..16, everything else fixed, 6 reps of "
                 "each L round-robin, plus a RUN-zero control at the end of every "
                 "round.\n")
    REPS_B = 6   # keep the session under ~10 min at 0.42 s/command
    lens = list(range(0, 17))
    gridB = {}
    ctrl = []
    for rep in range(REPS_B):
        for L in lens:
            b = rec_input(1, L)
            dt, r = h.send("RUN " + hx(b), "p5b|L%02d|r%02d" % (L, rep), "P5B")
            gridB.setdefault(L, []).append(dt)
        dt, r = h.send("RUN " + hx(ZERO24), "p5b|control|r%02d" % rep, "P5BC")
        ctrl.append(dt)
    h.logf.write("    %-4s %5s %10s %10s %10s %s\n"
                 % ("L", "n", "median", "mean", "stdev", "individual reps (s)"))
    for L in lens:
        v = gridB[L]
        dd = describe(v)
        h.logf.write("    %-4d %5d %10.6f %10.6f %10.6f %s\n"
                     % (L, dd["n"], dd["median"], dd["mean"], dd["stdev"],
                        " ".join("%.5f" % x for x in v)))
    meansB = [statistics.fmean(gridB[L]) for L in lens]
    bB, seB, rB = slope([float(L) for L in lens], meansB)
    h.logf.write("    OLS over the 17 length levels: slope = %+.6f s/step "
                 "(= %+.3f ms/step, 95%% CI [%+.3f, %+.3f] ms/step), r=%+.3f, "
                 "residual sd=%.6f s\n"
                 % (bB, 1e3 * bB, 1e3 * (bB - 2 * seB), 1e3 * (bB + 2 * seB),
                    rB, (seB * (len(lens) ** 0.5))))
    h.logf.write("    => per-step cost is bounded above (95%%) by %.3f ms = %.1f us "
                 "per walk step.  The control RUN-zero in this window: %s\n"
                 % (1e3 * (bB + 2 * seB), 1e6 * (bB + 2 * seB), fmt(describe(ctrl))))

    # ---- 5C offset staircase -----------------------------------------------
    h.logf.write("\n  5C. per-step staircase on walk DEPTH vs byte position: one "
                 "0x01 byte at offset k, k = 0..23, 6 reps each round-robin.\n")
    offs = list(range(0, 24))
    gridC = {}
    ctrlC = []
    for rep in range(REPS_B):
        for k in offs:
            b = bytearray(24)
            b[k] = 0x01
            dt, r = h.send("RUN " + hx(bytes(b)), "p5c|o%02d|r%02d" % (k, rep), "P5C")
            gridC.setdefault(k, []).append(dt)
        dt, r = h.send("RUN " + hx(ZERO24), "p5c|control|r%02d" % rep, "P5CC")
        ctrlC.append(dt)
    h.logf.write("    %-4s %5s %10s %10s %10s\n"
                 % ("off", "n", "median", "mean", "stdev"))
    for k in offs:
        dd = describe(gridC[k])
        h.logf.write("    %-4d %5d %10.6f %10.6f %10.6f\n"
                     % (k, dd["n"], dd["median"], dd["mean"], dd["stdev"]))
    meansC = [statistics.fmean(gridC[k]) for k in offs]
    bC, seC, rC = slope([float(k) for k in offs], meansC)
    h.logf.write("    OLS over the 24 offsets: slope = %+.3f ms/offset "
                 "(95%% CI [%+.3f, %+.3f]), r=%+.3f\n"
                 % (1e3 * bC, 1e3 * (bC - 2 * seC), 1e3 * (bC + 2 * seC), rC))
    spreadC = describe(meansC)
    h.logf.write("    spread of the 24 offset-means: %s\n" % fmt(spreadC))
    h.logf.write("    controls in this window: %s\n" % fmt(describe(ctrlC)))

    # ---- verdict -----------------------------------------------------------
    h.logf.write("\n  PHASE 5 VERDICT\n")
    h.logf.write("    - a walk step costs at most %.3f ms (95%% upper bound from 5B); "
                 "observed slope %+.3f ms/step.\n" % (1e3 * (bB + 2 * seB), 1e3 * bB))
    h.logf.write("    - GET shows the process CAN spend seconds inside one command "
                 "(median %.4f s), so the reply time is not hard-capped at ~0.1 s by "
                 "a timeout; the question is only whether walk work lands in the "
                 "measurable window.\n" % gd["median"])
    h.logf.write("    - RUN minus NONCE (the whole walk, start to finish) is "
                 "%+.6f s; a variable-depth walk would have to move that number.\n"
                 % (rn - nn))
    h.logf.flush()
    return dict(bB=bB, seB=seB, rB=rB, bC=bC, seC=seC, rC=rC,
                mint_delta=n16 - n1, run_minus_nonce=rn - nn,
                get_median=gd["median"], ctrlB=describe(ctrl), ctrlC=describe(ctrlC))


RUNISH = ("RUN", "P4CAND", "P4BASE", "DRIFT", "P5B", "P5BC", "P5C", "P5CC",
          "P5A:RUN-zero", "P6A", "P6AC", "P6B", "P6BC", "P6BASE",
          "P6CA", "P6CB")


def is_runish(kind):
    return kind in RUNISH or kind.startswith("RUN") or kind.startswith("smoke-run")


def final_reply_report(h):
    h.logf.write("\n" + "=" * 78 +
                 "\nREPLY TEXT AUDIT (every command, verbatim)\n" + "=" * 78 + "\n")
    h.logf.write("  total commands: %d\n" % len(h.samples))
    h.logf.write("  distinct replies, ALL commands (GET's image hex is shown "
                 "truncated, it is a 3076-byte program image as hex):\n")
    for r, c in sorted(h.replies.items(), key=lambda kv: -kv[1]):
        show = r if len(r) <= 60 else r[:50] + "...<truncated, len=%d>" % len(r)
        h.logf.write("    %5d x %r\n" % (c, show))
    h.logf.write("  distinct replies to RUN-family commands (RUN / retests / "
                 "staircases):\n")
    runish = {}
    for s in h.samples:
        if is_runish(s["kind"]):
            runish[s["reply"]] = runish.get(s["reply"], 0) + 1
    for r, c in sorted(runish.items(), key=lambda kv: -kv[1]):
        h.logf.write("    %5d x %r\n" % (c, r))
    notdenied = [s for s in h.samples if is_runish(s["kind"]) and s["reply"] != "denied"]
    h.logf.write("  RUN-family replies that were NOT exactly 'denied': %d of %d\n"
                 % (len(notdenied), sum(runish.values())))
    for s in notdenied[:60]:
        h.logf.write("    !!! conn=%d %-34s lat=%.6f reply=%r data=%s\n"
                     % (s["conn"], s["tag"], s["lat"], s["reply"], s["hex"]))
    h.logf.write("  non-RUN commands, grouped (kind -> distinct reply -> count):\n")
    grp = {}
    for s in h.samples:
        if not is_runish(s["kind"]):
            grp.setdefault(s["kind"], {})
            grp[s["kind"]][s["reply"]] = grp[s["kind"]].get(s["reply"], 0) + 1
    for kind in sorted(grp):
        for r, c in sorted(grp[kind].items(), key=lambda kv: -kv[1]):
            show = r if len(r) <= 60 else (r[:50] + "...<len=%d chars>" % len(r))
            h.logf.write("    %-14s %4d x %r\n" % (kind, c, show))
    h.logf.write("  connections used: %d (reconnects: %d)\n"
                 % (h.conn_n, h.reconnects))
    per_conn = {}
    for s in h.samples:
        per_conn[s["conn"]] = per_conn.get(s["conn"], 0) + 1
    h.logf.write("  samples per connection: %r\n" % per_conn)
    h.logf.flush()
    return notdenied


# --------------------------------------------------------------------------- #
# sample-log reader (insurance: a bug in the reporting code must not cost us a
# 5-minute measurement series, so every phase can be re-derived from the file)
# --------------------------------------------------------------------------- #
SAMPLE_RE = re.compile(
    r"^SAMPLE n=(\d+) conn=(\d+) kind=(\S+) tag=(\S+) lat=([0-9.]+) "
    r"reply=(.*?) data=(.*)$")
SAMPLE_RE_OLD = re.compile(
    r"^SAMPLE n=(\d+) conn=(\d+) tag=(\S+) lat=([0-9.]+) "
    r"reply=(.*?) data=(.*)$")


def kind_for_tag(tag):
    if "driftprobe" in tag:
        return "DRIFT"
    if tag.startswith("p1-run"):
        return "RUN"
    if tag.startswith("p1-nonce"):
        return "NONCE"
    if tag.startswith("p1-mint"):
        return "MINT"
    if tag.startswith("p2-"):
        return "RUN"
    if tag.startswith("p4-"):
        return "P4BASE" if "baseline" in tag else "P4CAND"
    if tag.startswith("p5a-get"):
        return "GET"
    if tag.startswith("p5a-"):
        return "P5A:" + tag[4:].rsplit("-r", 1)[0]
    if tag.startswith("p5b|control"):
        return "P5BC"
    if tag.startswith("p5b|"):
        return "P5B"
    if tag.startswith("p5c|control"):
        return "P5CC"
    if tag.startswith("p5c|"):
        return "P5C"
    if tag.startswith("p6-base"):
        return "P6BASE"
    if tag.startswith("p6-nonce"):
        return "P6NONCE"
    if tag.startswith("p6a|control"):
        return "P6AC"
    if tag.startswith("p6a|"):
        return "P6A"
    if tag.startswith("p6b|control"):
        return "P6BC"
    if tag.startswith("p6b|"):
        return "P6B"
    if tag.startswith("p6c|A"):
        return "P6CA"
    if tag.startswith("p6c|B"):
        return "P6CB"
    return "OTHER"


def load_samples(h, path):
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.startswith("SAMPLE"):
                continue
            m = SAMPLE_RE.match(line)
            if m:
                conn, kind, tag, lat, reply, hexs = (int(m.group(2)), m.group(3),
                                                     m.group(4), float(m.group(5)),
                                                     m.group(6), m.group(7))
            else:
                m = SAMPLE_RE_OLD.match(line)
                if not m:
                    continue
                conn, tag, lat, reply, hexs = (int(m.group(2)), m.group(3),
                                               float(m.group(4)), m.group(5), m.group(6))
                kind = kind_for_tag(tag)
            try:
                reply = ast.literal_eval(reply)
            except Exception:
                pass
            hexs = hexs.strip()
            if hexs.startswith("RUN "):
                hexs = hexs[4:]
            elif hexs.startswith("MINT "):
                hexs = hexs[5:]
            h.samples.append({"conn": conn, "kind": kind, "tag": tag, "lat": lat,
                              "reply": reply, "hex": hexs})
            h.replies[reply] = h.replies.get(reply, 0) + 1
            if kind == "RUN":
                h.run_replies[reply] = h.run_replies.get(reply, 0) + 1
    h.conn_n = max([s["conn"] for s in h.samples] or [0])
    return len(h.samples)


def stats_from_samples(h):
    """Rebuild the phase-1 calibration dict from stored samples."""
    groups = {"RUN-zero": [], "NONCE": [], "MINT": []}
    for s in h.samples:
        if s["tag"].startswith("p1-run"):
            groups["RUN-zero"].append(s["lat"])
        elif s["tag"].startswith("p1-nonce"):
            groups["NONCE"].append(s["lat"])
        elif s["tag"].startswith("p1-mint"):
            groups["MINT"].append(s["lat"])
    return {k: describe(v) for k, v in groups.items()}, groups


# --------------------------------------------------------------------------- #
# PHASE 2b: drift-corrected re-analysis of the stored samples.  No new traffic:
# the family z_floor numbers printed in PHASE 2 are inflated by a session-wide
# level shift, which must be measured and removed before any class can be
# called "distinguishable".
# --------------------------------------------------------------------------- #
def trim_mean(v, p=0.1):
    """10%-trimmed mean (statistics.trim_mean is absent in this CPython build)."""
    s = sorted(v)
    k = int(len(s) * p)
    core = s[k:len(s) - k] if len(s) - 2 * k >= 1 else s
    return statistics.fmean(core)


def robust_sigma(v):
    med = statistics.median(v)
    mad = statistics.median([abs(x - med) for x in v])
    return 1.4826 * mad if mad else statistics.pstdev(v)


def baseline_curve(h):
    """(index, latency) anchors of the SAME input (24 zero bytes) sampled at
    different times, in sweep-index order: phase-1 calibration before index 0,
    the interleaved drift probes inside the sweep, phase-4/5 controls after it."""
    pts = []
    p1 = [s["lat"] for s in h.samples if s["tag"].startswith("p1-run")]
    if p1:
        pts.append((-1.0, statistics.median(p1)))
    for s in h.samples:
        if s["kind"] == "DRIFT":
            try:
                pts.append((float(s["tag"].rsplit("-", 1)[1]), s["lat"]))
            except ValueError:
                pass
    late = ([s["lat"] for s in h.samples if s["kind"] == "P4BASE"]
            + [s["lat"] for s in h.samples if s["kind"] in ("P5BC", "P5CC")])
    if late:
        pts.append((431.0 + len(pts), statistics.median(late)))
    pts.sort()
    return pts


def interp_baseline(pts, x):
    if not pts:
        return 0.0
    if x <= pts[0][0]:
        return pts[0][1]
    if x >= pts[-1][0]:
        return pts[-1][1]
    for i in range(1, len(pts)):
        if pts[i][0] >= x:
            x0, y0 = pts[i - 1]
            x1, y1 = pts[i]
            if x1 == x0:
                return y1
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pts[-1][1]


def analyse_saved(h):
    pts = baseline_curve(h)
    sweep_all = [s for s in h.samples if s["tag"].startswith("p2-") and s["kind"] == "RUN"]
    # if the sample log holds more than one measurement series (a crash + a
    # restart appended to the same file), keep only the LAST complete sweep,
    # otherwise duplicate tags would be double counted.
    last = {}
    for i, s in enumerate(sweep_all):
        last[s["tag"]] = i
    keep = set(last.values())
    if len(keep) != len(sweep_all):
        h.logf.write("  NOTE: the log holds %d RUN sweep samples with only %d distinct "
                     "tags (more than one series appended); this analysis uses the "
                     "later occurrence of each tag only.\n"
                     % (len(sweep_all), len(keep)))
    sweep = [s for i, s in enumerate(sweep_all) if i in keep]
    conns = sorted({s["conn"] for s in sweep})
    h.logf.write("  sweep analysed: %d inputs, connection(s) %r\n" % (len(sweep), conns))
    if len(sweep) < 20:
        h.logf.write("\nPHASE 2b: not enough stored sweep samples to analyse.\n")
        return
    h.logf.write("\n" + "=" * 78 +
                 "\nPHASE 2b - DRIFT-CORRECTED RE-ANALYSIS (computed from the stored "
                 "PHASE 2 samples; NO new measurement)\n" + "=" * 78 + "\n")
    h.logf.write("  The PHASE 2 'z_floor' column compares each family with the "
                 "phase-1 calibration taken ~2 minutes EARLIER on the same socket, "
                 "so it is a TIME comparison, not an input comparison.  The same "
                 "input (24 zero bytes) was re-measured inside the sweep; that "
                 "control says how much of the family offsets is drift.\n")
    p1 = [s["lat"] for s in h.samples if s["tag"].startswith("p1-run")]
    dr = [s["lat"] for s in h.samples if s["kind"] == "DRIFT"]
    late = [s["lat"] for s in h.samples if s["kind"] in ("P4BASE", "P5BC", "P5CC")]
    h.logf.write("  SAME INPUT, four moments of the session:\n")
    for name, v in (("phase 1 (before the sweep)", p1),
                    ("inside the sweep (drift probes)", dr),
                    ("after the sweep (ph4/ph5 controls)", late)):
        if v:
            h.logf.write("    RUN 24*00 %-34s n=%-4d median=%.6f mean=%.6f stdev=%.6f\n"
                         % (name, len(v), statistics.median(v), statistics.fmean(v),
                            statistics.stdev(v) if len(v) > 1 else 0.0))
    if p1 and dr:
        h.logf.write("    => the identical input moved %+.6f s between phase 1 and the "
                     "sweep window.  That shift is COMMON to every family, so it has "
                     "to be subtracted before a family can be called slow.\n"
                     % (statistics.median(dr) - statistics.median(p1)))
    h.logf.write("  baseline anchors for the correction (sweep index / RUN-zero "
                 "latency): %s\n"
                 % ", ".join("%.0f/%.6f" % p for p in pts))
    inside = [p for p in pts if 0 <= p[0] <= 431]
    if len(inside) < 2:
        h.logf.write("  !! WARNING: fewer than 2 RUN-zero anchors were measured INSIDE "
                     "the sweep window, so the local baseline below is only a constant "
                     "and the z values that follow are NOT drift-corrected. Reload the "
                     "sample log (the in-sweep drift probes must parse).\n")

    resid, fam = [], {}
    # a fitted straight line through the RUN-zero anchors, not a piecewise
    # interpolation: the anchors are single samples, and interpolating through
    # their own noise would manufacture per-family offsets.
    bs, bse, _ = slope([p[0] for p in pts], [p[1] for p in pts])
    b0 = statistics.fmean([p[1] for p in pts]) - bs * statistics.fmean([p[0] for p in pts])
    h.logf.write("  fitted drift line through those anchors: baseline(i) = %.6f %+.3e*i "
                 "s  (slope %+.3e s per 100 commands = %+.2f ms; anchor-fit se of slope "
                 "%.3e) -> the session level is FLAT to within %s\n"
                 % (b0, bs, 100 * bs, 1e3 * 100 * bs, bse,
                    "0.5 ms" if abs(100 * bs) < 5e-4 else "MORE, treat with care"))
    for i, s in enumerate(sweep):
        r = s["lat"] - (b0 + bs * i)
        resid.append(r)
        fam.setdefault(family(s["tag"][3:]), []).append(r)
    sr = robust_sigma(resid)
    sd = statistics.pstdev(resid)
    h.logf.write("\n  drift-corrected residuals (lat - fitted RUN-zero baseline):\n")
    h.logf.write("    mean=%+.6f  median=%+.6f  robust sigma(MAD-based)=%.6f  "
                 "plain sd=%.6f  min=%+.6f  max=%+.6f\n"
                 % (statistics.fmean(resid), statistics.median(resid), sr, sd,
                    min(resid), max(resid)))
    h.logf.write("    (plain sd exceeds the robust sigma because the residuals have a "
                 "one-sided spike tail - see the spike audit below)\n")

    names = [k for k, v in fam.items() if len(v) >= 2]
    # permutation test on each family's 10%-trimmed mean: the heavy spike tail
    # makes a normal-theory z meaningless, and the trimmed mean is the location
    # estimate we actually care about (walk depth would shift the BULK).
    NPERM = 3000
    rngp = random.Random(0xBEEF)
    pool = []
    for k in names:
        pool += [(k, v) for v in fam[k]]
    obs = {k: trim_mean(v, 0.1) for k, v in fam.items() if len(v) >= 2}
    ns = {k: len(v) for k, v in fam.items() if len(v) >= 2}
    cnt = {k: 0 for k in obs}
    vals = [v for _, v in pool]
    for _ in range(NPERM):
        rngp.shuffle(vals)
        j = 0
        null = {}
        for k in names:
            null[k] = vals[j:j + ns[k]]
            j += ns[k]
        tm = {k: trim_mean(null[k], 0.1) for k in names}
        for k in obs:
            if abs(tm[k]) >= abs(obs[k]):
                cnt[k] += 1
    h.logf.write("\n  per-family test on the DRIFT-CORRECTED residuals.  Statistic = "
                 "10%% trimmed mean (spike-proof location); p from %d label "
                 "permutations, Bonferroni threshold p<%.4f over %d families:\n"
                 % (NPERM, 0.05 / max(1, len(obs)), len(obs)))
    h.logf.write("    %-16s %5s %12s %12s %12s %12s %8s %s\n"
                 % ("family", "n", "mean res", "median res", "trim10% res",
                    "trim in ms", "p(perm)", "verdict"))
    any_sig = False
    for k in sorted(obs, key=lambda k: -abs(obs[k])):
        p = (cnt[k] + 1) / (NPERM + 1)
        sig = p < 0.05 / max(1, len(obs))
        any_sig |= sig
        h.logf.write("    %-16s %5d %+12.6f %+12.6f %+12.6f %+12.3f %8.4f %s\n"
                     % (k, ns[k], statistics.fmean(fam[k]), statistics.median(fam[k]),
                        obs[k], 1e3 * obs[k], p, "SIGNIFICANT" if sig else "flat"))
    h.logf.write("  -> %s\n"
                 % ("NO input family is distinguishable from the noise floor once the "
                    "session level is fitted out: every family sits within the jitter "
                    "of the identical all-zero control. The PHASE 2 z_floor column was "
                    "a time shift plus the spike tail, not signal."
                    if not any_sig else
                    "at least one family survives the robust permutation test - "
                    "follow it up in phase 4/5"))

    thr = statistics.median(resid) + 0.003
    spikes = [s for (i, s), r in zip(enumerate(sweep), resid) if r > thr]
    h.logf.write("\n  spike audit: %d of %d sweep samples (%.1f%%) sit >3 ms above "
                 "their local baseline.  If spikes were walk-depth dependent they "
                 "would cluster in one family; compare with each family's share of "
                 "the inputs:\n"
                 % (len(spikes), len(sweep), 100.0 * len(spikes) / len(sweep)))
    tot = len(sweep)
    counts = {}
    for s in spikes:
        counts[family(s["tag"][3:])] = counts.get(family(s["tag"][3:]), 0) + 1
    h.logf.write("    %-16s %8s %10s %8s %8s %s\n"
                 % ("family", "inputs", "share", "spikes", "spike%", "binomial z"))
    for name in sorted(fam, key=lambda k: -counts.get(k, 0)):
        n = len(fam[name])
        c = counts.get(name, 0)
        exp = n / tot
        zz = (c - len(spikes) * exp) / max(0.5, (len(spikes) * exp * (1 - exp)) ** 0.5)
        h.logf.write("    %-16s %8d %9.1f%% %8d %7.1f%%  z=%+.2f\n"
                     % (name, n, 100 * exp, c, 100.0 * c / n, zz))
    h.logf.write("    spike samples, verbatim reply:\n")
    for s in spikes:
        h.logf.write("      %-24s lat=%.6f reply=%r\n" % (s["tag"], s["lat"], s["reply"]))
    h.logf.flush()


def phase6c(h, rand_hexes):
    """Paired A/B retest of the one family the robust permutation test flagged in
    PHASE 2b (random inputs, -0.23 ms).  Every candidate is measured immediately
    followed by the all-zero control, and the ANALYSED quantity is the within-pair
    difference, which cancels any session-level wander that a block comparison
    cannot separate from an input effect."""
    h.logf.write("\n  6C. paired A/B retest of the flagged 'random(100)' class: each "
                 "candidate immediately followed by the RUN-zero control on the SAME "
                 "socket. The statistic is the within-pair difference, so drift "
                 "cannot contribute to it.\n")
    if not rand_hexes:
        h.logf.write("    no stored random inputs found in the log; skipped.\n")
        return None
    diffs = []
    per_input = {}
    for rep in range(5):
        for j, hexs in enumerate(rand_hexes):
            dtA, rA = h.send("RUN " + hexs, "p6c|A|r%d|i%d" % (rep, j), "P6CA")
            dtB, rB = h.send("RUN " + hx(ZERO24), "p6c|B|r%d|i%d" % (rep, j), "P6CB")
            d = dtA - dtB
            diffs.append(d)
            per_input.setdefault(hexs, []).append(d)
    n = len(diffs)
    m = statistics.fmean(diffs)
    sd = statistics.stdev(diffs)
    se = sd / n ** 0.5
    t = m / se
    wins = sum(1 for d in diffs if d < 0)
    # exact-ish sign test via normal approximation on the paired differences
    zs = (wins - n / 2.0) / (n / 4.0) ** 0.5
    h.logf.write("    pairs=%d  mean(random - adjacent control) = %+.6f s  sd=%.6f "
                 "se=%.6f  paired t=%+.2f  (95%% CI [%+.6f, %+.6f])\n"
                 % (n, m, sd, se, t, m - 1.96 * se, m + 1.96 * se))
    h.logf.write("    sign test: random was FASTER than its adjacent control in "
                 "%d/%d pairs, z=%+.2f -> %s\n"
                 % (wins, n, zs,
                    "the PHASE 2b -0.23 ms 'fast random' effect does NOT survive a "
                    "paired design: it was session position, not the input"
                    if abs(zs) < 3 and 2 * normal_sf(abs(t)) > 0.001 else
                    "the paired test REPLICATES a class difference"))
    h.logf.write("    per-input means (random - control), s:\n")
    for hexs, v in per_input.items():
        h.logf.write("      %s n=%d mean=%+.6f  %s\n"
                     % (hexs, len(v), statistics.fmean(v),
                        " ".join("%+.5f" % x for x in v)))
    h.logf.flush()
    return dict(n=n, mean=m, se=se, t=t)


def phase6(h, rand_hexes=None):
    """Wide per-step staircase on ONE connection: the phase-5 length sweep only
    reached L=16, so a per-step cost of, say, 20 us would only move the reply by
    0.3 ms.  Driving the same length byte out to 255 amplifies any real per-step
    cost 16x, which is what turns an upper bound into a measurement."""
    h.logf.write("\n" + "=" * 78 +
                 "\nPHASE 6 - WIDE PER-STEP STAIRCASE (new connection => new "
                 "instance state; everything below is internally calibrated and "
                 "interleaved)\n" + "=" * 78 + "\n")
    base = []
    for i in range(20):
        dt, r = h.send("RUN " + hx(ZERO24), "p6-base-%02d" % i, "P6BASE")
        base.append(dt)
    nonce = []
    for i in range(10):
        dt, r = h.send("NONCE", "p6-nonce-%02d" % i, "P6NONCE")
        nonce.append(dt)
    h.logf.write("  this instance's own floor: %s\n" % fmt(describe(base)))
    h.logf.write("  this instance's NONCE    : %s\n" % fmt(describe(nonce)))
    h.logf.write("  floor median - nonce median = %+.6f s\n"
                 % (statistics.median(base) - statistics.median(nonce)))

    levels = [0, 1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 160, 192, 224, 255]
    REPS = 8
    h.logf.write("\n  6A length-byte staircase, L in %s, %d reps round-robin, "
                 "RUN-zero control every round.\n" % (levels, REPS))
    gA, ctrlA = {}, []
    for rep in range(REPS):
        for L in levels:
            b = rec_input(1, L)
            dt, r = h.send("RUN " + hx(b), "p6a|L%03d|r%02d" % (L, rep), "P6A")
            gA.setdefault(L, []).append(dt)
        dt, r = h.send("RUN " + hx(ZERO24), "p6a|control|r%02d" % rep, "P6AC")
        ctrlA.append(dt)
    h.logf.write("    %-5s %4s %10s %10s %10s %s\n"
                 % ("L", "n", "median", "mean", "stdev", "reps"))
    for L in levels:
        dd = describe(gA[L])
        h.logf.write("    %-5d %4d %10.6f %10.6f %10.6f %s\n"
                     % (L, dd["n"], dd["median"], dd["mean"], dd["stdev"],
                        " ".join("%.5f" % x for x in gA[L])))
    medA = [statistics.median(gA[L]) for L in levels]
    meanA = [statistics.fmean(gA[L]) for L in levels]
    for nm, ys in (("median", medA), ("mean", meanA)):
        bB, seB, rB = slope([float(L) for L in levels], ys)
        h.logf.write("    OLS on per-level %s vs L: slope = %+.6f us/step, 95%% CI "
                     "[%+.3f, %+.3f] us/step, r=%+.3f\n"
                     % (nm, 1e6 * bB, 1e6 * (bB - 2 * seB), 1e6 * (bB + 2 * seB), rB))
    lo, hi = statistics.median(gA[0]), statistics.median(gA[255])
    tt, df = welch(gA[0], gA[255])
    h.logf.write("    direct endpoints: L=0 median=%.6f  L=255 median=%.6f  "
                 "diff=%+.6f s  Welch t=%+.2f -> %s\n"
                 % (lo, hi, hi - lo, tt,
                    "the length byte DOES change the work" if abs(tt) > 3.5
                    else "the length byte changes NOTHING (flat within jitter)"))
    h.logf.write("    controls: %s\n" % fmt(describe(ctrlA)))

    ids = [0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 16, 32, 64, 100, 128, 200, 255, 256,
           512, 1000, 4096, 65535]
    REPS2 = 6
    h.logf.write("\n  6B id-field (2-byte LE) staircase, length fixed at 4, "
                 "%d reps round-robin.\n" % REPS2)
    gB, ctrlB = {}, []
    for rep in range(REPS2):
        for rid in ids:
            b = rec_input(rid, 4)
            dt, r = h.send("RUN " + hx(b), "p6b|I%05d|r%02d" % (rid, rep), "P6B")
            gB.setdefault(rid, []).append(dt)
        dt, r = h.send("RUN " + hx(ZERO24), "p6b|control|r%02d" % rep, "P6BC")
        ctrlB.append(dt)
    h.logf.write("    %-7s %4s %10s %10s %10s\n" % ("id", "n", "median", "mean", "stdev"))
    for rid in ids:
        dd = describe(gB[rid])
        h.logf.write("    %-7d %4d %10.6f %10.6f %10.6f\n"
                     % (rid, dd["n"], dd["median"], dd["mean"], dd["stdev"]))
    ys = [statistics.median(gB[r]) for r in ids]
    bC, seC, rC = slope([float(x) for x in ids], ys)
    h.logf.write("    OLS on per-id median vs id: slope = %+.6f us/id, 95%% CI "
                 "[%+.3f, %+.3f] us/id, r=%+.3f (log-ish spaced ids, so treat as a "
                 "trend check only)\n"
                 % (1e6 * bC, 1e6 * (bC - 2 * seC), 1e6 * (bC + 2 * seC), rC))
    h.logf.write("    spread of the %d id-level medians: %s\n"
                 % (len(ids), fmt(describe(ys))))
    h.logf.write("    controls: %s\n" % fmt(describe(ctrlB)))

    allv = [v for L in levels for v in gA[L]]
    bM, seM, _ = slope([float(L) for L in levels], medA)
    ab = phase6c(h, rand_hexes or [])
    run_replies_here = sorted({s["reply"] for s in h.samples
                               if s["kind"].startswith("P6") and s["kind"] != "P6NONCE"})
    h.logf.write("\n  PHASE 6 VERDICT\n")
    h.logf.write("    - 6A spans length 0..255 (%d levels x %d reps). 95%% CI on the "
                 "per-step cost = [%+.3f, %+.3f] us/step. A walk whose depth tracked "
                 "the length byte would show a monotone ramp far outside that.\n"
                 % (len(levels), REPS, 1e6 * (bM - 2 * seM), 1e6 * (bM + 2 * seM)))
    h.logf.write("    - distinct RUN-family replies in this phase: %r (n=%d samples)\n"
                 % (run_replies_here, len(allv) + len(ctrlA) + len(ctrlB)
                    + sum(len(v) for v in gB.values())))
    h.logf.flush()


def main():
    smoke = "--smoke" in sys.argv
    resume = "--resume" in sys.argv
    analyse = "--analyse" in sys.argv
    staircase = "--staircase" in sys.argv
    logf = open(OUT, "a", encoding="utf-8", errors="replace")
    logf.write("\n" + "#" * 78 + "\n# run started %s  pid=%d  argv=%r\n"
               % (time.strftime("%Y-%m-%d %H:%M:%S"), os.getpid(), sys.argv)
               + "#" * 78 + "\n")
    logf.flush()
    h = Harness(logf)
    h.log("=== latency side-channel measurement: %s:%d ===" % (HOST, PORT))
    try:
        if analyse:
            # OFFLINE ONLY: re-derive the statistics from the stored sample log.
            # This mode never opens a socket.
            n = load_samples(h, OUT)
            h.log("analyse: reloaded %d samples, computing the drift-corrected "
                  "re-analysis (no socket opened)" % n)
            analyse_saved(h)
            h.log("analyse done")
            logf.flush()
            return
        if smoke:
            plan = [("NONCE", "smoke-nonce", "NONCE"),
                    ("MINT 414243", "smoke-mint", "MINT"),
                    ("RUN " + hx(ZERO24), "smoke-run1", "RUN"),
                    ("RUN " + hx(ZERO24), "smoke-run2", "RUN"),
                    ("RUN " + hx(bytes([0xff]) * 24), "smoke-runff", "RUN"),
                    ("RUN " + hx(bytes([0x41]) * 24), "smoke-runA", "RUN"),
                    ("RUN " + hx(ZERO24), "smoke-run3", "RUN"),
                    ("RUN " + hx(bytes(range(1, 25))), "smoke-runseq", "RUN")]
            for c, tag, kind in plan:
                try:
                    dt, r = h.send(c, tag, kind)
                    h.log("smoke %-10s lat=%.6f reply=%r" % (kind, dt, r))
                except Fatal as e:
                    h.log("smoke stopped at %s: %s" % (tag, e))
                    break
            h.log("smoke distinct replies: %r" % sorted(h.replies))
            logf.flush()
            return
        if staircase:
            # carry on the connection numbering from the stored series so the two
            # series in the log can never be confused, then drop the old samples
            # from memory: phase 6 reports on its own connection only.
            n = load_samples(h, OUT)
            rnd = [s["hex"] for s in h.samples if s["tag"].startswith("p2-rand-")][:8]
            h.samples, h.replies, h.run_replies = [], {}, {}
            h.log("staircase: %d samples seen in the log, continuing from conn %d; "
                  "one connection, wide per-step staircases only (%d random inputs "
                  "carried over for the paired A/B retest)" % (n, h.conn_n, len(rnd)))
            h.logf.write("!! PHASE 6 runs on its own connection: the instance behind "
                         "it has a fresh nonce / program image / key, so its absolute "
                         "level is NOT comparable with phases 1-5. Only comparisons "
                         "INSIDE phase 6 (against its own interleaved RUN-zero "
                         "controls) are valid.\n")
            phase6(h, rnd)
            final_reply_report(h)
            h.log("phase6 done: samples=%d" % len(h.samples))
            logf.flush()
            return
        if resume:
            n = load_samples(h, OUT)
            stats, lat = stats_from_samples(h)
            h.log("resume: reloaded %d samples; phases 1-2 are NOT re-measured. "
                  "Phases 4/5 below run on a NEW connection, i.e. a NEW instance "
                  "state (fresh nonce/image/key) - every sample stays labelled with "
                  "its connection number." % n)
            h.logf.write("!! RESUME MODE: phase-4/5 confirmations are on a different "
                         "instance than the phase-2 sweep; compare only with the "
                         "interleaved baseline of the SAME connection.\n")
        else:
            stats, lat = phase1(h)
            phase2(h)
        outliers, d2, drift = report_phase2(h, stats)
        conf = phase4(h, outliers, stats["RUN-zero"])
        phase5(h, stats, conf)
        notdenied = final_reply_report(h)
        h.log("DONE. samples=%d  outliers=%d  non-denied RUN replies=%d"
              % (len(h.samples), len(outliers), len(notdenied)))
    except Fatal as e:
        h.log("FATAL: %s" % e)
        h.logf.write("\n!! STOPPED: %s\n" % e)
        try:
            final_reply_report(h)
        except Exception:
            pass
    except KeyboardInterrupt:
        h.log("interrupted")
        try:
            final_reply_report(h)
        except Exception:
            pass
    finally:
        try:
            if h.c is not None:
                h.c.close()
        except Exception:
            pass
        logf.close()


if __name__ == "__main__":
    main()
