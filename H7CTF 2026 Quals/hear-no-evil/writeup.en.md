# Hear No Evil — Hardware (Medium)

**Flag:** 2/2
`v1 = H7CTF{38b0e71c-6126-49f7-8692-3f0bf6bf31b0}` · `v2 = H7CTF{11945790-f241-4644-9e45-e19819bdc996}`
**Target:** `https://web-2c53753bcbf2c207.web.h7tex.com` · Artifact: `/capture.pcap` (2220 B, 50 packets)

## Challenge

A pair of NoiseGate earbuds talks to the app over BLE, and the recording holds more than just them. Two secrets are in the capture: one that the earbuds leak themselves during a config read, and one that is only handed over after the app authenticates. Take both.

## Initial Analysis

The home page points at a single file:

```
capture.pcap (open in Wireshark: it dissects btle / btatt natively)
There is more than one device in the air. Two secrets are in here: one the earbuds
leak in a config read, and one they only hand over after the app authenticates.
```

The host has no `tshark`, `capinfos`, `btlejack`. Dumping each packet by hand shows the capture is not standard btle:

- The 4 packets beginning with access address `D6BE898E` are real BLE advertisements, from `Mi Smart Band 6`,
  `JBUL TUNE 230NC`, `Galaxy Fit3` and `NoiseGate Buds`. The first three are decoy devices.
- The remaining 46 packets begin with `C3 B2 A1 50`, followed by a 6-byte header, the payload and a 3-byte CRC.
  The DLT in the pcap header says 251, but the content is a home-brew ATT-style transport.

So the parsing is done by hand: `payload = packet[11:-3]`.

## Approaches Ruled Out

1. Breaking BLE pairing and then decrypting. The capture contains no pairing PDU and no Start Encryption, so
   there is no LTK to decrypt with. The keys of both characteristics are derived from data that already went over
   the air. The real-crypto attack line is ruled out; what remains is a reassembly puzzle.
2. Dissecting it with off-the-shelf tools as if it were an ordinary btle capture. The host has no
   `tshark`/`btlejack`/`capinfos`, and 46/50 packets follow no LL framing at all: the DLT says 251 but the payload
   is home-brew ATT.
3. Treating every 2-byte payload as a handle-select request. `31 0a` reads as handle `0x0031`, but it is also the
   last 2 bytes of the blob being read. In the first reassembly I put the `len >= 11` condition ahead of the handle
   condition, so a 20-byte chunk was misread as "handle + data". Settled with a context check: a 2-byte payload is
   only a request if the next packet is exactly 20 bytes long.

## Exploit Chain

**Step 1 - Pinning down the transport format.** Three payload shapes are distinguishable by length and context:

| Shape | Example | Meaning |
| --- | --- | --- |
| 2 bytes | `21 00` | handle select, offset 0 |
| 4 bytes | `21 00 14 00` | handle + offset |
| 20 bytes (or the remainder) | `83 3c f9 ...` | data for the outstanding request |
| >= 11 bytes | `31 00 <16 byte>` | self-contained notify |

**Step 2 - Reading the specification from the capture itself.** Assembling the chunks of handle `0x0041` yields 322 bytes of pure ASCII:

```
NoiseGate fw1.4.2 [dbg]
provkey = adv mfg data (company 0x0f39) after the 0x01 type byte, 16 bytes
config@0x0021: plaintext = value XOR provkey (provkey repeated cyclically)
vault@0x0033: released after auth; plaintext = ct XOR ks,
  ks = sha256(provkey || nonce || byte(i)) for i=0,1,.. concatenated;
  nonce = notify@0x0031
```

The device writes down its own keying scheme. `config` is value XOR provkey. `vault` is ct XOR ks, with ks
built from the provkey and the notify's nonce - no authentication step beyond those two values having to be correct.

**Step 3 - Getting the keys.** In the NoiseGate advertisement packet, the AD structure `14 FF 39 0F 01 ...` is
Manufacturer Specific Data, company `0x0F39`, sub-type byte `0x01`, then exactly 16 bytes:

```
provkey = cb0bba6665a4fc08131cd624f22869ca
nonce   = ca2458f360ade373f6d055aeb0304501     (notify @ 0x0031)
```

**Step 4 - Decrypting the two characteristics.**

```python
v1 = bytes(c ^ provkey[i % 16] for i, c in enumerate(ct_0x21))

ks = b"".join(hashlib.sha256(provkey + nonce + bytes([i])).digest() for i in range(8))
v2 = bytes(c ^ ks[i] for i, c in enumerate(ct_0x33))
```

Both ciphertexts are 43 bytes long, and 43 bytes is exactly the length of the flag string.

**Step 5 - Verifying correctness.** The 322 bytes of the `0x0041` blob reassemble into unbroken ASCII from start to
end. A reassembler with a wrong offset, or one that confuses a request with continuation data, cannot produce a
string like that; so the chunk order and the offsets are right, not a lucky coincidence.

## Flag
```
python solve.py analysis/capture.pcap

[*] provkey          : cb0bba6665a4fc08131cd624f22869ca
[*] 0x0041 (322 byte) b'NoiseGate fw1.4.2 [dbg]\nprovkey = adv mfg data (company 0x0f'
[*] config@0x0021 -> b'H7CTF{38b0e71c-6126-49f7-8692-3f0bf6bf31b0}'
[*] vault @0x0033 -> b'H7CTF{11945790-f241-4644-9e45-e19819bdc996}'
```

```
v1: H7CTF{38b0e71c-6126-49f7-8692-3f0bf6bf31b0}
v2: H7CTF{11945790-f241-4644-9e45-e19819bdc996}
```
