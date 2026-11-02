---
title: "The Quiet Divide"
category: "NTA"
tags: []
solve_date: "2026-10-31"
language: "en"
---

# The Quiet Divide

## Challenge

A packet capture from Asterion Dynamics after an overnight maintenance window. Two domains (`fleet-prod` and `dr-ops`) disagree about what happened. The production branch is authoritative: a policy explicitly says recovery cannot finalize production. Reconstruct the signed custody chain, recover the QUIC key log from the split escrow shares, rebuild the evidence material from the public SDK, select the authoritative archive transaction, and decrypt the final seal.

## Solution

### Step 1: Extract the signed production evidence

From the HTTP JSON in the capture:

- Committee records `C0`-`C4`, threshold 3.
- Checkpoint `W0`: `terminal_event=b34dc728...`, `checkpoint_sha256=5e4f78ad...`.
- Five custody records `ROOT -> PREP -> COMMIT -> PREP -> COMMIT` with valid 3-of-3 signatures.
- Seal `mb-final-seal/10` containing `archive_salt_hex`, `salt_hex`, `nonce_hex`, and `ciphertext_b64`.

### Step 2: Recover the QUIC key log and observation

XOR the two escrow shares (`/v3/escrow`, `mb-diagnostic-share/3`) slot A + slot B. The result is the QUIC key log; its SHA-256 matches `keylog_sha256`. Decrypting the QUIC sessions yields an observation signed by `ARCH-14` (`mb-quic-observation/3`).

### Step 3: Build the evidence chain

Following the public SDK:

1. `chain = SHA256(canonical(custody_events))`.
2. HMAC over the `pulse-codec 7.7.0` firmware (assembled from four HTTP Range requests, SHA-256 `0835dfce...`).
3. Attestation signature.
4. QUIC observation signature.
5. `PulseWire` state digest from the `PLS2` frame served by `/v2/frames`.

### Step 4: Select the authoritative archive and decrypt the seal

HKDF with `archive_salt_hex=6d562eb7...` derives the AES-GCM key. Three `ops-17` candidates decrypt to SQLite databases (`transfers`, `receipts`, `fragments`, `operations`). The authoritative one is transaction `6dd9ec588c9914ca95df44b2` in archive `5a2c8adef3c0846a2d0fb62d00844c64`:

- `release_checkpoint = 5e4f78ad...` (the checkpoint witnessed by W0),
- `case_commit = b34dc728...`,
- receipt `accepted`, and the fragment commit matches the locally computed material.

Unmask the four fragments with HMAC-SHA256 and the codec digest to recover `material`. The final key is:

```
final_key = HKDF(material || evidence || witness_signature,
                 salt = ded3d12c..., info = "MIRRORBREAK/10/PRODUCTION-CASE")
```

Decrypt `ciphertext_b64` with nonce `0de2e11f...` and the canonical seal fields as AAD. The `dr-ops` recovery branch (QUIC 4434, escrow batch `fe3785...`) is a decoy: the policy forbids recovery from finalizing production.

## Result

```
hiCTF{c8c46fdbd6e5e4eacabfba53a156ff9ab10567f2}
```

## Reproduction notes

Values containing ... are shortened prefixes from the retained notes, not runnable decryption inputs. Full reproduction requires the PCAP, SDK, and complete original fields.
