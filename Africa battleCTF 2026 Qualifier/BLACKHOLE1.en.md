---
title: "Operation BLACKHOLE 1"
category: "Forensics"
tags: ["pcapng", "tshark", "ddos", "http-flood", "tcp-flags", "network-forensics"]
solve_date: "2026-10-07T09:30:00+07:00"
language: "en"
points: 5
---

# Operation BLACKHOLE 1 — tracking the flood source by volume direction

**Answer:** `192.168.43.128` · **Files:** `CTF1.pcapng`, 3 137 400 byte, sha256 `acc7bcb50585244b7f374e3402d157b605e9e5ef22f10ba223fce7e98536319b`

## Challenge

Acme Corp was hit by a DDoS attack; the SOC team recorded all traffic during the incident into
`CTF1.pcapng`. Question 1 asks for the IP address of the attacking machine. All 8 questions of the
series share this single capture, so the triage below is reused by the later writeups.

## Analysis

```text
Number of packets:   7665
Capture duration:    1060.814057483 seconds
Earliest packet time: 2026-09-17 17:40:33.888190960
```

The endpoint table shows that almost all traffic revolves around just two addresses:

```text
                       | Packets | |  Bytes  | | Tx Packets | | Tx Bytes | | Rx Packets | | Rx Bytes |
192.168.43.1                 7463   2857 kB          3450      2427 kB           4013      429 kB
192.168.43.128               7394   2841 kB          4032      431 kB            3362      2410 kB
239.255.255.250                53    14 kB             0        0 bytes            53       14 kB
84.77.195.114                  30  2700 bytes         15     1350 bytes           15     1350 bytes
```

Both candidates carry roughly 7.4k packets, so the packet count alone cannot separate them. The
difference is in the **direction of volume**: `192.168.43.1` sends 2 427 kB but receives only 429 kB,
so it is the responder; `192.168.43.128` sends 431 kB and receives 2 410 kB, so it is the initiator
that absorbs the replies. "one side issues small requests, the other returns bulk data" is the shape
of a flood aimed at a single service.

## Approaches tried

1. **`84.77.195.114` is an off-network attacker**: only 30 packets, all NTP in both directions
   (15 sent, 15 received) spread evenly over 521 s. No evidence of flooding.
2. **`192.168.43.1` is the attacker because it has the most packets**: wrong direction. This endpoint
   accepts 668 TCP connections and emits 667 HTTP `200 OK` responses, i.e. it plays the victim service.

3. **Multicast addresses (`239.255.255.250`, `224.0.0.22/251/252`)**: SSDP/IGMP announcements typical of
   a home network, not unicast sources.

## Solution

**Step 1 - Aggregate conversations to find the dominant pair.** The IPv4 conversations table shows the pair with the largest packet count:

```bash
tshark -r CTF1.pcapng -q -z conv,ip | head -8
```

```text
192.168.43.128  <-> 192.168.43.1   3344 2407 kB   4012 429 kB   7356 2836 kB   0.000000000   83.2457
192.168.43.1    <-> 239.255.255.250   0  0 bytes     52  14 kB     52   14 kB   6.362195476  534.8808
```

7 356 of the 7 665 packets belong to this pair, and it starts exactly at capture `t = 0`.

**Step 2 - Establish direction with TCP flags.** A SYN without ACK is a connection open, sent only by
the active side:

```bash
tshark -r CTF1.pcapng -Y 'tcp.flags.syn==1 && tcp.flags.ack==0 && tcp.dstport==8000' \
  -T fields -e ip.src | sort | uniq -c
```

```text
    668 192.168.43.128
```

All 668 connection attempts toward port 8000 are initiated by `192.168.43.128`; `192.168.43.1` only
appears with SYN-ACK. Combined with the volume direction from the Initial Analysis, the attack source
is `192.168.43.128`.

**Step 3 - Verification.** The measurements identify the same address: (a) it is the side
that sends fewer bytes yet creates all 668 connections; (b) it receives 2 410 kB of reply content;
(c) the post-flood ICMP echo probes also originate from it, so one host drives both activities.

## Result

```text
192.168.43.128
```

Submitted on ctf.bugpwn.com and accepted.

## Reproduce

```bash
cd "operation-blackhole-1"
bash triage.sh CTF1.pcapng          # toan bo so lieu dung cho 8 cau
```

Requires Wireshark ≥ 4.x, or `tshark`/`capinfos` on `PATH`.
