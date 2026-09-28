#!/usr/bin/env python
"""Minimal DEX reader: locate a class's methods and disassemble their bytecode.

Only what is needed to follow the string built by com.fleetlink.Signer.sign():
constants, method calls, and moves. Unknown opcodes are printed raw.
"""
import struct
import sys

DEX = sys.argv[1] if len(sys.argv) > 1 else "files/dex/classes.dex"
TARGET = sys.argv[2] if len(sys.argv) > 2 else "Lcom/fleetlink/Signer;"

d = open(DEX, "rb").read()
u16 = lambda o: struct.unpack_from("<H", d, o)[0]
u32 = lambda o: struct.unpack_from("<I", d, o)[0]

STRINGS_N, STRINGS_OFF = u32(0x38), u32(0x3c)
TYPES_N, TYPES_OFF = u32(0x40), u32(0x44)
PROTOS_N, PROTOS_OFF = u32(0x48), u32(0x4c)
FIELDS_N, FIELDS_OFF = u32(0x50), u32(0x54)
METHODS_N, METHODS_OFF = u32(0x58), u32(0x5c)
DEFS_N, DEFS_OFF = u32(0x60), u32(0x64)


def uleb(o):
    r = s = 0
    while True:
        b = d[o]
        o += 1
        r |= (b & 0x7F) << s
        s += 7
        if not b & 0x80:
            return r, o


S = []
for i in range(STRINGS_N):
    p = u32(STRINGS_OFF + 4 * i)
    n, p = uleb(p)
    S.append(d[p:p + n].decode("utf-8", "replace"))


def desc(t):
    if t == 0xFFFFFFFF or t >= TYPES_N:
        return "void"
    return S[u32(TYPES_OFF + 4 * t)]


def method_sig(mi):
    o = METHODS_OFF + 8 * mi
    cls = desc(u32(o) & 0xFFFF)
    proto = u32(o + 2) & 0xFFFF
    name = S[u32(o + 4)]
    po = u32(PROTOS_OFF + 12 * proto + 8)
    args = []
    if po:
        for k in range(u32(po)):
            args.append(desc(u16(po + 4 + 2 * k)))
    ret = desc(u32(PROTOS_OFF + 12 * proto + 4))
    return "%s %s.%s(%s)" % (ret, cls, name, ", ".join(args))


# --- opcode table (the subset that shows up in string building) ----------
OPS = {
    0x00: ("nop", 1), 0x01: ("move", 2), 0x02: ("move/from16", 3), 0x03: ("move/16", 4),
    0x04: ("move-wide", 2), 0x06: ("move-wide/16", 3), 0x07: ("move-object", 2),
    0x08: ("move-object/from16", 3), 0x0b: ("move-result", 1), 0x0c: ("move-result-wide", 1),
    0x0d: ("move-result-object", 1), 0x0e: ("move-exception", 1), 0x0f: ("return-void", 1),
    0x10: ("return", 2), 0x11: ("return-wide", 2), 0x12: ("return-object", 2),
    0x13: ("const/4", 2), 0x14: ("const/16", 3), 0x15: ("const", 5), 0x16: ("const/high16", 3),
    0x17: ("const-wide/16", 3), 0x19: ("const-wide/32", 5), 0x1a: ("const-string", 3),
    0x1b: ("const-string/jumbo", 5), 0x1c: ("const-class", 3),
    0x1d: ("monitor-enter", 2), 0x1e: ("monitor-exit", 2),
    0x20: ("array-length", 2), 0x22: ("throw", 2),
    0x23: ("goto", 2), 0x28: ("goto/16", 3),
    0x2d: ("cmpl-float", 4), 0x32: ("if-eq", 4), 0x33: ("if-ne", 4), 0x34: ("if-lt", 4),
    0x38: ("if-eqz", 3), 0x39: ("if-nez", 3), 0x3d: ("if-ltz", 3),
    0x44: ("aget", 4), 0x4b: ("aput", 4), 0x52: ("iget", 4), 0x54: ("iget-wide", 4),
    0x5b: ("iput", 4), 0x5d: ("iput-wide", 4), 0x50: ("iget-object", 4), 0x57: ("iput-object", 4),
    0x6e: ("invoke-virtual", 3), 0x6f: ("invoke-virtual/range", 2),
    0x70: ("invoke-super", 3), 0x71: ("invoke-super/range", 2),
    0x72: ("invoke-direct", 3), 0x73: ("invoke-direct/range", 2),
    0x74: ("invoke-static", 3), 0x75: ("invoke-static/range", 2),
    0x76: ("invoke-interface", 3), 0x77: ("invoke-interface/range", 2),
    0x78: ("invoke-polymorphic", 3), 0x7a: ("invoke-custom", 3),
    0x81: ("int-to-long", 3), 0x82: ("int-to-float", 3), 0x8b: ("int-to-byte", 3),
    0x8e: ("int-to-b", 3), 0x92: ("long-to-int", 3), 0xa0: ("add-int/2addr", 2),
    0xa2: ("sub/2addr", 2), 0xc4: ("add-int", 4), 0xc5: ("add-int/2addr", 2),
    0xb0: ("add-int/lit8", 3), 0xc9: ("shl/2addr", 2),
    0xd8: ("ushr-int/lit8", 3), 0xfa: ("rem-int/2addr", 2),
    0xed: ("mul-int/lit8", 3),
}
AGU_IS_RANGE = {0x6f, 0x71, 0x73, 0x75, 0x77}


