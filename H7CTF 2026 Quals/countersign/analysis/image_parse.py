"""image_parse.py - decode the captured Countersign program image (GET output).

Pure offline data analysis of analysis/image.txt.  No network, no execution of
the target binary.  Every structural claim below is derived from the GET
serializer loop in cs.asm (vma 0x1240..0x13d8, records at 0x462e0, stride 0x30c)
and from the opcode jump table at vma 0x406c (see DERIVATION notes next to each
layout constant).  stdlib only, no arguments, runs top to bottom.
"""

import collections
import math
import os
import re
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
IMAGE_TXT = os.path.join(HERE, "image.txt")
OUT_TXT = os.path.join(HERE, "image_parsed.txt")
EXPECT_LEN = 3037
HDR_LEN = 0x12          # lea rdi,[rbp+0x12]  @0x12bb -> body starts 18 bytes in
STRIDE = 0x30c          # add r13,0x30c       @0x1389
EDGE_LEN = 13           # add rax,0xd         @0x1344 (13 output bytes per edge)
WIN = 32                # entropy window

L = []                  # output lines


def emit(s=""):
    L.append(s)


def rule(title=""):
    emit("=" * 100)
    if title:
        emit(title)
        emit("=" * 100)


def sub(s):
    emit("")
    emit("--- " + s + " " + "-" * max(0, 95 - len(s)))


# ---------------------------------------------------------------------------
# 1. extract the hex run  (image.txt also carries banner/echo lines)
# ---------------------------------------------------------------------------
rule("1. INPUT")
raw = open(IMAGE_TXT, encoding="utf-8", errors="replace").read()
runs = re.findall(r"(?:[0-9a-fA-F]\s*){32,}", raw)
runs = [re.sub(r"\s", "", r) for r in runs]
runs = [r for r in runs if len(r) % 2 == 0]
runs.sort(key=len, reverse=True)
if not runs:
    raise SystemExit("NO HEX RUN in %s (file holds %d chars: %r). image.txt was overwritten by an empty "
                     "GET - re-capture it." % (IMAGE_TXT, len(raw), raw[:40]))
hexstr = runs[0].lower()
d = bytes.fromhex(hexstr)
emit("source file          : %s" % IMAGE_TXT)
emit("raw file chars       : %d" % len(raw))
emit("non-hex context lines: %s" % (
    [ln[:40] for ln in raw.splitlines() if re.search(r"[^0-9a-fA-F\s]", ln)] or "(none - file is pure hex)"))
emit("longest hex run      : %d chars -> %d bytes" % (len(hexstr), len(d)))
emit("assert len == %d     : %s" % (EXPECT_LEN, len(d) == EXPECT_LEN))
# integrity witness: grab.out holds the first 400 hex chars of the same capture
wit = ""
gw = os.path.join(HERE, "grab.out")
if os.path.exists(gw):
    t = open(gw, encoding="utf-8", errors="replace").read()
    m = re.findall(r"[0-9a-f]{200,}", t)
    wit = max(m, key=len) if m else ""
if wit:
    emit("grab.out witness     : %d chars, matches image.txt prefix: %s" % (len(wit), wit == hexstr[:len(wit)]))
if len(hexstr) < 2 * EXPECT_LEN:
    emit("!!! image.txt holds only %d hex chars (< %d).  It was clobbered by an empty GET"
         % (len(hexstr), 2 * EXPECT_LEN))
    emit("!!! (fetch_image.py writes image.txt unconditionally, even on a 0-byte read).  Re-capture or restore.")
assert len(d) == EXPECT_LEN, "decoded length %d != %d" % (len(d), EXPECT_LEN)

