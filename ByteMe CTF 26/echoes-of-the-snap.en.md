---
title: "Echoes of the Snap"
category: "Forensics"
tags: ["dns-txt", "stream-reassembly", "hex-decoding", "pcap-summary"]
solve_date: "2026-10-09"
language: "en"
---

# Echoes of the Snap

**Flag:** `OWASP{3ch03s_0f_th3_sn4p_r3m41n}`
**Artifact:** `capture.txt` (136 B as recorded) — a text summary of a packet capture, not a pcap file. Author: Pratik Jadhav.

## Challenge

The challenge title is taken from the platform's solved table; the description that was recorded for it reads:

```text
A network capture contains several streams, but one contains fragmented DNS TXT data carrying a hidden message.
```

Medium, 200 points. The statement sets three constraints: many streams, one stream that matters, and DNS TXT data that is fragmented and must be reassembled.

The actual input is not a trace but a two-line note:

```text
stream 31: DNS TXT query
stream 31 TXT chunks: 4f574153507b3363683033735f30665f7468335f736e34705f72336d34316e7d
```

## Analysis

What sets this apart from a normal pcap challenge: there is no packet to filter and no `tcp.stream` to follow. The artifact is already the output of the locating step — it names the stream number (31), the record type (DNS TXT), and it records the data of the fragments. The remaining work is reassembly and decoding.

`stream 31 TXT chunks:` lists the TXT fragments of stream 31. The summary records them already concatenated, with the per-fragment boundaries not preserved; the joined string is 64 hex characters, i.e. 32 bytes. All 64 characters are valid hex digits, so no fragment was corrupted during the join.

The input is a text summary, not the original PCAP. The hex decoding is reproducible; stream attribution and individual TXT fragment boundaries cannot be checked from this input.

## Solution

Joining the chunks and hex-decoding:

```console
$ python -c "h='4f574153507b3363683033735f30665f7468335f736e34705f72336d34316e7d'; print('len:', len(h)); print(bytes.fromhex(h).decode())"
```

Recorded output:

```text
len: 64
OWASP{3ch03s_0f_th3_sn4p_r3m41n}
```

The printed 64 is the length of the concatenated hex string, which decodes to 32 ASCII bytes; the decoded string is exactly 32 characters long and starts with `4f 57 41 53 50 7b` = `OWASP{`. There is no padding byte and no character outside the printable range.

Validation script, independent of the artifact:

```python
HEX = "4f574153507b3363683033735f30665f7468335f736e34705f72336d34316e7d"

raw = bytes.fromhex(HEX)
print("hex chars :", len(HEX))
print("bytes     :", len(raw))
print("printable :", all(32 <= b < 127 for b in raw))
print("text      :", raw.decode("ascii"))
```

```text
hex chars : 64
bytes     : 32
printable : True
text      : OWASP{3ch03s_0f_th3_sn4p_r3m41n}
```

## Result

```text
OWASP{3ch03s_0f_th3_sn4p_r3m41n}
```

The stream-31 hex string in the summary decodes to the flag. The original PCAP is unavailable for packet-level verification.

## Reproduce

Python 3 only (`bytes.fromhex`), no external libraries and no PCAP tooling.

```console
$ python -c "h='4f574153507b3363683033735f30665f7468335f736e34705f72336d34316e7d'; print(len(h), bytes.fromhex(h).decode())"
```

With `capture.txt` on disk, the `stream 31 TXT chunks:` line supplies exactly the hex string used above. Given a real pcap instead, the locating step becomes `tshark -r <file> -Y "dns.txt" -T fields -e frame.number -e dns.qry.name -e dns.txt`, after which the `dns.txt` values of one query are concatenated and hex-decoded as above; those two steps are not applicable to this challenge's artifact because it contains no trace.
