#!/usr/bin/env python3
"""Two-time-pad / reused-CTR-nonce helper (CDCTF "Cosmic Call" style).

Same nonce+counter => same keystream, so:
  C1 ^ C2 = P1 ^ P2                      (keystream cancels)  -> crib dragging
  KS = C ^ P  for any known plaintext    -> decrypts every other message

Modes
  --selftest
  --ct1 HEX --ct2 HEX --crib TEXT          drag TEXT across C1^C2
  --ct1 HEX --seed POS:TEXT [--others HEX[,HEX...]]
        treat TEXT as plaintext of ct1 at byte POS, print the recovered
        keystream and use it on any other ciphertexts given.
"""
import argparse, sys

PRINTABLE = set(range(0x20, 0x7F)) | {0x09, 0x0A, 0x0D}


def unhex(s):
    return bytes.fromhex("".join(str(s).split()))


def xor(a, b):
    n = min(len(a), len(b))
    return bytes(x ^ y for x, y in zip(a[:n], b[:n]))


def printable(b):
    return all(c in PRINTABLE for c in b)


def drag(ct1, ct2, crib, top=15):
    crib = crib.encode() if isinstance(crib, str) else crib
    x = xor(ct1, ct2)
    hits = []
    for pos in range(len(x) - len(crib) + 1):
        d = xor(x[pos:pos + len(crib)], crib)
        if printable(d):
            score = sum(1 for c in d if 0x61 <= c <= 0x7A or 0x30 <= c <= 0x39 or c == 0x20)
            hits.append((score, pos, d.decode("latin-1")))
    hits.sort(key=lambda t: (-t[0], t[1]))
    return hits[:top]


def recover_keystream(ct, pos, plain):
    """keystream bytes for [pos, pos+len(plain)) of ct."""
    ks = bytearray()
    for i, ch in enumerate(plain):
        ks.append(ct[pos + i] ^ ch)
    return bytes(ks)


def apply_keystream(pos, ks, other_cts):
    out = []
    for n, ct in enumerate(other_cts):
        buf = bytearray(ct)
        for i, k in enumerate(ks):
            j = pos + i
            if j < len(buf):
                buf[j] ^= k
        out.append(bytes(buf))
    return out


def selftest():
    from Crypto.Cipher import AES
    from Crypto.Util import Counter
    key = bytes(range(16))
    enc = lambda p: AES.new(key, AES.MODE_CTR, counter=Counter.new(128, initial_value=0)).encrypt(p)
    p1 = b"cdctf{FL@g!_g03s_h3r3} and the relay says hello over UDP"
    p2 = b"mission telemetry packet 7: uplink nominal, downlink jammed!!"
    p3 = b"cdctf{FL@g!_g03s_h3r3} is reused because nobody rotated the nonce"
    c1, c2, c3 = enc(p1), enc(p2), enc(p3)
    fails = 0

    assert xor(c1, c2) == xor(p1, p2)
    print("[1] C1^C2 == P1^P2 (keystream cancels) ......... ok")

    hits = drag(c1, c2, "cdctf{")
    ok = any(h[1] == 0 and h[2] == "missio" for h in hits)
    print(f"[2] crib 'cdctf{{' at pos 0 -> 'missio' ......... {'ok' if ok else 'FAIL'}")
    for s, pos, d in hits[:3]:
        print(f"      pos {pos:3d} score {s:2d}  {d!r}")
    fails += not ok

    ks = recover_keystream(c1, 0, p1[:20])
    ok2 = xor(c2[:20], ks[:20]) == p2[:20]
    print(f"[3] 20 known P1 bytes decrypt P2 prefix ........ {'ok' if ok2 else 'FAIL'}")
    print(f"      P2 prefix = {xor(c2, ks)[:20]!r}")
    fails += not ok2

    dec = apply_keystream(0, ks, [c3])[0]
    ok3 = dec[:20] == p3[:20]
    print(f"[4] same keystream lifts a 3rd message ......... {'ok' if ok3 else 'FAIL'}")
    print(f"      P3 prefix = {dec[:20]!r}")
    fails += not ok3

    bad = drag(c1, c2, "\x00\x01\x02\x03no-such-crib-here")
    print(f"[5] bogus crib yields no placement ............. {'ok' if not bad else 'FAIL'}")
    fails += bool(bad)

    print("\n" + ("SELFTEST FAILED" if fails else "SELFTEST PASSED"))
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ct1"); ap.add_argument("--ct2")
    ap.add_argument("--crib", default="cdctf{")
    ap.add_argument("--seed"); ap.add_argument("--others")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.ct1:
        print(__doc__); return 2
    c1 = unhex(a.ct1)
    if a.seed:
        pos, text = a.ct1 and a.seed.split(":", 1)
        pos = int(pos)
        ks = recover_keystream(c1, pos, text.encode())
        print(f"keystream[{pos}:{pos+len(ks)}] = {ks.hex()}")
        print(f"ct1 decoded there            = {text}")
        if a.others:
            for spec in a.others.split(","):
                oc = unhex(spec)
                d = apply_keystream(pos, ks, [oc])[0]
                print(f"other({len(oc)}B) with that keystream = {d!r}")
        return 0
    if not a.ct2:
        print("need --ct2 for crib dragging, or --seed POS:TEXT"); return 2
    c2 = unhex(a.ct2)
    print(f"len1={len(c1)} len2={len(c2)}")
    print(f"XOR = {xor(c1,c2).hex()}")
    hits = drag(c1, c2, a.crib)
    if not hits:
        print("no printable placement for that crib")
    for s, pos, d in hits:
        print(f"pos {pos:3d} score {s:2d}  other = {d!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
