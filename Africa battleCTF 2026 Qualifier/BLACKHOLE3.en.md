---
title: "Operation BLACKHOLE 3"
category: "Forensics"
tags: ["pcapng", "tshark", "http-flood", "tcp", "port-identification", "ssdp"]
solve_date: "2026-10-07T09:33:00+07:00"
language: "en"
points: 10
---

# Operation BLACKHOLE 3 — the non-standard port carrying the HTTP flood

**Answer:** `8000` · **Files:** shared `CTF1.pcapng`, 3 137 400 byte, sha256 `acc7bcb50585244b7f374e3402d157b605e9e5ef22f10ba223fce7e98536319b`

## Challenge

Question 3 of the series: name the TCP port the HTTP attack targets. The general triage of the capture
lives in [operation-blackhole-1](BLACKHOLE1.en.md).

## Analysis

All HTTP in the capture flows between exactly two addresses, `192.168.43.128 <-> 192.168.43.1`
(7 356 of 7 665 packets). There is no traffic on port 80 or 443, so the flooded service runs on a
non-standard port. The `conv,tcp` table lists 668 conversations, every one of the form
`192.168.43.128:<random source port> <-> 192.168.43.1:8000`.

## Approaches tried

1. **Port 80**: the capture contains not a single HTTP packet on 80.
2. **Port 1900 (SSDP)**: `http.request` also matches 45 `M-SEARCH` packets there, but they are **UDP**
   and are ordinary home-network service-discovery broadcasts, not the TCP flood. Eliminated from the
   scope of "TCP port".
3. **Source ports 42302, 42304, …**: these change per connection (668 distinct values), which is the
   signature of the client side, not of the called service.

## Solution

**Step 1 - Count destination ports of HTTP requests over TCP.**

```bash
tshark -r CTF1.pcapng -Y 'http.request && tcp' \
  -T fields -e tcp.dstport | sort | uniq -c
```

```text
    668 8000
```

A single port, with no second value present.

**Step 2 - Separate the UDP part to avoid confusing it with SSDP.**

```bash
tshark -r CTF1.pcapng -Y 'http.request && udp' \
  -T fields -e udp.dstport | sort | uniq -c
```

```text
     45 1900
```

The remaining 45 requests (which together with 668 make up 713) sit on UDP/1900, as eliminated above.

**Step 3 - Verify from the responding side.** `http.response` yields 667 `200` and one `404`, all with
`tcp.srcport == 8000` and `ip.src == 192.168.43.1`; the response count matches the number of SYN
connections to that same port.

## Result

```text
8000
```

## Reproduce

```bash
cd "operation-blackhole-3"
tshark -r CTF1.pcapng -Y 'http.request && tcp' -T fields -e tcp.dstport | sort | uniq -c
tshark -r CTF1.pcapng -Y 'http.request && udp' -T fields -e udp.dstport | sort | uniq -c
```
