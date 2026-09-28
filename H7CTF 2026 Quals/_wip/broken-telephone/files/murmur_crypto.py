import struct

MASK32 = 0xFFFFFFFF

BLAKE2S_IV = [
    0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A,
    0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19,
]

SIGMA = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    [14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3],
    [11, 8, 12, 0, 5, 2, 15, 13, 10, 14, 3, 6, 7, 1, 9, 4],
    [7, 9, 3, 1, 13, 12, 11, 14, 2, 6, 5, 10, 4, 0, 15, 8],
    [9, 0, 5, 7, 2, 4, 10, 15, 14, 1, 11, 12, 6, 8, 3, 13],
    [2, 12, 6, 10, 0, 11, 8, 3, 4, 13, 7, 5, 15, 14, 1, 9],
    [12, 5, 1, 15, 14, 13, 4, 10, 0, 7, 6, 3, 9, 2, 8, 11],
    [13, 11, 7, 14, 12, 1, 3, 9, 5, 0, 15, 4, 8, 6, 2, 10],
    [6, 15, 14, 9, 11, 3, 0, 8, 12, 2, 13, 7, 1, 4, 10, 5],
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
]


def _rotr32(x, n):
    return ((x >> n) | (x << (32 - n))) & MASK32


def _mix(v, a, b, c, d, x, y):
    v[a] = (v[a] + v[b] + x) & MASK32
    v[d] = _rotr32(v[d] ^ v[a], 16)
    v[c] = (v[c] + v[d]) & MASK32
    v[b] = _rotr32(v[b] ^ v[c], 12)
    v[a] = (v[a] + v[b] + y) & MASK32
    v[d] = _rotr32(v[d] ^ v[a], 8)
    v[c] = (v[c] + v[d]) & MASK32
    v[b] = _rotr32(v[b] ^ v[c], 7)


def _compress(h, block, counter, last):
    m = list(struct.unpack("<16I", block))
    v = h[:] + BLAKE2S_IV[:]
    v[12] ^= counter & MASK32
    v[13] ^= (counter >> 32) & MASK32
    if last:
        v[14] ^= MASK32
    for r in range(10):
        s = SIGMA[r]
        _mix(v, 0, 4, 8, 12, m[s[0]], m[s[1]])
        _mix(v, 1, 5, 9, 13, m[s[2]], m[s[3]])
        _mix(v, 2, 6, 10, 14, m[s[4]], m[s[5]])
        _mix(v, 3, 7, 11, 15, m[s[6]], m[s[7]])
        _mix(v, 0, 5, 10, 15, m[s[8]], m[s[9]])
        _mix(v, 1, 6, 11, 12, m[s[10]], m[s[11]])
        _mix(v, 2, 7, 8, 13, m[s[12]], m[s[13]])
        _mix(v, 3, 4, 9, 14, m[s[14]], m[s[15]])
    for i in range(8):
        h[i] ^= v[i] ^ v[i + 8]


def blake2s(data, digest_size=32):
    h = BLAKE2S_IV[:]
    h[0] ^= 0x01010000 ^ digest_size
    counter = 0
    offset = 0
    total = len(data)
    while total - offset > 64:
        counter += 64
        _compress(h, data[offset:offset + 64], counter, False)
        offset += 64
    remaining = data[offset:]
    counter += len(remaining)
    block = remaining + b"\x00" * (64 - len(remaining))
    _compress(h, block, counter, True)
    return struct.pack("<8I", *h)[:digest_size]


def hmac_blake2s(key, message):
    if len(key) > 64:
        key = blake2s(key)
    key = key + b"\x00" * (64 - len(key))
    ipad = bytes(b ^ 0x36 for b in key)
    opad = bytes(b ^ 0x5C for b in key)
    inner = blake2s(ipad + message)
    return blake2s(opad + inner)


def hkdf(chaining_key, ikm, num_outputs):
    temp_key = hmac_blake2s(chaining_key, ikm)
    out1 = hmac_blake2s(temp_key, b"\x01")
    if num_outputs == 1:
        return (out1,)
    out2 = hmac_blake2s(temp_key, out1 + b"\x02")
    if num_outputs == 2:
        return (out1, out2)
    out3 = hmac_blake2s(temp_key, out2 + b"\x03")
    return (out1, out2, out3)


def _rotl32(x, n):
    return ((x << n) | (x >> (32 - n))) & MASK32


def _quarter(s, a, b, c, d):
    s[a] = (s[a] + s[b]) & MASK32
    s[d] = _rotl32(s[d] ^ s[a], 16)
    s[c] = (s[c] + s[d]) & MASK32
    s[b] = _rotl32(s[b] ^ s[c], 12)
    s[a] = (s[a] + s[b]) & MASK32
    s[d] = _rotl32(s[d] ^ s[a], 8)
    s[c] = (s[c] + s[d]) & MASK32
    s[b] = _rotl32(s[b] ^ s[c], 7)


