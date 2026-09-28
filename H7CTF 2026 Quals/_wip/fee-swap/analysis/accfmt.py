"""Tim dinh dang dong account: thanh cong = thay 'ix len:', that bai = 'no flag'."""
import sys

import svc

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ORDER = ["pool", "authority", "user", "user_a", "user_b",
         "vault_a", "vault_b", "mint_a", "mint_b", "token_program"]


def try_accounts(label, n, mk, extra=None):
    s = svc.Svc()
    b = s.rd(6.0).decode("utf-8", "replace")
    A = {}
    for l in b.splitlines():
        if ": " in l:
            k, v = l.split(": ", 1)
            A[k.strip()] = v.strip()
    s.s.sendall((str(n) + "\n").encode())
    r0 = s.rd(3.0)
    lines = mk(A)
    if isinstance(lines, str):
        lines = [lines]
    got = None
    for ln in lines:
        s.s.sendall((ln + "\n").encode())
        r = s.rd(3.0)
        if r:
            got = r
            break
    ok = b"ix len" in (got or b"")
    print("%-34s n=%-3s -> %-10s %r" % (label, n, "IXLEN-OK" if ok else "abort",
                                        (got or r0 or b"")[:80]), flush=True)
    s.close()
    return ok


if __name__ == "__main__":
    P = lambda A: A["pool"]
    try_accounts("bare pk", 1, P)
    try_accounts("pk 0 1 (signer,wr)", 1, lambda A: P(A) + " 0 1")
    try_accounts("pk,true,true", 1, lambda A: P(A) + ",true,true")
    try_accounts("pk:1:1", 1, lambda A: P(A) + ":1:1")
    try_accounts("pk RW", 1, lambda A: P(A) + " RW")
    try_accounts("pk signer", 1, lambda A: P(A) + " signer")
    try_accounts("json", 1, lambda A: '{"pubkey":"%s","signer":false,"writable":true}' % P(A))
    try_accounts("10 pks one line", 10, lambda A: " ".join(A[k] for k in ORDER))
    try_accounts("10 pks own lines", 10, lambda A: [A[k] for k in ORDER])
    try_accounts("base64 of pk bytes", 1, lambda A: __import__("base64").b64encode(
        b"\x00" * 32).decode())
