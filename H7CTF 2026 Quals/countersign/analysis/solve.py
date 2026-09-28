"""Giải countersign trong MOT ket noi.

Diem quyet dinh (tu vm_notes.md + do dac cua chinh toi):
  `0x1d50` khong chon entry dau tien co bit khop, ma chon entry dau tien co bit khop
  VA co 6 byte tag kiem tra duoc.  Cac entry mồi co tag random -> bi bo qua.
  MINT(9 byte) tai tao duoc tag cua entry that, nen ta dunc duoc bang "entry nao that"
  bang cach hoi dich vu (125 entry = 125 lenh MINT, ~55s).

Sau do tim kiem hoan toan offline: thu input cho toi khi buoc di bo den record
LOADFLAG+SETDONE (0d 0e ...) -> RUN no tren cung ket noi.
"""
import binascii
import os
import random
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import session
import records
import walk

MAGIC_LEN = 9


def entry_msg(rid, tgt, bit, x):
    return struct.pack("<HHBI", rid, tgt, bit & 0xFF, x)[:MAGIC_LEN]


def build_validity(c, bytag):
    """Hoi MINT cho moi entry; tra ve dict (tag_rec, i) -> hop le."""
    val = {}
    n = 0
    for rid, rec in bytag.items():
        for i, s in enumerate(rec["stamps"]):
            e = walk.edge(s)
            x = struct.unpack_from("<I", s, 3)[0]
            mac = s[7:13]
            msg = entry_msg(rid, e[1], e[0], x)
            rep = c.mint(msg)
            n += 1
            ok = len(rep) >= 12 and binascii.unhexlify(rep[:12]) == mac
            val[(rid, i)] = ok
            if n % 25 == 0:
                print("   ... %d entry da do" % n, flush=True)
    return val


def step_v(bytag, val, tag, inp):
    rec = bytag.get(tag)
    if rec is None:
        return "unknown", tag
    st = walk.run(rec["code"], rec["ln"], inp)
    if st is None:
        return "loop", tag
    printed, loaded, regs = st
    if printed:
        return ("FLAG" if loaded else "emptyprint"), tag
    if rec["f1"] == 255:
        bpl = 255
    else:
        reg = regs[rec["f1"]] if rec["f1"] < 32 else 0
        bpl = (reg >> (rec["f2"] & 31)) & 1
    for i, s in enumerate(rec["stamps"]):
        t, tgt = walk.edge(s)
        if t == bpl and val.get((tag, i)):
            return "go", tgt
    return "go", rec["f3"]


def walk_v(bytag, val, start, inp, maxlen=200):
    tag, seen, path = start, set(), []
    for _ in range(maxlen):
        kind, tag = step_v(bytag, val, tag, inp)
        if kind != "go":
            return kind, tag, path
        if tag in seen:
            return "cycle", tag, path
        seen.add(tag)
        path.append(tag)
    return "long", tag, path


def main():
    c = session.Core()
    c.banner
    print("[*] nonce:", c.get_nonce())
    img = c.get_image(save="imgS.bin")
    hdr, _ = records.parse(img)
    bytag = {r["f0"]: r for r in hdr["recs"]}
    print("[*] %d record, start=%d" % (len(bytag), hdr["entry"]))
    print("[*] do bang entry that bang MINT...")
    val = build_validity(c, bytag)
    live = [k for k, v in val.items() if v]
    print("[*] entry that: %d/%d" % (len(live), len(val)))
    print("[*] walk voi input=0:", walk_v(bytag, val, hdr["entry"], bytes(24))[:2])

    rng = random.Random(0xC0FFEE)
    for t in range(300000):
        inp = bytes(rng.randrange(256) for _ in range(24))
        kind, tag, path = walk_v(bytag, val, hdr["entry"], inp)
        if kind in ("FLAG", "emptyprint"):
            print("[+] %s sau %d lan thu, input=%s" % (kind, t + 1, inp.hex()))
            rep = c.run(inp)
            print("[*] RUN ->", repr(rep)[:300])
            if "H7CTF{" in rep or "FLAG" in rep:
                import re
                m = re.search(r"H7CTF\{[^}\s]*\}", rep)
                if m:
                    open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "..", "flag.txt"), "w").write(m.group(0) + "\n")
                    print("[+] FLAG:", m.group(0))
                    c.close()
                    return 0
            if t > 20:
                break
        if t and t % 50000 == 0:
            print("   %d lan thu..." % t, flush=True)
    print("[-] chua tim duoc input thang loi")
    c.close()
    return 1


if __name__ == "__main__":
    sys.exit(main())
