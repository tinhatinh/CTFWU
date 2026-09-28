"""Mô hình quy tắc sinh của Hothouse, đối chiếu với server thật.

state: 32 hàng, mỗi hàng là bit vector 32 bit (bit c = cell (r,c)).
Một thế hệ:  new[r] = old[r-1] ^ old[r+1] ^ (old[r]<<1) ^ (old[r]>>1)
                    ^ (old[r-1]<<1) ^ (old[r+1]>>1)      (mask 32 bit, ngoài lattice = chết)
7 thế hệ, substrate = 0.
Pack: fabric[r*4 + (c>>3)] bit (c&7) = cell(r,c).
"""
MASK = (1 << 32) - 1
GENS = 7


def step(rows):
    out = []
    for r in range(32):
        up = rows[r - 1] if r > 0 else 0
        dn = rows[r + 1] if r < 31 else 0
        me = rows[r]
        v = up ^ dn ^ ((me << 1) & MASK) ^ (me >> 1) ^ ((up << 1) & MASK) ^ (dn >> 1)
        out.append(v & MASK)
    return out


def grow(seed_bits):
    """seed_bits: iterable của idx = r*32+c đã bật."""
    rows = [0] * 32
    for i in seed_bits:
        rows[i // 32] |= 1 << (i % 32)
    for _ in range(GENS):
        rows = step(rows)
    fab = bytearray(128)
    for r in range(32):
        for c in range(32):
            if (rows[r] >> c) & 1:
                fab[r * 4 + (c >> 3)] |= 1 << (c & 7)
    return bytes(fab)


def render(fab):
    lines = []
    for r in range(32):
        lines.append("".join("#" if (fab[r * 4 + (c >> 3)] >> (c & 7)) & 1 else "."
                             for c in range(32)))
    return "\n".join(lines)


if __name__ == "__main__":
    import socket
    import sys

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    seeds = [(0, 0), (1, 1), (5, 7), (31, 31), (16, 0)]
    s = socket.create_connection(("pwn.h7tex.com", 41676), timeout=20)

    def rd(t=1.5):
        s.settimeout(t)
        b = b""
        while True:
            try:
                c = s.recv(65536)
            except Exception:
                break
            if not c:
                break
            b += c
        return b

    rd(2.0)
    for r, c in seeds:
        s.sendall(b"SEED %d %d\n" % (r, c))
        rd(0.5)
    s.sendall(b"INCUBATE\n")
    rd(0.5)
    s.sendall(b"RENDER\n")
    real = rd(3.0).decode(errors="replace").strip()
    mine = render(grow([r * 32 + c for r, c in seeds]))
    ok = real == mine
    print("[*] mô hình khớp server:", ok)
    if not ok:
        print("--- server ---")
        print(real[:400])
        print("--- mô hình ---")
        print(mine[:400])
    s.close()