# ---------------------------------------------------------------------------
# 2. layout, derived from the serializer, byte by byte
# ---------------------------------------------------------------------------
#  @0x126e mov DWORD[60a0],'CSGN'         -> magic        0x00 u8[4]
#  @0x127f mov WORD [60a4],r12w           -> version      0x04 u16
#  @0x1261/0x1287 dx=u16[0x462d8] -> 60a6  -> rec count   0x06 u16
#  @0x128e movzx dx,u16[0x462d4] -> 60a8   -> start tag   0x08 u16
#  @0x129c mov  rdx,[0x76ee0] -> 60aa      -> seed        0x0a u64
# per record (in-memory slot base = 0x462e0, r13 = base+8):
#  @0x12d0 movzx ax,u16[r13-0x8] -> 60a0/1 -> tag         slot+0x00 u16
#  @0x12e5 movzx al,u8 [r13-0x6] -> 60a2   -> pred_reg    slot+0x02 u8   (0xff = unconditional)
#  @0x12f5 movzx al,u8 [r13-0x5] -> 60a3   -> pred_bit    slot+0x03 u8   (bit index tested)
#  @0x12fd movzx ax,u16[r13-0x4] -> 60a4/5 -> dflt_next   slot+0x04 u16  (no edge matched -> next tag)
#  @0x12d5 movzx r14d,u16[r13-0x2] ->60a6/7-> pay_len L   slot+0x06 u16  (also memcpy len @0x12ea)
#  @0x1306 memcpy(rdi=+8, rsi=r13, rdx=L)               -> payload verbatim
#  @0x130b movzx esi,u8 [r13+0x200] -> [rcx]            -> edge_cnt k slot+0x208 u8
#  @0x1340..0x137b, 13 bytes per edge (rdx = slot+0x214+16j, pre-incremented @0x1348):
#       [rax-0x14] u8  <- [rdx-0x8]  = entry+0x00 u8   type   (matched against pred bit / 0xff)
#       [rax-0x13] u16 <- [rdx-0x16] = entry+0x02 u16  target (next tag)
#       [rax-0x11] u32 <- [rdx-0x14] = entry+0x04 u32  tweak  (message word)
#       [rax-0x0d] u32 <- [rdx-0x10] = entry+0x08 u32  sig_lo \  6-byte countersignature
#       [rax-0x09] u16 <- [rdx-0xc]  = entry+0x0c u16  sig_hi /  (verified @0x1e3b/0x1e47)
#  cursor advance @0x1384 lea rdi,[rdi+r9+0xd], r9=13*(k-1)  => record size = 9 + L + 13k
rule("2. LAYOUT DERIVED FROM THE SERIALIZER (cs.asm 0x1240..0x13d8)")
emit("stream = header(0x12) then records;  record = 8B head + L payload + k byte + k * 13B edges")
emit("")
emit("  image field          off      width  serializer vma        in-memory slot")
emit("  ------------------   ------   -----  -------------------   --------------")
emit("  magic 'CSGN'         0x0000   4      0x126e                -")
emit("  version              0x0004   2      0x127f (r12w)         -")
emit("  record_count         0x0006   2      0x1261/0x1287         u16@0x462d8")
emit("  start_tag            0x0008   2      0x128e                u16@0x462d4")
emit("  seed                 0x000a   8      0x129c                u64 @0x76ee0")
emit("  rec.tag              rec+0x00 2      0x12d0 ([r13-0x8])    slot+0x00")
emit("  rec.pred_reg         rec+0x02 1      0x12e5 ([r13-0x6])    slot+0x02  (0xff=uncond)")
emit("  rec.pred_bit         rec+0x03 1      0x12f5 ([r13-0x5])    slot+0x03")
emit("  rec.dflt_next        rec+0x04 2      0x12fd ([r13-0x4])    slot+0x04")
emit("  rec.pay_len (L)      rec+0x06 2      0x12d5/0x12ea ([r13-0x2]) slot+0x06 = memcpy len")
emit("  rec.payload          rec+0x08 L      0x1306 memcpy          slot+0x08")
emit("  rec.edge_cnt (k)     rec+0x8+L 1     0x130b/0x1317          slot+0x208")
emit("  edge.type            e+0x00   1      0x1340/0x134c          slot+0x20c+16j+0x00")
emit("  edge.target          e+0x01   2      0x134f/0x1353          slot+0x20c+16j+0x02")
emit("  edge.tweak           e+0x03   4      0x1359/0x135e          slot+0x20c+16j+0x04")
emit("  edge.sig_lo          e+0x07   4      0x136d/0x1374          slot+0x20c+16j+0x08")
emit("  edge.sig_hi          e+0x11   2      0x1377/0x137b          slot+0x20c+16j+0x0c")
emit("")
emit("  record size = 9 + L + 13k   (@0x1384 lea rdi,[rdi+r9+0xd], r9=13*(k-1))")

# --- payload grammar (opcode table) : jump table @0x406c, handlers 0x1840..0x1ae0
OPS = {
    0x00: ("NOP", 1, ""),
    0x01: ("MOV.imm", 6, "reg,imm32"),
    0x02: ("MOV.reg", 3, "src,dst"),
    0x03: ("ADD.reg", 3, "dst,src"),
    0x04: ("XOR.reg", 3, "dst,src"),
    0x05: ("AND.reg", 3, "dst,src"),
    0x06: ("OR.reg", 3, "dst,src"),
    0x07: ("ROL.imm", 3, "reg,n"),
    0x08: ("SHR.imm", 3, "reg,n"),
    0x09: ("ADD.imm", 6, "reg,imm32"),
    0x0A: ("XOR.imm", 6, "reg,imm32"),
    0x0B: ("AND.imm", 6, "reg,imm32"),
    0x0C: ("LDIN", 3, "reg,inbyte"),
    0x0D: ("GETENV", 1, ""),
    0x0E: ("EMIT", 1, ""),
    0x0F: ("HALT", 1, ""),
}
IMM_OPS = {0x01, 0x09, 0x0A, 0x0B}

sub("hexdump of the first 0x40 bytes, named")
names = [(0x00, "magic", 4), (0x04, "version", 2), (0x06, "record_count", 2), (0x08, "start_tag", 2),
         (0x0A, "seed(nonce rev)", 8), (0x12, "rec0.tag", 2), (0x14, "rec0.pred_reg", 1),
         (0x15, "rec0.pred_bit", 1), (0x16, "rec0.dflt_next", 2), (0x18, "rec0.pay_len", 2),
         (0x1A, "rec0.payload[0]", 1)]
for i in range(0, 0x40, 16):
    ch = d[i:i + 16]
    parts = ["%s=%s" % (nm, d[o:o + w].hex()) for o, nm, w in names if i <= o < i + 16]
    emit("  %04x  %-47s  %s%s" % (i, " ".join("%02x" % b for b in ch),
                                  "".join(chr(b) if 32 <= b < 127 else "." for b in ch),
                                  ("   ; " + "  ".join(parts)) if parts else ""))

# ---------------------------------------------------------------------------
# 3. decode into a typed tree with per-byte accounting
# ---------------------------------------------------------------------------
CLASS_NAME = {"HDR": "header", "REC": "record header", "CODE": "bytecode op/operand",
              "IMM": "imm32 operand (per-instance)", "EDGE": "edge type+target",
              "TWE": "edge tweak u32", "SIG": "edge countersignature 6B", "??": "UNEXPLAINED"}
owner = [None] * len(d)      # every byte must be claimed exactly once


