---
title: "Soul Fragment Race"
category: "Web"
tags: ["flask", "session-cookie", "business-logic", "state-accumulation", "options-oracle"]
solve_date: "2026-10-09"
language: "en"
---

# Soul Fragment Race

**Flag:** `OWASP{byteme_soul_fragment_race}`
**Service:** `https://byteme-soul-fragment-race.onrender.com` (Flask behind gunicorn, fronted by Cloudflare).

## Challenge

Soul Fragment Race (Web, Hard, 300 points, 2 solves). The session cookie decodes to `{"uid": N}`. The goal is to get `claim` to accept and return the flag.

## Analysis

Additional routes were located with an OPTIONS oracle:

```text
POST /vault/recover
POST /vault/verify
POST /vault/claim
GET /api/events
```

A `claim` with a single proof returns:

```text
403 {"error":"the final fragment resists a single proof","hint":"the keeper expects contradictory proof"}
```

The successful flow uses two sequential recoveries more than three seconds apart. The observed ledger retains a `verified` proof from an expired attempt, and `claim` accepts once the account has two contradictory proofs. This supports a state-management flaw in the tested flow; it does not rule out other race conditions.

## Solution

On a fresh account (ledger state is per-account), run `recover` → wait past the 3-second window → `recover` a second time so the account accumulates two contradictory proofs, then `claim`. Recorded result from `soul/mech2.py` / `soul/race.py`:

```text
claim#2 (0.2301, 200, '{"flag":"OWASP{byteme_soul_fragment_race}","status":"awakened"}')
```

`claim` returns `200` with the flag; state moves `fragments 6 → 7`, `awakened: true`, and there is an `events` entry named `vault_awakened`.

## Result

```text
OWASP{byteme_soul_fragment_race}
```

The flag was read from the live service via `POST /vault/claim`. No submission response recorded.

## Reproduce

The instance must still be available and a fresh account is required. Keep the same session for `recover` → wait more than three seconds → `recover` → `claim`. Complete request bodies and a solver were not preserved, so the record is insufficient for a fully automated reproduction.
