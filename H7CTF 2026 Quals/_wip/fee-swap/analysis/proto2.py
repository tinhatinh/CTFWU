"""Quet cac dang input co the, tim dau ef khac 'not drained' (loi / prompt khac)."""
import sys

import svc

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ORDER = ["pool", "authority", "user", "user_a", "user_b",
         "vault_a", "vault_b", "mint_a", "mint_b", "token_program"]
DATA = "01" + "0a00000000000000"      # SwapAToB { amount: 10 }


def banner():
    sv = svc.Svc()
    b = sv.rd(6.0).decode("utf-8", "replace")
    A = {}
    for line in b.splitlines():
        if ": " in line:
            k, v = line.split(": ", 1)
            A[k.strip()] = v.strip()
    return sv, A


def trial(name, chunks, t=4.0):
    sv, A = banner()
    print("=== %s" % name, flush=True)
    for c in chunks:
        raw = c if not c.startswith("{") else c.format(**A)
        if "{" in raw:
            raw = raw.format(**A)
        sv.s.sendall((raw + "\n").encode())
        r = sv.rd(t)
        tag = "SAME" if r.strip() == b"vault_b remaining: %s\nreserve not drained. no flag." % A["reserve_b"].encode() else ("EMPTY" if not r.strip() else ">>>DIFF")
        print("  [%s] >> %-46s << %r" % (tag, raw[:46], r[:200]), flush=True)
    sv.close()
    print()


if __name__ == "__main__":
    cl = ",".join("{%s}" % k for k in ORDER)
    sp = " ".join("{%s}" % k for k in ORDER)
    trial("count, 10 lines, data", ["10"] + ["{%s}" % k for k in ORDER] + [DATA])
    trial("count, comma-list, data", ["10", cl, DATA])
    trial("count, space-list, data", ["10", sp, DATA])
    trial("comma-list then data", [cl, DATA])
    trial("count0 then data", ["0", DATA])
