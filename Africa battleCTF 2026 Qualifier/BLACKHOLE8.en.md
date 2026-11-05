---
title: "Operation BLACKHOLE 8"
category: "Forensics"
tags: ["pcap", "tshark", "ddos", "http-headers", "referer", "packet-analysis"]
solve_date: "2026-10-07T09:40:00+07:00"
language: "en"
points: 30
---

# Operation BLACKHOLE 8 — Flag hidden in the Referer header

**Flag:** `CTF{UF0N3t_DD0S_4n4lys1s_2026}` · **Files:** shared `CTF1.pcapng`, 3 137 400 byte, sha256 `acc7bcb50585244b7f374e3402d157b605e9e5ef22f10ba223fce7e98536319b`

## Challenge

The last question of the series: recover the flag hidden in an HTTP header. Unlike the previous six
questions, the answer here carries a wrapper, and the prefix is `CTF{`, not `battleCTF{`.

## Analysis

Among the 52 requests using `curl/8.21.0`, 50 target `/?debug=N` and contain the relevant header. URI and UA alone do not establish whether these requests were sent manually or by a script.

## Approaches tried

1. **Grep for suggestive strings**: `frame contains "battle"`, `"flag"`, `"Flag"`, `"FLAG"` all return
   **0** packets. The flag does not use the event prefix and does not appear literally as the word "flag".
   Direct grep is ruled out.
2. **A custom `X-...` header**: `frame contains "X-"` matches exactly one frame (6192), but the hex dump
   shows `58 2d` at packet offset 0x12-0x13, i.e. the **IP checksum** field, not HTTP payload:
   `45 00 00 3c 0a bd 40 00 40 06 58 2d c0 a8 2b 80`.
3. **Flag in a response body**: `http.response` contains only 667 `200` responses with an identical
   `Content-Length: 3114` plus one `404`; no response contains `CTF`.
4. **Flag in the URI**: the URI distribution only contains `/`, `/?debug=1..50` and `/fichier-inexistant`.

## Solution

**Step 1 - Grep for the flag's real prefix.** The string `CTF` appears in 50 frames:

```bash
tshark -r CTF1.pcapng -Y 'frame contains "CTF"' \
  -T fields -e frame.number | wc -l
```

```text
50
```

**Step 2 - Inspect those 50 frames.**

```bash
tshark -r CTF1.pcapng -Y 'http.request && http.referer != ""' \
  -T fields -e frame.number -e http.request.uri -e http.user_agent -e http.referer | head -3
```

```text
6757    /?debug=1       curl/8.21.0   http://ctf.local/CTF{UF0N3t_DD0S_4n4lys1s_2026}
6768    /?debug=2       curl/8.21.0   http://ctf.local/CTF{UF0N3t_DD0S_4n4lys1s_2026}
6779    /?debug=3       curl/8.21.0   http://ctf.local/CTF{UF0N3t_DD0S_4n4lys1s_2026}
```

The header carrying the flag is `Referer`, a client-to-server header — the attacker attached the flag to
its own requests; the service is not leaking it.

**Step 3 - Verify uniqueness.**

```bash
tshark -r CTF1.pcapng -Y 'http.request && http.referer != ""' \
  -T fields -e http.referer | sort -u
```

```text
http://ctf.local/CTF{UF0N3t_DD0S_4n4lys1s_2026}
```

Exactly one non-empty `Referer` value exists in the whole capture, repeated identically 50 times, and those
50 frames are precisely the 50 frames that matched `"CTF"` in Step 1. Preserve `UF0N3t_DD0S_4n4lys1s_2026` exactly as found in the header.

## Result

```text
CTF{UF0N3t_DD0S_4n4lys1s_2026}
```

Confirmation status: extracted directly from packets; the flag was submitted and accepted.

## Reproduce

```bash
cd "operation-blackhole-8"
tshark -r CTF1.pcapng -Y 'http.request && http.referer != ""' -T fields -e http.referer | sort -u
tshark -r CTF1.pcapng -Y 'frame contains "CTF"' -T fields -e frame.number | wc -l
```
