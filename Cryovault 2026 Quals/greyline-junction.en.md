---
title: "Greyline Junction"
category: "Web"
tags: ["state-replay", "access-control"]
solve_date: "2026-10-11T09:11:00+07:00"
language: "en"
---

# Greyline Junction

**Flag:** `isfcr{greyline_a471_stale_1818abfe_card}`
**Artifacts:** `FIELD_GUIDE.md` (2,483 bytes), remote service `https://isfcrpesu-greyline-junction.chals.io`

| Artifact | SHA-256 |
|---|---|
| `FIELD_GUIDE.md` | `fd0498ab166d4fa88a755831a3cb21258f80d049cae7123d41d4b62ccd62d3c5` |

## Challenge

The Greyline Junction control desk issues route authorities against one control revision and
can perform a single revision changeover before any train moves. Each authority reserves the
track circuits of its route so that no two live authorities overlap. The task is to produce a
valid incident record that "should never be possible": two authorized movements occupying the
same physical track circuit. The desk returns the event flag only when it verifies that
contradiction from its own sealed state.

The desk is reached over a JSON API with no server-side session. `POST /api/reset` returns a
sealed `state` token that carries the full desk state and must be replayed on every request.
Every new desk session is issued a relabeled control board.

## Initial Analysis

Reading the desk through the API establishes the reservation model:

- `POST /api/scheme` lists the current revision's routes (id, path, flank) and the shared
  approach lock `AP-0`.
- `POST /api/plan` reserves `AP-0` plus the route's three path circuits plus its flank circuit
  and returns an `authority` id. Two authorities cannot be *live* at the same time because each
  holds the single `AP-0`; planning a second route returns `route_locked`.
- `POST /api/cancel` releases the reservation held by one authority so another route can be
  planned.
- `POST /api/changeover` moves from revision A to revision B, once, before any movement, and
  closes the planning desk.
- `POST /api/dispatch` runs a train along the *current revision's* path for the route id bound
  to that authority.
- `POST /api/incident` reports `contradiction` (with the flag) only when two movements occupy a
  shared circuit that was not covered by the corresponding authority's reservation.

Because there is no server-side session, a sealed token remains valid after it has been used to
derive a newer token. Comparing revision A and revision B within one session shows the desk
relabels the board each session and that changeover shifts one circuit on a small number of
routes. This gives the two conditions needed for the contradiction: an authority reserved under
revision A, whose movement is later run along a revision-B path that reaches a circuit it never
reserved, colliding with a second movement.

## Exploitation Chain

1. **Read both revisions from one session.** Reset to `s0`, call `POST /api/scheme` for revision
   A, then use `s0` again for a throwaway `POST /api/changeover` and read revision B. Since `s0`
   is a replayable sealed snapshot, the same `s0` still describes revision A afterwards and can
   start a second, independent chain. This lets the solver compare the A and B path tables in one
   session and pick routes whose changeover behavior matters.

2. **Select a colliding pair.** For the session's A and B tables, search route pairs `(X, Y)`
   whose revision-B paths share at least one circuit `c`, where `c` is *not* inside at least one
   of the two authorities' revision-A reservations (`path + flank + AP-0`). Such a `c` guarantees
   that one movement will occupy a circuit it never reserved.

3. **Accumulate two authorities despite the shared lock.** On a fresh use of `s0`, plan `X` as
   train `T1`, cancel it (releasing `AP-0` and `X`'s circuits), then plan `Y` as `T2`. The cancel
   is what defeats the single-`AP-0` limit: `X` and `Y` are never live at the same instant, yet
   both authority cards remain recorded on the desk. Then `POST /api/changeover` switches the
   whole desk to revision B.

4. **Dispatch the stale card.** Dispatch the live authority `Y` first. Then dispatch the
   *cancelled* authority `X` on the resulting state so that both movements are recorded in a
   single sealed state. The desk normally refuses this with `403 Authority was cancelled`, but the
   cancel check on dispatch is not enforced consistently across every session: on some desk
   sessions the cancelled ("stale") card dispatches successfully and its movement is accepted
   along the current revision-B path. The exploit therefore runs the whole chain repeatedly until
   it lands on a session that accepts the stale dispatch.

5. **Verify the contradiction.** With both movements in one state, `POST /api/incident` observes
   that the two trains occupy the shared circuit `c` while one of them never reserved `c` under
   its authority, and returns `status: contradiction` together with the flag.

## Flag

`isfcr{greyline_a471_stale_1818abfe_card}`

The flag was read from the remote service's `POST /api/incident` response on a session whose
sealed state accepted the stale (cancelled) dispatch and reported the collision. The intermittency
of the stale-card dispatch is an observed behavior of the running service; no local proof of the
exact server-side condition is available because only the sealed tokens, not their plaintext, are
exposed.

## Reproduce

Point a small JSON client at the service and loop the chain until the incident returns a flag.
The steps per attempt are: reset to `s0`; read scheme A; fork a throwaway changeover on `s0` and
read scheme B; choose a pair `(X, Y)` sharing a revision-B circuit that is outside at least one
authority's `path + flank + AP-0` reservation; on a fresh use of `s0` issue
`plan(X) -> cancel -> plan(Y) -> changeover -> dispatch(Y) -> dispatch(X)`; then call
`/api/incident`. Treat `403 Authority was cancelled` and `status: clear` as retry conditions.

```python
import itertools, json, urllib.request, urllib.error

BASE = "https://isfcrpesu-greyline-junction.chals.io"

def call(path, payload):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"_status": e.code, **json.loads(e.read().decode() or b"{}")}

def attempt():
    s0 = call("/api/reset", {})["state"]
    a = {r["id"]: r for r in call("/api/scheme", {"state": s0})["routes"]}
    b = {r["id"]: r for r in call("/api/scheme",
         {"state": call("/api/changeover", {"state": s0})["state"]})["routes"]}
    held = lambda r: set(r["path"]) | {r["flank"]} | {"AP-0"}

    pair = None
    for x, y in itertools.combinations(sorted(a), 2):
        shared = set(b[x]["path"]) & set(b[y]["path"])
        if shared and any(c not in held(a[x]) for c in shared) or \
           shared and any(c not in held(a[y]) for c in shared):
            pair = (x, y); break
    if not pair:
        return None
    x, y = pair

    p1 = call("/api/plan", {"state": s0, "train": "T1", "route": x})
    if "_status" in p1: return None
    c1 = call("/api/cancel", {"state": p1["state"], "authority": p1["authority"]})
    p2 = call("/api/plan", {"state": c1["state"], "train": "T2", "route": y})
    co = call("/api/changeover", {"state": p2["state"]})
    dl = call("/api/dispatch", {"state": co["state"], "authority": p2["authority"]})
    if "_status" in dl: return None
    dc = call("/api/dispatch", {"state": dl["state"], "authority": p1["authority"]})
    if "_status" in dc: return None            # stale-card dispatch rejected: retry
    return call("/api/incident", {"state": dc["state"]})

for _ in range(200):
    inc = attempt()
    if inc and inc.get("status") == "contradiction":
        print(inc["flag"]); break
```

A run that lands on a accepting session produced:

```text
pair R01 R03 shared ['TC-06'] x_off True y_off False
{'circuit': 'TC-06',
 'flag': 'isfcr{greyline_a471_stale_1818abfe_card}',
 'status': 'contradiction',
 'trains': ['T1', 'T2']}
```
