---
title: "Rocinate"
category: "Crypto"
tags: []
solve_date: "2026-10-31"
language: "en"
---

# Rocinate

## Challenge

The challenge publishes 102 consecutive outputs of Python's `random.randint(1, N)` (`a`, `b`, and `C_0..C_99`). That is enough to reconstruct the MT19937 state, recover the hidden values, and solve the discrete-log relation for the secret.

## Solution

### Step 1: Model the leaked numbers correctly

`random.randint(1, N)` returns `1 + _randbelow(N)`, so the raw MT output is `value - 1`. Each draw consumes exactly 64 MT words: 63 full 32-bit words plus one 31-bit word.

### Step 2: Rewind MT19937

1. Find a window of 10 draws with no rejection by using the lag-624 recurrence.
2. Recover the missing least-significant bits using the next block.
3. Extend the state backwards word by word using two consecutive equations; the missing bit 31 determines the branch.
4. Once the state is recovered, `r` is the first draw.

### Step 3: Recover the secret and the flag

Compute `R_i` from the LCG used by the challenge, then use Bezout's identity on a coprime pair `(C_i, C_j)` to recover `s` from `s^{C_i}`. The check `T_i == R_i^e` holds for all 100/100 leaked entries, confirming the state.

## Result

```
hiCTF{lmaoooo_w0t???y0u_d1d_17_??435p37++}
```

## Reproduction notes

The retained summary does not contain the full N, LCG parameters, public outputs, or bit-system solver. Reproducing the complete state recovery requires those challenge inputs and implementation.
