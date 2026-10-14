---
title: "String Peek and Poke"
category: "Pwn"
tags: ["std-string","out-of-bounds-access","vtable-leak","rop"]
solve_date: "2026-10-10"
language: "en"
---

# String Peek and Poke

**Flag:** `FortID{wh3n_7h3_0nly_t00l_15_4_h4mm3r_3v3ry_5tr1ng_15_4_n41l_c8a5687cdf}`  
**Service:** `ncat --ssl string-peek-and-poke-2815b549b14a.inst17.ctf.fortid.com 1337` (instance that yielded the flag; `d6ffdf3c7593` was the instance connected to in the earlier run). Artifact: `handout.zip` 1.8 MB containing `chall` 19512 B (ELF64 PIE, full RELRO, canary, NX), `chall.cpp` 804 B, `libc-2.39.so` 2129424 B, `libstdc++.so.6.0.33` 2592224 B.

## Challenge

`chall.cpp` keeps its notes in a global array `std::string notes[CAP=8]` and exposes two operations, `put` and `get`, that take an `int` index with no bounds check. The service listens over TLS on port 1337.

## Analysis

The unchecked index turns an eight-element array into a pair of bidirectional out-of-bounds read/write primitives anchored at the address of `notes`. Each libstdc++ `std::string` occupies 32 bytes (data pointer, size, and a union holding capacity or the SSO buffer), and the gaps between the regions below are exactly nine indices wide:

| Object | Address (relative to image base) | `put`/`get` index range |
|---|---|---|
| `std::cout` | `exe + 0x203020` | -18 … -10 |
| `std::cin` | `exe + 0x203140` | -9 … -1 |
| `notes` | `exe + 0x203260` | 0 … 7 |

So a negative index lets `put`/`get` read and overwrite 32-byte blocks inside the two global stream objects.

Per the attributes of the binary in the handout, `chall` is ELF64 PIE with full RELRO, stack canary and NX. That set closes the usual routes: full RELRO rules out GOT rewriting, NX rules out injected shellcode, the canary rules out a direct stack smash, and PIE means an address leak is required before anything can be targeted. The chain therefore goes the other way: leak out of the global region, then ROP.

The chain has three moves:

1. **Leak.** `get -67825` reads a region containing libstdc++ pointers. Subtract the matched library symbol offset to obtain `lso`; the saved solver then uses deployment-specific mapping distances for libc and the executable. PIE alone does not establish a heap base or invariant low 20 bits.

## Solution

The whole chain ran against the live instance; `chall` was never executed offline (see Directions Tested).

1. Connect over TLS to the instance, use `get` with a negative index to pull the libstdc++ vtable pointer at index -67825, and compute the libc and image bases. The log of the first remote attempt records the base obtained:

   ```text
   remote#0 lso=0x7f8aee782000
   ```

2. Forge the fake `std::string` descriptor inside the `ctype<char>` facet to obtain the offset-controlled read/write window, then write the ROP chain to its destination. The log line confirms the chain's location and its first element:

   ```text
   chain at 0x7ffc1562a318: libc+0x10c08e
   ```

3. Call `exit` to hand control to the chain. The resulting shell prints the `SHELL` marker and the verification commands; `uid=10001(ctf)` is the privilege context of the process on the instance:

   ```text
   SHELL
   uid=10001(ctf)
   ```

4. In that shell, `ls /home/ctf` locates the flag file and `cat flag.txt` reads it. The output of `cat flag.txt` appears twice, and both occurrences are the same flag string.

The stack address in step 2 (`0x7ffc1562a318`) belongs to a range randomised per run, so it is a value from that specific attempt rather than a reusable constant; the `libc+0x10c08e` offset is fixed for the shipped libc.

## Result

```text
FortID{wh3n_7h3_0nly_t00l_15_4_h4mm3r_3v3ry_5tr1ng_15_4_n41l_c8a5687cdf}
```

The flag was read directly from the challenge service. No submission response recorded.

## Reproduce

A TLS client able to speak to port 1337 plus Python 3 to automate the `put`/`get` rounds. The three global-region offsets and everything derived from libc are constants for the shipped build; the image base, libc base, heap base and stack address must come from the leak of the run itself.

```text
ncat --ssl string-peek-and-poke-2815b549b14a.inst17.ctf.fortid.com 1337
```

| Fact | Value | Source |
|---|---|---|
| `std::cout` | `exe + 0x203020` | `chall` symbol table |
| `std::cin` | `exe + 0x203140` | `chall` symbol table |
| `notes` | `exe + 0x203260` | `chall` symbol table |
| stride per index | 32 bytes | `sizeof(std::string)` |
| index used for the vtable leak | -67825 | libstdc++ region |
| first chain element | `libc + 0x10c08e` | `libc-2.39.so` from the handout |

The `ret`, `pop rdi` and `system` gadgets and the `"/bin/sh"` string all come from the shipped `libc-2.39.so`; locating them is file analysis with objdump/readelf and does not require running `chall`. The driver script used against the instance was not part of the handout, so it is not reproduced here.
