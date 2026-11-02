---
title: "Cold Circuit"
category: "Reverse"
tags: []
solve_date: "2026-10-31"
language: "en"
---

# Cold Circuit

## Challenge

A stripped x86-64 checker decides whether a 32-hex-character flag body is correct. The checker contains anti-debugging, mathematically impossible decoy branches, and a reversible 20-round circuit over 16 bytes. Inverting the circuit recovers the expected input.

## Solution

### Step 1: Identify the input format

The binary reads from `argv[1]` or stdin and requires exactly `hiCTF{` + 32 hex characters + `}` (39 characters). The 32 hex characters are decoded into 16 bytes by the routine at `0x12d6`.

### Step 2: Avoid the anti-debug and the decoys

`ptrace(PTRACE_TRACEME)` is called at startup. If the process is traced, the checker XORs `table[0][0] ^= 1` (the table is copied to the stack from `0x2140`), corrupting the circuit. Run the checker without a debugger.

The branches at `0x1229` and `0x125c` print `unreachable` or return 98. They are impossible to reach mathematically (`x^2 + 1 ≡ 0 mod 4` has no solution), so they are decoys.

### Step 3: Invert the 20-round circuit

Each round is invertible and operates on the 16-byte state:

1. Add mod 256 with each 16-byte row of the 320-byte table at `0x2140`.
2. Substitute through the 256-byte S-box at `0x2020`.
3. Permute the 16 bytes according to the table at `0x2120`.

After 20 rounds, the state is compared with the 16-byte target at `0x2280`. Apply the inverse permutation, inverse S-box and row subtraction in reverse round order. The recovered body is `6e305f6a7461675f6e65656465642121`, which decodes to:

```
n0_jtag_needed!!
```

The binary prints `Access granted.` for the recovered input through both argv and stdin, confirming the inversion.

## Result

```
hiCTF{6e305f6a7461675f6e65656465642121}
```

## Reproduction notes

The addresses belong to the challenge binary. A standalone inversion script must extract the complete S-box, addition table, permutation, and target from that binary.