def claim(off, ln, cls, what):
    for i in range(off, off + ln):
        if owner[i] is not None:
            raise AssertionError("double claim at 0x%x (%s vs %s)" % (i, owner[i], what))
        owner[i] = (cls, what)
    return off


magic = d[0:4]
version, count, start_tag = struct.unpack_from("<HHH", d, 4)
seed = struct.unpack_from("<Q", d, 0x0A)[0]
claim(0, 4, "HDR", "magic")
claim(4, 2, "HDR", "version")
claim(6, 2, "HDR", "record_count")
claim(8, 2, "HDR", "start_tag")
claim(0x0A, 8, "HDR", "seed")
dflt_field = struct.unpack_from("<H", d, 4)[0]

rule("3. HEADER")
emit("  magic        : %r  (%s)" % (magic.decode("latin1"), magic.hex()))
emit("  version      : %d" % version)
emit("  record_count : %d   (u16@0x462d8; also the loop bound dword@0x462d8)" % count)
emit("  start_tag    : 0x%04x  (u16@0x462d4 -> RUN looks for the record whose tag == this)" % start_tag)
emit("  seed         : 0x%016x  bytes %s  (= nonce %s byte-reversed)"
     % (seed, d[0x0A:0x12].hex(), d[0x0A:0x12][::-1].hex()))
emit("  NOTE: the MAC key is at 0x76ef0..0x76eff (see 0x1b38) - a DIFFERENT 8 bytes than the")
emit("        leaked seed at 0x76ee0, so the signatures cannot be recomputed from the image.")

records = []
p = HDR_LEN
bad = []
for i in range(count):
    if p + 8 > len(d):
        bad.append(("header truncated", p))
        break
    tag, pr, pb, dflt, Llen = struct.unpack_from("<HBBHH", d, p)
    claim(p, 8, "REC", "rec%d.head" % i)
    if p + 8 + Llen + 1 > len(d):
        bad.append(("payload truncated", p + 8))
        break
    pay = d[p + 8:p + 8 + Llen]
    claim(p + 8, Llen, "CODE", "rec%d.payload" % i)
    k = d[p + 8 + Llen]
    claim(p + 8 + Llen, 1, "REC", "rec%d.edge_cnt" % i)
    if p + 9 + Llen + 13 * k > len(d):
        bad.append(("edges truncated", p + 9 + Llen))
        break
    edges = []
    for j in range(k):
        e = p + 9 + Llen + 13 * j
        ty = d[e]
        tgt, tweak, slo, shi = struct.unpack_from("<HIIH", d, e + 1)
        claim(e, 1, "EDGE", "rec%d.edge%d.type" % (i, j))
        claim(e + 1, 2, "EDGE", "rec%d.edge%d.target" % (i, j))
        claim(e + 3, 4, "TWE", "rec%d.edge%d.tweak" % (i, j))
        claim(e + 7, 6, "SIG", "rec%d.edge%d.sig" % (i, j))
        edges.append(dict(off=e, ty=ty, tgt=tgt, tweak=tweak, sig_lo=slo, sig_hi=shi, sig=slo | (shi << 32)))
    rec = dict(i=i, off=p, tag=tag, pred_reg=pr, pred_bit=pb, dflt=dflt, L=Llen, k=k,
               payoff=p + 8, pay=pay, edges=edges, size=9 + Llen + 13 * k)
    records.append(rec)
    p += rec["size"]

# --- disassemble each payload with the opcode table; check exact closure
for rec in records:
    ins, pc = [], 0
    while pc < rec["L"]:
        b = rec["pay"][pc]
        if b not in OPS:
            ins.append(dict(off=rec["payoff"] + pc, op=None, name="??", len=1, raw=rec["pay"][pc:pc + 1],
                            txt="unknown opcode %02x" % b))
            pc += 1
            continue
        name, ln, args = OPS[b]
        raw = rec["pay"][pc:pc + ln]
        if ln == 6:
            reg, imm = raw[1], struct.unpack_from("<I", raw, 2)[0]
            txt = "%-8s r%-2d, 0x%08x" % (name, reg, imm)
            ops = [("CODE", rec["payoff"] + pc, 2), ("IMM", rec["payoff"] + pc + 2, 4)]
        elif ln == 3:
            x, y = raw[1], raw[2]
            txt = "%-8s r%-2d, %s" % (name, x, ("0x%02x" % y) if name in ("ROL.imm", "SHR.imm", "LDIN") else "r%-2d" % y)
            ops = [("CODE", rec["payoff"] + pc, 3)]
        else:
            txt = "%-8s" % name
            ops = [("CODE", rec["payoff"] + pc, 1)]
        for cls, o, ln2 in ops:
            for q in range(o, o + ln2):
                if owner[q] and owner[q][0] == "CODE":
                    owner[q] = (cls, "rec%d.%s" % (rec["i"], "ins@%x" % (o)))
        ins.append(dict(off=rec["payoff"] + pc, op=b, name=name, len=ln, raw=raw, txt=txt))
        pc += ln
    rec["ins"] = ins
    rec["code_len"] = pc
    rec["closure"] = (pc == rec["L"])

rule("4. TYPED TREE / FULL BYTE ACCOUNTING")
un = [i for i, o in enumerate(owner) if o is None]
dbl = []
for i, o in enumerate(owner):
    if o is not None and o[0] == "??":
        dbl.append(i)
emit("declared record_count = %d, records parsed = %d, bytes consumed = %d of %d" %
     (count, len(records), p, len(d)))
