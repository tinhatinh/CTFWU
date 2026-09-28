"""Lai GET voi doc kien nhan.

Cores ghi ra tung byte bang printf("%02x") voi stdout _IONBF -> mot write() per byte,
~1 KB/s.  Toan bo image ~145 KB nen phai doc lien tuc hang chuc giay, khong co
break som.  Dung khi EOF hoac im lang > IDLE giay.  Image tu danh tinh: byte 0x0a..0x11
la nonce dao nguoc, nen in ra de doi chieu.
"""
import binascii
import os
import socket
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HOST, PORT = "pwn.h7tex.com", 43708
HERE = os.path.dirname(os.path.abspath(__file__))
IDLE = 20.0


def fetch():
    s = socket.create_connection((HOST, PORT), timeout=IDLE)
    s.settimeout(IDLE)
    buf = b""
    t0 = time.time()
    while True:
        try:
            c = s.recv(1 << 16)
        except socket.timeout:
            print("[!] timeout sau %.0fs" % (time.time() - t0))
            break
        except Exception as e:
            print("[!] %s sau %.0fs" % (type(e).__name__, time.time() - t0))
            break
        if not c:
            print("[*] EOF sau %.0fs" % (time.time() - t0))
            break
        buf += c
        if len(buf) % 100000 < len(c):
            print("    %d byte, %.0fs" % (len(buf), time.time() - t0), flush=True)
    # banner 2 dong, phan con lai la hex
    lines = buf.split(b"\n")
    body = b"".join(l.strip() for l in lines[2:])
    print("[*] hex chars=%d (chan=%s)" % (len(body), len(body) % 2 == 0))
    try:
        img = binascii.unhexlify(body)
    except Exception as e:
        print("[!] unhexlify fail:", e)
        img = binascii.unhexlify(body[:len(body) - len(body) % 2])
    print("[*] image %d byte" % len(img))
    print("[*] magic %s  nonce-field %s" % (img[:4], img[0x0a:0x12].hex()))
    open(os.path.join(HERE, "image.bin"), "wb").write(img)
    open(os.path.join(HERE, "image.txt"), "wb").write(body + b"\n")
    s.close()
    return img


if __name__ == "__main__":
    fetch()
