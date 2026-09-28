#!/usr/bin/env python3
"""Find / verify an Ed25519 custody seed against a target public key.

Given candidate 32-byte seeds (hex), check whether pubkey(seed) equals the
target public key read from a raw 32-byte file (default ..\\..\\files\\pubkey.bin),
and if so emit a signature over a test message (default a 24-byte nonce-sized
message).

Cross-check policy: when the `cryptography` library is importable we compute
the public key two ways -- our pure stdlib ed.py, and OpenSSL via
Ed25519PrivateKey.from_private_bytes(seed) (the OpenSSL-style seed is the very
same 32 bytes). If OpenSSL says MATCH but ed.py says NO-MATCH, that is a bug in
ed.py, so we flag it loudly. We also compare signatures byte-for-byte.

Usage:
    python find_seed.py <seed_hex | candidates_file> [options]
    python find_seed.py --seed <hex> [--seed <hex> ...]
    python find_seed.py candidates.txt
Options:
    --pubkey PATH   32-byte raw pubkey file (default ..\\..\\files\\pubkey.bin)
    --msg HEX       hex message to sign on a match (default 24 zero bytes)
    --file          treat the first positional arg as a file of hex seeds
    -h, --help
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ed

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
    )
    HAVE_CRYPTO = True
except Exception:  # noqa: BLE001
    HAVE_CRYPTO = False

DEFAULT_PUBKEY = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "..", "..", "files", "pubkey.bin")
)


def read_pubkey(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    if len(raw) != 32:
        raise SystemExit("pubkey file %s is %d bytes, expected 32" % (path, len(raw)))
    return raw


def clean_seed_hex(tok):
    tok = tok.strip()
    if not tok or tok.startswith("#"):
        return None
    # tolerate spaces / colons between bytes
    tok = tok.replace(" ", "").replace(":", "")
    return tok


def parse_candidates(args):
    seeds = []
    for s in args.seed:
        h = clean_seed_hex(s)
        if h:
            seeds.append(h)
    for pos in args.positional:
        h = clean_seed_hex(pos)
        if h is None:
            continue
        # If it names an existing file (and isn't pure hex) treat as candidate list.
        looks_like_hex = all(c in "0123456789abcdefABCDEF" for c in h) and len(h) == 64
        if (args.file or os.path.exists(pos)) and not looks_like_hex:
            with open(pos, "r") as fh:
                for line in fh:
                    hh = clean_seed_hex(line)
                    if hh:
                        seeds.append(hh)
        elif looks_like_hex:
            seeds.append(h)
        else:
            # fall back: assume it is a file of hex seeds
            with open(pos, "r") as fh:
                for line in fh:
                    hh = clean_seed_hex(line)
                    if hh:
                        seeds.append(hh)
    return seeds


def to_bytes(hexstr):
    if len(hexstr) != 64:
        return None
    try:
        return bytes.fromhex(hexstr)
    except ValueError:
        return None


def main():
    p = argparse.ArgumentParser(add_help=True, description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("positional", nargs="*", help="hex seed(s) or a file of hex seeds")
    p.add_argument("--seed", action="append", default=[], help="explicit hex seed (repeatable)")
    p.add_argument("--pubkey", default=DEFAULT_PUBKEY, help="path to 32-byte raw pubkey")
    p.add_argument("--msg", default="00" * 24, help="hex message to sign on a match")
    p.add_argument("--file", action="store_true", help="first positional is a file of hex seeds")
    args = p.parse_args()

    target = read_pubkey(args.pubkey)
    try:
        msg = bytes.fromhex(args.msg)
    except ValueError:
        raise SystemExit("--msg must be hex")

    print("target pubkey : " + target.hex())
    print("pubkey file   : " + args.pubkey)
    print("test message  : " + msg.hex() + " (%d bytes)" % len(msg))
    print("cryptography  : " + ("available" if HAVE_CRYPTO else "NOT available (ed.py only)"))
    print("-" * 72)

    candidates = parse_candidates(args)
    if not candidates:
        raise SystemExit("no candidate seeds given")

    found = 0
    bugs = 0
    for hexstr in candidates:
        seed = to_bytes(hexstr)
        if seed is None:
            print("  SKIP   %s  (not 32 raw bytes / 64 hex chars)" % hexstr)
            continue

        our_pk = ed.pubkey(seed)
        our_match = our_pk == target

        lib_match = None
        lib_pk = None
        sig_agree = None
        if HAVE_CRYPTO:
            lib_pk = Ed25519PrivateKey.from_private_bytes(seed).public_key().public_bytes_raw()
            lib_match = lib_pk == target

        tag = "MATCH   " if our_match else "no-match"
        print("  %s seed=%s" % (tag, hexstr))
        print("             ed.py pk = %s" % our_pk.hex())
        if HAVE_CRYPTO:
            print("             lib   pk = %s%s" % (lib_pk.hex(), "" if lib_match == our_match else "  <-- DIVERGE"))
            # Cross-check: library says match but ed.py does not => ed.py bug.
            if lib_match and not our_match:
                print("             !!! BUG: matches under cryptography but not ed.py -- ed.py is wrong")
                bugs += 1
            if our_match and not lib_match:
                print("             !!! ed.py matches but library does not -- investigate (target/transcription)")

        if our_match:
            found += 1
            sig = ed.sign(seed, msg)
            print("             ed.py signature : " + sig.hex())
            if HAVE_CRYPTO:
                lib_sig = Ed25519PrivateKey.from_private_bytes(seed).sign(msg)
                sig_agree = sig == lib_sig
                print("             lib signature   : " + lib_sig.hex())
                print("             signatures agree: %s" % sig_agree)
                if not sig_agree:
                    print("             !!! BUG: ed.py signature differs from cryptography")
                    bugs += 1
        print()

    print("=" * 72)
    print("candidates checked : %d" % len(candidates))
    print("matches (ed.py)    : %d" % found)
    if HAVE_CRYPTO:
        print("implementation bugs: %d" % bugs)
    if bugs:
        sys.exit(3)
    sys.exit(0 if found else 1)


if __name__ == "__main__":
    main()
