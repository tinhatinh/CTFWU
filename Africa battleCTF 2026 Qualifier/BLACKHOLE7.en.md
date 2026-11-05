---
title: "Operation BLACKHOLE 7"
category: "Forensics"
tags: ["pcap", "tshark", "ddos", "http-requests", "ssdp", "protocol-hierarchy"]
solve_date: "2026-10-07T09:38:00+07:00"
language: "en"
points: 15
---

# Operation BLACKHOLE 7 — Counting HTTP requests in the capture

**Answer:** `713` · **Files:** shared `CTF1.pcapng`, 3 137 400 byte, sha256 `acc7bcb50585244b7f374e3402d157b605e9e5ef22f10ba223fce7e98536319b`

## Challenge

Question 7 of the series: how many HTTP requests the capture contains. The phrase "does the capture
contain" asks about the whole file, not only the flood.

## Analysis

The protocol hierarchy shows two relevant lines:

```text
  ip
    tcp
      http                             frames:1336 bytes:2324378
        data-text-lines                frames:668  bytes:2121586
    udp
      ssdp                             frames:45   bytes:9315
```

`http` covers 1336 frames. If every request is paired with one response, 1336/2 = 668 requests, and the
`data-text-lines: 668` count matches the number of responses carrying a body. However, Wireshark dissects
SSDP using the HTTP dissector's own fields, so a higher-level request counter will exceed 668.

## Approaches tried

1. **668** (requests on TCP port 8000): correct for the flood, but it omits the 45 SSDP requests that
   Wireshark still flags as `http.request`. This would be the answer if the question asked "of the
   attack", not "of the capture".
2. **1336**: counts requests and responses together.
3. **7665**: the total packet count of the file, including ARP, IPv6, IGMP and pure TCP ACK frames.

## Solution

**Step 1 - Request counter over the whole capture.**

```bash
tshark -r CTF1.pcapng -Y 'http.request' 2>/dev/null | wc -l
```

```text
713
```

**Step 2 - Decompose the total to be sure 713 is not a double count.**

```bash
tshark -r CTF1.pcapng -Y 'http.request' \
  -T fields -e http.request.method | sort | uniq -c
```

```text
    668 GET
     45 M-SEARCH
```

668 + 45 = 713. Checking per transport confirms the surplus is UDP:

```bash
tshark -r CTF1.pcapng -Y 'http.request && tcp' -T fields -e tcp.dstport | sort | uniq -c
tshark -r CTF1.pcapng -Y 'http.request && udp' -T fields -e udp.dstport | sort | uniq -c
```

```text
    668 8000
     45 1900
```

**Step 3 - Verify there is no double counting.** Count the literal `GET ` bytes inside TCP payloads:

```bash
tshark -r CTF1.pcapng -Y 'tcp contains "GET "' 2>/dev/null | wc -l
```

```text
668
```

668 frames contain a `GET ` line, matching the HTTP-over-TCP request count exactly, cross-checking the dissector count for this capture. Counting frames containing a string is not a general validation of every reassembly or retransmission case.

## Result

```text
713
```

Confirmation status: measured directly from the capture; `713` was submitted and accepted. The `668` candidate
(TCP flood only) is eliminated because it misses the 45 SSDP requests the HTTP dissector still counts.

## Reproduce

```bash
cd "operation-blackhole-7"
tshark -r CTF1.pcapng -Y 'http.request' | wc -l
tshark -r CTF1.pcapng -Y 'http.request' -T fields -e http.request.method | sort | uniq -c
tshark -r CTF1.pcapng -Y 'tcp contains "GET "' | wc -l
```
