"""Tim input 24 byte tu state.json (image + bang entry do bang MINT).

Da sua hai loi mo hinh:
  1. bo thanh ghi DUNG CHUNG ca cuoc di bo (khong xoat giua cac buoc)
  2. entry co stamp gia bi bo qua khi chon nhanh
"""
import json
import os
import random
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import records
import walk

HERE = os.path.dirname(os.path.abspath(__file__))


def load_state(name="state.json", imgname="imgP.bin"):
    S = json.load(open(os.path.join(HERE, name)))
    img = open(os.path.join(HERE, imgname), "rb").read()
    hdr, _ = records.parse(img)
    bytag = {r["f0"]: r for r in hdr["recs"]}
    valid = {}
    for k, v in S["val"].items():
        t, i = k.split(":")
        valid[(int(t), int(i))] = bool(v)
    return S, bytag, valid


def search(bytag, valid, start, tries=400000, seed=1):
    rng = random.Random(seed)
    for n in range(tries):
        inp = bytes(rng.randrange(256) for _ in range(24))
        kind, tag, path = walk.walk(bytag, start, inp, valid=valid)
        if kind in ("FLAG", "emptyprint"):
            return inp, kind, tag, path, n
    return None, None, None, None, tries


if __name__ == "__main__":
    S, bytag, valid = load_state()
    start = S["entry"]
    print("[*] start=%d record=%d entry that=%d/%d" %
          (start, len(bytag), sum(valid.values()), len(valid)))
    k, t, p = walk.walk(bytag, start, bytes(24), valid=valid)
    print("[*] input=0 ->", k, t)
    inp, kind, tag, path, n = search(bytag, valid, start, tries=200000)
    if inp:
        print("[+] tim thay sau %d lan: kind=%s input=%s" % (n, kind, inp.hex()))
        print("    duong di (%d buoc): %s" % (len(path), "->".join(map(str, path))))
    else:
        print("[-] khong tim thay trong 200000 lan")