emit("leftover after the last record: %d bytes %s" % (len(d) - p, ("(%s)" % d[p:].hex()) if p < len(d) else ""))
emit("UNEXPLAINED BYTES: %s" % ("NONE - every one of the %d bytes is claimed by exactly one field" % len(d) if not un else "!!! %d bytes: %s" % (len(un), [hex(x) for x in un[:80]])))
if un:
    def ranges(xs):
        out, s, e = [], xs[0], xs[0]
        for x in xs[1:]:
            if x == e + 1:
                e = x
            else:
                out.append((s, e)); s = e = x
        out.append((s, e))
        return out
    for a, b in ranges(un):
        emit("   unexplained range 0x%04x..0x%04x (%d bytes): %s" % (a, b, b - a + 1, d[a:b + 1].hex()))
for w, r_ in [(x, y) for x, y in bad]:
    emit("   TRUNCATION %s at 0x%x" % (w, r_))
emit("")
emit("byte census by class:")
cen = collections.Counter((o[0] if o else "??") for o in owner)
for cls in ["HDR", "REC", "CODE", "IMM", "EDGE", "TWE", "SIG", "??"]:
    if cen.get(cls):
        emit("   %-5s %-30s %5d bytes  (%5.2f%%)" % (cls, CLASS_NAME[cls], cen[cls], 100.0 * cen[cls] / len(d)))
emit("   ----- entropy-carrying material (IMM+TWE+SIG) = %d bytes;  deterministic structure = %d bytes"
     % (cen["IMM"] + cen["TWE"] + cen["SIG"], len(d) - cen["IMM"] - cen["TWE"] - cen["SIG"]))

# ---------------------------------------------------------------------------
# 5. record table
# ---------------------------------------------------------------------------
tagset = set(r["tag"] for r in records)
sub("record table (offset / tag / predicate / default-next / L / k / size)")
emit("  idx off      size  tag    pred_reg pred_bit dflt_next  L    k   edges@  closure")
for r in records:
    emit("  %3d 0x%04x %5d  0x%04x   0x%02x      0x%02x       0x%04x   %4d %3d  0x%04x  %s" %
         (r["i"], r["off"], r["size"], r["tag"], r["pred_reg"], r["pred_bit"], r["dflt"], r["L"], r["k"],
          r["edges"][0]["off"] if r["edges"] else r["payoff"] + r["L"] + 1,
          "ok" if r["closure"] else "!!! opcode stream does not close (%d != %d)" % (r["code_len"], r["L"])))
emit("")
emit("  sum of record sizes = %d ; body = 0x%x-0x12 = %d  ->  %s" %
     (sum(r["size"] for r in records), len(d), len(d) - HDR_LEN,
      "exact" if sum(r["size"] for r in records) == len(d) - HDR_LEN else "MISMATCH"))
emit("  distinct tags: %d of %d records (tags are the record identity; no numbering field exists)" %
     (len(tagset), len(records)))
lc = collections.Counter((r["L"], r["k"]) for r in records)
emit("")
emit("  record shape (L,k) histogram:")
for (ll, kk), c in sorted(lc.items(), key=lambda x: (-x[1], x[0])):
    emit("     L=%3d k=%2d  x%2d   size=%d" % (ll, kk, c, 9 + ll + 13 * kk))

# ---------------------------------------------------------------------------
# 6. block grammar: every block, its leading tag byte and its length
# ---------------------------------------------------------------------------
rule("5. BLOCK GRAMMAR")
sub("5a. record blocks (leading byte = tag low half, block = 9+L+13k bytes)")
emit("  off      len   lead tag    type-class")
def rclass(r):
    if r["L"] == 252:
        return "packer (input->regs)"
    if r["tag"] == 0x04A3:
        return "goal (GETENV/EMIT/HALT)"
    if r["L"] == 1:
        return "sink (HALT only)"
    if r["L"] == 12:
        return "leaf arithmetic (2 insns)"
    if r["L"] == 30:
        return "mixing node (5 insns)"
    if r["L"] == 117:
        return "wide node (28 insns)"
    return "other"
for r in records:
    emit("  0x%04x %5d   0x%02x  0x%04x  %s" % (r["off"], r["size"], d[r["off"]], r["tag"], rclass(r)))
emit("")
emit("  record-block size histogram: %s" % ", ".join("%dB x%d" % (k, v) for k, v in sorted(collections.Counter(r["size"] for r in records).items())))

sub("5b. payload instruction blocks (opcode stream, sizes 1/3/6)")
opc = collections.Counter()
for r in records:
    for x in r["ins"]:
        opc[(x["op"], x["name"], x["len"])] += 1
emit("  opcode  name      insn-len  count   operand bytes")
for (o, nm, ln), c in sorted(opc.items(), key=lambda x: (x[0][0] is None, x[0][0])):
    emit("  %s     %-9s %3d      %4d   %s" % ("%02x" % o if o is not None else "??", nm, ln, c,
                                              "op+reg+imm32 (imm32 = per-instance random)" if ln == 6 else
                                              "op+2 operands" if ln == 3 else "op only"))
emit("  total instructions %d over %d payload bytes" % (sum(opc.values()), sum(r["L"] for r in records)))
emit("  instruction length histogram: %s" % ", ".join("%dB x%d" % (k, v) for k, v in sorted(collections.Counter(x["len"] for r in records for x in r["ins"]).items())))
emit("  => the payload is NOT a fixed-size record array; it is a variable-length opcode stream")

