"""Phan tich phep gan noi giua check_in.log va votes.log (khong co khoa chung).

Chay: python analysis/alignment.py files/catcounty_results.zip

In ra: tinh don dieu cua hai log, do lech thoi gian theo tung lag, va so cap
bi am neu dich phoi sang lag khac. Buoc nay tra loi cau hoi "votes.log khong
chua voter id thi gan phieu cho cua tri bang cach nao".
"""

import sys
import zipfile
from datetime import datetime
from pathlib import Path

if len(sys.argv) < 2:
    sys.exit("usage: python analysis/alignment.py files/catcounty_results.zip")

with zipfile.ZipFile(Path(sys.argv[1])) as zf:
    ci_lines = zf.read("gerry_final_files/check_in.log").decode().splitlines()
    vo_lines = zf.read("gerry_final_files/votes.log").decode().splitlines()

ci = [(datetime.strptime(" ".join(l.split()[:2]), "%Y-%m-%d %H:%M:%S"), int(l.split()[2]))
      for l in ci_lines]
vo = [(datetime.strptime(":".join(l.split(":")[:3]), "%Y-%m-%d %H:%M:%S"), int(l.split(":")[3]))
      for l in vo_lines]

for name, rows in (("check_in", ci), ("votes", vo)):
    mono_t = all(rows[i][0] <= rows[i + 1][0] for i in range(len(rows) - 1))
    mono_n = all(rows[i + 1][1] - rows[i][1] == 1 for i in range(len(rows) - 1))
    print(f"[*] {name:9s}: n={len(rows)}  don dieu thoi gian={mono_t}  "
          f"so thu tu lien tiep={mono_n}  ({rows[0][1]}..{rows[-1][1]})")
print(f"[*] cua so mo cua: check_in {ci[0][0].time()}..{ci[-1][0].time()}, "
      f"votes {vo[0][0].time()}..{vo[-1][0].time()}")

print("\n[*] do lech (vote[i] - check_in[i+lag]) theo tung cach phoi:")
print(f"    {'lag':>4} {'cap hop le':>10} {'min':>6} {'mean':>7} {'max':>6} {'am':>4}")
for lag in (-2, -1, 0, 1, 2):
    idx = [(i, i + lag) for i in range(len(vo)) if 0 <= i + lag < len(ci)]
    d = [(vo[i][0] - ci[j][0]).total_seconds() for i, j in idx]
    print(f"    {lag:+4d} {len(idx):10d} {min(d):6.0f} {sum(d)/len(d):7.1f} "
          f"{max(d):6.0f} {sum(1 for x in d if x < 0):4d}")

print("""
[*] Ket luan: hai log cung do dai (1067), cung don dieu theo thoi gian va theo
    so thu tu, va moi cu tri check-in dung mot lan. Mot phep gan 1-1 giu thu tu
    (ai vao truoc bo phieu truoc) chi co the la i <-> i; lag +/-1 de loi mot
    luot check-in va mot phieu khong co doi tuong, nen trai voi ngu nghia log.
    Do lech duoi lag 0 nam trong 560..1184 s, khong cap nao am.""")
