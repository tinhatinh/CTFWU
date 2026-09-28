"""Protocol driver: doc theo 'settle' (im lang = het phan hoi), khong doan prompt."""
import socket
import sys
import time

import svc

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ORDER = ["pool", "authority", "user", "user_a", "user_b",
         "vault_a", "vault_b", "mint_a", "mint_b", "token_program"]


class Settle:
    def __init__(self):
        self.s = socket.create_connection((svc.HOST, svc.PORT), timeout=25)
        self.s.settimeout(1.5)
        self.log = []

    def rd(self, quiet=1.2, cap=6.0):
        end = time.time() + cap
        buf = b""
        while time.time() < end:
            try:
                c = self.s.recv(65536)
            except Exception:
                break
            if not c:
                break
            buf += c
            end = min(end, time.time() + quiet)
        return buf

    def say(self, line, echo=True):
        self.s.sendall((line + "\n").encode())
        r = self.rd()
        if echo:
            print("   >> %-44s << %r" % (line[:44], r[:220]), flush=True)
        return r

    def close(self):
        try:
            self.s.close()
        except Exception:
            pass


def banner_of(t):
    b = t.rd(1.5, 8.0).decode("utf-8", "replace")
    A = {}
    for line in b.splitlines():
        if ": " in line:
            k, v = line.split(": ", 1)
            A[k.strip()] = v.strip()
    return A


def swap_data(amount, ix=1):
    import struct
    return ("%02x" % ix) + struct.pack("<Q", amount).hex()


def attempt(A, accounts, amount, ix=1, label=""):
    t = Settle()
    a = banner_of(t)
    if label:
        print("=== %s" % label)
    t.say(str(len(accounts)))
    for k in accounts:
        t.say(a[k])
    d = swap_data(amount, ix)
    t.say(str(len(d) // 2))
    t.say(d)
    t.close()


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "probe"
    t = Settle()
    A = banner_of(t)
    print("[*] reserve_b =", A.get("reserve_b"))
    if which == "probe":
        t.say("0")                       # 0 account -> mong "ix len: "
        t.say("0")                       # ix len 0 -> chay
    elif which == "swap":
        t.say("10")
        for k in ORDER:
            t.say(A[k])
        d = swap_data(int(sys.argv[2]) if len(sys.argv) > 2 else 10)
        t.say(str(len(d) // 2))
        t.say(d)
    t.close()
