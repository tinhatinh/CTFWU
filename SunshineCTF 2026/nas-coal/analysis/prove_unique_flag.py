#!/usr/bin/env python3
"""Chung minh: trong toan bo archive chi co DUNG MOT chuoi `sun{...}`.

Quet moi blob theo nhieu bien the ma hoa (raw, UTF-16, reversed, ROT13, hex,
base64 voi 4 offset lech, base64-cua-UTF-16), tren 63 entry ZIP, pixel da dao
filter PNG, bit-plane LSB va tung OLE stream.

Chay:  python prove_unique_flag.py ../files/gem_collection.pptm
"""
import base64
import codecs
import io
import re
import sys
import zipfile

import numpy as np
import olefile
from PIL import Image

B64_RUN = re.compile(rb"[A-Za-z0-9+/=]{80,}")
HEX_RUN = re.compile(rb"[0-9a-fA-F]{40,}")
NEEDLE = re.compile(rb"sun\{", re.I)


def variants(b):
    yield "raw", b
    for enc in ("utf-16-le", "utf-16-be"):
        yield enc, b.decode(enc, errors="ignore").encode("latin-1", errors="ignore")
    yield "rev", b[::-1]
    yield "rot13", codecs.encode(b.decode("latin-1", errors="ignore"), "rot_13").encode("latin-1", errors="ignore")
    yield "hex", b.hex().encode()
    s = re.sub(rb"[^A-Za-z0-9+/=]", b"", b)
    for skip in range(4):
        t = s[skip : skip + (len(s) - skip) // 4 * 4]
        try:
            d = base64.b64decode(t)
        except Exception:
            continue
        yield f"b64@{skip}", d
        yield f"b64@{skip}/u16", d.decode("utf-16-le", errors="ignore").encode("latin-1", errors="ignore")
    for m in B64_RUN.finditer(b):
        g = m.group()
        for skip in range(4):
            try:
                d = base64.b64decode(g[skip : skip + (len(g) - skip) // 4 * 4])
            except Exception:
                continue
            yield "inner-b64", d
            yield "inner-b64/u16", d.decode("utf-16-le", errors="ignore").encode("latin-1", errors="ignore")
    for m in HEX_RUN.finditer(b):
        h = m.group()
        try:
            yield "inner-hex", bytes.fromhex(h.decode()[: len(h) // 2 * 2])
        except Exception:
            pass


def blobs(path):
    z = zipfile.ZipFile(path)
    for n in z.namelist():
        data = z.read(n)
        yield n, data
        if n.startswith("ppt/media/") or "thumbnail" in n:
            try:
                a = np.array(Image.open(io.BytesIO(data))).astype(np.uint8).reshape(-1)
            except Exception:
                continue
            yield n + "#pixels", a.tobytes()
            yield n + "#lsb", bytes(np.packbits((a & 1).astype(np.uint8), bitorder="big"))
            yield n + "#b2lsb", bytes(np.packbits(((a >> 1) & 1).astype(np.uint8), bitorder="big"))
        if n == "ppt/vbaProject.bin":
            o = olefile.OleFileIO(io.BytesIO(data))
            for e in o.listdir():
                yield "ole:" + "/".join(e), o.openstream(e).read()


def main(path):
    hits = {}
    scanned = 0
    for name, b in blobs(path):
        for vn, v in variants(b):
            scanned += 1
            for m in NEEDLE.finditer(v):
                seg = v[m.start() : m.start() + 120]
                end = seg.find(b"}")
                hits.setdefault(seg[: end + 1] if end >= 0 else seg, []).append((name, vn, m.start()))
    print(f"[+] da quet {scanned} bien the blob")
    for flag, where in hits.items():
        print(f"[!] {flag.decode(errors='replace')}  xuat hien o {len(where)} noi")
        for name, vn, off in where[:6]:
            print(f"      {name} [{vn}] @{off}")
    if len(hits) == 1:
        print("[+] ket luan: chi mot co duy nhat trong archive -> khong phai moi nu")
    return 0 if hits else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
