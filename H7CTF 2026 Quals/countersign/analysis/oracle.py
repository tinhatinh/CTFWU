"""Black-box oracle probe for Countersign attestation core (pwn.h7tex.com:43708).

Data collection only. Strictly one connection at a time, sequential, socket
timeouts everywhere, max 3 attempts per command, bail out if silent.
"""

import sys
import os
import re
import time
import socket
import select
import hashlib
import binascii

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOST = "pwn.h7tex.com"
PORT = 43708
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "oracle_results.txt")
EXTRA = len(sys.argv) > 1 and sys.argv[1] == "extra"
fh = open(OUT, "a" if EXTRA else "w", encoding="utf-8", newline="\n")


def log(msg=""):
    s = str(msg)
    print(s, flush=True)
    fh.write(s + "\n")
    fh.flush()


def sec(title):
    log("")
    log("=" * 78)
    log("### " + title)
    log("=" * 78)


class Dead(Exception):
    pass


def connect(reason):
    s = socket.create_connection((HOST, PORT), timeout=15)
    s.settimeout(8)
    t0 = time.perf_counter()
    banner = read_until(s, quiet=0.5, max_time=6)
    log("[conn] %s" % reason)
    log("[conn] banner=%.3fs repr=%r" % (time.perf_counter() - t0, banner))
    return s


def read_until(s, quiet=0.45, max_time=15):
    """Read until socket quiet for `quiet` seconds, EOF, or `max_time`."""
    out = b""
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < max_time:
        remain = max_time - (time.perf_counter() - t0)
        r, _, _ = select.select([s], [], [], min(quiet, remain))
        if not r:
            break
        try:
            d = s.recv(65536)
        except (TimeoutError, socket.timeout):
            break
        except OSError as e:
            log("[read] OSError %r" % (e,))
            break
        if not d:
            out += b"<EOF>"
            break
        out += d
    return out


def cmd(s, line, quiet=0.45, max_time=15):
    """Send one command line; return (reply_str, elapsed, eofs)."""
    t0 = time.perf_counter()
    try:
        s.sendall((line + "\n").encode())
    except OSError as e:
        raise Dead("sendall failed for %r: %r" % (line, e))
    raw = read_until(s, quiet=quiet, max_time=max_time)
    el = time.perf_counter() - t0
    eof = raw.endswith(b"<EOF>")
    if eof:
        raw = raw[:-5]
    return raw.decode("latin-1").replace("\r", ""), el, eof


def one_shot(name, cmds, quiet=0.45, max_time=15, per_line=True):
    """Open a connection, run cmds (list of command lines), close, return dict."""
    res = {"name": name, "replies": [], "times": [], "err": None}
    tries = 0
    while tries < 3:
        tries += 1
        s = None
        try:
            s = connect(name + " (attempt %d)" % tries)
            for c in cmds:
                reply, el, eof = cmd(s, c, quiet=quiet, max_time=max_time)
                res["replies"].append({"cmd": c, "reply": reply, "t": el, "eof": eof})
                res["times"].append(el)
                if eof:
                    res["err"] = "EOF during/after %r" % c
                    break
            break
        except Dead as e:
            res["err"] = str(e)
            log("[one_shot] DEAD %r attempt %d" % (e, tries))
            time.sleep(2)
        except (OSError, socket.timeout) as e:
            res["err"] = "conn %r attempt %d" % (e, tries)
            log("[one_shot] net error %r attempt %d" % (e, tries))
            time.sleep(3)
        finally:
            if s is not None:
                try:
                    s.close()
                except OSError:
                    pass
        if res["err"] and "EOF" in str(res["err"]):
            break
    else:
        raise Dead("giving up after 3 attempts (%s)" % name)
    if per_line:
        for r in res["replies"]:
            log("[cmd] %r -> %r (%.3fs eof=%s)" % (r["cmd"], r["reply"], r["t"], r["eof"]))
    return res


def hexonly(txt):
    return "".join(ch for ch in txt if ch in "0123456789abcdefABCDEF")


