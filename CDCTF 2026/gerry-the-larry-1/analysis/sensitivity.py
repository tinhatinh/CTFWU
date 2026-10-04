"""Do nhay cua ket luan theo cach phoi doi lag (negative control).

Chay: python analysis/sensitivity.py files/catcounty_results.zip

Lap lai toan bo loi giai voi ba cach phoi i <-> i, i <-> i-1, i <-> i+1.
Lag +/-1 mat mot doi tuong (1066 cap) va cho so ghe khac, nen phep gan cua
exploit.py khong phai mot lua chon thoi: do lech thoi gian (+ phoi 1-1 giu
thu tu, xem analysis/alignment.py) la bang quyet dinh.
"""

import collections
import csv
import io
import sys
import zipfile
from pathlib import Path

if len(sys.argv) < 2:
    sys.exit("usage: python analysis/sensitivity.py files/catcounty_results.zip")

with zipfile.ZipFile(Path(sys.argv[1])) as zf:
    info = list(csv.DictReader(io.StringIO(zf.read("gerry_final_files/info.csv").decode())))
    ci = [l.split()[3] for l in zf.read("gerry_final_files/check_in.log").decode().splitlines()]
    vo = [":".join(l.split(":")[4:]) for l in zf.read("gerry_final_files/votes.log").decode().splitlines()]

vid2block = {r["id"]: r["block"] for r in info}


def seats(pairs):
    t = collections.defaultdict(collections.Counter)
    for voter, party in pairs:
        t[vid2block[voter]][party] += 1
    won = []
    for b, c in t.items():
        top = max(c.values())
        w = sorted(p for p, n in c.items() if n == top)
        if w == ["Meowjority"]:
            won.append(b)
    return len(won), sorted(won)


cases = {"lag -1": list(zip(ci[:-1], vo[1:])),
         "lag  0": list(zip(ci, vo)),
         "lag +1": list(zip(ci[1:], vo[:-1]))}
res = {name: seats(pairs) for name, pairs in cases.items()}
base = res["lag  0"][1]
for name in ("lag -1", "lag  0", "lag +1"):
    n, won = res[name]
    print(f"    {name}: cap={len(cases[name]):5d}  ghe Meowjority={n:2d}  "
          f"block lech voi lag 0 = {sorted(set(base) ^ set(won))}")

print("\n[*] Margin (Meowjority - phe thu nhi) trong 12 block thang o lag 0:")
t = collections.defaultdict(collections.Counter)
for voter, party in zip(ci, vo):
    t[vid2block[voter]][party] += 1
for b in base:
    m = t[b].most_common()
    print(f"    {b:24s} {m[0][1]:3d} - {m[1][1]:3d}   margin={m[0][1] - m[1][1]}")
