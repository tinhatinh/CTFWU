---
title: "Operation BLACKHOLE 4"
category: "Forensics"
tags: ["pcapng", "tshark", "http-method", "get-flood", "http-flood", "network-forensics"]
solve_date: "2026-10-07T09:34:00+07:00"
language: "en"
points: 10
---

# Operation BLACKHOLE 4 — the GET method behind every flood request

**Answer:** `GET` · **Files:** shared `CTF1.pcapng`, 3 137 400 byte, sha256 `acc7bcb50585244b7f374e3402d157b605e9e5ef22f10ba223fce7e98536319b`

## Challenge

Question 4 of the series: which HTTP method is used for flooding. The general triage lives in
[operation-blackhole-1](BLACKHOLE1.en.md).

## Analysis

The capture contains 668 TCP connections to `192.168.43.1:8000`, each carrying one HTTP request. There are 667 `200 OK` responses and one `404`. Count `http.request.method` within these connections to identify the method.

## Approaches tried

1. **`POST`:** absent from the method count for TCP requests on port 8000.
2. **`M-SEARCH`**: appears 45 times but is SSDP over UDP/1900, not part of the TCP flood (see
   [operation-blackhole-3](BLACKHOLE3.en.md)).
3. **`HEAD`:** absent from the filtered requests. This follows from the method field, rather than the response-body size.

## Solution

**Step 1 - Count HTTP methods across the whole capture.**

```bash
tshark -r CTF1.pcapng -Y 'http.request' \
  -T fields -e http.request.method | sort | uniq -c | sort -rn
```

```text
    668 GET
     45 M-SEARCH
```

**Step 2 - Restrict to the flood (TCP, port 8000).**

```bash
tshark -r CTF1.pcapng -Y 'http.request && tcp.dstport==8000' \
  -T fields -e http.request.method | sort | uniq -c
```

```text
    668 GET
```

All 668 flood requests are `GET`; no second method exists.

**Step 3 - Verify against real request samples.** Read the request line of the first few connections
(using `http.request.method` + `http.request.uri`; note that `http.request.line` holds the headers, not
the request line):

```bash
tshark -r CTF1.pcapng -Y 'http.request && tcp.dstport==8000' \
  -T fields -e frame.number -e http.request.method -e http.request.uri -e http.request.version | head -3
```

```text
4       GET     /       HTTP/1.1
15      GET     /       HTTP/1.1
26      GET     /       HTTP/1.1
```

The URI distribution shows 617 requests as `GET /`, 50 as `GET /?debug=N` and one as
`GET /fichier-inexistant`; all of them are still `GET`.

## Result

```text
GET
```

## Reproduce

```bash
cd "operation-blackhole-4"
tshark -r CTF1.pcapng -Y 'http.request' -T fields -e http.request.method | sort | uniq -c | sort -rn
tshark -r CTF1.pcapng -Y 'http.request && tcp.dstport==8000' -T fields -e frame.number -e http.request.method -e http.request.uri | head -3
```
