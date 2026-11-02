---
title: "Cold Chain"
category: "Hardware"
tags: []
solve_date: "2026-10-31"
language: "en"
---

# Cold Chain

## Challenge

A ColdLink CM-900 refrigeration controller has forced all six cases into continuous defrost. The technician toolkit contains the field master key, and a schedule plus a self-healing macro keep re-enabling the defrost. Disabling the macro, disabling the schedule, switching every case back to cooling, and holding the temperature below the compliance ceiling for 60 seconds releases a proof-of-repair token containing the flag.

## Solution

### Step 1: Authenticate to the controller

The toolkit contains the field master key. The login token is:

```
token = sha256(FIELD_MASTER_KEY | serial | nonce)[:16]
```

The CM-900 greeting returns `SERIAL CLX-900-SN-4417` and a fresh nonce per session, which is enough to answer `AUTH`.

### Step 2: Find why a naive fix does not stick

- Schedule `S9 WINTER_DEFROST_ALL` has `action=force_defrost enabled=1` and forces all six cases into defrost (12 °C).
- Macro `M2 AUTO_WINTERIZE` runs `ensure_schedule` every 90 seconds with target `S9`, so disabling the schedule is undone.

### Step 3: Apply the durable fix and hold compliance

Apply the changes in this order:

```
MACRO DISABLE M2
SCHED SET S9 enabled=0
MODE 1 cool
MODE 2 cool
MODE 3 cool
MODE 4 cool
MODE 5 cool
MODE 6 cool
```

Poll `STATUS` in the same session. The temperature falls below 5 °C and is held for 60 seconds (`held=61s`), at which point the controller releases the flag. A new session confirms the state is durable: `compliant=1`, `held=66s`, `M2 enabled=0`.

## Result

```
hiCTF{cold_chain_restored_defrost_cleared_3d93eb32ec}
```

## Reproduction notes

Reproduction requires the challenge toolkit containing the master key and a CM-900 instance. Follow the toolkit encoding for the authentication fields; the displayed formula is a protocol summary.
