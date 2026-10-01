"""Exact replica of flappy_board's fixed-point simulation + BFS route solver.

Ported from FUN_00106c0f (init), FUN_00106bc6/FUN_00106b88 (xorshift32) and
FUN_00106cfe (one tick). Units are 1/256 px, tick = 1/60 s.
Per tick, in this order:
  v = -1724 if flap else v ; v += 67 ; v = min(v, 2048) ; y += v ; tick++
  all pipes x -= 717
  die if y < 3073 or y > 119807
  per pipe 0..4: die if 30720 < x < 54272 and bird outside the gap;
                 else if x < 30720 and not credited: credit (only while alive)
  per pipe 0..4: if x < -17408: x = max(x)+69120, gap = rng()%231+125, credited = 0
"""
M32 = 0xFFFFFFFF
GRAV, FLAPV, VMAX = 0x43, -0x6BC, 0x800
YMIN, YMAX = 0xC01, 0x1D3FF
SPEED, SPACE, RECYCLE = 0x2CD, 0x10E00, -0x4400
XLO, XHI = 0x7800, 0xD400
HALF_BIRD, HALF_GAP = 0xBFF, 87


class World:
    def __init__(self, seed):
        s = seed & M32
        self.rng = s if s else 1
        self.pipes = []
        for i in range(5):
            self.pipes.append([(i * 0x10E + 0x410) * 0x100, self.draw(), 0])
        self.score = 0

    def draw(self):
        x = self.rng
        x ^= (x << 13) & M32
        x ^= x >> 17
        x ^= (x << 5) & M32
        x &= M32
        self.rng = x
        return x % 0xE7 + 0x7D

    def advance(self, alive=True):
        """Move pipes, credit scoring, recycle. Returns the new score."""
        for p in self.pipes:
            p[0] -= SPEED
        for p in self.pipes:
            if not p[2] and p[0] < XLO:
                p[2] = 1
                if alive:
                    self.score += 1
        for p in self.pipes:
            if p[0] < RECYCLE:
                mx = max(q[0] for q in self.pipes)
                p[0] = mx + SPACE
                p[1] = self.draw()
                p[2] = 0
        return self.score

    def collide_one(self, p, y):
        return y - HALF_BIRD <= (p[1] - HALF_GAP) * 0x100 or \
            (p[1] + HALF_GAP) * 0x100 <= y + HALF_BIRD

    def collide(self, y):
        for p in self.pipes:
            if XLO < p[0] < XHI and self.collide_one(p, y):
                return True
        return False


def out_of_bounds(y):
    return y < YMIN or y > YMAX


def _heuristic(w, y, v):
    """Prefer the middle of the nearest upcoming gap, with margin from floor/ceiling."""
    best = None
    for p in w.pipes:
        if p[0] > XLO - SPEED:
            if best is None or p[0] < best[0]:
                best = p
    want = best[1] * 0x100 if best else 0xF000
    d = abs(y - want)
    d += max(0, (YMIN + 0x1000) - y) + max(0, y - (YMAX - 0x1000))
    if v > 0x500 and y > YMAX - 0x6000:
        d += 0x4000
    return d


def solve(seed, target, beam=600, max_ticks=35998):
    """Beam search over the exact fixed-point dynamics; returns flap tick indices."""
    w = World(seed)
    states = {(0xF000, 0): None}
    hist = []
    done_at = None
    for tick in range(1, max_ticks + 1):
        for p in w.pipes:
            p[0] -= SPEED
        nxt = {}
        for (y, v) in states:
            for flap in (0, 1):
                v2 = (FLAPV if flap else v) + GRAV
                if v2 > VMAX:
                    v2 = VMAX
                y2 = y + v2
                if out_of_bounds(y2) or w.collide(y2):
                    continue
                if (y2, v2) not in nxt:
                    nxt[(y2, v2)] = (y, v, flap)
        for p in w.pipes:
            if not p[2] and p[0] < XLO:
                p[2] = 1
                w.score += 1
        for p in w.pipes:
            if p[0] < RECYCLE:
                mx = max(q[0] for q in w.pipes)
                p[0] = mx + SPACE
                p[1] = w.draw()
                p[2] = 0
        if not nxt:
            return None, "all routes died at tick %d (score %d/%d)" % (tick, w.score, target)
        if len(nxt) > beam:
            keep = sorted(nxt, key=lambda s: _heuristic(w, s[0], s[1]))[:beam]
            nxt = {k: nxt[k] for k in keep}
        hist.append(nxt)
        states = nxt
        if w.score >= target:
            done_at = tick
            break
    if done_at is None:
        return None, "target unreachable in %d ticks" % max_ticks

    st = min(states, key=lambda s: abs(s[0] - 0xF000))
    flaps = []
    for t in range(done_at, 0, -1):
        y, v, flap = hist[t - 1][st]
        if flap:
            flaps.append(t - 1)
        st = (y, v)
    return sorted(flaps), "%d ticks, %d flaps, score %d" % (done_at, len(flaps), w.score)


class Sim:
    """Single-run interpreter of a replay, mirroring the client exactly."""

    def __init__(self, seed):
        self.w = World(seed)
        self.y, self.v, self.tick, self.dead = 0xF000, 0, 0, 0

    @property
    def score(self):
        return self.w.score

    def step(self, flap):
        if self.dead or self.tick >= 36000:
            self.dead = 1
            return False
        if flap:
            self.v = FLAPV
        self.v += GRAV
        if self.v > VMAX:
            self.v = VMAX
        self.y += self.v
        self.tick += 1
        for p in self.w.pipes:
            p[0] -= SPEED
        if out_of_bounds(self.y):
            self.dead = 1
        for p in self.w.pipes:
            if XLO < p[0] < XHI and self.w.collide_one(p, self.y):
                self.dead = 1
            if not p[2] and p[0] < XLO:
                p[2] = 1
                if not self.dead:
                    self.w.score += 1
        for p in self.w.pipes:
            if p[0] < RECYCLE:
                mx = max(q[0] for q in self.w.pipes)
                p[0] = mx + SPACE
                p[1] = self.w.draw()
                p[2] = 0
        return not self.dead


def replay(seed, flaps, stop_score=None, max_ticks=35999):
    s = Sim(seed)
    fs = set(flaps)
    while s.tick < max_ticks and not s.dead:
        if stop_score is not None and s.score >= stop_score:
            break
        s.step(1 if s.tick in fs else 0)
    return s


if __name__ == "__main__":
    good = 0
    for seed in (1, 2, 7, 12345, 999999999, 424242424):
        f, msg = solve(seed, 10)
        if not f:
            print("seed=%-10d FAIL %s" % (seed, msg))
            continue
        s = replay(seed, f, stop_score=10)
        ok = (not s.dead) and s.score >= 10 and s.tick == int(msg.split()[0])
        good += ok
        print("seed=%-10d solve: %-34s replay: tick=%d score=%d dead=%d %s"
              % (seed, msg, s.tick, s.score, s.dead, "OK" if ok else "MISMATCH"))
    print("self-consistent %d/6" % good)
