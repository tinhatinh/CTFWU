import sys, math, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TEAMK = bytes.fromhex("1337df4e77c16cc7")
BODY = {n: open("files/%s.sav" % n, "rb").read()[12:] for n in
        ("sample1", "sample2", "sample3", "team")}

team_pt = bytes(x ^ TEAMK[i % 8] for i, x in enumerate(BODY["team"]))
hist = collections.Counter(team_pt)
tot = len(team_pt)
FLOOR = 0.3 / 256.0                      # prior so unseen bytes are penalised, not -inf
LOGP = [math.log(max(hist[b] / tot, FLOOR)) for b in range(256)]


def solve(name, body=None, L=8):
    body = body if body is not None else BODY[name]
    key = bytearray(L)
    for j in range(L):
        col = body[j::L]
        best = max(range(256), key=lambda x: sum(LOGP[c ^ x] for c in col))
        key[j] = best
    return bytes(key)


for n in ("sample1", "sample2", "sample3", "team"):
    k = solve(n)
    pt = bytes(x ^ k[i % 8] for i, x in enumerate(BODY[n]))
    ok = sum(1 for c in pt if c in TEAMK and False)  # unused
    print("%s key=%s" % (n, k.hex()))
    print("   ", pt[:64])
open("analysis/keys.txt", "w").write(
    "\n".join("%s %s" % (n, solve(n).hex()) for n in BODY) + "\n")