sub("5c. edge blocks (13B each, leading byte = selector type)")
emit("  rec  idx off      len lead target  tweak      sig(6B)                             selector")
for r in records:
    for j, e in enumerate(r["edges"]):
        sel = ("always" if r["pred_reg"] == 0xFF else "bit %d of r%d" % (r["pred_bit"], r["pred_reg"])) if e["ty"] != 0xFF else "uncond"
        emit("  %3d  %3d 0x%04x %3d  0x%02x  0x%04x  0x%08x  %08x %04x  %s" %
             (r["i"], j, e["off"], EDGE_LEN, e["ty"], e["tgt"], e["tweak"], e["sig_lo"], e["sig_hi"], sel))
ne = sum(r["k"] for r in records)
emit("  total edges %d  (%d bytes = %.1f%% of the image)" % (ne, 13 * ne, 100.0 * 13 * ne / len(d)))
emit("  edge type histogram: %s" % ", ".join("0x%02x x%d" % (k, v) for k, v in sorted(collections.Counter(e["ty"] for r in records for e in r["edges"]).items())))

# ---------------------------------------------------------------------------
# 7. tag vocabulary / frequency
# ---------------------------------------------------------------------------
rule("6. TAG FREQUENCY (the 2-byte values)")
sub("6a. structured u16 fields (authoritative positions, little-endian value)")
fr = collections.defaultdict(lambda: dict(a=0, tgt=0, dflt=0, hdr=0, offs=[]))
fr[start_tag]["hdr"] += 1
for r in records:
    fr[r["tag"]]["a"] += 1
    fr[r["tag"]]["offs"].append((r["off"], "rec.tag"))
    fr[r["dflt"]]["dflt"] += 1
for r in records:
    for e in r["edges"]:
        fr[e["tgt"]]["tgt"] += 1
        fr[e["tgt"]]["offs"].append((e["off"] + 1, "edge.target"))
emit("  tag    as rec.tag  as edge.target  as rec.dflt_next  in header  total  raw byte-pair 'lo hi'")
for t, c in sorted(fr.items(), key=lambda x: -(x[1]["a"] + x[1]["tgt"] + x[1]["dflt"] + x[1]["hdr"])):
    tot = c["a"] + c["tgt"] + c["dflt"] + c["hdr"]
    emit("  0x%04x  %9d     %9d        %9d          %6d   %5d   %02x %02x" %
         (t, c["a"], c["tgt"], c["dflt"], c["hdr"], tot, t & 0xFF, t >> 8))
emit("")
emit("  every edge.target resolves to a declared record tag: %s" %
     ("YES - all %d edges" % ne if all(e["tgt"] in tagset for r in records for e in r["edges"]) else "NO (see below)"))
dangling = [(r["i"], e["tgt"]) for r in records for e in r["edges"] if e["tgt"] not in tagset]
for x in dangling:
    emit("     DANGLING rec%d -> 0x%04x" % x)

sub("6b. raw 2-byte-pair census (all 3036 overlapping pairs, to answer 'where does 66 0d occur?')")
pairs = collections.Counter()
poff = collections.defaultdict(list)
for i in range(len(d) - 1):
    key = d[i:i + 2]
    pairs[key] += 1
    if len(poff[key]) < 60:
        poff[key].append(i)
asked = ["660d", "0b48", "5724", "b14a", "e452", "2764", "1de8", "9a85", "ae38", "312c", "1541", "4115"]
emit("  pair  occurrences  first positions (class of the low byte's field)")
for hxv in asked:
    key = bytes.fromhex(hxv)
    c = pairs[key]
    ps = poff[key][:14]
    emit("  %s %2s %5d   %s" % (hxv[0:2], hxv[2:4], c, ", ".join("0x%x(%s)" % (x, owner[x][0] if owner[x] else "??") for x in ps)))
emit("")
top = [x for x in pairs.most_common(12)]
emit("  most frequent raw pairs overall: %s" % ", ".join("%s=%d" % (k.hex(), v) for k, v in top))
uniq2 = sum(1 for k, v in pairs.items() if v == 1)
emit("  distinct pair values %d ; pairs occurring exactly once %d (random filler) " % (len(pairs), uniq2))

sub("6c. the 6-byte countersignatures: unique per edge (signed) vs tags (derived)")
sigc = collections.Counter("%012x" % e["sig"] for r in records for e in r["edges"])
twk = collections.Counter("%08x" % e["tweak"] for r in records for e in r["edges"])
immc = collections.Counter(struct.unpack_from("<I", x["raw"], 2)[0] for r in records for x in r["ins"] if x["len"] == 6)
emit("  edges %d ; distinct 6B signatures %d ; repeats %s" % (ne, len(sigc), [k for k, v in sigc.items() if v > 1] or "none"))
emit("  edges %d ; distinct 4B tweaks  %d ; repeats %s" % (ne, len(twk), [k for k, v in twk.items() if v > 1] or "none"))
emit("  imm32 operands %d ; distinct %d ; repeats %s" % (sum(immc.values()), len(immc),
                                                         [ "%08x x%d" % (k, v) for k, v in immc.items() if v > 1] or "none"))
emit("  => the 40 tag values recur (up to %d times) and are enumerable => DERIVED identifiers/labels;" % max(v["a"] + v["tgt"] + v["dflt"] + v["hdr"] for v in fr.values()))
emit("     the 6-byte sig (edge+7, sig_lo u32 + sig_hi u16) never repeats => the SIGNED material.")
emit("     verification site: 0x1de1 builds msg 'E' || tag(2) || target(2) || type(1) || tweak(4) = 9 bytes,")
emit("     0x1af0 = SipHash-2-4 (constants 0x736f6d6570736575 / 0x646f72616e646f6d / 0x6c7967656e657261 /")
emit("     0x7465646279746573, 2+4 rounds) keyed from 0x76ef0, truncated to 6 bytes (0x1d00..0x1d19);")
emit("     0x1e3b/0x1e47 compare it against sig_lo/sig_hi.  MINT uses the same hash with domain byte 'M'.")

