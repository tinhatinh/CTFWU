---
title: "Operation BLACKHOLE 2"
category: "Forensics"
tags: ["pcapng", "tshark", "ddos", "http-flood", "tcp-flags", "network-forensics"]
solve_date: "2026-10-07T09:32:00+07:00"
language: "en"
points: 5
---

# Operation BLACKHOLE 2 — naming the flooded host from SYN destinations

**Answer:** `192.168.43.1` · **Files:** shared `CTF1.pcapng`, 3 137 400 byte, sha256 `acc7bcb50585244b7f374e3402d157b605e9e5ef22f10ba223fce7e98536319b`

## Challenge

Same capture `CTF1.pcapng` from the Acme Corp DDoS incident. Question 2 asks for the IP address of the
target. The full triage of the capture lives in
[operation-blackhole-1](BLACKHOLE1.en.md); this writeup only covers identifying the
called side.

## Analysis

The endpoint table leaves exactly two candidates, and the direction of volume already says who answers:

```text
                       | Packets | |  Bytes  | | Tx Packets | | Tx Bytes | | Rx Packets | | Rx Bytes |
192.168.43.1                 7463   2857 kB          3450      2427 kB           4013      429 kB
192.168.43.128               7394   2841 kB          4032      431 kB            3362      2410 kB
```

`192.168.43.1` sends 2 427 kB while receiving only 429 kB. A host returning roughly 5.6 times the data
it takes in is serving content, not issuing requests.

## Approaches tried

1. **`192.168.43.128` is the target because it appears in every conversation**: wrong role. This host
   sends the 668 SYN packets and absorbs the responses, i.e. it is the attacker (see question 1).
2. **`192.168.43.254` as gateway/target**: only 5 packets, including DHCP/ARP broadcast traffic. No TCP
   connection is addressed to it.
3. **Broadcast/multicast addresses `.255`, `224.0.0.x`, `239.255.255.250`**: SSDP, mDNS, IGMP and DHCP
   broadcasts typical of a home network; they never accept unicast connections.

## Solution

**Step 1 - Read the destination of the connection-open packets.** A SYN without ACK names the callee:

```bash
tshark -r CTF1.pcapng \
  -Y 'tcp.flags.syn==1 && tcp.flags.ack==0 && tcp.dstport==8000' \
  -T fields -e ip.dst | sort | uniq -c
```

```text
    668 192.168.43.1
```

All 668 connection attempts target the same address.

**Step 2 - Confirm the service role from the responding side.** If `192.168.43.1` is the target, it must
be the side emitting HTTP responses:

```bash
tshark -r CTF1.pcapng -Y 'http.response' \
  -T fields -e ip.src -e http.response.code | sort | uniq -c
```

```text
    667 192.168.43.1 200
      1 192.168.43.1 404
```

Every one of the capture's 668 HTTP responses originates from this address, matching the connection
count from Step 1 exactly.

**Step 3 - Verification.** Two independent measurements (outgoing TCP flags, incoming HTTP status codes)
return the same address and the same count of 668, confirming the client and server roles in this capture.

## Result

```text
192.168.43.1
```

## Reproduce

```bash
cd "operation-blackhole-2"
tshark -r CTF1.pcapng \
  -Y 'tcp.flags.syn==1 && tcp.flags.ack==0 && tcp.dstport==8000' -T fields -e ip.dst | sort | uniq -c
tshark -r CTF1.pcapng -Y 'http.response' \
  -T fields -e ip.src -e http.response.code | sort | uniq -c
```
