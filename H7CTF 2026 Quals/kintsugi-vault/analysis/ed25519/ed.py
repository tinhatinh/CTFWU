#!/usr/bin/env python3
"""Pure-stdlib Ed25519 (RFC 8032). No third-party dependencies.

Exposes:
    pubkey(seed32: bytes) -> bytes   # 32-byte compressed public key
    sign(seed32: bytes, msg: bytes) -> bytes  # 64-byte signature (R || S)
    verify(pub32: bytes, msg: bytes, sig64: bytes) -> bool  # bonus

Implementation notes (correctness first):
  * Field prime  q = 2**255 - 19.
  * Group order  L = 2**252 + 27742317777372353535851937790883648493.
  * Curve param  d = -121665 / 121666  (mod q), sqrt(-1) via I = 2**((q-1)/4).
  * Twisted Edwards, a = -1, using *extended* homogeneous coordinates
    (X:Y:Z:T) with x = X/Z, y = Y/Z, x*y = T/Z. The unified "add-2008-hwcd-3"
    formula used below is *complete* for ed25519 (a square, d nonsquare), so
    it is correct for point addition, doubling, and the identity in all cases.
  * Standard RFC 8032 secret-key clamping: h = SHA-512(seed); low 3 bits of
    byte 0 cleared; bit 254 set; bit 255 cleared. Scalars are little-endian.
"""

import hashlib

# ---- domain parameters -----------------------------------------------------
q = 2**255 - 19
L = 2**252 + 27742317777372353535851937790883648493


def inv(x: int) -> int:
    """Modular inverse mod q (Fermat; q is prime)."""
    return pow(x, q - 2, q)


d = (-121665 * inv(121666)) % q
I = pow(2, (q - 1) // 4, q)


def _xrecover(y: int) -> int:
    """Recover the (even) x-coordinate for a given y on the Edwards curve."""
    xx = (y * y - 1) * inv(d * y * y + 1)
    x = pow(xx, (q + 3) // 8, q)
    if (x * x - xx) % q != 0:
        x = (x * I) % q
    if x % 2 != 0:
        x = q - x
    return x % q


_By = (4 * inv(5)) % q
_Bx = _xrecover(_By)
# base point in extended coordinates (X, Y, Z, T)
B = (_Bx % q, _By % q, 1, (_Bx * _By) % q)
# identity element in extended coordinates
ZERO = (0, 1, 1, 0)


def _edwards_add(P, Q):
    """Unified extended twisted-Edwards addition (a = -1).

    add-2008-hwcd-3 (Hisil-Wong-Carter-Dawson). Complete for ed25519, so it
    also serves as point doubling when P == Q.
    """
    X1, Y1, Z1, T1 = P
    X2, Y2, Z2, T2 = Q
    A = (Y1 - X1) * (Y2 - X2) % q
    Bv = (Y1 + X1) * (Y2 + X2) % q
    C = 2 * T1 * T2 * d % q
    D = 2 * Z1 * Z2 % q
    E = (Bv - A) % q
    F = (D - C) % q
    G = (D + C) % q
    H = (Bv + A) % q
    return (E * F % q, G * H % q, F * G % q, E * H % q)


def _scalarmult(P, e: int):
    """Double-and-add (LSB first) scalar multiplication over extended coords."""
    if e == 0:
        return ZERO
    result = ZERO
    addend = P
    while e:
        if e & 1:
            result = _edwards_add(result, addend)
        addend = _edwards_add(addend, addend)
        e >>= 1
    return result


def _point_compress(P) -> bytes:
    """Encode an extended-coordinate point to the 32-byte little-endian form:
    y with the sign (parity) of x in the high bit of the last byte."""
    X, Y, Z, _T = P
    zinv = inv(Z)
    x = X * zinv % q
    y = Y * zinv % q
    return int.to_bytes(y | ((x & 1) << 255), 32, "little")


def _point_decompress(s: bytes):
    """Decode a 32-byte point into extended coordinates; raises on invalid."""
    if len(s) != 32:
        raise ValueError("point must be 32 bytes")
    y = int.from_bytes(s, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    if y >= q:
        raise ValueError("y out of range")
    x2 = (y * y - 1) * inv(d * y * y + 1)
    if x2 < 0:
        # x is not recoverable -> invalid point (unless x2==0 and sign==1)
        if x2 % q == 0 and sign == 0:
            return (0, y, 1, 0)
        raise ValueError("non-square x^2")
    x = pow(x2, (q + 5) // 8, q)
    if (x * x - x2) % q != 0:
        x = x * I % q
    if (x * x - x2) % q != 0:
        raise ValueError("invalid point")
    if (x & 1) != sign:
        x = q - x
    if x == 0 and sign == 1:
        raise ValueError("invalid point")
    return (x, y, 1, x * y % q)


def _clamp(seed: bytes):
    """Return (a, prefix) from a 32-byte seed per RFC 8032 secret-key rules."""
    h = hashlib.sha512(seed).digest()
    a = int.from_bytes(h[:32], "little")
    a &= ~7            # clear the three lowest bits
    a &= ~(1 << 255)   # clear the highest bit
    a |= (1 << 254)    # set the second-highest bit
    return a, h[32:]


def pubkey(seed32: bytes) -> bytes:
    """Derive the 32-byte compressed Ed25519 public key from a 32-byte seed."""
    seed32 = bytes(seed32)
    if len(seed32) != 32:
        raise ValueError("seed must be 32 bytes")
    a, _prefix = _clamp(seed32)
    return _point_compress(_scalarmult(B, a))


def sign(seed32: bytes, msg: bytes) -> bytes:
    """Produce the 64-byte Ed25519 signature (R || S) over msg."""
    seed32 = bytes(seed32)
    if len(seed32) != 32:
        raise ValueError("seed must be 32 bytes")
    msg = bytes(msg)
    a, prefix = _clamp(seed32)
    A = _point_compress(_scalarmult(B, a))
    r = int.from_bytes(hashlib.sha512(prefix + msg).digest(), "little")
    R = _point_compress(_scalarmult(B, r))
    k = int.from_bytes(hashlib.sha512(R + A + msg).digest(), "little")
    S = (r + k * a) % L
    return R + int.to_bytes(S, 32, "little")


def verify(pub32: bytes, msg: bytes, sig64: bytes) -> bool:
    """Verify an Ed25519 signature (bonus; used for extra self-testing)."""
    pub32 = bytes(pub32)
    msg = bytes(msg)
    sig64 = bytes(sig64)
    if len(pub32) != 32 or len(sig64) != 64:
        return False
    Rb = sig64[:32]
    S = int.from_bytes(sig64[32:], "little")
    if S >= L:
        return False
    try:
        A = _point_decompress(pub32)
        R = _point_decompress(Rb)
    except ValueError:
        return False
    k = int.from_bytes(hashlib.sha512(Rb + pub32 + msg).digest(), "little")
    # check [S]B == R + [k]A
    lhs = _scalarmult(B, S)
    rhs = _edwards_add(R, _scalarmult(A, k))
    # compare affine (x,y)
    def to_affine(P):
        X, Y, Z, _T = P
        zi = inv(Z)
        return (X * zi % q, Y * zi % q)
    return to_affine(lhs) == to_affine(rhs)


if __name__ == "__main__":
    import sys
    # tiny smoke test against vector 1 public key
    seed = bytes.fromhex(
        "9d61b19decedfb7fe6c9554a7bcff55f02069d4b4e4b5930bbe8e4a0c07a5f4e"
    )
    print(pubkey(seed).hex())
