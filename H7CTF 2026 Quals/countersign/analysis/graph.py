"""Do thi walk cua countersign + tim record muc tieu.

Layout da kien chung (agent image + toi doi chieu serializer):
  rec = tag u16 | pred_reg u8 (0xff=vo dk) | pred_bit u8 | dflt_next u16
      | pay_len u16 | payload| edge_cnt u8 | edge*13
  edge = type u8 (0x00/0x01/0xff) | target u16 | tweak u32 | sig_lo u32 | sig_hi u16
Muc tieu: record co payload chua op13(LOADFLAG)+op14(SETPRINT) roi ket thuc.
"""
import struct
import sys

sys.path.insert(0, sys.dir if False else ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import records


def edge(s):
    return dict(type=s[0], target=struct.unpack_from("<H", s, 1)[0],
                tweak=struct.unpack_from("<I", s, 3)[0],
                sig=struct.unpack_from("<I", s, 7)[0],
                hi=struct.unpack_from("<H", s, 11)[0])


def ops(code, ln):
    out = []
    for j in range(ln):
        if code[j] > 15:
            out.append(("HALT", code[j]))
        else:
            out.append((j, code[j]))
    return out


def main():
    img = open(sys.argv[1] if len(sys.argv) > 1 else "imgE.bin", "rb").read()
    hdr, end = records.parse(img)
    recs = hdr["recs"]
    bytag = {r["f0"]: r for r in recs}
    print("records=%d  start(entry field)=%d  parse end=%d/%d" %
          (len(recs), hdr["entry"], end, len(img)))
    goal = deny = None
    for r in recs:
        c, ln = r["code"], r["ln"]
        has = {c[j] for j in range(ln)} if ln else set()
        r["has13"] = 13 in has
        r["has14"] = 14 in has
        r["halt"] = any(c[j] > 15 for j in range(ln))
        if r["has13"] and r["has14"]:
            goal = r
        if ln and all(c[j] > 15 for j in range(min(1, ln))) and r["ns"] == 0:
            deny = deny or r
    print("goal (LOADFLAG+SETPRINT): tag=%s  deny-ish: %s" %
          (goal["f0"] if goal else None, deny["f0"] if deny else None))
    print("\n%-7s %-6s %-4s %-4s %-7s %-4s %-4s  edges(type->target)" %
          ("tag", "predR", "bit", "dflt", "plen", "nedge", "ops"))
    for r in recs:
        es = [edge(s) for s in r["stamps"]]
        print("%-7d %-6d %-4d %-7d %-4d %-4d %-4s %s" %
              (r["f0"], r["f1"], r["f2"], r["f3"], r["ln"], r["ns"],
               ("G" if r.get("has13") and r.get("has14") else
                "H" if r.get("halt") else "."),
               " ".join("%d->%d" % (e["type"], e["target"]) for e in es)))
    # bac vao cua goal
    if goal:
        din = [(r["f0"], e["type"]) for r in recs for e in [edge(s) for s in r["stamps"]]
               if e["target"] == goal["f0"]]
        print("\ncanh dan vao goal %d: %s" % (goal["f0"], din))
        print("payload goal:", goal["code"][:goal["ln"]].hex())
        print("payload start:", recs[0]["code"][:recs[0]["ln"]].hex())


if __name__ == "__main__":
    main()
