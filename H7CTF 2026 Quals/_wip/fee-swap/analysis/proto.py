"""Xac dinh dang thuc cua danh sach account: N dong hay 1 dong chen cach."""
import sys
import time

import svc

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ORDER = ["pool", "authority", "user", "user_a", "user_b",
         "vault_a", "vault_b", "mint_a", "mint_b", "token_program"]


def banner():
    sv = svc.Svc()
    b = sv.rd(6.0).decode("utf-8", "replace")
    A = {}
    for line in b.splitlines():
        if ": " in line:
            k, v = line.split(": ", 1)
            A[k.strip()] = v.strip()
    return sv, A


def feed(sv, chunks, t=4.0):
    for c in chunks:
        sv.s.sendall((c + "\n").encode())
        r = sv.rd(t)
        yield c, r
        if b"remaining" in r:
            return


def trial(name, chunks):
    sv, A = banner()
    print("=== %s" % name, flush=True)
    for c, r in feed(sv, [x.format(**A) for x in chunks]):
        print("   >> %-40r << %r" % (c[:40], r[:110]), flush=True)
    sv.close()
    print()


if __name__ == "__main__":
    # 2 accounts, cung 1 dong (cach = space)
    trial("N=2 one-line space", ["2", "{pool} {user}"])
    # 2 accounts, 2 dong
    trial("N=2 two-lines", ["2", "{pool}", "{user}"])
    # 2 accounts, 1 dong phay
    trial("N=2 one-line comma", ["2", "{pool},{user}"])
    # count = so dong thuc te, danh sach 10 account tren 1 dong
    trial("N=10 one-line", ["10"] + [" ".join("{%s}" % k for k in ORDER)])
    # khong co count, vao thang 1 dong danh sach
    trial("no-count list line", [" ".join("{%s}" % k for k in ORDER)])
