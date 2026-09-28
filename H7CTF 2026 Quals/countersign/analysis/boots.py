"""Gia thuyet A: `done` la thuoc BOOT (khong nam tren wire), nen chi can quay
ket noi cho toi khi boot may mo co record duoc chien thang loi.

Moi ket noi = mot boot moi (nonce doi 16/16 lan, image doi).  Mot ket noi chi can
1 lenh RUN 24 byte = 0 de lay prob.  ~1 giay/lan.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import session

N = int(sys.argv[1]) if len(sys.argv) > 1 else 120


def main():
    t0 = time.time()
    seen = {}
    for i in range(N):
        try:
            c = session.Core()
            n = c.get_nonce()
            r = c.run(bytes(24))
        except Exception as e:
            print("[%3d] loi %s" % (i, type(e).__name__))
            time.sleep(1.0)
            continue
        finally:
            try:
                c.close()
            except Exception:
                pass
        seen[r] = seen.get(r, 0) + 1
        if r != "denied":
            print("[%3d] *** nonce=%s RUN -> %r" % (i, n, r), flush=True)
        if i % 10 == 0:
            print("[%3d] %.0fs  %s" % (i, time.time() - t0, seen), flush=True)
    print("[*] %d boot trong %.0fs -> %s" % (N, time.time() - t0, seen))


if __name__ == "__main__":
    main()
