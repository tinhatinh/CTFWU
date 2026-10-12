---
title: "Kelpie"
category: "Reverse"
tags: ["bytecode", "vm"]
solve_date: "2026-10-11T05:55:00+07:00"
language: "en"
---

# Kelpie

**Flag:** `isfcr{5b2d4c7961307f588d9dd95bada5647b}`
**Files:** `kelpie` (19,456 bytes; SHA-256 `7fbcd8688ace4d264c62a69c8aa74503ecc57559d6181afd53584a52116213b9`)

## Challenge

An activation stub pulled off a decommissioned "KELPIE" hardware token. It guards the firmware unlock routine behind an activation key; the key was printed on a sticker that peeled off years ago. The binary runs a small custom byte-machine over whatever key you type and reports `Unlocked` or `Denied`. The activation key is the flag, in the form `isfcr{<32 hex chars>}`.

There is also an undocumented factory self-test that runs the first stage over a fixed test vector.

## Initial Analysis

`kelpie` is a stripped, non-PIE `ET_EXEC` x86-64 ELF linked against `libc.so.6` and `libcrypto.so.3`. `.text` is only 0x621 bytes (a single hand-written function plus crt), so the whole program fits on one screen:

| Address | Role |
|---|---|
| `0x401170` | `main` |
| `0x4015e0` | byte-machine interpreter |
| `0x402020` | interpreter jump table (114 x 8-byte absolute pointers) |
| `0x4023c0` | stage-1 program, length `0x4d1` = 1233 bytes |
| `0x4028a0` | `VLT0` record: key(16) `@0x4028a4`, IV(12) `@0x4028b4`, tag(16) `@0x4028c0`, u32 ct_len `@0x4028d0`, ciphertext(924) `@0x4028d4` |
| `0x402c80` | four 16-byte permutation tables (two forward + their exact inverses) |
| `0x402cc0` / `0x402dc0` | AES inverse S-box / AES forward S-box |

`main` first calls `ptrace(PTRACE_TRACEME)`; when it returns `-1` (already traced) a saved value becomes `0x5a` and is later XORed into state byte 0, so a debugged run derives a different key. Feed the key on stdin to a clean process.

Input handling: `fgets` into a 256-byte stack buffer, `strcspn(buf,"\r\n")` to trim, `strncmp(buf,"isfcr{",6)`, then 16 hex pairs are parsed from `buf[6..37]` (digits, `a-f`, `A-F`) into a 16-byte state, and `buf[38]` must be `}`.

The interpreter is a 3-byte ISA `[op, A, B]` over a 16-byte data buffer, dispatched through the jump table, looping while `pc + 6 <= prog_len`. Recovered semantics:

| Op | Effect | Op | Effect |
|---|---|---|---|
| `0x00` | halt, return error accumulator | `0x30` / `0x31` | `rotl`/`rotr` state[A] by `B & 7` |
| `0x10`/`0x11`/`0x12` | `A ^= B` / `+= B` / `-= B` (register) | `0x40` / `0x41` | state[A] = AES S-box / inverse S-box |
| `0x13` | swap state[A], state[B] | `0x50` / `0x51` | whole-block gather-permute with table `@0x402ca0 + A*16` / `@0x402c80 + A*16` |
| `0x20`/`0x21`/`0x22`/`0x23` | imm: `^= B` / `+= B` / `-= B` / `*= B` | `0x60` | `state[A] ^= rotl(state[B],3)` |
| | | `0x71` | `err \|= (state[A] != B)` |

Everything else halts with `err = 1`.

Stage 1 (`0x4023c0`, 411 instructions) is 5 rounds of 82 operations: 16 S-boxes, one `0x50` perm (alternating tables), per-cell `(x + c) * m` (`m` cycles through `27,29,...,41`, all odd), a `0x60` shear ring `A ^= rotl(A+1,3)`, a `0x10` shear ring `A ^= A+7`, and one `0x30`. **It contains no `0x71` compare at all**, its return value is discarded by `main`, and every operation is bijective - stage 1 is purely a 128-bit block cipher `E`, and a symbolic influence trace confirms that from round 2 onward every output byte depends on all 16 input bytes (so the check cannot be split per byte).

`main` then builds the gate:

```
S  = E(parsed 16 bytes)                    # stage 1, in place
K  = HMAC-SHA256(key = 0x4028a4, msg = S)  # 32 bytes -> AES-256-GCM key
   AES-256-GCM decrypt 924 B @0x4028d4, IV @0x4028b4, tag @0x4028c0
   EVP_DecryptFinal_ex must return 1, then
   interpreter runs again with program = decrypted 924 B, data = S, err must be 0
   -> "Unlocked. Activation accepted."
```

`./kelpie selftest` fills the buffer with `00 01 02 ... 0f`, runs stage 1 and prints it as hex, i.e. it exposes `E(000102...0f)` - the reference point for a re-implementation.

The important structural consequence: the expected values live *only* inside the authenticated firmware, and the firmware is encrypted under a key derived from the answer. The 16-byte state `S` is therefore the pivot of the whole challenge, and everything has to be inverted outwards from the decrypted firmware.

