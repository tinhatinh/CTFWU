"""Column-existence battery: COUNT(<col>)>=0 is true iff the column exists.

Usage: python battery3.py <table> [col col ...]
"""
import sys
import time
from oracle import ask

GAP = 2.0

DEFAULT_COLS = ["id", "name", "designation", "planet", "telemetry", "signature", "sig",
                "distance", "mass", "radius", "gravity", "atmosphere", "spectral",
                "discovered", "year", "notes", "note", "class", "type", "hidden",
                "flag", "secret", "value", "data", "content", "payload", "token",
                "description", "desc", "status", "clearance", "restricted", "code"]

if __name__ == "__main__":
    table = sys.argv[1]
    cols = sys.argv[2:] or DEFAULT_COLS
    for c in cols:
        expr = "(SELECT COUNT(%s) FROM %s)>=0" % (c, table)
        r = None
        for _ in range(2):
            r = ask(expr)
            if r:
                break
            time.sleep(0.4)
        print("%-14s.%-14s %s" % (table, c, r), flush=True)
        time.sleep(GAP)
