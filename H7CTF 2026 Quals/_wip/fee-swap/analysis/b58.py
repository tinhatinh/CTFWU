"""Do dung cua thuat toan: base58 + SPL Token account layout (165 byte)."""
import struct

B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
ALPH = {c: i for i, c in enumerate(B58)}


def b58encode(raw):
    n = int.from_bytes(raw, "big")
    out = ""
    while n:
        n, r = divmod(n, 58)
        out = B58[r] + out
    pad = 0
    for b in raw:
        if b == 0:
            pad += 1
        else:
            break
    return "1" * pad + (out or "1")


def b58decode(s):
    n = 0
    for c in s:
        n = n * 58 + ALPH[c]
    body = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    pad = 0
    for c in s:
        if c == "1":
            pad += 1
        else:
            break
    return b"\x00" * pad + body


def is_pubkey(s):
    try:
        return len(s) <= 44 and len(b58decode(s)) == 32
    except Exception:
        return False


SYSTEM = "11111111111111111111111111111111"
TOKEN2022 = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
TOKENCLASSIC = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"


def token_account(mint, owner, amount, delegate=None, state=1,
                  close_authority=None):
    """serailize AccountLayout cua SPL Token (165 byte)."""
    UNSET = bytes([0]) * 32
    d = bytearray()
    d += b58decode(mint)
    d += b58decode(owner)
    d += struct.pack("<Q", amount)
    if delegate is None:
        d += struct.pack("<I", 0) + UNSET
    else:
        d += struct.pack("<I", 1) + b58decode(delegate)
    d += bytes([state])
    d += struct.pack("<I", 0)          # is_native: None
    d += struct.pack("<Q", 0)
    d += struct.pack("<Q", 0)          # delegated_amount
    if close_authority is None:
        d += struct.pack("<I", 0) + UNSET
    else:
        d += struct.pack("<I", 1) + b58decode(close_authority)
    assert len(d) == 165, len(d)
    return bytes(d)


def pool_data(initialized, bump, vault_a, vault_b, mint_a, mint_b):
    d = bytearray()
    d += bytes([1 if initialized else 0])
    d += bytes([bump])
    for k in (vault_a, vault_b, mint_a, mint_b):
        d += b58decode(k)
    return bytes(d)


def ix_swap_a_to_b(amount):
    return b"\x01" + struct.pack("<Q", amount)


def ix_swap_b_to_a(amount):
    return b"\x02" + struct.pack("<Q", amount)


def randkey(seed):
    """32 byte deterministic, base58."""
    import hashlib
    h = hashlib.sha256(b"feeswap" + str(seed).encode()).digest()
    # tranh byte dau > 0x80 de chac chan base58 dai 43-44 ky tu
    return b58encode(h)


if __name__ == "__main__":
    # tu kiem: layout 165 byte, base58 vong quay quanh
    ta = token_account(SYSTEM, SYSTEM, 1234)
    assert len(ta) == 165
    assert struct.unpack_from("<Q", ta, 64)[0] == 1234
    k = randkey(1)
    assert b58decode(k) == __import__("hashlib").sha256(b"feeswap1").digest()
    print("selftest ok; sample key", k, "len", len(k))
    print("pool_data len", len(pool_data(1, 255, SYSTEM, SYSTEM, SYSTEM, SYSTEM)))
