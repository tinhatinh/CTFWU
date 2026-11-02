---
title: "Apex Engine"
category: "Pwn"
tags: []
solve_date: "2026-10-31"
language: "en"
---

# Apex Engine

## Challenge

The Apex Multi-Threaded Settlement Engine is a high-frequency custody vault. Its risk model assumes funds cannot be double-spent and that classified vault records are shielded from non-root clearance. The engine loses a race between concurrent settlement operations, and the vault's document-slot target path can be edited to an arbitrary file. Pointing a slot at `/flag` and streaming it through the enclave discloses the flag.

## Solution

### Step 1: Win the settlement race

The engine processes settlement/withdrawal operations asynchronously. Issuing concurrent operations bypasses the balance check and produces a double-spend, which supplies the balance/clearance needed to reach the vault interface. The winning flag text itself names the bug: `mult1thr34d_r4c3_c0nd1t10n`.

### Step 2: Edit a document slot target

The secure vault enclave menu offers:

```
1. Create Document Slot
2. Stream Document via Enclave
3. Edit Document Target Path
4. Return to Main Menu
```

The target path of a slot is not restricted. Edit slot #3 (or any controllable slot) and set its target to `/flag`:

```
[+] Slot #3 target updated to '/flag'
```

### Step 3: Stream the file

Choose "Stream Document via Enclave" for the modified slot. The enclave treats `/flag` as the slot's document and emits its contents:

```
================ [SECURE ENCLAVE DATA STREAM] ================
hiCTF{t0ct0u_mult1thr34d_r4c3_c0nd1t10n_w1n_8d3f_a996c1e412}
==============================================================
```

The flag was reproduced with a clean exploit run against the remote instance.

## Result

```
hiCTF{t0ct0u_mult1thr34d_r4c3_c0nd1t10n_w1n_8d3f_a996c1e412}
```

## Reproduction notes

The retained notes do not include the complete settlement-race client or its request schedule. The remote output above records the result; the flag text alone is not evidence for the race mechanism.
