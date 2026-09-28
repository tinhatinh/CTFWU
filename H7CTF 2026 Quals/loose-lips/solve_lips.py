#!/usr/bin/env python
"""Loose Lips (H7TEX crypto) -- recover both CKKS service secret keys.

ckks.py (shipped by the challenge):
    ct = (b, a) with b = -a*s + m + e   (mod Q),  e = small(3), a uniform
    decrypt: d = b + a*s = m + e, returned as approximate decoded slots

The key is `small(1)`, i.e. a ternary vector of length N=8 -> only 3**8 = 6561
candidates. The service hands out (b, a) for any plaintext we ask for, so we can
encrypt zeros (m = 0) and keep only the keys for which b + a*s has every centred
coefficient inside [-3, 3], which is exactly the noise budget. No decrypt oracle
is needed at all, so v2's noise flooding protects nothing.

usage: python solve_lips.py [base_url]
"""
import itertools
import json
import sys

import requests

sys.path.insert(0, "files")
import ckks  # the scheme itself, imported so ring arithmetic matches the server

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://web-550a48e366fd77e3.web.h7tex.com"
N = ckks.N
NOISE_BOUND = 3          # encrypt() uses small(3)
ZERO = [0.0] * (N // 2)
FLAG = __import__("re").compile(rb"H7CTF\{[^{}]*\}")


def post(path, payload):
    r = requests.post(BASE + path, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def candidates(b, a, values):
    """Ternary keys s with b + a*s - encode(values) inside the noise budget."""
    m = ckks.encode(values)
    out = []
    for s in itertools.product((-1, 0, 1), repeat=N):
        s = list(s)
        d = ckks.ring_add(b, ckks.ring_mul(a, s))
        res = ckks.ring_sub(d, m)
        if max(abs(int(c.real)) for c in ckks._center(res)) <= NOISE_BOUND:
            out.append(s)
    return out


def claim(version):
    print("\n=== %s ===" % version)
    c1 = post("/%s/encrypt" % version, {"values": ZERO})
    print("[*] ct id=%s" % c1["id"])
    cand = candidates(c1["b"], c1["a"], ZERO)
    print("[*] ternary keys matching the zero-plaintext ciphertext: %d -> %s"
          % (len(cand), cand[:4]))
    if len(cand) > 1:                      # disambiguate with a second, nonzero ct
        vals = [1.5, -2.25, 0.5, 3.0][: N // 2]
        c2 = post("/%s/encrypt" % version, {"values": vals})
        keep = [s for s in cand if s in candidates(c2["b"], c2["a"], vals)]
        cand = keep
        print("[*] after a second ciphertext with values=%s: %d left" % (vals, len(cand)))
    if not cand:
        sys.exit("[-] no candidate key for %s" % version)
    s = cand[0]
    print("[+] secret key %s = %s" % (version, s))
    resp = post("/%s/recover" % version, {"s": s})
    print("[*] /recover -> %s" % json.dumps(resp)[:400])
    m = FLAG.search(json.dumps(resp).encode())
    if m:
        print("[+] FLAG %s: %s" % (version, m.group().decode()))
        return m.group().decode()
    print("[!] no H7CTF{...} in this response")
    return None


def main():
    flags = {}
    for v in ("v1", "v2"):
        try:
            f = claim(v)
        except Exception as exc:                      # noqa: BLE001
            print("[-] %s failed: %r" % (v, exc))
            f = None
        if f:
            flags[v] = f
    with open("flags.txt", "w") as fh:
        for k, v in flags.items():
            fh.write("%s %s\n" % (k, v))
    print("\n[*] recovered: %s" % (flags or "nothing"))


if __name__ == "__main__":
    main()
