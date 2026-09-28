import socket, sys, time
HOST, PORT = "chal.sunshinectf.games", 26001
def io(lines, drain=1.5, pre=None):
    s = socket.create_connection((HOST, PORT), timeout=12)
    s.settimeout(6)
    def rd():
        out = b""
        try:
            while True:
                b = s.recv(65536)
                if not b: break
                out += b
        except socket.timeout: pass
        return out
    head = rd()
    for l in lines:
        s.sendall(l if isinstance(l, bytes) else l.encode() + b"\n")
        time.sleep(0.25)
        head += rd()
    if pre is None:
        try:
            s.sendall(b"\n"); time.sleep(0.4); head += rd()
        except Exception: pass
    s.close()
    return head
if __name__ == "__main__":
    print(io(sys.argv[1:]).decode("utf-8","replace"))
