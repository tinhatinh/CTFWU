"""Thu kiem gia thiet 'mot word = mot ky tu' kieu Polybius homophonic (huong da loai).
Chay: python analysis/radix_probe.py

 Voi moi tap vi tri mang thong tin, moi cach quy doi chu cai -> chu so, moi radix
(van deu hooc mixed-radix), moi endian va moi bang ky tu: ghep thanh gia tri va xem
ket qua co chua manh roi co khong.

Co so duong: cung may do duoc cho chay tren 5 word tong hop, trong do cac nguyen am
o vi tri 1-2 ma hoa duoi co 6 thuc day dung chuoi 'cdctf'. May PHAI no hit o do,
neu khong thi negative tren du lieu that vo nghia.
"""
import itertools
import re
from pathlib import Path

VOWELS = "aeiouy"
CONS = "bcdfghklmnprstvzx"
ALPHABETS = {
    "az09": "abcdefghijklmnopqrstuvwxyz0123456789",
    "09az": "0123456789abcdefghijklmnopqrstuvwxyz",
    "az09_": "abcdefghijklmnopqrstuvwxyz0123456789_",
}
FLAGISH = re.compile(r"cdctf|ctf\{|flag|pass|jeff|barrett|crimson", re.I)


def groups_from(path):
    raw = [w.strip(".").lower() for w in Path(path).read_text().split(":")[-1].split()]
    return [w for w in raw if len(w) == 5 and w.isalpha()]


def build_maps(groups):
    """Ten map -> ham chu cai -> chu so, cho tung vi tri."""
    per_pos = []
    for i in range(5):
        chars = sorted(set(g[i] for g in groups))
        table = VOWELS if all(c in VOWELS for c in chars) else CONS
        per_pos.append({
            "obs_rank": {c: k for k, c in enumerate(chars)},
            "full_rank": {c: table.index(c) for c in chars if c in table},
        })
    return per_pos


def be(digits, rads):
    """Chu so dau tien la hang so lon nhat (mixed radix, big endian)."""
    v = 0
    for k, x in enumerate(digits):
        v = v * rads[k] + x
    return v


def le(digits, rads):
    v = 0
    w = 1
    for k, x in enumerate(digits):
        v += x * w
        w *= rads[k]
    return v


def decode(groups, per_pos):
    tried, hits = 0, []
    names = sorted(per_pos[0])
    for subset in range(1, 32):
        idx = [i for i in range(5) if subset >> i & 1]
        for order in itertools.permutations(idx):
            for combo in itertools.product(names, repeat=len(order)):
                digs = []
                for g in groups:
                    if any(g[i] not in per_pos[i][m] for i, m in zip(order, combo)):
                        break
                    digs.append([per_pos[i][m][g[i]] for i, m in zip(order, combo)])
                else:
                    rads = [max(d[k] for d in digs) + 1 for k in range(len(order))]
                    vals_be = [be(d, rads) for d in digs]
                    vals_le = [le(d, rads) for d in digs]
                    for endian, vals in (("be", vals_be), ("le", vals_le)):
                        for aname, alpha in ALPHABETS.items():
                            if max(vals) >= len(alpha):
                                continue
                            s = "".join(alpha[v] for v in vals)
                            tried += 1
                            if FLAGISH.search(s):
                                hits.append((subset, combo, endian, aname, s))
                        for off in (0, 1, 32, 33, 48, 64, 96, 97):
                            if any(v + off < 32 or v + off > 126 for v in vals):
                                continue
                            s = "".join(chr(v + off) for v in vals)
                            tried += 1
                            if FLAGISH.search(s):
                                hits.append((subset, combo, endian, f"ascii+{off}", s))
    return tried, hits


def synth_control():
    """5 word ma hoa 'cdctf' = chi so az09 viet co 6, nguyen am vi tri 1 va 2."""
    out = []
    for ch in "cdctf":
        v = ALPHABETS["az09"].index(ch)
        d0, d1 = v // 6, v % 6
        out.append("b" + VOWELS[d0] + VOWELS[d1] + "kl")
    return out


real = groups_from("files/cred_call_transcript.txt")
per_pos = build_maps(real)
tried, hits = decode(real, per_pos)
print(f"[*] du lieu that: {len(real)} word, thu {tried} bo tham so")
print(f"[-] {len(hits)} ket qua chua manh roi co")

ctrl = synth_control()
per_c = build_maps(ctrl)
ct, ch = decode(ctrl, per_c)
print(f"[+] positive control ({''.join(ctrl)}): thu {ct} bo, {len(ch)} hit")
for h in ch[:3]:
    print("     ", h[4])
if not ch:
    raise SystemExit("[-] CONTROL CHAY: may do khong phat hien duoc chuoi de trong "
                     "khong gian tim kiem, negative o tren khong co gia tri")