def decode_hex_payload(txt):
    """Longest contiguous run of hex chars, ignoring whitespace/newline wrapping."""
    nospace = re.sub(r"\s+", "", txt)
    runs = re.findall(r"[0-9a-fA-F]+", nospace)
    if not runs:
        return ""
    best = max(runs, key=len)
    return best[:-1] if len(best) % 2 else best


def diffbytes(h1, h2):
    """Number of differing output bytes between two equal-length hex strings."""
    if len(h1) != len(h2):
        return None
    a = binascii.unhexlify(h1)
    b = binascii.unhexlify(h2)
    return sum(1 for x, y in zip(a, b) if x != y)


def pat_a(n):
    return bytes(range(n))


def pat_b(n):
    return bytes(((i * 7 + 0x5A) & 0xFF for i in range(n)))


# ---------------------------------------------------------------- phase 1
def phase1():
    sec("PHASE 1 - connection model: nonce + image per-connection or per-instance")
    rows = []
    for i in range(1, 4):
        res = one_shot("phase1-conn%d" % i, ["NONCE", "GET"], quiet=1.2, max_time=40)
        nonce = None
        img_h = None
        img_sha = None
        img_len = None
        for r in res["replies"]:
            if r["cmd"] == "NONCE":
                nonce = hexonly(r["reply"]).lower() or r["reply"]
            else:
                img_h = decode_hex_payload(r["reply"])
                head = r["reply"][:60]
                tail = r["reply"][-60:]
                log("  GET rawlen=%d head=%r tail=%r" % (len(r["reply"]), head, tail))
                if img_h:
                    try:
                        raw = binascii.unhexlify(img_h)
                        img_len = len(raw)
                        img_sha = hashlib.sha256(raw).hexdigest()
                    except binascii.Error as e:
                        log("  GET unhexlify error %r" % (e,))
        rows.append((i, nonce, img_len, img_sha, res["err"]))
        log("[p1] conn%d nonce=%r imgbytes=%r sha=%r err=%r" % (i, nonce, img_len, img_sha, res["err"]))
    log("")
    log("[p1] nonces distinct? %s" % (len({r[1] for r in rows}) > 1))
    log("[p1] images distinct?  %s" % (len({r[3] for r in rows}) > 1))
    return rows


