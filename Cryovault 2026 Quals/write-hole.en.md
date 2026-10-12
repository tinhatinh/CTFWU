---
title: "Write Hole"
category: "Forensics"
tags: ["raid5", "recovery"]
solve_date: "2026-10-10T11:41:00+07:00"
language: "en"
---

# Write Hole

**Flag:** `isfcr{p4r1ty_n3v3r_l13s_wr1t3_h0l3_r3m3mb3rs}`  
**Artifacts:** `bay0.img`, `bay1.img`, `bay2.img` (17,825,792 bytes each)

| Artifact | SHA-256 |
|---|---|
| `bay0.img` | `38226d020b3cfc46f587dae721df0ed61d9886e36043abaa0d3071c3635258a6` |
| `bay1.img` | `18b526944cc99801152c49724cb03cbdb4ab6eeb566f0c82c8b60fe802c21860` |
| `bay2.img` | `2e6ee1100f9bb2d68a85f85e6992d0f0eb6cfe5df3e487c4fba8c0b004d455d0` |

## Challenge

A three-drive NAS lost power during a write to an encrypted evidence report. The RAID configuration was not saved. Recover enough of the array to reconstruct the report and its custody token, which is the flag.

## Initial Analysis

All three raw images have the same size. Printable strings in the images reveal an ext4 NAS volume, an `isfc-stage.py` sealing script, and a write-ahead intent file for job 7. The script describes independent 32 KiB AES-GCM records. The intent contains a SHA-256 digest for each of the six records, giving us a reliable way to identify valid data after reconstructing the RAID.

The key must also be recovered: the stage notes say that `/stage/.keyslot` is deleted after it is read. The job 7 keyslot appears in raw disk remnants. Its CRC is valid, and the SHA-256 key identifier derived from its key matches the one in the intent file. This ties the recovered key to the interrupted job.

## Exploitation Chain

1. **Reconstruct the filesystem.** The ext4 superblock is found at a 1 MiB offset into the member images. Testing RAID-5 mappings against the filesystem metadata and directory entries identifies a consistent three-member layout with 32 KiB chunks and left-symmetric parity. This exposes `/stage/job-0007.intent`, `/stage/payload.bin`, the keyslot remnants, and the NAS notes. The notes independently identify the volume as three-disk RAID-5.

2. **Recover and validate records.** For each 32 KiB logical record, use the member data or XOR the other two member chunks when parity reconstruction is needed. Compare the SHA-256 of each candidate record with the corresponding digest in the intent. The record format is `nonce (12 bytes) || ciphertext || GCM tag (16 bytes)`. Decrypt matching records with AES-GCM using the job 7 key, nonce, and AAD `payload.bin|7|<record index>`. All six records are recovered and authenticated.

3. **Repair the damaged record.** The parity reconstruction for record 3 has one flipped bit. Decrypting its ciphertext for inspection reveals the expected custody-token prefix `isfcr{`; this locates a one-bit correction at byte offset 8876 of the sealed record (`XOR 0x02`). After the correction, the record matches its intent SHA-256 and its AES-GCM tag verifies. These two independent checks confirm the repair.

4. **Assemble the token.** The authenticated report labels three shards and gives their order:

   - Shard 1: `isfcr{p4r1ty_n3`
   - Shard 2: `v3r_l13s_wr1t3_`
   - Shard 3: `h0l3_r3m3mb3rs}`

   Concatenating them produces the flag below.

## Flag

`isfcr{p4r1ty_n3v3r_l13s_wr1t3_h0l3_r3m3mb3rs}`

The flag was recovered from the disk images and verified through the intent hashes and AES-GCM authentication of all six report records. It was not submitted to a CTF service, so acceptance is unconfirmed.

## Reproduce

Extract the supplied ZIP, then run the RAID reconstruction against the three images. The reconstruction parameters are a 1 MiB member offset, 32 KiB RAID-5 chunks, and a three-member left-symmetric layout. Recover the job 7 key from a CRC-valid `KSLT` keyslot and select it by matching `SHA256(key)[:16]` to the intent's `key_id`. For each of the six logical records, test the available member data and XOR reconstructions against the corresponding intent digest; decrypt only matching candidates with AES-GCM and AAD `payload.bin|7|<index>`. For record 3, apply the single-bit correction at record offset 8876 (`^= 0x02`) before the digest and tag checks. Extract shard lines matching `[custody-token] shard N/3 = ...` from the authenticated plaintext in numeric order and concatenate them. The expected result is:

```text
All six record hashes and AES-GCM tags verified.
FLAG isfcr{p4r1ty_n3v3r_l13s_wr1t3_h0l3_r3m3mb3rs}
```
