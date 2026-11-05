---
title: "Operation BLACKHOLE 6"
category: "Forensics"
tags: ["pcap", "tshark", "ddos", "conversations", "icmp", "http-flood"]
solve_date: "2026-10-07T09:37:00+07:00"
language: "en"
points: 15
---

# Operation BLACKHOLE 6 — DDoS duration from conversations

**Answer:** `83` · **Files:** shared `CTF1.pcapng`, 3 137 400 byte, sha256 `acc7bcb50585244b7f374e3402d157b605e9e5ef22f10ba223fce7e98536319b`

## Challenge

Question 6 of the series: the duration of the attack in seconds. General triage is in
`operation-blackhole-1`.

## Analysis

The capture is 1060.814 s long, but most of it is background (SSDP, mDNS, NTP, ARP). The attack traffic
concentrates on a single address pair and ends early:

```text
192.168.43.128  <-> 192.168.43.1   3344 2407 kB   4012 429 kB   7356 2836 kB   0.000000000   83.2457
```

`Relative Start = 0` marks the pair’s first captured packet, not necessarily the start of the incident. `Duration = 83.2457 s` measures the interval between this pair’s first and last captured packets.

## Approaches tried

1. **`Capture duration` = 1060.814 s**: that is the file length, including ~16 minutes of background
   traffic after the attack stopped.
2. **Cut the window to the HTTP flood only**: the last packet on `tcp.port==8000` sits at `t = 79.154051`
   and the first at `t = 0`, giving `79.154` s. This describes the flood more precisely but is **not the
   answer the author accepted**; it drops the 5 ICMP packets from the same attacker that follow
   immediately. Eliminated because it disagrees with Wireshark's statistics table.
3. **Sum the lengths of the flood bursts**: traffic arrives in two waves (`0 → 4.030` and
   `69.909 → 79.154`, separated by 65.88 s of silence), so total "time with attack packets" is only ~13 s.
   Nothing in the question suggests this method.

## Solution

**Step 1 - Take the conversations table as the reference.** `Duration` for the `.128 <->.1` pair in
Statistics → Conversations (the same data `tshark` prints):

```bash
tshark -r CTF1.pcapng -q -z conv,ip | sed -n '6p'
```

```text
192.168.43.128       <-> 192.168.43.1            3344 2407 kB      4012 429 kB       7356 2836 kB       0.000000000        83.2457
```

**Step 2 - Identify what occupies 79.154 → 83.2457.** This is what decides between 79 and 83:

```bash
tshark -r CTF1.pcapng -Y 'ip.src==192.168.43.128 && icmp' \
  -T fields -e frame.time_relative -e icmp.type -e icmp.ident -e icmp.seq
```

```text
79.156784851        8       60542   1
80.173473554        8       60542   2
81.197433216        8       60542   3
82.221454444        8       60542   4
83.245389592        8       60542   5
```

Five ICMP echoes (type 8) with the same `ident`, spaced ~1.02 s apart, sent from the attacker to the
target right after the flood stops. `83.245389592 - 0 = 83.2454` is close to the `Duration` value in Step 1.

**Step 3 - Take the integer duration.** The address-pair interval includes HTTP and the later ICMP packets, spanning about 83.25 s. The answer `83` was accepted. Restricting the measurement to TCP/8000 gives 79.154 s; these values describe different scopes.

## Result

```text
83
```

Submitted on ctf.bugpwn.com and accepted. The `79.154` s measurement (HTTP flood only) is technically
correct but is not how the author grades — see the note in the event `README.md`.

## Reproduce

```bash
cd "operation-blackhole-6"
tshark -r CTF1.pcapng -q -z conv,ip | sed -n '6p'
tshark -r CTF1.pcapng -Y 'ip.src==192.168.43.128 && icmp' -T fields -e frame.time_relative -e icmp.type -e icmp.ident -e icmp.seq
tshark -r CTF1.pcapng -Y 'tcp.port==8000' -T fields -e frame.time_relative | sed -n '1p;$p'
```
