import json
import re
import sys
import time
import urllib.request

import sim

BASE = "http://34.116.80.78:8765"


def post(path, body=None, token=None):
    data = None if body is None else body.encode()
    req = urllib.request.Request(BASE + path, data=data, method="POST" if data is not None else "GET")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def jload(txt):
    txt = txt.strip()
    if txt.startswith("{"):
        try:
            return json.loads(txt)
        except Exception:
            pass
    out = {}
    for k, v in re.findall(r"([A-Za-z_]+)=([^&]*)", txt):
        out[k] = v
    return out


def flaps_body(flaps):
    out = "flaps="
    for i, t in enumerate(flaps):
        out += ("&" if i else "") + str(t)
    return out


def start():
    st, txt = post("/api/attempt", "")
    print("attempt:", st, txt[:400])
    return jload(txt)


def practice_with(token, target=5, seed=None):
    if seed is None:
        st, txt = post("/api/practice", "", token)
        print("practice:", st, txt[:300])
        d = jload(txt)
        token, seed = d.get("token", token), int(d.get("seed", 0))
    f, msg = sim.solve(seed, target)
    s = sim.replay(seed, f, stop_score=target)
    print("solved seed=%d -> %s (local replay tick=%d score=%d dead=%d)"
          % (seed, msg, s.tick, s.score, s.dead))
    body = "sequence=0&ticks=%d&final=1&score=%d&flaps=%s" % (len(f), s.score,
                                                              "&".join(str(x) for x in f))
    st, txt = post("/api/practice/check", body, token)
    print("check:", st, txt[:300])
    d = jload(txt)
    print("server verified_score=%s complete=%s cheated=%s   (local %d)"
          % (d.get("verified_score"), d.get("complete"), d.get("cheated"), s.score))
    return d.get("verified_score") == s.score


if __name__ == "__main__":
    mode = sys.argv[1] if sys.argv[1:] else "start"
    if mode == "start":
        start()
    elif mode == "session":
        d = start()
        practice_with(d.get("token"), int(sys.argv[2]) if len(sys.argv) > 2 else 5)
    elif mode == "practice":
        practice_with(None, int(sys.argv[2]) if len(sys.argv) > 2 else 5)
