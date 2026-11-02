---
title: "Ground Station"
category: "Hardware"
tags: []
solve_date: "2026-10-31"
language: "en"
---

# Ground Station

## Challenge

A satellite ground-support controller (GSC-7) must be authenticated with the maintenance toolkit, its altered fueling interlock must be corrected, the fix must survive the controller's watchdog/backup behavior, and a validation run must complete cleanly. The controller then prints a validation token containing the flag.

## Solution

### Step 1: Reverse the engineer authentication

The firmware is a stripped x86-64 ELF (`gsc-fw.bin`).

- `0x40048e` derives a 16-byte key from an LCG: `state = state*0x19660d + 0x3c6ef35f`, `key[i] = (state>>17) ^ (i*0x5b)`.
- `0x400589` is the access routine: 12 ARX rounds (rotations 7/11/17/19/13, nonce and constant `0x9e3779b9`), output `a^c || b^d`.
- Re-implementing the routine reproduces the firmware's anchor signature `image-sig=de8c1297`; `AUTH` then returns `OK access=engineer`.

### Step 2: Find the altered interlock

The live interlock reads:

```
INTERLOCK_OK expr=(TANK_TEMP <= 145) AND (TANK_PSI <= 100)
```

The temperature limit was raised from the safe 45 °C to 145 °C, far above the hard limit of 60 °C. The other interlocks (coolant pump, vent valve, fuel valve) match the narrative.

### Step 3: Correct it and make the fix stick

The controller's watchdog restores a backup on `runtest`, and the old backup still contains the faulty expression and trusted checksum. Instead of disabling the watchdog, re-baseline the backup:

```
PROG SET INTERLOCK_OK (TANK_TEMP <= 45) AND (TANK_PSI <= 100)
# live_checksum = 9ebaae207f06
BACKUP SAVE
# backup = live = trusted = 9ebaae207f06
# arm_will_restore = 0, watchdog remains enabled
```

Then run the validation:

```
DATA result=SUCCESS reason=fill_target_reached_scan_51
DATA flag=hiCTF{ground_station_fueling_test_nominal_9fe94378dd}
```



## Result

```
hiCTF{ground_station_fueling_test_nominal_9fe94378dd}
```

## Reproduction notes

Full authentication reproduction requires the firmware/toolkit, including the LCG initial state and complete ARX routine. The shortened formulas and addresses above are not a complete implementation.
