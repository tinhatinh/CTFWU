# Kick the CAN - Hardware (Medium)

**Flag:** `H7CTF{6360cbb3-73fc-4ba5-a9e6-0229a3b1a008}` · 125 pts · H7TEX 2026
**Target:** `https://web-5c6688f7ad7feac6.web.h7tex.com` · Artifact: `/capture.log` (candump with 132 frames, 5248 bytes)

## Challenge

A CAN bus capture taken from the OBD-II port of a vehicle in the shop. Most of it is engine gossip, but two devices are having a private conversation and one of them talks too much. The job: recover what the ECU handed back.

## Initial Analysis

The home page is `Python SimpleHTTP/0.6` listing exactly one file:

```
file: capture.log (SocketCAN candump log: (timestamp) can0 ID#DATA)
Read it with candump/can-utils, Wireshark (SocketCAN), or python-can.
```

Counting the frequency of CAN IDs:

```
0C9 158 1A0 1F1 244 2C0 316 3B0   -> mỗi ID hàng chục frame, payload ngắn, vô cấu trúc
7E0                               -> 4 frame
7E8                               -> 8 frame
```

`0x7E0`/`0x7E8` are the standard request/response pair of UDS diagnostics over CAN, carried by ISO-TP
(ISO 15765-2). The other eight IDs are periodic engine traffic, with no question-answer cadence.

## Exploit Chain

**Step 1 - Reassembling the ISO-TP messages.** The first 4 bits of the first byte are the PCI: `0` Single Frame,
`1` First Frame, `2` Consecutive Frame. The First Frame gives the total length (`0x102E` → 46 bytes), and each CF
contributes 7 bytes.

The most notable sequence, all on `0x7E8`:

```
7E8#102E62F1A0483743   FF, total = 46
7E8#2154467B36333630   CF 1
7E8#22636262332D3733   CF 2
7E8#2366632D34626135   CF 3
7E8#242D613965362D30   CF 4
7E8#2532323961336231   CF 5
7E8#26613030387D0000   CF 6 (last 2 bytes are padding)
```

Glued back together this is `62 F1 A0` + 43 bytes of data. `62` is the positive response of service `22`
(ReadDataByIdentifier), `F1A0` is the DID. The remaining 43 bytes are pure ASCII:

```
H7CTF{6360cbb3-73fc-4ba5-a9e6-0229a3b1a008}
```

**Step 2 - Rebuilding the entire diagnostic session,** to be certain this is the leak and not a coincidental ASCII
string:

| Direction | Message | Decoded |
| --- | --- | --- |
| `7E0 →` | `10 03` | DiagnosticSessionControl: enable extended session |
| `← 7E8` | `50 03 0032 01F4` | Positive, P2=50 ms, P2*=5000 ms |
| `7E0 →` | `27 01` | SecurityAccess: request seed |
| `← 7E8` | `67 01 470C3712` | Positive, seed `47 0C 37 12` |
| `7E0 →` | `27 02 1D566D48` | SecurityAccess: send key |
| `← 7E8` | `67 02` | Positive: unlocked |
| `7E0 →` | `22 F1A0` | ReadDataByIdentifier DID 0xF1A0 |
| `← 7E8` | `62 F1A0 <43 byte>` | Flag |

The requester entered extended session, got past SecurityAccess with the seed/key pair `47 0C 37 12` / `1D566D48`,
and only then read the DID. `0xF1A0` is normally the ECU's hardware code; here it returns the flag.

**Step 3 - Rerunning.** `solve.py` downloads the log, parses candump, reassembles ISO-TP per CAN ID, looks for the UDS
`0x62` and regexes `H7CTF\{[^}\n]*\}` over the reassembled bytes themselves:

```
python solve.py --url https://web-5c6688f7ad7feac6.web.h7tex.com/capture.log

[*] 132 dòng log -> 132 frame hợp lệ
[*] CAN 0x7E0: 4 thông điệp ISO-TP hoàn chỉnh
[*] CAN 0x7E8: 4 thông điệp ISO-TP hoàn chỉnh

[+] 0x7E8 msg#3: RDBT DID=0xF1A0, 43 byte dữ liệu
    ascii: b'H7CTF{6360cbb3-73fc-4ba5-a9e6-0229a3b1a008}'
```

## Flag
```
H7CTF{6360cbb3-73fc-4ba5-a9e6-0229a3b1a008}
```
