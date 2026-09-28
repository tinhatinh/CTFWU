"""Quet RUN theo id record.

Model tu vm_notes.md:
  - RUN doc 24 byte, duoc cat thanh id=u16 LE (p[0:2]) va 22 byte con lai.
  - Core duyet moi record co id khop, chay VM cua no; record thang loi khi
    code_len == 0 (khong verify gi ca), va khi do [rec+0x208] = done quyet dinh:
    done != 0 -> in "FACTORY DIAG UNLOCKED" / "FLAG: ...".
  - done = rand(26) tai boot, nen trong ~40 record the nao cung co cai khac 0.
  - done nam trong code blob o byte 488 (code[0x1f8]) neu code_len > 488.

Moi thu RUN = 1 lenh, ~0.42s.  Quat toan bo id co trong image.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import session
import records


def main():
    c = session.Core()
    c.get_nonce()
    img = c.get_image(save="imgC.bin")
    hdr, _ = records.parse(img)
    recs = hdr["recs"]
    ids = sorted({r["f0"] for r in recs})
    print("[*] %d record, %d id khac biet, entry=%d" % (len(recs), len(ids), hdr["entry"]))
    for r in recs[:8]:
        d = r["code"][488] if r["ln"] > 488 else None
        print("    id=%5d f1=%3d f2=%3d f3=%5d ln=%4d ns=%2d done@488=%s"
              % (r["f0"], r["f1"], r["f2"], r["f3"], r["ln"], r["ns"], d))
    zero22 = bytes(22)
    hits = []
    for i, rid in enumerate(ids):
        inp = struct.pack("<H", rid) + zero22
        try:
            r = c.run(inp)
        except Exception as e:
            print("[!] mat ket noi o id %d (%s), moi lai" % (rid, e))
            c.close()
            return main()
        tag = "" if r == "denied" else "  <<<< %r" % r
        if r != "denied":
            hits.append((rid, r))
        if i % 10 == 0 or tag:
            print("  id %5d -> %s%s" % (rid, r, tag))
    print("[+] khong denied:", hits)
    c.close()


if __name__ == "__main__":
    main()
