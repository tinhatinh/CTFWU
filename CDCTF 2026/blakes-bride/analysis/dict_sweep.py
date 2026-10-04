"""Lan quet tu dien day du trong phien solve: blake2b(<tu> + 3 chu so) tren
toan bo words_alpha.txt, chia 16 tien trinh.

Day la ban da sua. Ban dau khong co `if __name__ == "__main__"` va tren Windows
`multiprocessing` dung spawn: moi tien trinh con import lai module, chay lại
doan tao Pool, de quy den khi in ra 1,2 MB log. Phai co guard.

Chay:  python analysis/dict_sweep.py <wordlist.txt>
"""

import hashlib
import multiprocessing as mp
import sys

TARGETS = set(bytes.fromhex(l.strip()) for l in open("targets.txt") if l.strip())
WORDS = [w.strip() for w in open(sys.argv[1], encoding="utf-8", errors="ignore")
         if 2 <= len(w.strip()) <= 20]
WORDS = list(dict.fromkeys(WORDS))
DIGITS = ["%03d" % i for i in range(1000)]


def work(idx):
    b = hashlib.blake2b
    hits = []
    for w in WORDS[idx::16]:
        for d in DIGITS:
            h = b((w + d).encode()).digest()
            if h in TARGETS:
                hits.append((w + d, h.hex()))
    return hits


if __name__ == "__main__":
    print("words", len(WORDS), "mode lower", flush=True)
    with mp.Pool(16) as p:
        for r in p.imap_unordered(work, range(16)):
            for v, h in r:
                print("HIT", v, h, flush=True)
    print("done", flush=True)
