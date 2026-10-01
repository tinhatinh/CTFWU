import time

import bot
import sim

T0 = time.time()
log = lambda *a: print("[%7.1fs]" % (time.time() - T0), *a, flush=True)

d = bot.jload(bot.post("/api/attempt", "")[1])
token = d["token"]
log("session: %s" % d)

for rnd in (1, 2, 3):
    seed, target = int(d["seed"]), int(d["target"])
    wait, rem = int(d["wait_seconds"]), int(d["remaining_seconds"])
    t_start = time.time() - T0
    flaps, msg = sim.solve(seed, target)
    s = sim.replay(seed, flaps, stop_score=target)
    log("round %d seed=%d target=%d wait=%ds left=%ds | %s replay(tick=%d score=%d)"
        % (rnd, seed, target, wait, rem, msg, s.tick, s.score))
    body = "round=%d&wait_ms=%d&ticks=%d&score=%d&flaps=%s" % (
        rnd, wait * 1000, s.tick, s.score, ",".join(str(x) for x in flaps))
    for attempt in range(2):
        gap = wait + 0.7 - ((time.time() - T0) - t_start)
        if attempt == 1:
            gap = wait + s.tick / 60.0 + 0.7 - ((time.time() - T0) - t_start)
        if gap > 0:
            log("   round %d attempt %d: sleeping %.1fs" % (rnd, attempt, gap))
            time.sleep(gap)
        st, txt = bot.post("/api/complete", body, token)
        log("complete r%d (try %d) -> %s %s" % (rnd, attempt, st, txt[:200]))
        if st == 200:
            break
    if st != 200:
        log("FAILED at round %d" % rnd)
        raise SystemExit(1)
    d = bot.jload(txt)
    if "flag" in d:
        print("FLAG:", d["flag"], flush=True)
        raise SystemExit(0)

st, txt = bot.post("/api/attempt", "", token)
log("final attempt: %s" % txt[:300])
print("FLAG:", bot.jload(txt).get("flag"), flush=True)
