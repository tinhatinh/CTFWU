# Patient Exfil — Forensics (Medium)

**Flag:** `H7CTF{6787b86cc777f426b9c0}` · Files: `capture (2).pcap`, 108,604 bytes, sha256 `3ab17689659f80efadceea1adc2eea5e9bddfcc3254ad85e89c4c75ee20bbb76`

## Challenge

A machine in the lab has been "talking to the outside" on a very slow schedule, raising no alert across six weeks.
The challenge gives a single network capture (`capture.pcap`) and asks for the secret message the attacker sent out.
The event's flag format is `H7CTF{...}`.

## Initial Analysis

Triage with `node ~/.qoder/skills/ctf-solve/scripts/triage.cjs`:

- `magic = libpcap capture (little-endian)`, `entropy = 5.084/8`, only 87 printable strings, `flag-pattern hits = 0`.
  Conclusion right away: no flag lies in the clear in the file, the information must be encoded or spread over several places.
- `survey.py` (scapy): 1260 packets over 148.31 seconds, all of them loopback `127.0.0.1`;
  1080 TCP packets + 180 DNS packets. No ICMP, no exotic protocol.
- Destination ports: `8080` (534 packets), `8443` (114 packets), the rest are ephemeral server-side ports, 4 packets each.
- HTTP: on 8080 only 5 request types repeat (`/assets/app.js` x28, `/api/health` x22, `/index` x20, `/` x19);
  on 8443 there are 19 `GET /api/v2/checkin` with `User-Agent: telemetry-agent/1.4` - this is the C2 heartbeat
  the challenge hints at ("very patient schedule"), but it is 100% uniform: every response is `ok`, 66 bytes long.
- DNS: 10 unique qnames, of which 7 are innocuous names (`pool.ntp.org`, `updates.ubuntu.com`, `mirror.lab.local`,
  `grafana.internal.lab`, `logging.googleapis.com`, `api.weather.example`, `cdn.jsdelivr.net`)
  and 3 odd ones sharing the same parent:

  ```
  00ja3ugvcgpm3doobx.sync.cdn-telemetry-lab.net.
  01mi4dmy3dg43tozru.sync.cdn-telemetry-lab.net.
  02gi3geoldgb6q.sync.cdn-telemetry-lab.net.
  ```

Suspicion: DNS tunneling. The domain `cdn-telemetry-lab.net` impersonates a telemetry service, the `00/01/02`
prefixes are fragment indices, and this is the classic way to slip past a dashboard because each query is just a DNS lookup.

## Exploit Chain

**Step 1 - Counting queries by parent domain.** Filter every DNS query whose `qname` ends in `.sync.cdn-telemetry-lab.net.`.
There are 12 packets, but only 3 unique labels: each label is sent in pairs (retries), looping over 2 rounds,
spread from second 5.60 to second 47.02 of the capture session. This is exactly the "low and slow": 12 queries in 148 seconds,
never dense enough to trip any threshold.

**Step 2 - Separating the index from the payload.** Regex `^(\d{2})([a-z2-7]+)\.sync\.cdn-telemetry-lab\.net$`.
The payload part only contains characters from `[a-z2-7]`, i.e. the base32 alphabet (no `0`,`1`,`8`,`9`).
This forces us to read `00/01/02` as an index rather than as data: folding the prefix in makes the decode impossible.

**Step 3 - Reassembling in index order and base32-decoding.**

```python
blob = "".join(chunks[k] for k in sorted(chunks))     # 00,01,02
pad  = blob.upper() + "=" * ((8 - len(blob) % 8) % 8)
data = base64.b32decode(pad)
```

```
blob (44 ký tự): ja3ugvcgpm3doobxmi4dmy3dg43tozrugi3geoldgb6q
decoded (27 byte): H7CTF{6787b86cc777f426b9c0}
```

**Step 4 - Verifying completeness.** 44 % 8 = 4, so the last chunk is shorter (12 characters instead of 16), exactly the
sign of the final fragment in a cut data stream; the result ends precisely with `}` and begins with `H7CTF{`.
Had the chunk order been wrong, or had a chunk still been missing, the output would be garbage and could not line up
the brackets like that. That is evidence the reassembly structure is correct, not speculation.

## Flag
Reproducible with:

```bash
python _ctf/patient-exfil/exploit.py "C:/Users/Administrator/Downloads/capture (2).pcap"
```

```
[+] 3 chunks: ['00', '01', '02']
[+] base32 blob (44 chars): ja3ugvcgpm3doobxmi4dmy3dg43tozrugi3geoldgb6q
[+] decoded 27 bytes -> b'H7CTF{6787b86cc777f426b9c0}'
[+] flag: H7CTF{6787b86cc777f426b9c0}
```
