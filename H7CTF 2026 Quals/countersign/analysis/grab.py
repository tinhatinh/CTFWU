"""Lay artefact theo instance: banner, NONCE, va chuong trinh (hex image)."""
import os
import socket
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HOST, PORT = "pwn.h7tex.com", 43708
OUT = os.path.dirname(os.path.abspath(__file__))


def read_until_prompt(s, buf, markers=("CSGN", ">", "$ "), t=8.0):
    """Doc tho: lay het du lieu dang co, dung khi im lang > t giay."""
    s.settimeout(t)
    while True:
        try:
            c = s.recv(1 << 20)
        except socket.timeout:
            break
        except Exception as e:
            buf += b" [" + type(e).__name__.encode() + b"]"
            break
        if not c:
            buf += b" [EOF]"
            break
        buf += c
        if any(m.encode() in buf for m in markers):
            break
    return buf


def main():
    s = socket.create_connection((HOST, PORT), timeout=30)
    buf = read_until_prompt(s, b"", (), t=3.0)
    print("== banner ==")
    print(buf.decode(errors="replace"))
    for cmd in ("NONCE", "GET", "MINT 414243", "RUN " + "00" * 24, "QUIT"):
        t0 = time.time()
        s.sendall(cmd.encode() + b"\n")
        buf = read_until_prompt(s, b"", (), t=6.0)
        print("\n== %s ==  (%.1fs, %d byte)" % (cmd, time.time() - t0, len(buf)))
        print(buf[:400].decode(errors="replace"))
        if len(buf) > 400:
            name = {"GET": "image.txt", "NONCE": "nonce.txt"}.get(cmd.split()[0])
            if name:
                open(os.path.join(OUT, name), "wb").write(buf)
                print("[*] da luu %s (%d byte)" % (name, len(buf)))
    s.close()


if __name__ == "__main__":
    main()
