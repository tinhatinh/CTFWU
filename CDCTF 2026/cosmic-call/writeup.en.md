# Cosmic Call - Scanning / NTA / Crypto (797 points)

**Flag:** `cdctf{W3_@rE_n0T_AL0n3_OuT_h3r3?_5d68a0e7}` · **Points:** 797 · **Authors:** b0b, adlee7 (CDCTF)
**Artifact:** a ttyd terminal on the relay box (`player@router`), nothing to download

## The task

"ping... ping... there's something out there... I sure hope Command didn't reuse the CTR Nonce".
We get a shell on the relay and have to work out what is talking on the network and what it says.

## First look

The relay acts as the **router** between two containers on the instance's own docker network:

```text
player@router:~$ ip -o addr | cut -c1-90; ip neigh
1: lo    ...
2: eth0  inet 172.25.191.2/24
3: eth1  inet 172.25.190.2/24      -> Command   172.25.190.3:41100   REACHABLE
4: eth2  inet 172.25.189.2/24      -> satellite 172.25.189.3:41200   REACHABLE
```

`tcpdump` works unprivileged, so the whole conversation is in reach. Observed packet structure:

```text
REQ  172.25.190.3:41100 -> 172.25.189.3:41200   payload 53 B, one packet every 4.000 s
REP  172.25.189.3:41200 -> ...                  payload 10 B (pong), 226/227/228 B (telemetry),
                                                21 B and 25 B (errors), 53 B (the flag)
```

Every payload = **6 cleartext header bytes** + ciphertext:

```text
REQ  10 65 | c0 12 | 00 2e | 61 8f 8e ae ...        marker | 16-bit BE counter | 00 (len(ct)-1)
REP  00 64 | c0 55 | 00 0e | 77 89 9d da ...
```

The counter rises by exactly one per REQ (`c012` at 01:22:59.38 -> `c137` at 01:42:31.63 = +293 steps
/ 1172 s = 4.000 s per step) and is **not encrypted**, so editing it does not shift keystream alignment.
A REP carries the satellite's own monotonic counter; it never echoes the REQ counter.

The captured packets reuse an 8-byte keystream. Recovering it from known plaintext allows other messages to be decrypted.

## Routes ruled out

1. **Mining ttyd traffic on port 7681.** `grep -aoE '[ -~]{12,}' /tmp/all.pcap | sort -u` returns only the
   static xterm.js/zmodem/trzsz bundle plus `GET / Host: 127.0.0.1:7681`. No terminal I/O is captured.
2. **Looking for the flag in the shipped pcaps.** `grep -ac cdctf` = 0 in both `all.pcap` and `pass.pcap`;
   after removing the operator script's length filter, `other_payloads 0` and every REP is telemetry whose
   digits merely change. The flag is **not** in any capture - we must ask the satellite to downlink it.
3. **Two-time-pad on the 16-byte `session` block.** `status` and `ping` carry the **same** block
   (`grep -ac '^REQ'` = 2), so there is no second ciphertext to XOR.
