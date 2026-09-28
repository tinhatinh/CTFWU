#!/usr/bin/env python
"""Owner's Draw (H7TEX crypto) -- forge an owner payout with one captured slip.

The receiver authenticates webhooks with   X-Signature = SHA256(secret || body).
SHA-256 is Merkle-Damgard, so a captured tag *is* the cipher state after the
message and its padding: continuing that state over extra bytes yields a valid
tag for  body || pad || extra  without ever learning the secret.

The original message length (secret + body) is unknown, but the padding depends
on it, so the secret length is brute-forced; each guess produces one (body, tag)
pair and the server itself is the oracle.

usage: python solve_draw.py [base_url]
"""
import hashlib
import re
import struct
import sys

import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://web-b39cfff63c4c78b9.web.h7tex.com"
K = [
    0x428A2F98, 0x71374491, 0xB5C0FBCF, 0xE9B5DBA5, 0x3956C25B, 0x59F111F1, 0x923F82A4, 0xAB1C5ED5,
    0xD807AA98, 0x12835B01, 0x243185BE, 0x550C7DC3, 0x72BE5D74, 0x80DEB1FE, 0x9BDC06A7, 0xC19BF174,
    0xE49B69C1, 0xEFBE4786, 0x0FC19DC6, 0x240CA1CC, 0x2DE92C6F, 0x4A7484AA, 0x5CB0A9DC, 0x76F988DA,
    0x983E5152, 0xA831C66D, 0xB00327C8, 0xBF597FC7, 0xC6E00BF3, 0xD5A79147, 0x06CA6351, 0x14292967,
    0x27B70A85, 0x2E1B2138, 0x4D2C6DFC, 0x53380D13, 0x650A7354, 0x766A0ABB, 0x81C2C92E, 0x92722C85,
    0xA2BFE8A1, 0xA81A664B, 0xC24B8B70, 0xC76C51A3, 0xD192E819, 0xD6990624, 0xF40E3585, 0x106AA070,
    0x19A4C116, 0x1E376C08, 0x2748774C, 0x34B0BCB5, 0x391C0CB3, 0x4ED8AA4A, 0x5B9CCA4F, 0x682E6FF3,
    0x748F82EE, 0x78A5636F, 0x84C87814, 0x8CC70208, 0x90BEFFFA, 0xA4506CEB, 0xBEF9A3F7, 0xC67178F2,
]
M = 0xFFFFFFFF


def ror(x, n):
    return ((x >> n) | (x << (32 - n))) & M


def compress(h, block):
    w = list(struct.unpack(">16I", block))
    for i in range(16, 64):
        s0 = ror(w[i - 15], 7) ^ ror(w[i - 15], 18) ^ (w[i - 15] >> 3)
        s1 = ror(w[i - 2], 17) ^ ror(w[i - 2], 19) ^ (w[i - 2] >> 10)
        w.append((w[i - 16] + s0 + w[i - 7] + s1) & M)
    a, b, c, d, e, f, g, hh = h
    for i in range(64):
        S1 = ror(e, 6) ^ ror(e, 11) ^ ror(e, 25)
        ch = (e & f) ^ (~e & g)
        t1 = (hh + S1 + ch + K[i] + w[i]) & M
        S0 = ror(a, 2) ^ ror(a, 13) ^ ror(a, 22)
        mj = (a & b) ^ (a & c) ^ (b & c)
        t2 = (S0 + mj) & M
        hh, g, f, e, d, c, b, a = g, f, e, (d + t1) & M, c, b, a, (t1 + t2) & M
    return tuple((x + y) & M for x, y in zip(h, (a, b, c, d, e, f, g, hh)))


def sha256_state(msg):
    return list(hashlib.sha256(msg).digest())


def len_extend(tag, orig_total, suffix):
    """tag: 32 raw bytes of SHA256(secret||body); orig_total: len(secret)+len(body).

    The published tag is the state after the *whole* padded original message, so
    the bytes we splice in must be that padding in full: 0x80, zero fill, and the
    64-bit big-endian bit length of the original message. Continuing from the tag
    then hashes suffix||padding||new_length.
    """
    h = struct.unpack(">8I", tag)
    pad = (b"\x80" + b"\x00" * ((55 - orig_total) % 64) + struct.pack(">Q", orig_total * 8))
    new_total = orig_total + len(pad) + len(suffix)
    data = suffix + b"\x80"
    data += b"\x00" * ((56 - len(data) % 64) % 64)
    data += struct.pack(">Q", new_total * 8)
    for i in range(0, len(data), 64):
        h = compress(h, data[i:i + 64])
    return pad + suffix, struct.pack(">8I", *h).hex()


def self_test():
    """Prove the pure-python extension agrees with hashlib on a known secret."""
    secret, body, suffix = b"hunter2hunter2", b"a=1&role=guest", b"&role=owner"
    tag = hashlib.sha256(secret + body).digest()
    ext, forged = len_extend(tag, len(secret) + len(body), suffix)
    # the server hashes secret || body || spliced-padding || suffix
    real = hashlib.sha256(secret + body + ext).hexdigest()
    ok = forged == real
    print("[*] self-test: hashlib=%s  forged=%s  ->  %s"
          % (real[:16], forged[:16], "OK" if ok else "MISMATCH"))
    if not ok:
        sys.exit("[-] length-extension implementation is wrong")
    return body + ext


def main():
    self_test()
    sample = requests.get(BASE + "/sample", timeout=30).json()
    body = sample["body"].encode()
    tag = bytes.fromhex(sample["X-Signature"])
    print("[*] captured body (%d B): %s" % (len(body), body.decode()))
    print("[*] captured tag        : %s" % tag.hex())
    print("[*] genuine POST: %s" % requests.post(BASE + "/webhook", data=body,
                                                 headers={"X-Signature": tag.hex()},
                                                 timeout=30).text)

    suffix = b"&role=owner"
    for s_len in range(0, 65):
        ext, forged = len_extend(tag, s_len + len(body), suffix)
        r = requests.post(BASE + "/webhook", data=body + ext,
                          headers={"X-Signature": forged}, timeout=30)
        txt = r.text.strip()
        if r.status_code != 401:
            print("[+] secret length guess=%2d  body tail=%r  sig=%s"
                  % (s_len, (body + ext)[-16:], forged[:16]))
            print("[+] /webhook -> %d %s" % (r.status_code, txt))
            m = re.search(r"H7CTF\{[^{}]*\}", txt)
            if m:
                print("[+] FLAG: %s" % m.group())
                open("flag.txt", "w").write(m.group())
                return
            return
    print("[-] no guess in 0..64 accepted")


if __name__ == "__main__":
    main()