def chacha20_block(key, counter, nonce):
    consts = struct.unpack("<4I", b"expand 32-byte k")
    state = list(consts) + list(struct.unpack("<8I", key)) + [counter] + list(struct.unpack("<3I", nonce))
    working = state[:]
    for _ in range(10):
        _quarter(working, 0, 4, 8, 12)
        _quarter(working, 1, 5, 9, 13)
        _quarter(working, 2, 6, 10, 14)
        _quarter(working, 3, 7, 11, 15)
        _quarter(working, 0, 5, 10, 15)
        _quarter(working, 1, 6, 11, 12)
        _quarter(working, 2, 7, 8, 13)
        _quarter(working, 3, 4, 9, 14)
    out = [(working[i] + state[i]) & MASK32 for i in range(16)]
    return struct.pack("<16I", *out)


def chacha20_keystream(key, nonce, counter, length):
    stream = bytearray()
    while len(stream) < length:
        stream += chacha20_block(key, counter, nonce)
        counter += 1
    return bytes(stream[:length])


def chacha20_xor(key, nonce, counter, data):
    ks = chacha20_keystream(key, nonce, counter, len(data))
    return bytes(a ^ b for a, b in zip(data, ks))


P1305 = (1 << 130) - 5


def _clamp_r(r):
    return r & 0x0FFFFFFC0FFFFFFC0FFFFFFC0FFFFFFF


def poly1305_mac(key, message):
    r = _clamp_r(int.from_bytes(key[:16], "little"))
    s = int.from_bytes(key[16:32], "little")
    acc = 0
    for i in range(0, len(message), 16):
        chunk = message[i:i + 16]
        n = int.from_bytes(chunk + b"\x01", "little")
        acc = ((acc + n) * r) % P1305
    acc = (acc + s) & ((1 << 128) - 1)
    return acc.to_bytes(16, "little")


def _pad16(data):
    if len(data) % 16 == 0:
        return b""
    return b"\x00" * (16 - (len(data) % 16))


def aead_mac_data(aad, ciphertext):
    return (aad + _pad16(aad) + ciphertext + _pad16(ciphertext)
            + struct.pack("<Q", len(aad)) + struct.pack("<Q", len(ciphertext)))


def aead_encrypt(key, nonce, plaintext, aad):
    poly_key = chacha20_block(key, 0, nonce)[:32]
    ciphertext = chacha20_xor(key, nonce, 1, plaintext)
    tag = poly1305_mac(poly_key, aead_mac_data(aad, ciphertext))
    return ciphertext + tag


def aead_decrypt(key, nonce, sealed, aad):
    ciphertext, tag = sealed[:-16], sealed[-16:]
    poly_key = chacha20_block(key, 0, nonce)[:32]
    expected = poly1305_mac(poly_key, aead_mac_data(aad, ciphertext))
    if expected != tag:
        raise ValueError("auth failed")
    return chacha20_xor(key, nonce, 1, ciphertext)


def _decode_u(u):
    return int.from_bytes(u, "little") & ((1 << 255) - 1)


def x25519(scalar, point):
    a24 = 121665
    p = (1 << 255) - 19
    k = int.from_bytes(scalar, "little")
    k &= ~7
    k &= ~(1 << 255)
    k |= 1 << 254
    x1 = _decode_u(point)
    x2, z2 = 1, 0
    x3, z3 = x1, 1
    swap = 0
    for t in range(254, -1, -1):
        bit = (k >> t) & 1
        swap ^= bit
        if swap:
            x2, x3 = x3, x2
            z2, z3 = z3, z2
        swap = bit
        A = (x2 + z2) % p
        AA = (A * A) % p
        B = (x2 - z2) % p
        BB = (B * B) % p
        E = (AA - BB) % p
        C = (x3 + z3) % p
        D = (x3 - z3) % p
        DA = (D * A) % p
        CB = (C * B) % p
        x3 = pow((DA + CB) % p, 2, p)
        z3 = (x1 * pow((DA - CB) % p, 2, p)) % p
        x2 = (AA * BB) % p
        z2 = (E * ((AA + (a24 * E) % p) % p)) % p
    if swap:
        x2, x3 = x3, x2
        z2, z3 = z3, z2
    result = (x2 * pow(z2, p - 2, p)) % p
    return result.to_bytes(32, "little")


X25519_BASE = (9).to_bytes(32, "little")


def dh(private, public):
    return x25519(private, public)


PROTOCOL_NAME = b"Noise_XKpsk3_25519_ChaChaPoly_BLAKE2s"