4. **Recovering the key by per-column scoring (the operator's own solver).** Keeping every `k < 128` that
   leaves all bytes `< 128` and taking the argmax of a letter-frequency score is unreliable for this capture: on
   lowercase text a one-bit-off key scores almost the same. Reproduced on a synthetic capture - 4 of 8
   columns wrong, `SIGNAL REPORT` printed as `SNYLAL'TEWQPT`. A key is only proven by decrypting a **reply**
   into meaningful prose, not by a score. Scoring rejected, verification kept.
5. **"The channel drops bit 5" as a fixed XOR.** False: the positions that lose bit 5 are not periodic with
   the keystream's period 8 or 16, so the loss is on the **plaintext**, not a key bug.

## The chain

**Step 1 - the 8-byte key, from known plaintext.** Every REQ starts with `status\x00session\x1d`
(15 bytes), so one packet is enough:

```python
K = bytes(a ^ b for a, b in zip(ct[:15], b'status\x00session\x1d'))
```

```text
KEY 12fbefdadf548eba          # this instance; the first instance was ca62daa60ca22627
```

Prove the key by decrypting an **answer**, not a question: a 21-byte REP yields
`err\x00bad\x00session` (14 of 15 bytes clean ASCII), and the 221-byte telemetry decrypts to a structurally valid telemetry report:

```text
cosmic-1 status report. mode nominal. uptime 2289 seconds. battery at 85 percent. panel temperature
minus 9 celsius. attitude stable. next pass in 45 minutes. accepted commands: status, ping,
downlink flag. end of report.
```

The protocol's symbol table falls straight out of that report:

| byte | meaning | byte | meaning |
|---|---|---|---|
| `0x00` | field separator / space | `0x0e` | `.` |
| `0x0c` | `,` | `0x1a` | `:` |
| `0x10 + n` | digit `n` (digits are **never** `0x30+`) | `0x1d` | separator before the token |
| `0x7f` | **a space inside one field** (escaped space) | | |

So `downlink\x7fflag` in the report is the command name verbatim, and the session token is 32 nibbles
(`6287E973D50005EB450005EB43093359`) - exactly one 16-byte block, used as the session token in requests. Its role as a nonce in an actual CTR implementation has not been established.

**Step 2 - build the downlink command ourselves.** No captured REQ ever issued `downlink flag`, so we must
send it. Assemble the plaintext, XOR with `K`, and fill the length field:

```python
pt  = b'downlink\x7fflag\x00session\x1d' + token          # 54 bytes
ct  = bytes(b ^ K[i % 8] for i, b in enumerate(pt))
pkt = b'\x10\x65' + counter.to_bytes(2, 'big') + bytes([0, len(pt) - 1]) + ct
```

Seven variants go out in one burst, which also hands us the satellite's rule table
(`python3 /tmp/c.py`; `exploit.py --probe` reproduces it from a pcap):

```text
sent 0  status (verbatim replay)   -> REP 227 B = the report           -> token ACCEPTED
sent 1  downlink_flag  (0x5f)      -> REP 25 B  = err unknown command
sent 2  downlink_flag  (0x5f)      -> REP 25 B  = err unknown command
sent 3  downlink flag  (0x20)      -> REP 25 B  = err unknown command
sent 4  downlink\x7fflag (0x7f)    -> REP 53 B  = flag\x00...          -> CORRECT COMMAND
sent 5  flag                       -> REP 25 B  = err unknown command
sent 6  downlink\x00flag (0x00)    -> REP 21 B  = err bad session      (extra field breaks the parser)
```

Three earlier replays returned `err bad session` because manually copied ciphertext changed two token bytes (`ff ca` -> `bf fa`). Subsequent packets were extracted directly from the pcap:

```python
i = D.rfind(bytes.fromhex('618f8eaeaa278ec9'))   # first 8 ciphertext bytes, constant for the session
pkt = D[i - 6:i + 47]                             # 6 header bytes + exactly 47 ciphertext bytes, verbatim
```

**Step 3 - read the flag, and the case problem.** The 53-byte reply decrypts to:

```text
flag\x00CDCTF[w\x13\x7f`Re\x7fN\x10t\x7fal\x10N\x13\x7foUt\x7fH\x13R\x13\x1f\x7f\x15D\x16\x18A\x10E\x17]
```

Apply the symbol table: `0x10+n` -> digit, `0x7f` -> `_` (the flag is **one field**, so every space is
escaped), `[`->`{`, `]`->`}`, `0x1f`->`?`, and an uppercase letter is a lowercase letter whose bit 5 the
channel erased. The 42-character result: `cdctf{w3_?re_n0t_al0n3_out_h3r3?_5d68a0e7}`.

The channel only ever **clears** bit 5, so the byte `0x60` (bit 5 already set) can only be `` ` ``, while a
real `@` (0x40) would have arrived as 0x40. Both readings were rejected, along with every case combination
of the hex suffix. The reason: **letter case cannot be recovered from a single sample** - the satellite
corrupts each transmission independently, and the true flag is `W3_@rE_n0T_AL0n3_OuT_h3r3?`. The correct
move (implemented as `analysis/twopad.py` plus the sampling loop in `exploit.py --samples`) is to request
the downlink **many times** and, per position, OR in bit 5: if any sample has bit 5 set, the original
character had it set; if all samples have the bit clear, a finite sample set cannot prove the original bit was zero. Additional samples and submission provide further checks.

## Flag

```text
cdctf{W3_@rE_n0T_AL0n3_OuT_h3r3?_5d68a0e7}
```

## Reproduce

```bash
# 1) on the relay: capture one live REQ, then capture only replies addressed to this box
timeout -s INT 6  tcpdump -i any -nn -s0 -w /tmp/f.pcap 'udp and src 172.25.190.3'
(timeout -s INT 25 tcpdump -i any -nn -s0 -w /tmp/b.pcap 'udp and dst host 172.25.189.2' >/dev/null 2>&1 &)

# 2) build and fire the seven command variants, then read once the capture window has closed
python3 exploit.py --probe /tmp/f.pcap        # prints the 7 packets sent
sleep 20 && python3 exploit.py --decode /tmp/b.pcap

# 3) or decrypt any pcap offline
python3 exploit.py --decode /tmp/b.pcap
```

## Reproduction notes

- The `udp[4:2] = 61` filter excluded a 21-byte reply. Inspect packet lengths before filtering by an expected size.
- **`-i any` doubles every count** (one frame appears as both `eth1 In` and `eth2 Out`); a count of 2 is
  not a nonce collision.
- **Read a capture only after tcpdump has exited**, otherwise the bytes are still in its buffer and you
  "see" silence.
- Extract ciphertext directly from the pcap to avoid transcription errors.