def disasm(code_off, label):
    insns_size = u16(code_off + 2)
    regs = u16(code_off + 4)
    ins = u16(code_off + 6)
    outs = u16(code_off + 8)
    o = code_off + 0x10
    end = o + insns_size * 2
    print("  --- %s  regs=%d ins=%d outs=%d insns=%d ---" % (label, regs, ins, outs, insns_size))
    pos = 0
    while o < end:
        op = d[o]
        w = u16(o)
        at = o - (code_off + 0x10)
        name, width = OPS.get(op, ("op_%02x" % op, 1))
        if op in (0x1A, 0x1B):                      # const-string
            print("    %4d %-22s v%d, \"%s\"" % (at, name, w >> 8, S[u32(o + 4) if op == 0x1B else u16(o + 2)]))
        elif op in (0x6E, 0x70, 0x72, 0x74, 0x76):   # invoke (reg/slice form)
            cnt = u16(o + 2)
            mref = u32(o + 4)
            print("    %4d %-22s {%d regs}, %s" % (at, name, cnt, method_sig(mref)))
        elif op in AGU_IS_RANGE:
            cnt = u16(o + 2)
            mref = u32(o + 4)
            print("    %4d %-22s v%d..(+%d), %s" % (at, name, d[o + 2], cnt, method_sig(mref)))
        elif op in (0x22,):
            print("    %4d %-22s v%d" % (at, name, w >> 8))
        elif name.startswith("op_"):
            print("    %4d %-22s raw=%04x %s" % (at, name, w, d[o + 2:o + 8].hex()))
        else:
            print("    %4d %-22s %04x  %s" % (at, name, w, d[o + 2:o + 8].hex()))
        o += width * 2
        pos += 1


def methods_of(cls_desc_idx):
    for i in range(DEFS_N):
        base = DEFS_OFF + 0x70 * i
        if u32(base) != cls_desc_idx:
            continue
        cdo = u32(base + 0x18)
        if not cdo:
            return
        sf, o = uleb(cdo)
        af, o = uleb(o)
        sm, o = uleb(o)
        am, o = uleb(o)
        mid = 0
        for _ in range(sm):
            diff, o = uleb(o)
            _af, o = uleb(o)
            code, o = uleb(o)
            mid += diff
            yield ("direct", mid, code)
        mid = 0
        for _ in range(am):
            diff, o = uleb(o)
            _af, o = uleb(o)
            code, o = uleb(o)
            mid += diff
            yield ("virtual", mid, code)


for t in range(TYPES_N):
    if desc(t) == TARGET:
        for kind, mid, code in methods_of(t):
            o = METHODS_OFF + 8 * mid
            nm = S[u32(o + 4)]
            if code:
                disasm(code, "%s %s()" % (kind, nm))
            else:
                print("  (no code) %s %s" % (kind, method_sig(mid)))
