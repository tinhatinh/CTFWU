---
title: "Titan Relay"
category: "Pwn"
tags: []
solve_date: "2026-10-31"
language: "en"
---

# Titan Relay

## Challenge

A Rust PE32+ relay console runs under Wine and feeds operator input into a small custom VM. The VM's store instruction allows negative memory indices, which overwrite the VM's integrity fields. Rebuilding the cookie and the order structure lets the VM construct a file path to the flag at `Z:\flag.txt` (the Wine mapping of `/flag.txt`).

## Solution

### Step 1: Reverse the input and VM

- Input format: capsule length (1..512) followed by hex bytes. Before execution, each byte is XORed with `(0x71 + 0x3d*i) & 0xff`.
- The VM has 8 registers at `ctx+0x18`, 16 memory cells at `ctx+0x58`, and a special table at `ctx+0xd8` holding `cookie_lo`, `cookie_hi`, `cookie^func`, and zero.
- The integrity fields are at `ctx+0x8` (must equal the cookie) and `ctx+0x10` (must equal `&0x1400018c0`).

### Step 2: Abuse the negative store index

Opcode `0x32` stores a dword from register A to `mem[imm16] + D*4`. The bounds check is signed, so `imm16 = -10` or `-9` reaches backwards and overwrites the two integrity fields.

### Step 3: Build the order and read the flag

1. Read the cookie from special table entries 0..2.
2. Reconstruct the cookie and function pointer.
3. Build an order structure at `mem[0..]` whose path is XORed with the cookie.
4. Set register 6 to `&mem[0]` and halt with `0x51`.

The VM then writes/opens the path under Wine's `Z:` drive, which maps to the host root; `/flag.txt` becomes `Z:\flag.txt`.





## Result

```
hiCTF{ru5t_vm_g4te_and_h4ndler_ch41n_5e8259594d}
```

## Reproduction notes

The retained summary does not include the complete capsule assembler and order-field layout. Full reproduction requires the original binary or solver to supply those details.