class SymmetricState:
    def __init__(self):
        h = PROTOCOL_NAME
        if len(h) <= 32:
            h = h + b"\x00" * (32 - len(h))
        else:
            h = blake2s(h)
        self.h = h
        self.ck = h
        self.key = None
        self.nonce = 0

    def mix_key(self, ikm):
        self.ck, temp = hkdf(self.ck, ikm, 2)
        self.key = temp
        self.nonce = 0

    def mix_hash(self, data):
        self.h = blake2s(self.h + data)

    def mix_key_and_hash(self, ikm):
        self.ck, temp_h, temp_k = hkdf(self.ck, ikm, 3)
        self.mix_hash(temp_h)
        self.key = temp_k
        self.nonce = 0

    def _nonce_bytes(self):
        return b"\x00\x00\x00\x00" + struct.pack("<Q", self.nonce)

    def encrypt_and_hash(self, plaintext):
        if self.key is None:
            self.mix_hash(plaintext)
            return plaintext
        sealed = aead_encrypt(self.key, self._nonce_bytes(), plaintext, self.h)
        self.nonce += 1
        self.mix_hash(sealed)
        return sealed

    def decrypt_and_hash(self, sealed):
        if self.key is None:
            self.mix_hash(sealed)
            return sealed
        plaintext = aead_decrypt(self.key, self._nonce_bytes(), sealed, self.h)
        self.nonce += 1
        self.mix_hash(sealed)
        return plaintext

    def split(self):
        k1, k2 = hkdf(self.ck, b"", 2)
        return k1, k2


class Handshake:
    def __init__(self, initiator, static_priv, static_pub, remote_static_pub, psk, prologue=b""):
        self.initiator = initiator
        self.ss = SymmetricState()
        self.s_priv = static_priv
        self.s_pub = static_pub
        self.rs = remote_static_pub
        self.psk = psk
        self.e_priv = None
        self.e_pub = None
        self.re = None
        self.h2 = None
        self.ss.mix_hash(prologue)
        self.ss.mix_hash(self.rs if initiator else self.s_pub)

    def set_ephemeral(self, priv, pub):
        self.e_priv = priv
        self.e_pub = pub

    def _dh(self, letters):
        if self.initiator:
            first = self.e_priv if letters[0] == "e" else self.s_priv
            other = self.re if letters[1] == "e" else self.rs
        else:
            first = self.e_priv if letters[1] == "e" else self.s_priv
            other = self.re if letters[0] == "e" else self.rs
        return dh(first, other)

    def write_msg1(self, payload):
        buf = self.e_pub
        self.ss.mix_hash(self.e_pub)
        self.ss.mix_key(self._dh("es"))
        buf += self.ss.encrypt_and_hash(payload)
        return buf

    def read_msg1(self, data):
        self.re = data[:32]
        self.ss.mix_hash(self.re)
        self.ss.mix_key(self._dh("es"))
        return self.ss.decrypt_and_hash(data[32:])

    def write_msg2(self, payload):
        buf = self.e_pub
        self.ss.mix_hash(self.e_pub)
        self.ss.mix_key(self._dh("ee"))
        buf += self.ss.encrypt_and_hash(payload)
        self.h2 = self.ss.h
        return buf

    def read_msg2(self, data):
        self.re = data[:32]
        self.ss.mix_hash(self.re)
        self.ss.mix_key(self._dh("ee"))
        pt = self.ss.decrypt_and_hash(data[32:])
        self.h2 = self.ss.h
        return pt

    def write_msg3(self, payload):
        buf = self.ss.encrypt_and_hash(self.s_pub)
        self.ss.mix_key(self._dh("se"))
        self.ss.mix_key_and_hash(self.psk)
        buf += self.ss.encrypt_and_hash(payload)
        return buf

    def read_msg3(self, data):
        self.rs = self.ss.decrypt_and_hash(data[:48])
        self.ss.mix_key(self._dh("se"))
        self.ss.mix_key_and_hash(self.psk)
        return self.ss.decrypt_and_hash(data[48:])

    def transport_keys(self):
        return self.ss.split()


LEN_LABEL = b"MURMUR-len"


def length_mask(binding, index):
    digest = blake2s(binding + LEN_LABEL + struct.pack("<I", index))
    return int.from_bytes(digest[:2], "little")


TYPE_DATA = 0x00
TYPE_CONTROL = 0x01

TELEMETRY_MAGIC = b"MURMUR\x12"


def build_telemetry(seq, uptime, link_rssi, queue_depth):
    body = TELEMETRY_MAGIC
    body += struct.pack("<I", seq)
    body += struct.pack("<Q", uptime)
    body += struct.pack("<h", link_rssi)
    body += struct.pack("<H", queue_depth)
    body += b"NODE-GUEST-0001\x00"
    body += b"\x00" * (64 - len(body))
    return body
