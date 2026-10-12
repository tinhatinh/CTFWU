---
title: "C-Laude"
category: "Forensics"
tags: ["incident-response", "pcap", "mysql-binlog", "systemd", "auditd", "log-analysis"]
solve_date: "2026-10-10T14:42:00+07:00"
language: "en"
points: 508
---

# C-Laude

**Flag:** `kBxAc{y35_f1n477y_y0u_f0und_17_r1ght_175_r3l473d_t0_th3_4g3n71c_r4n50mw4r3_4tt4ck}`  
**Author:** adithG17  
**Attachment:** `evidence.zip`  
**Service:** `nc 35.232.188.8 31337`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `evidence.zip` | 1,647,181 | `e1054144808d8cd40ffb643a96f37d1e9639522cf072cb0bc6c2504d29b8c126` |

## Challenge

> Something doesn't quite add up.  
> You have been given a collection of artifacts recovered from a small production environment. Logs, network captures, service data, and filesystem remnants are all that remain.  
> There may be more to these files than meets the eye. Piece together the evidence, follow the traces, and answer the questions to uncover what happened.

The challenge provides an incident response artifact package `evidence.zip` collected from a compromised production environment. An intruder gained initial execution, persisted on an edge node, accessed cloud configuration stores, and tampered with the production database. Answering all nine sequential forensic questions via `nc 35.232.188.8 31337` yields the flag.

## Evidence Package Layout

The archive `evidence.zip` is structured into three primary directories:

1. `sensor/`:
   - `dmz.pcap`: Network packet captures across the DMZ perimeter.
   - `east-west.pcap`: Internal east-west traffic between production hosts.
   - `queries.log`: DNS resolver query logs recorded by internal sensors.
2. `exports/`:
   - `vault-02/`: Object store audit log (`audit.jsonl`) and asset `profile-r17.yaml`.
   - `atlas-01/`: Centralized authentication and configuration service logs (`auth-audit.jsonl`).
   - `ledger-01/`: Production MySQL artifacts including binary logs (`binlog.000001` - `000003`), SQL dumps, and connection records (`connection-audit.tsv`).
3. `collection/`:
   - `edge-runner-02/`: Compromised edge runner forensics including a filesystem timeline (`file-timeline.txt`), systemd unit files (`agent-cache.timer`, `agent-cache.service`), and host logs (`auth.log`, `audit.log`, `session-errors.log`, `preview-worker.jsonl`).

## Forensic Investigation & Questions

### Question 1: Production configuration settings modified in the database

- **Prompt:** *How many unique production configuration settings were modified as part of the incident-related database activity?*
- **Analysis:** Inspecting `exports/ledger-01/binlog.000003` reveals a transaction committed at timestamp 12:08:27 executing batch `UPDATE` statements on the settings table. The attacker sequentially altered configuration parameters ranging from `setting_10` to `setting_46`.
- **Calculation:** Exactly $46 - 10 + 1 = 37$ distinct configuration settings were updated.
- **Answer:** `37`

### Question 2: Systemd scheduled task unit installed on edge-runner-02

- **Prompt:** *After the intrusion, a user-level scheduled task was established on edge-runner-02. What is the full filename of the systemd unit?*
- **Analysis:** In `collection/edge-runner-02/fs/file-timeline.txt` and `collection/edge-runner-02/runtime/`, a new timer unit was established immediately following the initial exploit window: `agent-cache.timer` along with its service counterpart `agent-cache.service`.
- **Answer:** `agent-cache.timer`

### Question 3: Configuration object path retrieved from the release-assets bucket

- **Prompt:** *During the intrusion, a configuration file was retrieved from the release-assets storage bucket. What is its full object path?*
- **Analysis:** Checking `exports/vault-02/audit.jsonl` around 12:08:27 shows a `GetObject` call targeting:
  ```json
  {"operation": "GetObject", "bucket": "release-assets", "path": "releases/2026.10/profile-r17.yaml"}
  ```
- **Answer:** `releases/2026.10/profile-r17.yaml`

### Question 4: External IP initiating the anomalous preview execution

- **Prompt:** *Which external IP address initiated the preview request associated with the anomalous execution on edge-runner-02?*
- **Analysis:** In `collection/edge-runner-02/logs/preview-worker.jsonl`, the malicious execution was labeled `preview-7f4a`. Correlating incoming HTTPS traffic on port 8443 within `sensor/dmz.pcap` traces the origin of this request to external IP address `203.0.113.74`.
- **Answer:** `203.0.113.74`

### Question 5: Credential ID accepted by Atlas configuration service

- **Prompt:** *The retrieved release profile contained multiple candidate credentials. Which credential ID was successfully accepted by the Atlas configuration service when accessing the production profile?*
- **Analysis:** The downloaded file `profile-r17.yaml` contained candidate credentials (`runtime-r15`, `runtime-r16`, `runtime-r17`). Checking `exports/atlas-01/auth-audit.jsonl` for queries hitting `/v1/runtime/production`, only `credential_id: "runtime-r17"` produced an `accepted: true` response.
- **Answer:** `runtime-r17`

