---
title: "Labyrinth"
category: "Misc"
tags: []
solve_date: "2026-10-31"
language: "en"
---

# Labyrinth

## Challenge

A custom binary protocol speaks an undocumented language behind the socket. After learning the handshake, solving the challenge/response, and navigating the maze to the sealed gate, the server returns the real flag. The obvious exit door returns a decoy.

## Solution

### Step 1: Reverse the framing and handshake

Every frame is:

```
LBY\x7f | opcode (1 byte) | body length (2 bytes, big-endian) | body
```

- `0x01` HELLO -> server nonce.
- `0x10` PROBE with the nonce -> 28-byte challenge.

### Step 2: Solve the challenge

For challenge bytes `c`:

```
k  = challenge[4:8]
w6 = challenge[24:28]
answer = k XOR reverse(w6)
```

Send the 4-byte answer with opcode `0x30`. The server opens the maze.

### Step 3: Navigate to the sealed gate

Each room reply carries `x, y, exit_mask, flag, token`; the mask bits are `N=1, E=2, S=4, W=8`. The `flag` field in ordinary rooms is a decoy. Reach the sealed gate, then send `0x30` with the shortest route from the entrance. Each step is one byte:

```
N=0, E=1, S=2, W=3
```

The route length equals the number of steps. The `0x40` opcode only returns the fake flag `hiCTF{not_the_exit}`; the real flag comes from the sealed-gate route response.

## Result

```
hiCTF{l34rn3d_th3_t0ngu3_w4lk3d_th3_l4byr1nth_2b3f484331}
```

## Reproduction notes

The framing line uses textual escape notation for the byte 0x7f. The retained notes do not include a complete client or the concrete route from the recorded run.
