"""Interactive driver for the Sparrow Freight checkpoint service.

Usage: python driver.py "<line1>" "<line2>" ...
"""
import socket
import sys

HOST, PORT = "pwn.h7tex.com", 42578


def recv(sock, timeout=2.0, cap=65536):
    sock.settimeout(timeout)
    buf = b""
    while len(buf) < cap:
        try:
            chunk = sock.recv(4096)
        except socket.timeout:
            break
        if not chunk:
            break
        buf += chunk
    return buf


def main():
    lines = sys.argv[1:]
    s = socket.create_connection((HOST, PORT), timeout=15)
    out = [recv(s)]
    for line in lines:
        s.sendall(line.encode(errors="surrogateescape") + b"\n")
        out.append(recv(s))
    s.close()
    for i, o in enumerate(out):
        print("---- phase %d ----" % i)
        sys.stdout.write(o.decode(errors="replace"))
        if o and not o.endswith(b"\n"):
            print()
        print("[len=%d]" % len(o))


if __name__ == "__main__":
    main()