# ---------------------------------------------------------------------------
# 8. entropy profile
# ---------------------------------------------------------------------------
rule("7. ENTROPY PROFILE (window = %d bytes)" % WIN)
def stats(w):
    c = collections.Counter(w)
    n = len(w)
    ent = -sum((v / n) * math.log2(v / n) for v in c.values())
    e = n / 256.0
    chi2 = sum(((c.get(v, 0) - e) ** 2) / e for v in range(256))
    return len(c), ent, chi2
emit("  off      dist/32  entropy  chi2     rand-class  verdict")
first_rand = None
rows = []
for i in range(0, len(d) - WIN + 1, WIN):
    w = d[i:i + WIN]
    nd, ent, chi2 = stats(w)
    rnd = sum(1 for q in range(i, i + WIN) if owner[q] and owner[q][0] in ("IMM", "TWE", "SIG"))
    frac = rnd / WIN
    verdict = "RANDOM" if frac >= 0.75 else ("structure" if frac == 0 else ("mixed" if frac < 0.5 else "mostly-rand"))
    if first_rand is None and frac > 0:
        first_rand = i
    rows.append((i, nd, ent, chi2, frac, verdict))
for i, nd, ent, chi2, frac, verdict in rows:
    emit("  0x%04x   %4d    %5.3f   %7.1f    %5.1f%%      %s" % (i, nd, ent, chi2, 100 * frac, verdict))
emit("")
emit("  chi2 is against a uniform 256-symbol alphabet with n=32 (E=0.125 per bin).  Its FLOOR is 224.0,")
emit("  reached exactly when all 32 bytes in the window are distinct (i.e. maximal randomness); every")
emit("  repeated byte pushes it up (a window of 32 identical bytes would give 8196).  So:")
emit("     chi2 ~ 224 and dist=32   -> random material      chi2 > 1000 and dist < 16 -> structure")
emit("  min/max chi2 over the image: %.1f / %.1f ; windows at the floor: %d of %d" %
     (min(r[3] for r in rows), max(r[3] for r in rows),
      sum(1 for r in rows if r[3] < 240), len(rows)))
seq = [1 if (owner[q] and owner[q][0] in ("IMM", "TWE", "SIG")) else 0 for q in range(len(d))]
emit("")
sub("where structure ends and randomness begins (field-level, exact)")
rand_capable = [q for q in range(len(d)) if seq[q]]
struct_end = rand_capable[0] if rand_capable else len(d)
# rec0's 6 register-zeroing immediates ARE imm32 fields but their value is 0x00000000,
# so the first byte that actually carries per-instance entropy is the first non-zero one.
first_real = next((q for q in rand_capable if d[q] != 0), struct_end)
emit("  first byte inside a per-instance field : 0x%04x  (%s) field %s" %
     (struct_end, d[struct_end:struct_end + 4].hex(), owner[struct_end][1]))
emit("  first byte of REAL entropy             : 0x%04x  (%s) field %s of rec%d" %
     (first_real, d[first_real:first_real + 10].hex(), owner[first_real][1],
      next(r["i"] for r in records if r["off"] <= first_real < r["off"] + r["size"])))
emit("  fully deterministic prefix             : 0x0000 .. 0x%04x  (%d bytes = %.1f%% of the image)" %
     (first_real - 1, first_real, 100.0 * first_real / len(d)))
emit("")
emit("  offset map, per region (live = bytes that actually carry per-instance entropy; a 6-byte")
emit("     instruction's imm32 counts as live only when it is not 0x00000000):")
emit("     range                 rec  role                        size  live  where the determinism stops")
for r in records:
    zeroimm = sum(4 for x in r["ins"] if x["len"] == 6 and x["raw"][2:6] == b"\0\0\0\0")
    live = sum(seq[r["off"]:r["off"] + r["size"]]) - zeroimm
    code_end = r["off"] + 8 + r["L"] - 1
    if r["k"]:
        stop = ("header+program up to 0x%04x, then %d edge B (%d per-instance: 4B tweak + 6B sig each)"
                % (code_end, 13 * r["k"], live))
    elif zeroimm:
        stop = "whole record deterministic (%d imm32 bytes are 0)" % zeroimm
    else:
        stop = "whole record deterministic (no edges, no live immediate)"
    emit("     0x%04x..0x%04x  %3d  %-25s %5d  %5d   %s" %
         (r["off"], r["off"] + r["size"] - 1, r["i"], rclass(r), r["size"], live, stop))
runs_rand = []
q = 0
while q < len(d):
    if seq[q]:
        e = q
        while e + 1 < len(d) and seq[e + 1]:
            e += 1
        runs_rand.append((q, e))
        q = e + 1
    else:
        q += 1
struct_runs = []
q = 0
while q < len(d):
    if not seq[q]:
        e = q
        while e + 1 < len(d) and not seq[e + 1]:
            e += 1
        if e - q + 1 >= 8:
            struct_runs.append((q, e))
        q = e + 1
    else:
        q += 1
emit("  maximal deterministic stretches >= 8 bytes (%d total, first 30 shown):" % len(struct_runs))
for a, b in struct_runs[:30]:
    nxt = owner[b + 1][1] if b + 1 < len(d) and owner[b + 1] else "end of image"
    emit("     0x%04x .. 0x%04x  (%4d B)  next field: %s" % (a, b, b - a + 1, nxt))
