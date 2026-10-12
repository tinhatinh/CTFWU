---
title: "SoulVault"
category: "Reverse"
tags: ["go-binary", "stripped", "ghidra-headless", "polymorphic-vm", "arx-inversion", "sha256-keystream"]
solve_date: "2026-10-09"
language: "en"
---

# SoulVault

**Flag:** `OWASP{s0ul_v4ult_byt3c0d3_vm_r3v3rs3d_7a8f9c2e}`
**Artifact:** `soulvault` (1,806,496 B) — ELF x86-64, Go 1.27.1 static, stripped. Author: Suyog Jadhav.

The title collides with a different ByteMe CTF 26 challenge also named SoulVault, in the Mobile category (slug `soulvault-mobile`); this writeup covers the Go binary and has nothing to do with the Mobile entry.

## Challenge

An Expert task worth 500 points, shipped as a single Linux binary. The program asks for an *access sequence*, validates its shape, maps it into a buffer, and feeds that buffer to a polymorphic VM. Once the VM reaches its accepting state, the flag is reconstructed from encrypted blobs stored in the binary and printed.

Everything below is a static reconstruction: the binary was never executed. The three message strings `ACCESS GRANTED`, `[+] Flag: %s` and `[-] ACCESS DENIED: Invalid sequence structure or` were read from `.rodata` only.

## Analysis

### Re-basing the symbols

`file soulvault` reports a 64-bit static ELF with no Go symbol table. GoReSym run against the binary returns a **wrong text base**; addresses taken from its output had to be shifted by one constant before they could be matched against Ghidra:

```text
addr_corrected = addr_goresym - 0xcb6c8
```

After the correction, Ghidra ran headless and decompiled **65 `main.*` functions**. The Ghidra script used here is written in Java, since the host has no PyGhidra.

### Stage 1 — `ValidateStructureStage1`

This function checks the string shape plus a rolling hash accumulated over the bytes of the string itself:

```text
string form: SV-XXXX-XXXX-XXXX-XXXX-XXXX
h init     : 0x5a17f00d
update     : h = i*0xd + c*0x11 + h*0x1f        (i = index, c = byte value)
target     : h == 0x1248d50d
```

The constant pair `0x5a17f00d` / `0x1248d50d` is the only condition in this stage; no lookup table or other state is involved.

### Stage 2 — `ProcessAccessSequence`

A string that passes stage 1 is mapped into the buffer `buf` through three constant tables in `.rodata`:

```text
buf[i] = ROT_L8(seq[PERM[i]] ^ XORKEY[i], (i % 7) + 1) + ADDKEY[i]

PERM    @ 0x5ab920
XORKEY  @ 0x5ab940
ADDKEY  @ 0x5ab960
```

Three consecutive 32-byte blocks sit at those addresses, in the order they appear in the formula. Because `PERM` is a bijection, the map `seq -> buf` is invertible byte by byte:

```python
def rot_l8(v, s):
    s &= 7
    return ((v << s) | (v >> (8 - s))) & 0xFF if s else v & 0xFF

def rot_r8(v, s):
    s &= 7
    return ((v >> s) | (v << (8 - s))) & 0xFF if s else v & 0xFF

def un_process(buf, perm, xorkey, addkey):
    out = [0] * len(buf)
    for i, b in enumerate(buf):
        x = rot_r8((b - addkey[i]) & 0xFF, (i % 7) + 1)
        out[perm[i]] = x ^ xorkey[i]
    return out
```

### Stage 3 — the polymorphic VM

The VM exposes **23 opcodes** and is seeded with `seed = 0x5a17f00dc0ffee11` and `k32 = 1`; the polymorphic opcode generator decides which operation each opcode decodes to. The program it runs is **576 bytes** long and consists of **8 reversible ARX rounds**, so every round has a deterministic inverse and no search is required. The acceptance test compares register group 8–11 against the constant `CHK`.

## Solution

Since the 8 ARX rounds are reversible and `un_process` is one-to-one, the accepted sequence is derived by running the chain backwards: start from a VM state satisfying `regs[8..11] == CHK`, invert each round to obtain the VM input, then invert `ProcessAccessSequence` to recover the string.

The recovered sequence:

```text
SV-8F4C-3B91-7E02-A6D5-C918-B472
```

Verification is a **forward** run of an emulator implementing the three stages above with that sequence. Recorded output:

```text
r0=1 halted=1 err=None steps=142 regs8-11==CHK: True
```

`r0=1` and `regs8-11==CHK: True` are the VM acceptance flags; `steps=142` is the number of opcodes executed by the 576-byte program on that path.

With the `buf` produced by the accepted sequence, the flag is recovered through a SHA-256 derived key:

```text
ReconstructFlag = (blob1..4) XOR (SHA256(CHK || "SoulVault::MasterFlagKeystream::v1" || buf)
                                    || SHA256(master || "SoulVault::SubStreamKey::v1"))
```

The two digests are concatenated to form the keystream; the four encrypted blobs and the `CHK`/`master` constants all come straight out of `.rodata`, so the reconstruction needs no execution of the binary. The following lines from the same verification run:

```text
cipher len 47 c00e123f...
FLAG = b'OWASP{s0ul_v4ult_byt3c0d3_vm_r3v3rs3d_7a8f9c2e}'
```

`cipher len 47` matches the 47-byte length of the flag string printed right after it.

## Result

```text
OWASP{s0ul_v4ult_byt3c0d3_vm_r3v3rs3d_7a8f9c2e}
```

The flag is a static reconstruction from the supplied binary, confirmed by a forward emulator run against the accepted sequence (`r0=1 halted=1 err=None steps=142 regs8-11==CHK: True`); the binary itself was never executed. No submission response recorded.

The saved emulator run checks VM state, but a complete independent check of `ValidateStructureStage1` was not preserved. The full emulator and ARX rounds are also missing, so the two Markdown files do not yet reproduce the entire chain.

## Reproduce

Requirements: GoReSym, Ghidra (headless, Java script), Python 3. Keep `soulvault` in the working directory.

```console
$ file soulvault
$ goresym -d soulvault              # compare with Ghidra addresses, apply addr -= 0xcb6c8
$ analyzeHeadless <dir> <proj> -import soulvault -process -nolog \
    -scriptPath <dir> -postScript DecompileMain.java -savelocation
$ strings -a soulvault | grep -E "ACCESS GRANTED|ACCESS DENIED|Flag: %s"
```

To rebuild the accepted sequence, carve the three constant tables at `0x5ab920`, `0x5ab940`, `0x5ab960` and the blobs/`CHK`/`master` out of `.rodata`, then:

1. Run the 8 VM ARX rounds backwards from a state with `regs[8..11] == CHK` (same `seed = 0x5a17f00dc0ffee11`, `k32 = 1`, same 23-opcode polymorphic generator) to get the VM input.
2. Apply `un_process` from the Analysis section to get the `SV-...` string.
3. Run the forward emulator on that string to reproduce `r0=1 halted=1 err=None steps=142 regs8-11==CHK: True`.
4. Compute `SHA256(CHK || "SoulVault::MasterFlagKeystream::v1" || buf)` concatenated with `SHA256(master || "SoulVault::SubStreamKey::v1")` and XOR it against the four blobs to print the flag.