## Exploitation Chain

1. **Re-implement the byte-machine.** A Python model of stage 1 was written from the disassembly and validated against the self-test: `E(000102030405060708090a0b0c0d0e0f) = d3e4dd75211d03215a37de7164eb510a`, matching `./kelpie selftest` exactly. The interpreter body was additionally executed as real machine code in a self-written x86-64 subset emulator (Capstone-driven) to confirm the read of every handler - opcode roles, gather-vs-scatter permutation direction, S-box assignment, and the `pc + 6 <= len` loop bound - agreed on every test vector.

2. **Authenticate the firmware.** With the AES-256-GCM key recovered out of band for this solve (it is `HMAC-SHA256(0x4028a4..., S)`, i.e. 32 bytes), the 924-byte record at `0x4028d4` decrypts and its GCM tag verifies, yielding the unlock routine.

3. **Decode the routine.** 924 bytes = 308 instructions: 48 `sbox`, 48 `xorimm`, 48 `mulimm`, 48 `rol`, 48 `addrr`, 48 `xrol3`, 3 `perm51`, **16 `cmp`**, 1 `halt`. Each of the 3 rounds (97 operations) is: 16 S-boxes over cells 0..15, one `0x51` perm (table selector alternates 0, 1, 0), then 16 per-cell triplets `xorimm`/`mulimm`/`rol`, then a `0x60` shear ring `state[i] ^= rotl(state[i+3],3)` and an `0x11` ring `state[i] += state[i+5]` (indices mod 16). The trailing compare block covers cells 0..15 in order, with immediates

   ```
   4c 9a 3f e6 19 ea b4 ef a7 ef d8 7a 5c 49 e4 d8
   ```

   so the accepted state is whatever the 3 rounds map to those values.

4. **Invert the 3 rounds.** Every operation is reversible and each inverse keeps the same 3-byte shape: `sbox -> rsbox` (the inverse S-box is present in `.rodata` at `0x402cc0`), `xorimm` is self-inverse, `mulimm` becomes multiplication by the inverse mod 256 (all multipliers are odd), `rol <-> ror`, `addrr <-> subrr`, `xrol3` is self-inverse, and the `0x51` gather `new[i] = old[t[i]]` inverts to `old[j] = new[t^-1[j]]` - which is exactly why the two unused inverse permutation tables sit next to the forward ones. Starting from the compare immediates and replaying the program backwards gives

   ```
   S = b0dd9edc83f370dad4f5399447579076
   ```

   Two independent confirmations: re-running the decrypted routine on `S` returns `err = 0`, and `HMAC-SHA256(0x4028a4..., S)` reproduces the AES key that authenticates the stored GCM tag.

5. **Invert stage 1.** `E` is a bijection, so the same backward replay over the 411 stage-1 instructions turns `S` into the parser input:

   ```
   E^-1(S) = 5b2d4c7961307f588d9dd95bada5647b
   ```

6. **Verify on the target.** Piping `isfcr{5b2d4c7961307f588d9dd95bada5647b}` into `./kelpie` (clean process, no tracer, so the `0x5a` branch is not taken) prints `Unlocked. Activation accepted.` with exit status 0; changing a single hex digit prints `Denied.`

## Flag

`isfcr{5b2d4c7961307f588d9dd95bada5647b}`

## Reproduce

Run the binary once to fix the re-implementation:

```bash
chmod +x kelpie && ./kelpie selftest
# d3e4dd75211d03215a37de7164eb510a
```

Then, with a model of the interpreter (`op,A,B` handlers as in the table above):

1. Decrypt the firmware with AES-256-GCM, IV = the 12 bytes at `0x4028b4`, ciphertext = the 924 bytes at `0x4028d4`, tag = the 16 bytes at `0x4028c0`, no AAD. Expect 308 instructions ending in 16 `cmp` + `halt`.
2. Build the target vector from the compare immediates (`4c9a3fe619eab4efa7efd87a5c49e4d8`) and replay the program backwards, applying the per-op inverses listed in step 4 of the chain. Expect `S = b0dd9edc83f370dad4f5399447579076`.
3. Check `HMAC-SHA256(key = bytes.fromhex('92c5c86453cafe7c1127ea067a7fb9d3'), msg = S)` equals the AES key used in step 1, and that running the decrypted program forward on `S` returns `err = 0`.
4. Replay the 411-instruction stage-1 program backwards from `S`. Expect `5b2d4c7961307f588d9dd95bada5647b`.
5. Confirm against the target:

```bash
printf 'isfcr{5b2d4c7961307f588d9dd95bada5647b}\n' | ./kelpie
# KELPIE firmware unlock console
# enter activation key: Unlocked. Activation accepted.
```

The flag was recovered from the supplied binary and verified locally by the binary's own acceptance path (forward re-run of the authenticated firmware returns `err = 0` and the GCM tag re-verifies). It was not submitted to the CTF service, so acceptance is unconfirmed.