emit("")
emit("  random-run summary (start / end / len / classes), first 12 of %d runs:" % len(runs_rand))
for a, b in runs_rand[:12]:
    emit("     0x%04x   0x%04x   %4d   %s" % (a, b, b - a + 1, "+".join(sorted(set(owner[x][0] for x in range(a, b + 1))))))
agg = collections.Counter(b - a + 1 for a, b in runs_rand)
emit("")
emit("  random-run length histogram: %s" % ", ".join("%dB x%d" % (k, v) for k, v in sorted(agg.items())))
emit("  => random material NEVER aligns to a fixed block size: it is 4-byte imm32/tweak fields at")
emit("     +2 mod 6 inside instructions and 4+6 bytes at +3/+7 mod 13 inside edges, so the runs above")
emit("     are 4B and 6B pieces interleaved by the grammar.")

# ---------------------------------------------------------------------------
# 9. self-similarity
# ---------------------------------------------------------------------------
rule("8. SELF-SIMILARITY")
sub("8a. identical records?")
bybytes = collections.defaultdict(list)
for r in records:
    bybytes[d[r["off"]:r["off"] + r["size"]]].append(r["i"])
dup = {k: v for k, v in bybytes.items() if len(v) > 1}
emit("  byte-identical records: %s" % (["rec%s at %s" % (v, k.hex()[:24]) for k, v in dup.items()] or "NONE"))
sub("8b. identical records modulo per-instance constants?")
def shape(r):                      # opcode skeleton + edge selector pattern
    return (tuple(x["name"] for x in r["ins"]), tuple(e["ty"] for e in r["edges"]))
def skeleton(r):                   # + every register operand, all constants/targets zeroed
    sk = bytearray(d[r["off"]:r["off"] + r["size"]])
    sk[0:2] = b"\0\0"                                   # own tag
    sk[4:6] = b"\0\0"                                   # dflt_next
    for x in r["ins"]:
        o = x["off"] - r["off"]
        if x["len"] == 6:
            sk[o + 2:o + 6] = b"\0" * 4                 # imm32
    for e in r["edges"]:
        o = e["off"] - r["off"]
        sk[o + 1:o + 13] = b"\0" * 12                   # target, tweak, signature
    return bytes(sk)
g1, g2 = collections.defaultdict(list), collections.defaultdict(list)
for r in records:
    g1[shape(r)].append(r["i"])
    g2[skeleton(r)].append(r["i"])
grp = {k: v for k, v in g2.items() if len(v) > 1}
emit("  opcode-skeleton classes: %d ; identical-modulo-constants groups (>1 member): %d" % (len(g1), len(grp)))
for k, v in sorted(g1.items(), key=lambda x: -len(x[1])):
    emit("     x%-2d  %s  edges%s" % (len(v), " ".join(k[0]), "".join("%02x" % t for t in k[1])))
emit("  => the 24 leaf nodes (L=12) split into two families: 'XOR.imm r,imm ; ADD.reg ; ROL.imm' with")
emit("     k=3 and the same program with k=2, i.e. identical *code shape*, differing only in their")
emit("     4-byte immediate, their target set and their 6-byte per-edge signatures.")
sub("8c. identical edges / repeated tweaks / repeated signatures")
for lbl, key in (("full 13B edge", lambda e: d[e["off"]:e["off"] + 13]),
                 ("target+tweak", lambda e: (e["tgt"], e["tweak"])),
                 ("signature", lambda e: e["sig"])):
    c = collections.Counter(key(e) for r in records for e in r["edges"])
    rep = [x for x in c.items() if x[1] > 1]
    emit("  %-14s: %d distinct / %d, repeats: %s" % (lbl, len(c), ne, (rep[:5] or "none")))
sub("8d. graph self-similarity (in/out degree, reachability from start_tag)")
indeg = collections.Counter(e["tgt"] for r in records for e in r["edges"])
bytag = {r["tag"]: r for r in records}
emit("  tag     rec  L    k  indeg  indeg(deny-sink)  role")
for r in sorted(records, key=lambda x: -indeg[x["tag"]]):
    role = "START" if r["tag"] == start_tag else ("GOAL(GETENV/EMIT)" if any(x["name"] == "GETENV" for x in r["ins"]) else ("SINK(HALT,k=0)" if r["k"] == 0 else ""))
    emit("  0x%04x  %3d %4d %3d %5d   %6d      %s" % (r["tag"], r["i"], r["L"], r["k"], indeg[r["tag"]], indeg[r["dflt"]], role))
unreach = [r["tag"] for r in records if indeg[r["tag"]] == 0 and r["tag"] != start_tag]
emit("  nodes with no incoming edge (unreachable): %s" % ([("0x%04x(rec%d)" % (t, bytag[t]["i"])) for t in unreach] or "none"))
emit("  self loops: %s" % [(("rec%d" % r["i"])) for r in records if any(e["tgt"] == r["tag"] for e in r["edges"])] or "none")
emit("  default-next is 0x%04x in %d of %d records -> one shared deny sink node" %
     (records[0]["dflt"], sum(1 for r in records if r["dflt"] == records[0]["dflt"]), len(records)))

