"""Gerrymandering solver for the Cat County district puzzle.

Model: rows x cols grid of precincts, each holding votes for two camps.
Partition into K districts of exactly n//K cells, every district contiguous
on the 4-neighbour grid, maximise the seats our candidate wins by majority.

Search = ruin & recreate: single-cell swaps between adjacent districts plus
whole two-district boundary redraws. Both move families preserve district
size and any candidate that breaks contiguity is discarded, so the search
only ever visits legal maps. Acceptance signal:
    margin = seats*10000 - (surplus votes in won districts)
seats stay primary, but ties prefer not wasting our own votes.
"""
import random
from collections import deque


def build(rows, cols):
    adj = {}
    for r in range(rows):
        for c in range(cols):
            nb = []
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    nb.append(nr * cols + nc)
            adj[r * cols + c] = nb
    return adj


def connected(cells, adj):
    cs = set(cells)
    if not cs:
        return False
    start = next(iter(cs))
    seen = {start}
    dq = deque([start])
    while dq:
        u = dq.popleft()
        for v in adj[u]:
            if v in cs and v not in seen:
                seen.add(v)
                dq.append(v)
    return len(seen) == len(cs)


def tally(assign, votes, K):
    lav = [0] * K
    oth = [0] * K
    for i, d in enumerate(assign):
        lav[d] += votes[i][0]
        oth[d] += votes[i][1]
    won = [d for d in range(K) if lav[d] > oth[d]]
    return lav, oth, won


def evaluate(assign, votes, adj, K, ideal):
    """-> (seats, penalty); penalty == 0 means the map is legal."""
    memb = [[] for _ in range(K)]
    for i, d in enumerate(assign):
        memb[d].append(i)
    pen = 0
    for d in range(K):
        if not memb[d] or (ideal and len(memb[d]) != ideal) or not connected(memb[d], adj):
            pen += 10 ** 6
    return len(tally(assign, votes, K)[2]), pen


def margin(assign, votes, K):
    lav, oth, won = tally(assign, votes, K)
    return len(won) * 10000 - sum(lav[d] - oth[d] for d in won)


def grow(n, K, adj, ideal):
    seeds = [round(i * n / K) for i in range(K)]
    assign = [-1] * n
    qs, counts = {}, [0] * K
    for d in range(K):
        qs[d] = deque([seeds[d]])
        assign[seeds[d]] = d
        counts[d] = 1
    moved = True
    while any(counts[d] < ideal for d in range(K)) and moved:
        moved = False
        for d in range(K):
            while qs[d] and counts[d] < ideal:
                u = qs[d].popleft()
                for v in adj[u]:
                    if assign[v] == -1 and counts[d] < ideal:
                        assign[v] = d
                        counts[d] += 1
                        qs[d].append(v)
                        moved = True
    for i in [x for x in range(n) if assign[x] == -1]:
        for v in adj[i]:
            if assign[v] >= 0:
                assign[i] = assign[v]
                break
    return assign


def start_map(rows, cols, K, adj):
    n = rows * cols
    ideal = n // K
    s = [min(i // ideal, K - 1) for i in range(n)]
    if all(connected([i for i in range(n) if s[i] == d], adj) for d in range(K)):
        return s
    return grow(n, K, adj, ideal)


def rand_pair_split(cells, adj, ideal, rng):
    """Cut a cell set into two connected parts: one of `ideal` cells, the rest."""
    cs = set(cells)
    for _ in range(300):
        seed = rng.choice(sorted(cs))
        grp = {seed}
        front = [v for v in adj[seed] if v in cs]
        while len(grp) < ideal and front:
            v = front.pop(rng.randrange(len(front)))
            if v in grp:
                continue
            grp.add(v)
            front.extend(w for w in adj[v] if w in cs and w not in grp and w not in front)
        if len(grp) != ideal:
            continue
        rest = cs - grp
        if rest and connected(grp, adj) and connected(rest, adj):
            return grp, rest
    return None


def solve(rows, cols, votes, K, tries=1500, seed=1, ideal=None, restarts=8):
    n = rows * cols
    adj = build(rows, cols)
    if ideal is None:
        ideal = n // K if n % K == 0 else None
    rng = random.Random(seed)
    overall = None
    for _rs in range(restarts):
        assign = start_map(rows, cols, K, adj)
        seats, pen = evaluate(assign, votes, adj, K, ideal)
        if pen:
            continue
        cur = margin(assign, votes, K)
        best = (seats, list(assign))
        for _step in range(tries):
            snap = list(assign)
            members = [[] for _ in range(K)]
            for i, d in enumerate(assign):
                members[d].append(i)
            if rng.random() < 0.35:
                i = rng.randrange(n)
                opts = [v for v in adj[i] if assign[v] != assign[i]]
                if not opts:
                    continue
                j = rng.choice(opts)
                assign[i], assign[j] = assign[j], assign[i]
            else:
                d1 = rng.randrange(K)
                nb = {assign[u] for x in members[d1] for u in adj[x] if assign[u] != d1}
                if not nb:
                    continue
                d2 = rng.choice(sorted(nb))
                sp = rand_pair_split(members[d1] + members[d2], adj, ideal, rng)
                if not sp:
                    continue
                a, b = sp
                if rng.random() < 0.5:
                    a, b = b, a
                for i in a:
                    assign[i] = d1
                for i in b:
                    assign[i] = d2
            g, p = evaluate(assign, votes, adj, K, ideal)
            if p:
                assign = snap
                continue
            val = margin(assign, votes, K)
            if val >= cur or rng.random() < 0.12:
                cur = val
                if g > best[0]:
                    best = (g, list(assign))
            else:
                assign = snap
            if best[0] == K:
                break
        if overall is None or best[0] > overall[0]:
            overall = best
    return overall


def show(assign, rows, cols, marks=None):
    return [' '.join(((marks[r * cols + c] if marks else '.') + str(assign[r * cols + c])).rjust(3)
                     for c in range(cols)) for r in range(rows)]
