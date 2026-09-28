"""Bao banner thanh dict de script giao dich voi dich."""
import sys

import svc


def connect():
    sv = svc.Svc()
    b = sv.rd(6.0).decode("utf-8", "replace")
    acc = {}
    for line in b.splitlines():
        if ": " in line:
            k, v = line.split(": ", 1)
            acc[k.strip()] = v.strip()
    acc["_raw"] = b
    return sv, acc


def show(log):
    for sent, rep in log:
        print(">>> %s" % sent)
        print("<<< %r" % (rep,), flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sv, a = connect()
    print("[*] keys:", {k: v for k, v in a.items() if k != "_raw"})
    print("[*] last prompt:", repr(a["_raw"].splitlines()[-1]))
    print("[*] reserve_b:", a.get("reserve_b"))
    sv.close()
