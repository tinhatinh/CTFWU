"""Do giao thuc cua dich web3: noi chuyen bang cach gui danh sach dong, in moi buoc."""
import socket
import sys
import time

HOST, PORT = "web3.h7tex.com", 42600


class Svc:
    def __init__(self, host=HOST, port=PORT, t=8):
        self.s = socket.create_connection((host, port), timeout=t)
        self.s.settimeout(t)

    def rd(self, t=4.0):
        self.s.settimeout(t)
        out = b""
        end = time.time() + t
        while time.time() < end:
            try:
                c = self.s.recv(65536)
            except Exception:
                break
            if not c:
                break
            out += c
        return out

    def send(self, line, t=4.0):
        raw = line.encode() if isinstance(line, str) else line
        if not raw.endswith(b"\n"):
            raw += b"\n"
        self.s.sendall(raw)
        return self.rd(t)

    def close(self):
        try:
            self.s.close()
        except Exception:
            pass


def chat(lines, prelude=True, t=4.0):
    sv = Svc()
    log = []
    b = sv.rd(5.0) if prelude else b""
    log.append(("<banner>", b))
    for l in lines:
        r = sv.send(l.encode() if isinstance(l, str) else l)
        log.append((l, r))
    sv.close()
    return log


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    lines = sys.argv[1:]
    for sent, rep in chat(lines):
        print(">>> %s" % sent)
        print("<<< %r" % (rep,))
