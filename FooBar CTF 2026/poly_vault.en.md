---
title: "poly_vault"
category: "Reverse"
tags: ["linux-elf", "sigusr1", "signal-trampoline", "sbox", "matrix", "xor", "permutation"]
solve_date: "2026-10-10T19:56:00+07:00"
language: "en"
points: 250
---

# poly_vault

**Flag:** `foobarctf{s1gn4l_m4tr1x_v4ult_x}`  
**Artifact:** `poly_vault` — stripped, non-PIE Linux x86_64 ELF executable (14,600 bytes).

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `poly_vault` | 14,600 | `838d664d9a32550fe3f19d6196ed7bbb7f0da9457ca51aa446cf0bf5f7dbc7a6` |

## Challenge

We are given a proprietary key-verification ELF guarding a vault. Normal decompilation fails to recover a meaningful call graph because the control flow is redirected through signal traps instead of ordinary calls. The objective is to bypass the signal trampoline, reverse the transformation layers, and recover the master passphrase in the `foobarctf{...}` format.

## Initial reconnaissance

```bash
file poly_vault
sha256sum poly_vault
readelf -h -S poly_vault
objdump -d -M intel poly_vault
objdump -s -j .rodata poly_vault
```

The ELF is stripped and of type `EXEC`, with a fixed image base rather than PIE. The main routine requires exactly **one 32-byte argument**. The following status messages can be found in `.rodata`:

```text
[+] Access Granted! Flag verified.
[-] Access Denied! Invalid key.
[-] Key must be exactly 32 bytes.
Usage: %s <flag_key>
```

The flag is not present as a plaintext string; we need to reverse the verifier.

## Uncovering the signal trampoline

The argument-processing routine at `0x4010e0`:

1. Checks `strlen(argv[1]) == 0x20` and copies the 32 bytes into the state buffer at `0x404080`.
2. Registers a `SIGUSR1` signal handler at `0x4012e0` using `sigaction` with `SA_SIGINFO`.
3. Calls `raise(10)` to enter the transformation pipeline.

Crucially, the handler does **not call** the individual transformation functions. It overwrites the saved instruction pointer in `ucontext_t` (RIP is at offset `0xa8` in this Linux x86_64 context), so that the next signal return resumes execution at the selected stage:

```c
// Pseudocode for handler 0x4012e0
void signal_handler(int sig, siginfo_t *info, void *ctx) {
    if (round < 4) {
        saved_RIP(ctx) = stage_table[stage];
        if (++stage == 4) { stage = 0; round++; }
    } else {
        saved_RIP(ctx) = 0x4014a0; // final comparison
    }
}
```

The four function pointers at `0x403dc0` resolve to:

| Stage | Address | Role |
|---|---|---|
| 0 | `0x401340` | Substitute each byte with an S-box lookup |
| 1 | `0x401380` | Apply a 4×4 matrix to each 4-byte block, modulo 256 |
| 2 | `0x401400` | XOR with a round-dependent key |
| 3 | `0x401450` | Permute all 32 bytes |

Each stage ends with `raise(SIGUSR1)`, dispatching to the next one. The program executes **4 rounds × 4 stages = 16 transformations** and then jumps to the final verifier at `0x4014a0`. This explains why conventional call graphs are misleading.

## Reconstructing the transformation

All required tables are stored in `.rodata`. In this non-PIE binary, each `.rodata` file offset is the corresponding virtual address minus `0x400000`.

| Virtual address | File offset | Size | Purpose |
|---|---:|---:|---|
| `0x4020a0` | `0x20a0` | 16 | 4×4 matrix, row-major |
| `0x4020c0` | `0x20c0` | 32 | Byte permutation, `out[p[i]] = in[i]` |
| `0x4020e0` | `0x20e0` | 32 | Expected transformed bytes |
| `0x402100` | `0x2100` | 128 | Four round-dependent XOR keys, 32 bytes each |
| `0x402180` | `0x2180` | 256 | Substitution table / S-box |

The 4×4 matrix at `0x4020a0` is:

```text
M = [ [1, 9, 4, 9],
      [7, 4, 8, 5],
      [1, 3, 7, 6],
      [5, 3, 4, 6] ]
```

For a 32-byte state `x`, every round `r ∈ {0,1,2,3}` applies:

```text
1. x[i] = S[x[i]]                                  (S-box)
2. x[4b:4b+4] = M * x[4b:4b+4] mod 256             (8 blocks)
3. x[i] ^= K[r*32 + i]                             (round-key XOR)
4. out[P[i]] = x[i]                                (permutation)
   x = out
```

At `0x4014a0`, the verifier compares the resulting 32-byte state with the target at `0x4020e0` using 64-bit XOR/OR comparisons. An exact match prints `Access Granted`.

## Inverting the layers

Every operation is reversible:

