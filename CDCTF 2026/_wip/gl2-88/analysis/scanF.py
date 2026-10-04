"""Hypothesis F: chi co 'cdctf{' o dau chuoi, KHONG gia dinh '}' o cuoi.
Dim = 5 -> 67^5 = 1.35 ty khoa. Chap nhan moi ung vien co >=36/38 vi tri khong
bai la chu cai (neu ciphertext bi cat khi paste thi prefix van lo ra co that).
"""
import sys, os, importlib.util, time
import numpy as np

spec = importlib.util.spec_from_file_location(
    'ex', os.path.join(os.path.dirname(__file__), "..", "exploit.py"))
ex = importlib.util.module_from_spec(spec)
sys.modules['ex'] = ex
spec.loader.exec_module(ex)          # chay selftest khi load -> kiem port van khop GHC

CT = ex.CIPHERTEXT
N = len(CT)
kvec, avec, BET = ex.basis_tables(N)
known = {i: c for i, c in enumerate('cdctf{')}
t0 = time.time()
cands, dim = ex.scan(CT, kvec, avec, BET, known, ex.ALPHA, min_letters=36, chunk=400_000)
print('dim', dim, 'survivors', len(cands), 'secs', round(time.time() - t0, 1), flush=True)
with open('hits_F_real.txt', 'w') as fh:
    for lam, txt in cands:
        fh.write('%d\t%s\n' % (lam, txt))

DICT = 'words_alpha.txt'
if not os.path.exists(DICT):
    print('Bo qua cham diem tu dien. Tai ve bang: curl -sL -o words_alpha.txt '
          'https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt')
    sys.exit(0)
import re
WORDS = set(w.strip().lower() for w in open(DICT, encoding='utf-8', errors='ignore')
            if 3 <= len(w.strip()))


def wscore(s):
    t = re.split(r'(?<=[a-z])(?=[A-Z])', re.sub(r'[^A-Za-z]', ' ', s))
    return sum(len(x) for x in [w.lower() for w in t] if x in WORDS)


top = sorted(((wscore(t), t) for _, t in cands), reverse=True)[:15]
for sc, t in top:
    print(sc, t)
