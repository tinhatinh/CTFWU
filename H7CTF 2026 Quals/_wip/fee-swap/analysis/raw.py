"""In NGUYEN TINH stream trai qua tung buoc, khong cat ngon, khong doan nhan."""
import sys
import time

import svc

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ORDER = ["pool", "authority", "user", "user_a", "user_b",
         "vault_a", "vault_b", "mint_a", "mint_b", "token_program"]


def run(steps, gap=2.5, quiet=1.0):
    s = svc.Svc()
    acc = {}
    stream = b""

    def pump(label):
        nonlocal stream
        end = time.time() + gap
        while time.time() < end:
            try:
                s.s.settimeout(quiet)
                c = s.s.recv(65536)
            except Exception:
                c = b""
                break
            if not c:
                break
            stream += c
        print("[%s] stream now: %r" % (label, stream[-300:]), flush=True)
        return stream

    pump("connect")
    for line in stream.decode("utf-8", "replace").splitlines():
        if ": " in line and len(line.split(": ")) == 2:
            acc[line.split(": ")[0]] = line.split(": ", 1)[1]
    print("[*] reserve_b=%s" % acc.get("reserve_b"), flush=True)
    for st in steps:
        raw = st.format(**acc) if "{" in st else st
        print("---- SEND: %r" % (raw[:120],), flush=True)
        s.s.sendall((raw + "\n").encode())
        pump("after-send")
    s.close()


if __name__ == "__main__":
    which = sys.argv[1]
    if which == "A":            # 0 accounts -> xem co "ix len:" roi chay luon
        run(["0"])
    elif which == "B":          # 1 account
        run(["1", "{pool}"])
    elif which == "C":          # 10 accounts
        run(["10"] + ["{%s}" % k for k in ORDER])
    elif which == "D":          # 10 accounts + ix len + data
        run(["10"] + ["{%s}" % k for k in ORDER] + ["9", "010a00000000000000"])
