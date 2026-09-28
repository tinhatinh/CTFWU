#!/usr/bin/env python
"""Explore capture.vcd: per-channel activity, timing and bit periods."""
import collections
import sys

VCD = sys.argv[1] if len(sys.argv) > 1 else "files/capture.vcd"

ids = {}            # symbol -> name
events = collections.defaultdict(list)   # symbol -> [(t, value)]
t = 0
cur = {}
for line in open(VCD):
    line = line.strip()
    if not line:
        continue
    if line.startswith("#"):
        t = int(line[1:])
    elif line.startswith("$var"):
        p = line.split()
        ids[p[3]] = p[4]
    elif line[0] in "01XZ":
        val, sym = line[0], line[1:]
        cur[sym] = val
        events[sym].append((t, val))
    elif line[0] == "b":                       # multi-bit vector
        val, sym = line[1:].split()
        cur[sym] = val
        events[sym].append((t, val))

print("channels:", ", ".join("%s=%s" % (s, n) for s, n in sorted(ids.items(), key=lambda kv: kv[1])))
print("end of simulation: %d ns (%.3f ms)" % (t, t / 1e6))
print()
for sym, label in sorted(ids.items(), key=lambda kv: kv[1]):
    ev = events.get(sym, [])
    if not ev:
        print("%-9s constant 0 (never toggles)" % label)
        continue
    gaps = [ev[i + 1][0] - ev[i][0] for i in range(len(ev) - 1)]
    print("%-9s transitions=%-5d  first=%8d ns   level-0 time frac=%.3f  gap hist(top5)=%s"
          % (label, len(ev), ev[0][0],
             sum(g for (tt, v), g in zip(ev, gaps + [0]) if v == "0") / max(1, t),
             collections.Counter(gaps).most_common(5)))
