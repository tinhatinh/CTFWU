---
title: "Last Packet"
category: "Forensics"
tags: ["pcap", "debug-leak"]
solve_date: "2026-10-11T04:06:00+07:00"
language: "en"
---

# Last Packet

**Flag:** `isfcr{l33t_c0d3_tw0_sum_f0und}`  
**Artifact:** `challenge2.pcap` (13,348 bytes)

| Artifact | SHA-256 |
|---|---|
| `challenge2.pcap` | `b6f1c693be40d65df509f5830dbbacd02a2cc7f4e2418444d8a3c9fb3afb8eae` |

## Challenge

A developer noticed strange behavior from an internal microservice during a debugging session. Security captured the network traffic. Identify the relevant conversation and recover the leaked secret.

## Initial Analysis

The supplied PCAP contains 112 packets, including DNS lookups and several ordinary HTTP exchanges. The relevant internal hosts are `10.0.1.50` (client), `10.0.1.100:8080` (user service), and `10.0.1.200:9090` (Two Sum API).

To narrow down the traffic, open `challenge2.pcap` in Wireshark and apply:

```wireshark
http || tcp.port == 9090
```

The suspicious conversation is a debug-mode API call to `twosum-api.internal.corp`. Packet **56** contains the request; packet **58** contains the response, both on the TCP connection `10.0.1.50:52042` → `10.0.1.200:9090`.

## Exploitation Chain

1. **Locate the debug request.** Packet 56 is an HTTP POST to the Two Sum endpoint. It explicitly enables debug mode and identifies the developer:

   ```http
   POST /api/v1/twosum/solve HTTP/1.1
   Host: twosum-api.internal.corp:9090
   X-Debug-Mode: enabled
   X-Developer: raj.kumar
   Content-Type: application/json

   {"nums": [24, 42, 7, 15], "target": 66}
   ```

2. **Inspect the response for leaked internal state.** Packet 58 is an HTTP `200 OK` response with `X-Debug-Level: VERBOSE` and `X-Service: twosum-api-v2.3.1`. Its JSON payload includes a `debug` object that exposes an `internal_key`:

   ```json
   {
     "status": "ok",
     "result": [0, 1],
     "debug": {
       "internal_key": "4b7a456b495441354c6e46784e68306863695a7848545931636830784e7938644a4849334c43592f",
       "enc": "xor",
       "cache_hit": false,
       "exec_time_ms": 12,
       "node": "worker-3",
       "build": "twosum-api-v2.3.1-debug",
       "heap_mb": 247,
       "gc_pause_ms": 3
     }
   }
   ```

   A service response should not expose internal key material. The `enc: xor` value also hints at the final transformation.

3. **Decode the key through three layers.** First, hex-decode the `internal_key` string to obtain the ASCII text:

   ```text
   KzEkITA5LnFxNh0hciZxHTY1ch0xNy8dJHI3LCY/
   ```

   This is Base64. Decoding it yields the following 30 bytes, shown in hexadecimal to preserve the non-printable bytes:

   ```text
   2b31242130392e7171361d217226711d3635721d31372f1d2472372c263f
   ```

   XOR every decoded byte with `0x42`. The result is a UTF-8 flag:

   ```text
   isfcr{l33t_c0d3_tw0_sum_f0und}
   ```

## Flag

`isfcr{l33t_c0d3_tw0_sum_f0und}`

The secret was recovered directly from the HTTP debug response in the capture. The three decoding layers reproduce the flag exactly; submission to a CTF service was not verified here.

## Reproduce

Open the PCAP in Wireshark, filter for `tcp.port == 9090`, and select frame 58. Use **Follow → TCP Stream** to inspect the HTTP request/response and copy the `debug.internal_key` value. Then run the following standalone Python 3 code (standard library only):

```python
import base64

internal_key = (
    "4b7a456b495441354c6e46784e68306863695a7848545931636830784e793864"
    "4a4849334c43592f"
)

step1 = bytes.fromhex(internal_key)
step2 = base64.b64decode(step1, validate=True)
flag = bytes(byte ^ 0x42 for byte in step2).decode("ascii")

assert flag == "isfcr{l33t_c0d3_tw0_sum_f0und}"
print("FLAG", flag)
```

Expected output:

```text
FLAG isfcr{l33t_c0d3_tw0_sum_f0und}
```
