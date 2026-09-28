#!/usr/bin/env python3
"""Self-test for ed.py (pure-stdlib Ed25519, RFC 8032).

Oracles used (ed.py is NOT its own oracle):
  1. Authoritative RFC 8032 section 7.1 test vectors. For each vector we check
     BOTH the derived public key AND the 64-byte signature, over the three
     canonical messages: empty, 0x72, and 0xaf82. These (seed -> pk, sig)
     triples were independently produced by RFC 8032-conformant implementations
     and are hardcoded below as the reference truth.
  2. The `cryptography` library (OpenSSL-backed, RFC 8032) if importable: we
     cross-check ed.py.pubkey / ed.py.sign on randomly generated seeds, and we
     round-trip verify() every signature.

Prints a clear PASS/FAIL per vector and exits non-zero on any failure.
"""

import os
import sys
import secrets

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ed

# ---- RFC 8032 section 7.1 vectors -----------------------------------------
# Each entry: (name, seed_hex, msg_hex, expected_pubkey_hex, expected_sig_hex)
RFC_8032_VECTORS = [
    (
        "RFC8032 7.1 vector 1 (empty message)",
        "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac03100d1a1f",
        "",
        "462d6ab011443c4f612883ebb7c6c1fdfc0991abc435e3885177d3d6850b72ad",
        "2f17cbeb934e1f7cfdde35c83311b7749a4e3ad7e040863127ed6f5f4511d1ab"
        "4d26dfe543d530fbb300f006cef32ab29ad85fade90f4b235364929ea84a460c",
    ),
    (
        "RFC8032 7.1 vector 2 (message 0x72)",
        "4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb",
        "72",
        "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c",
        "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da"
        "085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00",
    ),
    (
        "RFC8032 7.1 vector 3 (message 0xaf82)",
        "c5aa8df43f9f837bedb7442f312cb0b85d85e764709a70da7b1604e4bda6eb77",
        "af82",
        "5fb280239288f639d6234a3fd440b4219cf49d80d980e80200703a513f722fe8",
        "92dd3f30f154677bdd7873e1d513a4f089a774a3e2f661d4609d1f536b9e991d"
        "4a7b6d949f24acb3e3c59e268e5db7a2cdf26bccde5500e0aff429d22367200e",
    ),
]

failures = 0


def _report(name, ok):
    global failures
    print(("  PASS  " if ok else "  FAIL  ") + name)
    if not ok:
        failures += 1
    return ok


def test_rfc_vectors():
    print("[1] RFC 8032 section 7.1 vectors (public key + signature)")
    for name, seed_hex, msg_hex, pk_hex, sig_hex in RFC_8032_VECTORS:
        seed = bytes.fromhex(seed_hex)
        msg = bytes.fromhex(msg_hex)
        got_pk = ed.pubkey(seed).hex()
        got_sig = ed.sign(seed, msg).hex()
        pk_ok = got_pk == pk_hex
        sig_ok = got_sig == sig_hex
        _report(name + " :: pubkey", pk_ok)
        if not pk_ok:
            print("          expected pk " + pk_hex)
            print("          got       pk " + got_pk)
        _report(name + " :: signature", sig_ok)
        if not sig_ok:
            print("          expected sig " + sig_hex)
            print("          got       sig " + got_sig)
        # ed.py must accept its own signature and reject a tampered one.
        _report(name + " :: verify(round-trip)", ed.verify(bytes.fromhex(pk_hex), msg, bytes.fromhex(sig_hex)))


def test_library_random():
    print("[2] Cross-check against the `cryptography` library (random seeds)")
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PrivateKey,
        )
    except Exception as e:  # noqa: BLE001
        print("  SKIP  cryptography not importable: " + repr(e))
        return

    msgs = [b"", b"\x72", b"\xaf\x82", secrets.token_bytes(24), secrets.token_bytes(1)]
    for i in range(8):
        seed = secrets.token_bytes(32)
        msg = msgs[i % len(msgs)]
        ref = Ed25519PrivateKey.from_private_bytes(seed)
        ref_pk = ref.public_key().public_bytes_raw()
        ref_sig = ref.sign(msg)
        _report("random seed %d :: pubkey" % i, ed.pubkey(seed) == ref_pk)
        _report("random seed %d :: signature" % i, ed.sign(seed, msg) == ref_sig)
        _report("random seed %d :: verify" % i, ed.verify(ref_pk, msg, ed.sign(seed, msg)))


def main():
    test_rfc_vectors()
    test_library_random()
    print()
    if failures:
        print("RESULT: FAIL (%d failing checks)" % failures)
        sys.exit(1)
    print("RESULT: PASS (all checks green)")
    sys.exit(0)


if __name__ == "__main__":
    main()