# ---------------------------------------------------------------------------
# 10. per-node disassembly (the actual route semantics)
# ---------------------------------------------------------------------------
rule("9. PER-RECORD DISASSEMBLY (typed tree, deepest level)")
for r in records:
    emit("")
    emit("rec%-2d @0x%04x  tag=0x%04x  pred=%s  dflt_next=0x%04x  L=%d  k=%d  size=%d" %
         (r["i"], r["off"], r["tag"],
          "unconditional (pred_reg=0xff)" if r["pred_reg"] == 0xFF else "take edge with type == bit %d of r%d" % (r["pred_bit"], r["pred_reg"]),
          r["dflt"], r["L"], r["k"], r["size"]))
    for x in r["ins"]:
        emit("    +0x%03x 0x%04x  %-28s %s" % (x["off"] - r["payoff"], x["off"], x["txt"], x["raw"].hex()))
    if r["L"] and not r["closure"]:
        emit("    !!! opcode stream ended at %d but L=%d" % (r["code_len"], r["L"]))
    for j, e in enumerate(r["edges"]):
        emit("    edge %2d @0x%04x  type=0x%02x target=0x%04x%s tweak=0x%08x sig=%06x" %
             (j, e["off"], e["ty"], e["tgt"], (" (missing tag!)" if e["tgt"] not in tagset else ""), e["tweak"], e["sig"]))

sub("9b. rec0 payload = the input packer, decoded")
r0 = records[0]
grp = collections.defaultdict(list)
for x in r0["ins"]:
    if x["op"] == 0x01:
        emit("    MOV.imm r%d, 0   (init accumulator, @0x%04x)" % (x["raw"][1], x["off"]))
    elif x["op"] == 0x0C:
        grp[("ldin", x["raw"][2])] = x
n_in = sum(1 for x in r0["ins"] if x["op"] == 0x0C)
emit("  rec0 loads %d distinct input bytes (LDIN idx range 0x%02x..0x%02x) into r6, rotates by" %
     (n_in, min(x["raw"][2] for x in r0["ins"] if x["op"] == 0x0C), max(x["raw"][2] for x in r0["ins"] if x["op"] == 0x0C)))
emit("  0/8/16/24 and ORs them into r0..r5 => the 24 RUN bytes become 6 little-endian u32 registers.")
emit("  That is exactly the 9-byte 'group' the question asked about:")
emit("     0c 06 <idx> | 07 06 <shift> | 06 <reg> 06   = LDIN r6,[idx] ; ROL r6,shift ; OR r<reg>,r6")
emit("  and the 6-byte 'separator' 01 <g> 00 00 00 00 = MOV.imm r<g>,0 (zero the accumulator).")

# ---------------------------------------------------------------------------
# 11. unexplained / caveats
# ---------------------------------------------------------------------------
rule("10. WHAT THIS PARSER COULD NOT EXPLAIN")
notes = []
if un:
    notes.append("%d bytes are not covered by any field (offsets listed above)." % len(un))
if p != len(d):
    notes.append("%d trailing bytes after the last record are unclaimed." % (len(d) - p))
nc = [r["i"] for r in records if not r["closure"]]
if nc:
    notes.append("payloads of records %s do not close under the opcode table." % nc)
notes.append("The seed at 0x76ee0 is NOT the SipHash key (key lives at 0x76ef0/0x76ef8, 0x1b38); "
             "no field in the image equals the key, so signatures are not recomputable offline.")
notes.append("rec0's %d imm32 fields are all 0x00000000 (register zeroing). The other %d imm32 operands "
             "carry per-instance constants whose meaning (which predicate they feed) is only recoverable "
             "by simulating the opcode stream, not from the image alone." %
             (sum(1 for r in records for x in r["ins"] if x["len"] == 6 and x["raw"][2:6] == b"\0\0\0\0"),
              sum(1 for r in records for x in r["ins"] if x["len"] == 6 and x["raw"][2:6] != b"\0\0\0\0")))
notes.append("The image does not store record indices or the group numbering the question mentions: "
             "those are positional (array index) and derived (MOV.imm dst), respectively.")
notes.append("No numbering/counter field exists anywhere in the header or records; nothing in the image "
             "correlates with the 24-byte RUN input besides the LDIN byte indices 0x00..0x17.")
for i, s in enumerate(notes, 1):
    emit("  (%d) %s" % (i, s))

rule("SUMMARY")
emit("  image = 'CSGN' v%d header(18B) + %d records, all %d bytes accounted for." %
     (version, len(records), len(d)))
emit("  nodes are keyed by a u16 tag (from the start_tag field, not by index); %d distinct tags." % len(tagset))
emit("  record = 8B head + L-byte opcode stream + 1B edge count + k*13B edges; size = 9+L+13k.")
emit("  %d edges total; each edge = type(1) target(2) tweak(4) countersignature(6)." % ne)
emit("  opcode sizes 1/3/6: %d instructions, %d of them carry a 4-byte immediate." %
     (sum(opc.values()), sum(1 for r in records for x in r["ins"] if x["len"] == 6)))
emit("  structure: 0x000..0x%03x deterministic; per-instance fields start at 0x%03x, real entropy at 0x%03x."
     % (struct_end - 1, struct_end, first_real))
emit("  goal/sink: start=0x%04x(rec%d), the only GETENV node is 0x04a3(rec%d), the shared deny sink is 0x%04x(rec%d, HALT, k=0)." %
     (start_tag, bytag[start_tag]["i"],
      [r["i"] for r in records if any(x["name"] == "GETENV" for x in r["ins"])][0] if any(any(x["name"] == "GETENV" for x in r["ins"]) for r in records) else -1,
      records[0]["dflt"], bytag.get(records[0]["dflt"], {"i": -1})["i"]))

text = "\n".join(L) + "\n"
sys.stdout.write(text)
with open(OUT_TXT, "w", encoding="utf-8", newline="\n") as f:
    f.write(text)
sys.stderr.write("wrote %s (%d lines, %d bytes)\n" % (OUT_TXT, len(L), len(text.encode("utf-8"))))
