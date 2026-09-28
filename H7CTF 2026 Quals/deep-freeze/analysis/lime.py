"""LiME memory-image helper: section table, needle scan, region extract.

LiME layout: repeated 32-byte headers {magic 'LIME', version, start, end, type}
each followed by (end-start+1) bytes of physical memory. So a file offset maps to a
virtual address only through the section it belongs to.

usage:
  python lime.py sections <dump>
  python lime.py find <dump> <needle> [needle...]      # needles: ascii, or hex:NNNNAABB
  python lime.py extract <dump> <hex-vaddr> <len> <out>
"""

import re
import struct
import sys

MAGIC = 0x4C694D45  # "LiME"
HDR = 32
TYPES = {0: "raw", 1: "pagedsf", 2: "elf32", 3: "elf64", 4: "mach-o64", 5: "hibernate"}


def sections(path):
    """Yield (idx, start, end, type, data_file_off)."""
    out = []
    with open(path, "rb") as f:
        pos = 0
        idx = 0
        while True:
            f.seek(pos)
            h = f.read(HDR)
            if len(h) < HDR:
                break
            magic, version, start, end, typ = struct.unpack("<IIQQQ", h)
            if magic != MAGIC:
                if idx == 0:
                    sys.exit(f"[-] not a LiME image at offset 0 (magic 0x{magic:08x})")
                break
            size = end - start + 1
            out.append((idx, start, end, typ, pos + HDR))
            idx += 1
            pos += HDR + size
    return out


def vaddr_of(secs, file_off):
    for _, start, end, _t, doff in secs:
        if doff <= file_off < doff + (end - start + 1):
            return start + (file_off - doff)
    return None


def file_off_of(secs, vaddr):
    for _, start, end, _t, doff in secs:
        if start <= vaddr <= end:
            return doff + (vaddr - start)
    return None


def parse_needle(s):
    if s.startswith("hex:"):
        return bytes.fromhex(s[4:])
    return s.encode()


def scan(path, needles, max_hits=25, window=96):
    secs = sections(path)
    total = sum(s[2] - s[1] + 1 for s in secs)
    print(f"[*] {len(secs)} section(s), {total / 2**30:.2f} GiB of mapped memory")
    counts = {n.decode(errors='replace'): 0 for n in needles}
    CHUNK = 1 << 24
    OVERLAP = max(len(n) for n in needles) - 1
    f = open(path, "rb")
    off = 0
    carried = b""
    shown = 0
    while True:
        f.seek(off)
        buf = f.read(CHUNK)
        if not buf:
            break
        data = carried + buf
        base = off - len(carried)
        for n in needles:
            start = 0
            while True:
                i = data.find(n, start)
                if i < 0:
                    break
                fo = base + i
                va = vaddr_of(secs, fo)
                key = n.decode(errors="replace")
                counts[key] += 1
                if counts[key] <= max_hits:
                    ctx = data[i - 16 if i >= 16 else 0: i + len(n) + window]
                    printable = re.sub(rb"[^\x20-\x7e]", b".", ctx).decode()
                    print(f"\n[hit] needle={key!r}\n  file=0x{fo:x}  vaddr={'0x%x' % va if va else '??'}")
                    print(f"  ctx: {printable}")
                    shown += 1
                start = i + 1
        carried = data[-OVERLAP:] if OVERLAP > 0 else b""
        off += len(buf)
        if shown and shown % 40 == 0:
            print(f"    ... scan progress {off / 2**30:.2f} GiB", flush=True)
    f.close()
    print("\n=== totals ===")
    for k, v in counts.items():
        print(f"  {v:6d}  {k!r}")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    mode, path = sys.argv[1], sys.argv[2]
    if mode == "sections":
        secs = sections(path)
        for idx, s, e, t, doff in secs:
            print(f"  [{idx}] 0x{s:016x} - 0x{e:016x}  {TYPES.get(t, t):10s} "
                  f"{(e - s + 1) / 2**20:8.2f} MiB  file=0x{doff:x}")
        print(f"total mapped: {sum(e - s + 1 for _i, s, e, _t, _d in secs) / 2**30:.2f} GiB")
    elif mode == "find":
        scan(path, [parse_needle(x) for x in sys.argv[3:]])
    elif mode == "extract":
        secs = sections(path)
        va, ln, out = int(sys.argv[3], 0), int(sys.argv[4], 0), sys.argv[5]
        with open(path, "rb") as f, open(out, "wb") as g:
            done = 0
            while done < ln:
                fo = file_off_of(secs, va + done)
                if fo is None:
                    print(f"[!] unmapped at 0x{va + done:x}")
                    done += 4096
                    continue
                run = ln - done
                for _i, s, e, _t, doff in secs:
                    if s <= va + done <= e:
                        run = min(run, (e - (va + done)) + 1)
                        break
                f.seek(fo)
                g.write(f.read(run))
                done += run
        print(f"[+] wrote {out}")
    else:
        sys.exit(f"unknown mode {mode}")


if __name__ == "__main__":
    main()