### Question 6: Path of the SSH key created on edge-runner-02

- **Prompt:** *Following the anomalous preview execution, a file was created on edge-runner-02 and subsequently used for SSH authentication. What is the full path of this file?*
- **Analysis:** Cross-referencing `collection/edge-runner-02/fs/file-timeline.txt` and `auth.log`, the worker process dropped an authorized key into:
  ```text
  /home/svc_preview/.ssh/authorized_keys
  ```
  The adversary subsequently authenticated via SSH using this injected key.
- **Answer:** `/home/svc_preview/.ssh/authorized_keys`

### Question 7: MySQL username used by edge-runner-02 to alter configuration

- **Prompt:** *Which MySQL username was used by edge-runner-02 when connecting to the production database and modifying configuration data?*
- **Analysis:** In `exports/ledger-01/connection-audit.tsv`, session connection ID 13 originated from edge-runner-02 and performed the modifications logged in `binlog.000003`. The authenticated MySQL user was `svc_cfg_apply`.
- **Answer:** `svc_cfg_apply`

### Question 8: MySQL error code returned during file-writing probe

- **Prompt:** *Before the production configuration was modified, a database operation was attempted to determine whether the server permitted file-writing through the database. What MySQL error code was returned?*
- **Analysis:** In `collection/edge-runner-02/logs/session-errors.log`, the attacker attempted file write operations (such as `SELECT ... INTO OUTFILE`), which the database rejected due to `--secure-file-priv`:
  ```text
  ERROR 1290 (HY000): The MySQL server is running with the --secure-file-priv option so it cannot execute this statement
  ```
- **Answer:** `1290`

### Question 9: External IP contacted by recurring outbound beacon connections

- **Prompt:** *After the intrusion, edge-runner-02 generated recurring outbound network connections to an external host. What external IP address was contacted?*
- **Analysis:** In `sensor/queries.log`, recurring DNS requests were resolved for `telemetry-gateway.c-laude.test`. Packet analysis in `sensor/dmz.pcap` verifies periodic TCP telemetry beacons to external address `203.0.113.91`.
- **Answer:** `203.0.113.91`

## Questions & Answers Summary

| # | Question Summary | Answer | Evidence File |
|---|---|---|---|
| 1 | Modified production settings count | `37` | `ledger-01/binlog.000003` |
| 2 | Scheduled systemd timer unit name | `agent-cache.timer` | `edge-runner-02/fs/file-timeline.txt` |
| 3 | Asset bucket configuration object path | `releases/2026.10/profile-r17.yaml` | `vault-02/audit.jsonl` |
| 4 | External IP sending preview request | `203.0.113.74` | `sensor/dmz.pcap` |
| 5 | Accepted Atlas service credential ID | `runtime-r17` | `atlas-01/auth-audit.jsonl` |
| 6 | Injected SSH key full filepath | `/home/svc_preview/.ssh/authorized_keys` | `edge-runner-02/fs/file-timeline.txt` |
| 7 | MySQL user performing writes | `svc_cfg_apply` | `ledger-01/connection-audit.tsv` |
| 8 | MySQL error code on blocked file write | `1290` | `edge-runner-02/logs/session-errors.log` |
| 9 | Outbound beacon external IP | `203.0.113.91` | `sensor/dmz.pcap` & `queries.log` |

## Result

Submitting all nine answers to the challenge service:

```text
After 37:
Correct.

[2/9] After the intrusion, a user-level scheduled task was established on edge-runner-02. What is the full filename of the systemd unit?
...
[9/9] After the intrusion, edge-runner-02 generated recurring outbound network connections to an external host. What external IP address was contacted?
Correct.

========================================
All 9 answers are correct.
========================================

Flag: kBxAc{y35_f1n477y_y0u_f0und_17_r1ght_175_r3l473d_t0_th3_4g3n71c_r4n50mw4r3_4tt4ck}
```

Flag:

```text
kBxAc{y35_f1n477y_y0u_f0und_17_r1ght_175_r3l473d_t0_th3_4g3n71c_r4n50mw4r3_4tt4ck}
```

## Reproduce

Run the Python script below to connect to the challenge instance and submit the verified answers:

```python
import socket
import time

HOST = "35.232.188.8"
PORT = 31337

answers = [
    "37",
    "agent-cache.timer",
    "releases/2026.10/profile-r17.yaml",
    "203.0.113.74",
    "runtime-r17",
    "/home/svc_preview/.ssh/authorized_keys",
    "svc_cfg_apply",
    "1290",
    "203.0.113.91",
]

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
time.sleep(0.5)
banner = s.recv(4096).decode(errors="ignore")
print(banner)

for i, ans in enumerate(answers, 1):
    print(f"[*] Sending answer [{i}/9]: {ans}")
    s.sendall(ans.encode() + b"\n")
    time.sleep(0.5)
    response = s.recv(4096).decode(errors="ignore")
    print(response)

s.close()
```
