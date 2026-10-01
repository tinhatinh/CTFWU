import random, subprocess, sys

M = 65521
C = 0x58862fdccdf01111
K = 0x1000f00e10d2f
TS = [0xf04814392f59c642, 0x74c1d75b9e5e4786, 0xcee61f7bd841abd9, 0x80368331afe94eab]
MASK = (1 << 64) - 1


def rot16(v, n):
    return ((v << n) | (v >> (16 - n))) & 0xFFFF


def O(t):
    x = (t ^ 0x5AA5) & 0xFFFF
    if x >= M:
        x -= M
    a = pow(x, 17, M)
    v = rot16(a, 7) ^ 0x1337
    if v >= M:
        v -= M
    return v


def gates(w, beacon, active=(0, 1, 2, 3, 4, 5)):
    """returns the tag of the first failing gate, 1 if all pass"""
    t = [(w[k] + M - beacon) % M for k in range(4)]
    u = [O(x) for x in t]
    c = [(u[0] + t[1]) % M, (u[1] + t[2]) % M, (u[2] + t[3]) % M, (u[3] + t[0]) % M]
    X = [(c[0] * c[0] + u[0] * c[1] + M - c[3]) & MASK,
         (c[1] * c[1] + u[1] * c[2] + M - c[0]) & MASK,
         (c[2] * c[2] + u[2] * c[3] + M - c[1]) & MASK,
         (c[3] * c[3] + u[3] * c[0] + M - c[2]) & MASK]
    ok = [(((X[i] * C + TS[i]) & MASK) <= K) for i in range(4)]
    ok.append((c[1] * c[1]) % M == ((c[0] * c[0] % M + 17) * c[0] + 43) % M)
    ok.append((c[3] * c[3]) % M == ((c[2] * c[2] % M + 17) * c[2] + 43) % M)
    for i in active:
        if not ok[i]:
            return 10 + i
    return 1


def gatevals(w, beacon):
    """the six boolean verdicts"""
    t = [(w[k] + M - beacon) % M for k in range(4)]
    u = [O(x) for x in t]
    c = [(u[0] + t[1]) % M, (u[1] + t[2]) % M, (u[2] + t[3]) % M, (u[3] + t[0]) % M]
    X = [(c[0] * c[0] + u[0] * c[1] + M - c[3]) & MASK,
         (c[1] * c[1] + u[1] * c[2] + M - c[0]) & MASK,
         (c[2] * c[2] + u[2] * c[3] + M - c[1]) & MASK,
         (c[3] * c[3] + u[3] * c[0] + M - c[2]) & MASK]
    o = [(((X[i] * C + TS[i]) & MASK) <= K) for i in range(4)]
    o.append((c[1] * c[1]) % M == ((c[0] * c[0] % M + 17) * c[0] + 43) % M)
    o.append((c[3] * c[3]) % M == ((c[2] * c[2] % M + 17) * c[2] + 43) % M)
    return o, c, u, t


def oracle(states):
    inp = "\n".join("%d %d %d %d %d" % s for s in states)
    p = subprocess.run(["harness.exe", "gran"], input=inp, capture_output=True, text=True)
    out = []
    for line in p.stdout.strip().splitlines():
        f = line.split()
        out.append((tuple(int(x) for x in f[:5]), int(f[5])))
    return out


if __name__ == "__main__":
    random.seed(int(sys.argv[1]) if len(sys.argv) > 1 else 7)
    states = [tuple([random.randrange(M) for _ in range(4)] + [random.randrange(M)])
              for _ in range(300)]
    bad = 0
    for (w, tag) in oracle(states):
        mine = gates(w, w[4])
        if mine != tag:
            bad += 1
            if bad < 12:
                print("MISMATCH", w, "model", mine, "oracle", tag, flush=True)
    print("compared", len(states), "mismatches", bad, flush=True)
