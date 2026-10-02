"""Hear No Evil - BLE pcap (fmt tự chế) : lấy provkey từ ADV rồi giải hai đặc tính.

Đặc tả do chính capture chép ra ở handle 0x0041:
  provkey          = 16 byte manufacturer data (company 0x0f39) ngay sau byte 0x01
  config  @ 0x0021 = ct XOR provkey (lặp theo chu kỳ)
  vault   @ 0x0033 = ct XOR ks,  ks = nối sha256(provkey || nonce || byte(i)), i = 0,1,..
  nonce   @ 0x0031 = 16 byte

Cấu trúc packet giả lập: 4 byte sync C3B2A150 + 7 byte header + payload + 3 byte CRC.
Payload:
  2 byte         = chọn handle, offset 0
  4 byte         = handle (LE) + offset (LE)
  20 / n byte    = dữ liệu cho request đang chờ
  >= 11 byte     = handle (LE) + dữ liệu (notify, tự chứa)

Dùng: python solve.py analysis/capture.pcap
"""
import hashlib
import re
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SYNC = bytes.fromhex("C3B2A150")
HDR, CRC = 11, 3
FLAG_RE = re.compile(rb"H7CTF\{[^}\n]*\}")


def records(path):
    d = open(path, "rb").read()
    assert d[:4] in (b"\xd4\xc3\xb2\xa1", b"\xa1\xb2\xc3\xd4"), "không phải pcap"
    off, out = 24, []
    while off + 16 <= len(d):
        _, _, cap, _ = struct.unpack("<IIII", d[off:off + 16])
        off += 16
        out.append(d[off:off + cap])
        off += cap
    return out


def provkey_from_adv(recs):
    for p in recs:
        if p.startswith(SYNC):
            continue
        m = re.search(rb"\xff\x39\x0f\x01(.{16})", p, re.S)
        if m:
            return m.group(1), p
    raise SystemExit("[-] không thấy provkey trong packet ADV")


def reassemble(recs):
    """Trả về dict handle -> bytes đã ghép."""
    bodies = [p[HDR:len(p) - CRC] for p in recs if p.startswith(SYNC)]
    blobs, pending = {}, None
    for i, b in enumerate(bodies):
        nxt = bodies[i + 1] if i + 1 < len(bodies) else None
        if pending and len(b) <= 20 and not (len(b) == 4 and b[:2] == struct.pack("<H", pending[0])):
            h, off = pending                              # data nối tiếp
            blobs[h][off:off + len(b)] = b
            pending = (h, off + len(b)) if len(b) == 20 else None
        elif len(b) == 4:                                 # handle + offset
            h, off = struct.unpack("<HH", b)
            blobs.setdefault(h, bytearray())
            pending = (h, off)
        elif len(b) == 2 and nxt is not None and len(nxt) == 20:
            h = struct.unpack("<H", b)[0]                 # chọn handle, offset 0
            blobs.setdefault(h, bytearray())
            pending = (h, 0)
        elif len(b) >= 11:                                # notify tự chứa: handle + data
            h = struct.unpack("<H", b[:2])[0]
            blobs.setdefault(h, bytearray())[0:] = b[2:]
            pending = None
        else:
            pending = None
    return {h: bytes(v) for h, v in blobs.items()}


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "analysis/capture.pcap"
    recs = records(path)
    key, adv = provkey_from_adv(recs)
    print("[*] ADV chứa provkey : %s" % adv.hex().upper())
    print("[*] provkey          : %s" % key.hex())

    blobs = reassemble(recs)
    for h in sorted(blobs):
        v = blobs[h]
        tag = repr(v[:60]) if all(32 <= c < 127 or c in (10, 9) for c in v) else v.hex()
        print("[*] 0x%04X (%2d byte) %s" % (h, len(v), tag))

    ct_cfg, nonce, ct_vault = blobs.get(0x21, b""), blobs.get(0x31, b""), blobs.get(0x33, b"")
    if not (ct_cfg and nonce and ct_vault):
        print("[-] thiếu một trong ba đặc tính 0x0021 / 0x0031 / 0x0033")
        return 1

    ks = b"".join(hashlib.sha256(key + nonce + bytes([i])).digest() for i in range(8))
    v1 = bytes(c ^ key[i % len(key)] for i, c in enumerate(ct_cfg))
    v2 = bytes(c ^ ks[i] for i, c in enumerate(ct_vault))
    print("\n[*] config@0x0021 -> %r" % v1)
    print("[*] vault @0x0033 -> %r" % v2)

    found = [m.group(0).decode() for m in (FLAG_RE.search(v1), FLAG_RE.search(v2)) if m]
    if len(found) < 2:
        print("\n[-] mới có %d/2 flag" % len(found))
        return 1
    open("flag.txt", "w", encoding="utf-8").write("\n".join(found) + "\n")
    print("\n[+] v1 = %s\n[+] v2 = %s" % tuple(found))
    return 0


if __name__ == "__main__":
    sys.exit(main())
