"""Ma trận tuyến tính của quy tắc sinh Hothouse.

Mỗi ô mang một bit vector 1024 bit (số nguyên Python), chạy 7 thế hệ bằng XOR.
Sau đó M[out_bit][in_bit] = 1 nếu in_bit ảnh hưởng tới out_bit.
"""
import sys

sys.path.insert(0, ".")
import ca  # noqa: E402

MASK = (1 << 32) - 1


def build_matrix():
    rows = [0] * 32
    for r in range(32):
        for c in range(32):
            rows[r] |= (1 << (r * 32 + c)) << (c * 1024) if False else 0
    # mỗi ô là một int 1024 bit; đóng gói 32 ô/hàng thành một int lớn 32*1024 bit
    # để dùng phép shift/XOR theo word. Đơn giản hơn: giữ list 32*32 int.
    cell = [[0] * 32 for _ in range(32)]
    for r in range(32):
        for c in range(32):
            cell[r][c] = 1 << (r * 32 + c)

    def get(rr, cc):
        if 0 <= rr < 32 and 0 <= cc < 32:
            return cell[rr][cc]
        return 0

    for _ in range(ca.GENS):
        new = [[0] * 32 for _ in range(32)]
        for r in range(32):
            for c in range(32):
                v = get(r - 1, c) ^ get(r + 1, c) ^ get(r, c + 1) ^ get(r, c - 1) \
                    ^ get(r - 1, c + 1) ^ get(r + 1, c - 1)
                new[r][c] = v
        cell = new

    # M[out][in]: bit 'in' của seed ảnh hưởng tới ô 'out'
    M = []
    for r in range(32):
        for c in range(32):
            out = r * 4 + (c >> 3)                       # chỉ số byte fabric
            bitpos = out * 8 + (c & 7)                   # chỉ số bit trong 1024 bit fabric
            vec = cell[r][c]
            M.append((bitpos, vec))
    return M


def apply_seed_to_bits(seed_bits, M):
    """Trả về tập 1024 bit fabric từ seed, bỏ qua substrate (tuyến tính thuần)."""
    acc = 0
    for i in seed_bits:
        for bitpos, vec in M:
            if (vec >> i) & 1:
                acc ^= 1 << bitpos
    return acc


def matvec(M, x_bits):
    """x_bits: int 1024 bit (seed). Trả về int 1024 bit fabric."""
    acc = 0
    for bitpos, vec in M:
        if bin(vec & x_bits).count("1") & 1:
            acc |= 1 << bitpos
    return acc


def bits_to_bytes(v, n=128):
    b = bytearray(n)
    for i in range(n * 8):
        if (v >> i) & 1:
            b[i // 8] |= 1 << (i % 8)
    return bytes(b)


def bytes_to_bits(b):
    v = 0
    for i in range(len(b) * 8):
        if (b[i // 8] >> (i % 8)) & 1:
            v |= 1 << i
    return v


if __name__ == "__main__":
    import socket
    import time

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    t0 = time.time()
    M = build_matrix()
    print("[*] ma trận %dx%d, %.1fs" % (len(M), 1024, time.time() - t0))

    # hạng của M qua khử Gauss
    rows = [vec for _, vec in M]
    piv = {}
    for i, v in enumerate(rows):
        b = v
        for bit in range(1023, -1, -1):
            if (b >> bit) & 1:
                if bit in piv:
                    b ^= rows[piv[bit]]
                else:
                    piv[bit] = i
                    rows[i] = b
                    break
        else:
            pass
    print("[*] hạng = %d / 1024" % len(piv))

    # đối chiếu trên đích: seed ngẫu nhiên vài ô, đọc fabric bằng PROBE
    seeds = [(3, 5), (10, 20), (25, 7)]
    s = socket.create_connection(("pwn.h7tex.com", 41676), timeout=20)

    def rd(t=1.0):
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

    rd(1.5)
    for r, c in seeds:
        s.sendall(b"SEED %d %d\n" % (r, c))
        rd(0.3)
    s.sendall(b"INCUBATE\n")
    rd(0.5)
    srv = bytearray(128)
    for r in range(32):
        for k, c in enumerate((0, 8, 16, 24)):
            s.sendall(b"PROBE %d %d\n" % (r, c))
            txt = rd(0.4).decode(errors="replace")
            srv[r * 4 + k] = int(txt.split(":")[1]) & 0xFF
    s.close()
    print("[*] đọc fabric qua PROBE: %d byte" % len(srv))
    print("    ", srv[:16].hex())
    import pickle
    pickle.dump((M, bytes(srv), [r * 32 + c for r, c in seeds]),
                open("analysis/state.pkl", "wb"))
    print("[*] đã lưu analysis/state.pkl")
