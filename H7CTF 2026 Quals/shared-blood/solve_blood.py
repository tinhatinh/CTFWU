#!/usr/bin/env python
"""Shared Blood (H7TEX crypto) -- recover a VoltEye admin token from the fleet.

GET /fleet  -> 30 device moduli, all e=65537
GET /captured -> RSA/PKCS1v1.5 ciphertext encrypted to device VE-C1E90650

The fleet was keyed "in the same hurry": a pairwise GCD over the moduli finds
exactly one collision, so the target's modulus shares a 512-bit prime with
another device. One gcd + one modular inverse is a full private key.

usage: python solve_blood.py [base_url]
"""
import json
import math
import sys

import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://web-bd09e5c5af420bbc.web.h7tex.com"


def main():
    fleet = requests.get(BASE + "/fleet", timeout=30).json()
    cap = requests.get(BASE + "/captured", timeout=30).json()
    e = fleet["e"]
    devs = [(d["serial"], int(d["n"])) for d in fleet["devices"]]
    tgt = cap["serial"]
    n = dict(devs)[tgt]
    ct = int(cap["ciphertext"], 16)
    print("[*] %d devices, e=%d, target %s (%d-bit modulus), ct %d bits"
          % (len(devs), e, tgt, n.bit_length(), ct.bit_length()))

    shared = [(a, b, math.gcd(an, bn))
              for i, (a, an) in enumerate(devs) for j, (b, bn) in enumerate(devs)
              if j > i and math.gcd(an, bn) > 1]
    print("[*] shared-prime pairs: %d" % len(shared))
    for a, b, g in shared:
        print("    %s ~ %s   gcd = %d-bit prime" % (a, b, g.bit_length()))
    if not shared:
        sys.exit("[-] no repeated prime found")

    a, b, p = next((x, y, g) for x, y, g in shared if tgt in (x, y))
    if n % p:
        sys.exit("[-] gcd does not divide the target modulus")
    q = n // p
    print("[+] target %s factored: p=%d bits, q=%d bits, p*q==n -> %s"
          % (tgt, p.bit_length(), q.bit_length(), p * q == n))

    phi = (p - 1) * (q - 1)
    d = pow(e, -1, phi)
    m = pow(ct, d, n)
    k = (n.bit_length() + 7) // 8          # fixed ciphertext length: PKCS#1's
    msg = m.to_bytes(k, "big")             # leading 0x00 is otherwise lost
    print("[*] decrypted block (%d bytes): %s" % (len(msg), msg.hex()))
    if len(msg) < 3 or msg[0] != 0x00 or msg[1] != 0x02:
        sys.exit("[-] not PKCS#1 v1.5 (00 02 ...); wrong key?")
    sep = msg.index(b"\x00", 2)
    token = msg[sep + 1:]
    print("[+] token = %r" % token.decode(errors="replace"))

    r = requests.post(BASE + "/admin", json={"token": token.decode()}, timeout=30)
    print("[*] POST /admin -> %d %s" % (r.status_code, r.text[:500]))
    j = r.text
    import re
    fl = re.search(r"H7CTF\{[^{}]*\}", j)
    if fl:
        print("[+] FLAG: %s" % fl.group())
        open("flag.txt", "w").write(fl.group())
    else:
        print("[!] no flag in the response")


if __name__ == "__main__":
    main()