- **S-box:** all 256 output values are unique, so `S_inv[S[x]] = x`.
- **XOR:** XOR with the same key reverses itself.
- **Permutation:** because `out[P[i]] = in[i]`, the inverse is `in[i] = out[P[i]]`.
- **Matrix:** `det(M) = -981 ≡ 43 (mod 256)`. Since `gcd(43, 256) = 1`, `M` has a modular inverse over `Z/256Z`.

Start from the 32-byte target and process rounds **3, 2, 1, 0**. Within each round, undo the steps in reverse order: **permutation → XOR → matrix → S-box**. Importantly, the matrix arithmetic is modulo 256, not modulo a prime.

### Complete solver (Python 3; standard library only)

Save the following as `solve_poly_vault.py`:

```python
#!/usr/bin/env python3
"""Offline solver for poly_vault (Linux x86_64, non-PIE ELF)."""
from pathlib import Path
import sys

MOD = 256
N = 32


def invert_matrix_mod256(matrix):
    """Gauss-Jordan elimination over Z/256Z (requires odd pivots)."""
    a = [row[:] + [int(i == j) for j in range(4)]
         for i, row in enumerate(matrix)]
    for col in range(4):
        pivot = next((row for row in range(col, 4) if a[row][col] % 2), None)
        if pivot is None:
            raise ValueError("Matrix is not invertible modulo 256")
        a[col], a[pivot] = a[pivot], a[col]
        scale = pow(a[col][col], -1, MOD)
        a[col] = [(v * scale) % MOD for v in a[col]]
        for row in range(4):
            if row != col:
                factor = a[row][col]
                a[row] = [(x - factor * y) % MOD
                          for x, y in zip(a[row], a[col])]
    return [row[4:] for row in a]


def mul_blocks(data, matrix):
    out = []
    for pos in range(0, N, 4):
        block = data[pos:pos + 4]
        out.extend(sum(matrix[i][j] * block[j] for j in range(4)) % MOD
                   for i in range(4))
    return out


def solve(path):
    blob = Path(path).read_bytes()
    # For this non-PIE ELF, the .rodata VA 0x402000 maps to file offset 0x2000.
    matrix_data = blob[0x20A0:0x20B0]
    matrix = [list(matrix_data[i:i+4]) for i in range(0, 16, 4)]
    permutation = list(blob[0x20C0:0x20E0])
    goal = list(blob[0x20E0:0x2100])
    keys = blob[0x2100:0x2180]
    sbox = list(blob[0x2180:0x2280])
    assert len(matrix_data) == 16 and len(goal) == N and len(keys) == 128
    assert sorted(permutation) == list(range(N))
    assert sorted(sbox) == list(range(MOD))

    inv_sbox = [0] * MOD
    for x, y in enumerate(sbox):
        inv_sbox[y] = x
    inv_matrix = invert_matrix_mod256(matrix)

    state = goal
    for round_index in range(3, -1, -1):
        # Forward permutation: out[permutation[i]] = in[i].
        state = [state[permutation[i]] for i in range(N)]
        # XOR is its own inverse.
        state = [value ^ keys[round_index * N + i]
                 for i, value in enumerate(state)]
        # Undo 4x4 matrix on eight 4-byte blocks.
        state = mul_blocks(state, inv_matrix)
        # Undo the substitution table.
        state = [inv_sbox[value] for value in state]

    candidate = bytes(state).decode('ascii')
    assert len(candidate) == N

    # Independent verification: re-encrypt recovered input using forward layers.
    check = list(candidate.encode('ascii'))
    for round_index in range(4):
        check = [sbox[v] for v in check]
        check = mul_blocks(check, matrix)
        check = [value ^ keys[round_index * N + i]
                 for i, value in enumerate(check)]
        permuted = [0] * N
        for i, value in enumerate(check):
            permuted[permutation[i]] = value
        check = permuted
    assert check == goal, "Forward transform does not match stored target"
    print('FLAG:', candidate)
    print('Verification: forward transform matches the 32-byte target')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python3 solve_poly_vault.py <path-to-poly_vault>')
    solve(sys.argv[1])
```

## Reproduction and validation

With `poly_vault` and `solve_poly_vault.py` in the same directory:

```bash
python3 solve_poly_vault.py ./poly_vault
chmod +x ./poly_vault
./poly_vault 'foobarctf{s1gn4l_m4tr1x_v4ult_x}'
```

Observed output:

```text
FLAG: foobarctf{s1gn4l_m4tr1x_v4ult_x}
Verification: forward transform matches the 32-byte target
[+] Access Granted! Flag verified.
```

Changing the final byte makes the binary reject the key:

```bash
./poly_vault 'foobarctf{s1gn4l_m4tr1x_v4ult_y}'
# [-] Access Denied! Invalid key.
```

As an independent offline validation, the solver runs the **forward pipeline** on the recovered passphrase and asserts that the result exactly matches the 32-byte target embedded in the ELF.

## Result

The signal trampoline conceals execution order, but all four transformation layers are invertible. Recovering the stage order and reversing the four rounds directly from `.rodata` yields the master passphrase:

```text
foobarctf{s1gn4l_m4tr1x_v4ult_x}
```
