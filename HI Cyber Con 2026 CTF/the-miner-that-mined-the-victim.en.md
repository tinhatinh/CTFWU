---
title: "The Miner That Mined The Victim"
category: "Forensics"
tags: []
solve_date: "2026-11-01"
language: "en"
---

# The Miner That Mined The Victim

## Challenge

A Windows forensics challenge served over a TLS question/answer instance. The instance asks 14 questions in order; three wrong answers in a row reset progress, so the answers must be collected offline and submitted in one clean run. The evidence is a Windows disk/memory artifact set from a fake "free mining optimizer" infection. The final flag is printed by the instance after all 14 answers.

## Solution

### Step 1: Reconstruct the infection timeline

- The victim `milon1` visits the Telegraph page `CoinBoost-Pro-v32--Free-Mining-Optimizer-05-12` and downloads `miner.zip` (77,944 bytes) from LimeWire.
- Download completes at `2026-05-13 14:25:36 UTC`; `miner.exe` first runs at `2026-05-13 14:26:55 UTC` (Prefetch run count 1, `PcaAppLaunchDic`).
- The payload loads `System.Security.Cryptography.dll` from `C:\Program Files\dotnet\shared\Microsoft.NETCore.App\9.0.16\` at `14:26:58 UTC`.
- It sets `HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\DisableAntiSpyware` (MITRE ATT&CK T1685), then encrypts 34 files to `.vibed`.
- The malware folder `C:\Users\milon1\Downloads\miner` is deleted to the Recycle Bin at `2026-05-13 14:27:47 UTC`; size 179,623 bytes.

### Step 2: Recover the shredded content

The Sysmon archive under `C:\Sysmon` is content-addressed and keeps the original plaintext of monitored files, which recovers `bar.txt`:

```
I will always be there for you bro!
```

The live `Microsoft-Windows-Sysmon%4Operational.evtx` has only 58 live records, but the file contains stale chunks. Carving 126 chunks yields 7,460 events, including the deletion of `C:\Users\milon1\Documents\noting.txt` with the shred pattern `0x706c6568`. On little-endian x86 the bytes are `68 65 6c 70`, i.e. **"help"**.

### Step 3: Answer all 14 questions in one session

| # | Answer |
|---|--------|
| 1 | `Microsoft Windows NT 10.0.26200.0` |
| 2 | `UTC-7, 420` |
| 3 | `https://limewire.com/d/Ak55K#Yrx3FgK3du` |
| 4 | `42d377fe-8948-4a32-809f-69a51e6dbcfa` |
| 5 | `2026-05-13 14:25:36 UTC` |
| 6 | `2026-05-13 14:26:55 UTC, 1` |
| 7 | `C:\Program Files\dotnet\shared\Microsoft.NETCore.App\9.0.16\System.Security.Cryptography.dll, 2026-05-13 14:26:58 UTC` |
| 8 | `HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\DisableAntiSpyware` |
| 9 | `T1685` |
| 10 | `hiCTF{finally_u_proved_ur_worthiness}` |
| 11 | `C:\Users\milon1\Downloads\miner, 2026-05-13 14:27:47 UTC` |
| 12 | `179623` |
| 13 | `I will always be there for you bro!` |
| 14 | `help` |

Answer 10 is **not** the final flag; it is the hidden "important text" file. The instance prints the real flag only after the full 14-answer run.



## Result

```
hiCTF{c4r3ful_4b0ut_cr4ck3d_t001s_34aa866011}
```

## Reproduction notes

T1685 is preserved as the recorded answer accepted by the instance, not as an independently verified ATT&CK classification. The original disk/memory evidence and automated TLS client are not included. The LimeWire URL is evidence from the scenario, not a required download for reading this writeup.