# ---------------------------------------------------------------- phase 2
def phase2():
    sec("PHASE 2 - MINT output length vs input length (two content patterns)")
    lengths = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 16, 17]
    table = {}
    for label, fn in (("A_000102", pat_a), ("B_5a6168", pat_b)):
        cmds = []
        for n in lengths:
            hx = fn(n).hex()
            cmds.append("MINT " + hx if hx else "MINT ")
        res = one_shot("phase2-pattern%s" % label, cmds)
        for n, r in zip(lengths, res["replies"]):
            h = hexonly(r["reply"]).lower()
            table.setdefault(n, {})[label] = (r["reply"].strip(), len(h) // 2 if len(h) % 2 == 0 else "odd:%d" % len(h), h)
        log("[p2] pattern %s err=%r" % (label, res["err"]))
    log("")
    log("len_in | patternA_reply (out_bytes) | patternB_reply (out_bytes)")
    log("-" * 78)
    for n in lengths:
        a = table[n]["A_000102"]
        b = table[n]["B_5a6168"]
        log("%6d | %-34r %3s | %-34r %3s" % (n, a[0][:34], a[1], b[0][:34], b[1]))
    log("")
    for n in lengths:
        log("[p2] len_in=%d A_out=%s" % (n, table[n]["A_000102"][2] or "<none>"))
        log("[p2] len_in=%d B_out=%s" % (n, table[n]["B_5a6168"][2] or "<none>"))
    same = [n for n in lengths if table[n]["A_000102"][2] == table[n]["B_5a6168"][2]]
    log("[p2] lengths where A output == B output (=> content-independent!): %s" % same)
    return table


# ---------------------------------------------------------------- phase 3+4
def phase34():
    sec("PHASE 3 - MINT sensitivity / avalanche (414243 vs 414244 vs 424243)")
    inputs = ["414243", "414244", "424243", "414242", "41424344"]
    res = one_shot("phase3-sens", inputs)
    outs = {}
    for c, r in zip(inputs, res["replies"]):
        outs[c] = hexonly(r["reply"]).lower()
        log("[p3] MINT %s -> %r  (hex=%s)" % (c, r["reply"].strip(), outs[c]))
    base = outs["414243"]
    for c in inputs[1:]:
        d = diffbytes(base, outs[c])
        log("[p3] vs 414243: %s diffbytes=%s (lenA=%d lenB=%d)" % (c, d, len(base) // 2, len(outs[c]) // 2))
    log("[p3] err=%r" % res["err"])

    sec("PHASE 4 - MINT determinism")
    res = one_shot("phase4-det-session1", ["MINT 414243"] * 4)
    s1 = [hexonly(r["reply"]).lower() for r in res["replies"]]
    log("[p4] session1 x4: %s" % s1)
    log("[p4] session1 all equal? %s err=%r" % (len(set(s1)) == 1, res["err"]))
    time.sleep(1)
    res = one_shot("phase4-det-session2", ["MINT 414243"] * 3)
    s2 = [hexonly(r["reply"]).lower() for r in res["replies"]]
    log("[p4] session2 x3: %s" % s2)
    log("[p4] session1 == session2 union size=%d (1 => deterministic across sessions) err=%r"
        % (len(set(s1 + s2)), res["err"]))
    time.sleep(1)
    res = one_shot("phase4-det-session3-zeros", ["MINT 414243"] * 3)
    s3 = [hexonly(r["reply"]).lower() for r in res["replies"]]
    log("[p4] session3 x3: %s" % s3)
    log("[p4] total distinct outputs over %d calls: %d" % (len(s1 + s2 + s3), len(set(s1 + s2 + s3))))

    sec("PHASE 5 - reference vectors (empty / all-zero)")
    ref = ["MINT ", "MINT 00", "MINT 0000", "MINT 00000000", "MINT " + "00" * 3,
           "MINT " + "00" * 8, "MINT " + "00" * 16]
    res = one_shot("phase5-ref", ref + ["MINT " + "00" * 16])
    for c, r in zip(ref, res["replies"]):
        log("[p5] %-24r -> %r" % (c, r["reply"].strip()))
    log("[p5] %-24r -> %r  (repeat)" % ("MINT " + "00" * 16, res["replies"][-1]["reply"].strip()))
    log("[p5] err=%r" % res["err"])


# ---------------------------------------------------------------- phase 6
def phase6(nonce_hint):
    sec("PHASE 6 - RUN behaviour surface")
    res = one_shot("phase6-run-n", ["NONCE"], per_line=True)
    nonce = hexonly(res["replies"][0]["reply"]).lower()
    log("[p6] fresh session nonce=%s (phase1 sample=%s)" % (nonce, nonce_hint))
    nb = binascii.unhexlify(nonce) if len(nonce) % 2 == 0 and nonce else b""
    guesses = [
        ("24 zero", "00" * 24),
        ("24 ff", "ff" * 24),
        ("24 41", "41" * 24),
        ("nonce8+16zero", nb.hex() + "00" * 16),
        ("revnonce8+16zero", nb[::-1].hex() + "00" * 16),
        ("CSGN+20zero", "4353474e" + "00" * 20),
        ("CSGN+nonce+12zero", "4353474e" + nb.hex() + "00" * 12),
        ("nonce8+7zero+CSGN", nb.hex() + "00" * 7 + "4353474e"),
        ("24 30 ascii0", "30" * 24),
    ]
    cmds = ["RUN " + hx for _, hx in guesses]
    res = one_shot("phase6-run-surface", cmds)
    for (lbl, hx), r in zip(guesses, res["replies"]):
        flag = "" if r["reply"].strip().lower() == "denied" else "   <<< NOT 'denied'"
        log("[p6] RUN %-18s %-50s -> %r (%.3fs)%s" % (lbl, hx, r["reply"].strip(), r["t"], flag))
    log("[p6] err=%r" % res["err"])
    log("")
    log("[p6] length validation:")
    bad = [("23 bytes", "00" * 23), ("25 bytes", "00" * 25), ("0 bytes", ""), ("1 byte", "00"),
           ("24 non-hex", "zz" * 24), ("24 odd-hex", "0" * 47)]
    res = one_shot("phase6-run-badlen", ["RUN " + hx for _, hx in bad])
    for (lbl, hx), r in zip(bad, res["replies"]):
        log("[p6] RUN %-10s -> %r" % (lbl, r["reply"].strip()))
    log("[p6] err=%r" % res["err"])


# ---------------------------------------------------------------- phase 7
def phase7():
    sec("PHASE 7 - command budget per connection + per-command latency")
    cmds = ["NONCE"] * 40
    s = connect("phase7-budget")
    n_ok = 0
    times = []
    replies_seen = []
    closed_at = None
    for i, c in enumerate(cmds, 1):
        try:
            reply, el, eof = cmd(s, c, quiet=0.3, max_time=12)
        except Dead as e:
            closed_at = i
            log("[p7] send/receive died at command #%d: %r" % (i, e))
            break
        n_ok += 1
        times.append(el)
        if reply.strip() not in replies_seen:
            replies_seen.append(reply.strip())
        if eof:
            closed_at = i
            log("[p7] server closed after command #%d reply=%r" % (i, reply))
            break
        if i % 5 == 0:
            log("[p7] ...%d commands done, latest %.3fs" % (i, el))
    try:
        s.close()
    except OSError:
        pass
    log("[p7] commands sent=%d replies=%d closed_after=%s" % (len(cmds), n_ok, closed_at))
    log("[p7] distinct replies seen=%r" % (replies_seen,))
    if times:
        log("[p7] NONCE latency: min=%.3f med=%.3f max=%.3f mean=%.3f (n=%d)"
            % (min(times), sorted(times)[len(times) // 2], max(times), sum(times) / len(times), len(times)))

    time.sleep(1)
    for name, mk in (("MINT", lambda i: "MINT " + "%02x" % (i % 251)),
                     ("RUN", lambda i: "RUN " + "%02x" % (i % 251) + "00" * 23)):
        s = connect("phase7-latency-" + name)
        ts = []
        rep = None
        for i in range(12):
            reply, el, eof = cmd(s, mk(i), quiet=0.3, max_time=12)
            ts.append(el)
            rep = reply
            if eof:
                break
        s.close()
        log("[p7] %s x%d latency: min=%.3f med=%.3f max=%.3f mean=%.3f sample_reply=%r"
            % (name, len(ts), min(ts), sorted(ts)[len(ts) // 2], max(ts), sum(ts) / len(ts), rep.strip()))
        time.sleep(1)
    sec("PHASE 7b - long session: 60 mixed commands, does it survive?")
    s = connect("phase7b-long")
    survived = 0
    for i in range(60):
        c = "MINT " + "%04x" % i if i % 2 == 0 else "RUN " + "%02x" % i + "00" * 23
        try:
            reply, el, eof = cmd(s, c, quiet=0.3, max_time=12)
        except Dead as e:
            log("[p7b] died at #%d %r" % (i + 1, e))
            break
        survived += 1
        if eof:
            log("[p7b] EOF at command #%d reply=%r" % (i + 1, reply))
            break
    s.close()
    log("[p7b] completed %d/60 mixed commands" % survived)


def get_image(s):
    reply, el, eof = cmd(s, "GET", quiet=2.5, max_time=60)
    h = decode_hex_payload(reply)
    raw = binascii.unhexlify(h) if h else b""
    return raw, h, el, eof, reply


def analyze(tag, raw, h):
    sha = hashlib.sha256(raw).hexdigest() if raw else None
    log("[img] %s: hexchars=%d bytes=%d sha256=%s" % (tag, len(h), len(raw), sha))
    log("[img] %s: head=%s tail=%s distinct_byte_values=%d"
        % (tag, raw[:16].hex(), raw[-16:].hex(), len(set(raw))))
    return raw, sha


def phase1b():
    sec("PHASE 1b - GET completeness, within-session determinism, cross-session image diff")
    store = []
    for i in range(1, 4):
        s = connect("phase1b-conn%d" % i)
        nraw, _, _ = cmd(s, "NONCE", quiet=0.4, max_time=10)
        nonce = hexonly(nraw).lower()
        r1, h1, t1, eof1, rep1 = get_image(s)
        log("[p1b] conn%d nonce=%s GET#1 t=%.3fs eof=%s reply_chars=%d" % (i, nonce, t1, eof1, len(rep1)))
        a1, sha1 = analyze("conn%d#get1" % i, r1, h1)
        r2, h2, t2, eof2, rep2 = get_image(s)
        a2, sha2 = analyze("conn%d#get2" % i, r2, h2)
        log("[p1b] conn%d GET#1 vs GET#2 same session: identical=%s (sha %s / %s)"
            % (i, sha1 == sha2, sha1[:12] if sha1 else None, sha2[:12] if sha2 else None))
        # does the session nonce appear in the image, forwards or reversed?
        nb = binascii.unhexlify(nonce) if len(nonce) == 16 else b""
        log("[p1b] conn%d nonce fwd found at offset=%s ; reversed found at offset=%s"
            % (i, r1.find(nb) if nb else "n/a", r1.find(nb[::-1]) if nb else "n/a"))
        s.close()
        store.append((i, nonce, r1, sha1))
        time.sleep(1)

    log("")
    log("[p1b] byte-lengths seen across 3 sessions: %s" % [len(x[2]) for x in store])
    log("[p1b] sha256 distinct: %s" % (len({x[3] for x in store}) > 1,))
    for a in range(len(store)):
        for b in range(a + 1, len(store)):
            ia, ib = store[a][2], store[b][2]
            n = min(len(ia), len(ib))
            diff = sum(1 for x, y in zip(ia[:n], ib[:n]) if x != y)
            same_multiset = sorted(ia) == sorted(ib)
            log("[p1b] conn%d vs conn%d: lenA=%d lenB=%d differing_bytes_in_first_%d=%d (%.1f%%) same_byte_multiset=%s"
                % (store[a][0], store[b][0], len(ia), len(ib), n, diff, 100.0 * diff / max(n, 1), same_multiset))
            # where do they differ? coarse map
            blocks = []
            for k in range(0, n, 64):
                d = sum(1 for x, y in zip(ia[k:k + 64], ib[k:k + 64]) if x != y)
                if d:
                    blocks.append((k, d))
            log("[p1b]   64-byte blocks containing diffs: %d of %d; first 12: %s"
                % (len(blocks), (n + 63) // 64, blocks[:12]))
    log("[p1b] magic at image start (ascii): %r" % (bytes([store[0][2][0], store[0][2][1], store[0][2][2], store[0][2][3]]),))
    log("[p1b] first 32 bytes of each session image:")
    for i, nonce, raw, sha in store:
        log("[p1b]   conn%d (%s): %s" % (i, nonce, raw[:32].hex()))
    return store


def phase3fix():
    sec("PHASE 3 (fixed) - MINT avalanche, all in ONE session, with nonce recorded")
    inputs = ["414243", "414244", "424243", "414242", "41424344", "4142434445", "000000", "000001"]
    cmds = ["NONCE"] + ["MINT " + x for x in inputs] + ["MINT " + inputs[0]]
    res = one_shot("phase3fix", cmds)
    nonce = hexonly(res["replies"][0]["reply"]).lower()
    log("[p3] session nonce=%s" % nonce)
    outs = {}
    for c, r in zip(cmds[1:-1], res["replies"][1:-1]):
        outs[c[5:]] = hexonly(r["reply"]).lower()
        log("[p3] MINT %-12s -> %r  raw=%r" % (c[5:], outs[c[5:]], r["reply"].strip()))
    log("[p3] repeat of 414243 (same session, last cmd) -> %r equal=%s"
        % (res["replies"][-1]["reply"].strip(),
           hexonly(res["replies"][-1]["reply"]).lower() == outs.get("414243")))
    base = outs.get("414243", "")
    for k in ["414244", "424243", "414242"]:
        v = outs.get(k, "")
        if len(v) == len(base) and base:
            d = diffbytes(base, v)
            per = [1 if x != y else 0 for x, y in zip(binascii.unhexlify(base), binascii.unhexlify(v))]
            log("[p3] 414243 vs %s -> differing output bytes = %d/6  per-byte-mask=%s" % (k, d, per))
            log("[p3]   nibble diffs: %d/12" % sum(1 for a, b in zip(base, v) if a != b))
    # prefix sensitivity: does a longer input sharing the 3-byte prefix agree on anything?
    log("[p3] 414243=%s 41424344=%s 4142434445=%s (shared prefix bytes equal? %s)"
        % (base, outs.get("41424344"), outs.get("4142434445"),
           [outs.get("41424344", "")[:j] == base[:j] for j in range(0, 12, 2)]))


def phase8():
    sec("PHASE 8 - session-keyed reference vectors (NONCE + MINT + RUN in ONE connection, x2 sessions)")
    mints = ["", "00", "0000", "000000", "00000000", "0000000000000000",
             "00" * 16, "414243", "414244", "424243", "ff" * 16, "000102030405060708090a0b"]
    for sess in range(1, 3):
        cmds = ["NONCE"] + ["MINT " + m for m in mints]
        s = connect("phase8-session%d" % sess)
        reply, _, _ = cmd(s, "NONCE", quiet=0.4, max_time=10)
        nonce = hexonly(reply).lower()
        log("[p8] === session %d, nonce=%s ===" % (sess, nonce))
        nb = binascii.unhexlify(nonce)
        runs = [
            ("24 zero", "00" * 24),
            ("24 ff", "ff" * 24),
            ("24 41", "41" * 24),
            ("nonce8+16zero", nb.hex() + "00" * 16),
            ("revnonce8+16zero", nb[::-1].hex() + "00" * 16),
            ("CSGN+20zero", "4353474e" + "00" * 20),
            ("CSGN+nonce4+16zero", "4353474e" + nb[:4].hex() + "00" * 16),
            ("nonce+CSGN+12zero", nb.hex() + "4353474e" + "00" * 12),
            ("minttag(414243)+18zero", None),
        ]
        for m in mints:
            reply, _, _ = cmd(s, "MINT " + m, quiet=0.4, max_time=10)
            log("[p8] MINT %-34s -> %r" % (m, reply.strip()))
            if m == "414243":
                tag = hexonly(reply).lower()
        for lbl, hx in runs:
            if hx is None:
                hx = (tag or "") + "00" * (24 - len(tag or "") // 2)
            reply, _, _ = cmd(s, "RUN " + hx, quiet=0.4, max_time=10)
            mark = "" if reply.strip().lower() == "denied" else "   <<< NOT denied"
            log("[p8] RUN %-24s %-52s -> %r%s" % (lbl, hx, reply.strip(), mark))
        s.close()
        log("[p8] session %d err=None (closed cleanly)" % sess)
        time.sleep(1)


def phase9():
    sec("PHASE 9 - protocol / parser edge cases (exact error texts)")
    probes = [
        "MINT " + "00" * 17, "MINT " + "0" * 33, "MINT 4", "MINT zz", "MINT 414",
        "MINT " + "00" * 32, "MINT  414243", "mint 414243", "MINT",
        "RUN " + "00" * 23, "RUN " + "00" * 25, "RUN " + "4142" * 12, "RUN " + "00 " * 24,
        "run " + "00" * 24, "RUN", "RUN  " + "00" * 24,
        "FOO", "", "  ", "GET ", "NONCE extra", "QUIT",
    ]
    res = one_shot("phase9-parser", probes)
    for c, r in zip(probes, res["replies"]):
        log("[p9] %-34r -> %r" % (c, r["reply"]))
    log("[p9] err=%r" % res["err"])


def phase10():
    sec("PHASE 10 - idle lifetime of a connection (no command budget seen; is there a time cap?)")
    s = connect("phase10-idle")
    t0 = time.perf_counter()
    cum = 0
    for wait in (30, 60, 120):
        time.sleep(wait)
        cum += wait
        try:
            reply, el, eof = cmd(s, "NONCE", quiet=0.6, max_time=12)
            log("[p10] after %ds idle -> %r (%.3fs, eof=%s)" % (cum, reply.strip(), el, eof))
        except Dead as e:
            log("[p10] after %ds idle -> DEAD %r" % (cum, e))
            break
    log("[p10] total connection age now %.1fs" % (time.perf_counter() - t0))
    s.close()


def phase11():
    sec("PHASE 11 - nonce<->tag pairs over fresh sessions + RUN reply vocabulary sweep")
    import random
    random.seed(20260927)
    log("%-4s %-18s %-14s %-14s %s" % ("#", "NONCE", "MINT(empty)", "MINT(414243)", "RUN(random24)"))
    pairs = []
    for i in range(1, 9):
        s = connect("phase11-pair%d" % i)
        r1, _, _ = cmd(s, "NONCE", quiet=0.4, max_time=10)
        r2, _, _ = cmd(s, "MINT ", quiet=0.4, max_time=10)
        r3, _, _ = cmd(s, "MINT 414243", quiet=0.4, max_time=10)
        rnd = bytes(random.randrange(256) for _ in range(24)).hex()
        r4, _, _ = cmd(s, "RUN " + rnd, quiet=0.4, max_time=10)
        nonce, e, t41, rr = (r1.strip(), r2.strip(), r3.strip(), r4.strip())
        pairs.append((nonce, e, t41))
        log("%-4d %-18s %-14s %-14s %r" % (i, nonce, e, t41, rr))
        s.close()
        time.sleep(0.5)
    log("[p11] distinct empty-tags=%d over %d sessions; distinct 414243-tags=%d"
        % (len({p[1] for p in pairs}), len(pairs), len({p[2] for p in pairs})))

    log("")
    log("[p11] RUN reply vocabulary: 24 random well-formed 24-byte inputs in one session")
    s = connect("phase11-sweep")
    r1, _, _ = cmd(s, "NONCE", quiet=0.4, max_time=10)
    seen = {}
    odd = []
    for i in range(24):
        rnd = bytes(random.randrange(256) for _ in range(24)).hex()
        rr, _, _ = cmd(s, "RUN " + rnd, quiet=0.4, max_time=10)
        v = rr.strip()
        seen[v] = seen.get(v, 0) + 1
        if v.lower() != "denied":
            odd.append((rnd, v))
    s.close()
    log("[p11] session nonce=%s reply histogram=%r" % (r1.strip(), seen))
    log("[p11] non-'denied' replies: %r" % (odd,))

    log("")
    log("[p11] MINT reply histogram over the same kind of sweep (24 random 16-byte inputs, one session)")
    s = connect("phase11-mint-sweep")
    r1, _, _ = cmd(s, "NONCE", quiet=0.4, max_time=10)
    lens = {}
    for i in range(24):
        k = random.choice([1, 2, 3, 4, 6, 8, 11, 16])
        hx = bytes(random.randrange(256) for _ in range(k)).hex()
        rr, _, _ = cmd(s, "MINT " + hx, quiet=0.4, max_time=10)
        body = rr.strip()
        lens[(k, len(body) // 2 if all(c in "0123456789abcdef" for c in body) else body)] = \
            lens.get((k, len(body) // 2 if all(c in "0123456789abcdef" for c in body) else body), 0) + 1
    s.close()
    log("[p11] session nonce=%s (len_in, out_bytes_or_text) histogram=%r" % (r1.strip(), lens))


def main():
    log("oracle.py run %s mode=%s" % (time.strftime("%Y-%m-%d %H:%M:%S"), "EXTRA" if EXTRA else "FULL"))
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "p11":
            phase11()
        elif EXTRA:
            phase1b()
            phase3fix()
            phase8()
            phase9()
            phase10()
        else:
            rows = phase1()
            hint = rows[0][1] if rows else None
            phase2()
            phase34()
            phase6(hint)
            phase7()
    except Dead as e:
        log("!!! ABORT: service unresponsive: %r" % (e,))
    except Exception as e:
        log("!!! ERROR %r" % (e,))
        raise
    finally:
        log("")
        log("=== END ===")
        fh.close()


if __name__ == "__main__":
    main()
