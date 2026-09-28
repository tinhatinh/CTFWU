"""Focused battery: does the flag live in planets, and what is the 2nd table called?"""
import sys
import time
from oracle import ask

GAP = 2.0
out = open("battery2.log", "a", buffering=1)


def p(s):
    out.write(s + "\n")
    print(s, flush=True)


def ask2(expr, tries=2):
    for _ in range(tries):
        if ask(expr):
            return True
        time.sleep(GAP)
    return False


p("=== %s ===" % time.strftime("%H:%M:%S"))
T = [
    ("row_to_json ok", "(SELECT row_to_json(p)::text FROM planets p LIMIT 1) LIKE '{%"),
    ("planets has 'sun'", "(SELECT COUNT(*) FROM planets WHERE row_to_json(planets)::text LIKE '%sun%')>0"),
]
for n in ["probe", "stars", "vault", "world", "venus", "pluto", "relic", "ruins",
          "terra", "secret", "users", "tokens", "oracle", "archive", "signals", "flags2"]:
    T.append(("table " + n, "(SELECT COUNT(*) FROM %s)>=0" % n))

for name, e in T:
    t = time.time()
    r = ask2(e)
    p("%-18s %-6s (%.0fs)" % (name, r, time.time() - t))
    time.sleep(GAP)
p("done")
