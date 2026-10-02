"""Kick the CAN - reassemble ISO-TP (ISO 15765-2) từ candump log, giải UDS ReadDataByIdentifier.

Dùng:
    python solve.py <capture.log>
    python solve.py --url https://<host>/capture.log
"""
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FRAME = re.compile(r"^\(\d+\.\d+\)\s+\S+\s+([0-9A-Fa-f]{3,8})#([0-9A-Fa-f]+)\s*$")
FLAG_RE = re.compile(rb"H7CTF\{[^}\n]*\}")


def load(path=None, url=None):
    if url:
        with urllib.request.urlopen(url, timeout=60) as r:
            return r.read().decode(errors="replace").splitlines()
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read().splitlines()


def parse(lines):
    frames = []
    for ln in lines:
        m = FRAME.match(ln.strip())
        if m:
            frames.append((m.group(1).upper(), bytes.fromhex(m.group(2))))
    return frames


def isotp_reassemble(frames):
    """Trả về dict: can_id -> list (payload, các frame đã dùng)."""
    out = {}
    pending = {}
    for can_id, data in frames:
        if not data:
            continue
        pci = data[0]
        if pci >> 4 == 1:                       # First Frame
            total = ((pci & 0x0F) << 8) | data[1]
            pending[can_id] = {"total": total, "buf": bytearray(data[2:]), "next": 1}
            out.setdefault(can_id, [])
        elif pci >> 4 == 2 and can_id in pending:   # Consecutive Frame
            p = pending[can_id]
            if pci & 0x0F != p["next"] & 0x0F:
                continue
            p["buf"] += data[1:]
            p["next"] += 1
            if len(p["buf"]) >= p["total"]:
                out[can_id].append(bytes(p["buf"][:p["total"]]))
                del pending[can_id]
        elif pci >> 4 == 0 and pci & 0x0F:         # Single Frame
            out.setdefault(can_id, []).append(bytes(data[1:1 + (pci & 0x0F)]))
    return out


def main():
    args = [a for a in sys.argv[1:]]
    if args and args[0] == "--url":
        lines = load(url=args[1])
    elif args:
        lines = load(path=args[0])
    else:
        sys.exit("dùng: python solve.py <capture.log> | --url <url>")

    frames = parse(lines)
    print("[*] %d dòng log -> %d frame hợp lệ" % (len(lines), len(frames)))
    msgs = isotp_reassemble(frames)
    for can_id in sorted(msgs):
        print("[*] CAN 0x%s: %d thông điệp ISO-TP hoàn chỉnh" % (can_id, len(msgs[can_id])))

    hit = None
    for can_id, payloads in sorted(msgs.items()):
        for i, p in enumerate(payloads):
            m = FLAG_RE.search(p)
            if m:
                hit = m.group(0).decode()
            if len(p) >= 3 and p[0] == 0x62:            # UDS ReadDataByIdentifier positive
                sid = (p[1] << 8) | p[2]
                body = p[3:]
                print("\n[+] 0x%s msg#%d: RDBT DID=0x%04X, %d byte dữ liệu"
                      % (can_id, i, sid, len(body)))
                print("    hex  : %s" % body.hex())
                print("    ascii: %r" % bytes(c if 32 <= c < 127 else 46 for c in body))
                if m:
                    print("    >>> khớp mẫu flag: %s" % hit)

    if not hit:
        print("\n[-] không thấy flag trong các thông điệp đã reassemble")
        return 1
    with open("flag.txt", "w", encoding="utf-8") as fh:
        fh.write(hit + "\n")
    print("\n[+] FLAG: %s" % hit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
