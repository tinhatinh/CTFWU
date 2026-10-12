---
title: "simphell"
category: "Reverse"
tags: ["haskell", "ghc", "elf", "reverse-engineering", "flag-validation"]
solve_date: "2026-10-10"
language: "en"
---

# simphell

**Flag:** `kBxAc{__y3t_4n0th3r_fl4g_v3ry_3a5y__}`  
**Challenge:** *Yet another simple challenge.*  
**Artifact:** `chall (1)` (rename to `chall` for the commands below).

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `chall (1)` | 1,012,400 | `0c1f44233e1dde1c7c28718a12040559375c05a060c11b15dcb4583e2c5f97e4` |

## Goal

Reverse the `simphell` executable and find an input accepted by the flag checker. The required flag format is `kBxAc{...}`.

## Initial examination

`file` identifies a stripped, dynamically linked **64-bit x86-64 ELF**. Numerous `GHC.Internal.*` runtime strings indicate that the program was built using the **Glasgow Haskell Compiler (GHC)**. This matters during static analysis: GHC binaries contain runtime code and closures in addition to application-specific flag logic.

```bash
file 'chall (1)'
readelf -S 'chall (1)'
strings -a 'chall (1)' | grep -E 'Enter the secret|Success|Failure|GHC.Internal'
```

The binary contains these user-facing strings:

```text
Enter the secret flag:
Success! Valid flag.
Failure! Invalid flag.
```

The flag itself is not visible as a plain contiguous ASCII string, so a direct `strings` search is insufficient.

## Analysis and result

The executable reads a supplied string and chooses between a success and failure branch. The recovered candidate flag was **validated against the original uploaded ELF**. A deliberately invalid candidate takes the failure branch, ruling out an unconditional success message.

**Evidence limitation:** the preserved material contains the final flag and original executable, but **not a step-by-step instruction trace, exact encoded-data offsets, or a verified XOR key**. The reproduction below verifies the recovered answer rather than independently extracting it from the binary.

## Reproduction / validation

On x86-64 Linux, copy `chall (1)` to `chall`, then run:

```bash
# Linux x86_64 (the uploaded ELF itself is not marked executable)
chmod +x ./chall
printf '%s\n' 'kBxAc{__y3t_4n0th3r_fl4g_v3ry_3a5y__}' | ./chall
printf '%s\n' 'kBxAc{wrong}' | ./chall
```

Observed output:

```text
Enter the secret flag: Success! Valid flag.
Enter the secret flag: Failure! Invalid flag.
```

## Flag

```text
kBxAc{__y3t_4n0th3r_fl4g_v3ry_3a5y__}
```

## Conclusion

The stripped GHC executable hides its flag-checking path among a comparatively large runtime. The candidate above is **accepted by the binary itself**. A fully instruction-level reverse-engineering writeup would require retaining and documenting the relevant GHC control-flow trace and constants; no unverified decoding algorithm is asserted here.
