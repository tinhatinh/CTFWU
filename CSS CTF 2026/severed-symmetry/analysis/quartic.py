"""Kiem tra du doan 1: khong gian to hop tuyen tinh cua cac public polynomial
ma khong phan tu bac 4 chinh la 16 thanh thu dau cua central map (w_1..w_16).

public = A1 . (w, U)  voi  w bac <=2, U(w, z[t:]) bac <=4  =>  phan bac 4 cua
mot to hop triet tieu khi va chi khi to hop do chi dung 16 toan hang dau.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "files"))
from source import rref, rank_of, unpack  # noqa: E402


def quartic_matrix(polys):
    mons = sorted({mon for poly in polys for mon in poly if len(mon) == 4})
    rows = [[poly.get(mon, 0) for mon in mons] for poly in polys]
    return rows, len(mons)


def analyse(polys, p, label):
    rows, ncols = quartic_matrix(polys)
    rk = rank_of(rows, ncols, p)
    print("%s: %d da thuc, %d monomial bac 4 | hang = %d | kernel bac<=2 = %d"
          % (label, len(polys), ncols, rk, len(polys) - rk))
    lin = sorted({mon for poly in polys for mon in poly if len(mon) == 1})
    lrows = [[poly.get(mon, 0) for mon in lin] for poly in polys]
    print("        hang cua phan bac 1 (34 x 32) = %d" % rank_of(lrows, len(lin), p))
    return rk


def main():
    d = json.load(open("files/out.txt"))
    pub = d["public_key"]
    analyse(unpack(pub["polynomials"]), pub["parameters"]["p"], "that")

    # doi chung: sinh khoa cua chinh source.py voi cung tham so
    import secrets
    from source import keygen, encrypt_bytes
    rng = secrets.SystemRandom()
    public, private = keygen(**pub["parameters"], rng=rng)
    analyse(unpack(public["polynomials"]), public["parameters"]["p"], "tu sinh")
    print("        (kernel 16 = dung cau truc; dung no de lay lai w)")


if __name__ == "__main__":
    main()
