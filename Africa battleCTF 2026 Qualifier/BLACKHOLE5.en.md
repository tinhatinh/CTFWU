---
title: "Operation BLACKHOLE 5"
category: "Forensics"
tags: ["pcapng", "tshark", "user-agent", "curl", "http-flood", "network-forensics"]
solve_date: "2026-10-07T09:36:00+07:00"
language: "en"
points: 10
---

# Operation BLACKHOLE 5 — the curl User-Agent carrying the debug requests

**Answer:** `curl/8.21.0` · **Files:** shared `CTF1.pcapng`, 3 137 400 byte, sha256 `acc7bcb50585244b7f374e3402d157b605e9e5ef22f10ba223fce7e98536319b`

## Challenge

Question 5 of the series: which User-Agent is associated with the malicious requests. General triage is
in [operation-blackhole-1](BLACKHOLE1.en.md).

## Analysis

The 668 flood requests use **108 distinct User-Agents**, showing that requests use several UA strings. The way they were generated is not established by this count.
The frequency distribution is very flat: the most common browser UA appears only 12 times, most others
between 2 and 10. "Most frequent UA" is therefore not a reliable discriminator when looking only at
`Mozilla/5.0...` strings.

The real outlier is the format of the string itself: exactly one UA does not look like a browser.

## Approaches tried

1. **Pick the most frequent `Mozilla/5.0` UA**: the maximum is 12/668 (1.8%), followed by 10, 10, 10, 9…
   There is no statistical gap; any choice within this group is arbitrary.
2. **`Chromium/146.0.7680.179 Windows` and `Chromium/128.0.6613.138 Windows`** (20 occurrences each):
   these are malformed UA strings, yet each is only 3% of the traffic and still part of the flood's
   random pool, with no specific suspicious behaviour attached.
3. **`Downloader`**: that is the User-Agent of the `0byte.exe` binary in the reverse challenge of the same
   event; it does not appear in this capture.

## Solution

**Step 1 - Count User-Agents within the flood.**

```bash
tshark -r CTF1.pcapng -Y 'http.request && tcp.dstport==8000' \
  -T fields -e http.user_agent | sort | uniq -c | sort -rn | head -8
```

```text
     52 curl/8.21.0
     12 Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1
     10 Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Vivaldi/7.0.3495.18 Chrome/134.0.0.0 Safari/537.36
     10 Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36
     10 Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36
     10 Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36
```

`curl/8.21.0` leads with 52 occurrences, above the Chromium strings occurring 20 times, and identifies a command-line client.

**Step 2 - Bind the UA to behaviour.** What does this UA request?

```bash
tshark -r CTF1.pcapng -Y 'http.request && http.user_agent=="curl/8.21.0"' \
  -T fields -e http.request.uri | sed 's/=[0-9][0-9]*$/=N/' | sort | uniq -c
```

```text
      1 /
     50 /?debug=N
      1 /fichier-inexistant
```

50 of them are the sequence `GET /?debug=1..50`, and each carries
`Referer: http://ctf.local/CTF{UF0N3t_DD0S_4n4lys1s_2026}` — the flag of question 8. The
`/fichier-inexistant` request receives the `404`, the only unsuccessful request in the whole capture.

**Step 3 - Verification.** `curl/8.21.0` appears in 52 of 668 requests and accompanies the 50 `/?debug=N` requests carrying the flag header. This association supports the answer; frequency alone does not establish what every request does.

## Result

```text
curl/8.21.0
```

## Reproduce

```bash
cd "operation-blackhole-5"
tshark -r CTF1.pcapng -Y 'http.request && tcp.dstport==8000' -T fields -e http.user_agent | sort | uniq -c | sort -rn | head
tshark -r CTF1.pcapng -Y 'http.request && http.user_agent=="curl/8.21.0"' -T fields -e http.request.uri | sort | uniq -c
```
