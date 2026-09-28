# Aria Acoustic Control Port (firmware r7.2)

Aria is an OEM smart speaker. Field devices and the vendor provisioning tool
drive it entirely through sound: the speaker listens on its microphone and acts
on control frames it hears. This document describes the acoustic control
interface exposed by the diagnostic bridge.

## Transport

The diagnostic bridge accepts one capture per line over TCP. A capture is a
base64-encoded WAV:

- RIFF/WAVE, mono
- 24-bit signed PCM
- 96000 Hz sample rate
- at most 2 seconds

Each connection has a fixed capture budget. When the budget is spent the
session closes.

For every accepted capture the bridge prints a result block terminated by a
line containing `----`.

## Microphone front end

The capture is run through the modeled analog front end before any decoding:

1. Parametric EQ (see "Defensive profile").
2. Analog gain stage.
3. The transducer response.
4. A 7 kHz anti-alias low-pass.
5. Decimation to the 16 kHz codec rate.

The microphone bandwidth reaches well past the audible range. The vendor
pairing beacon lives above it.

## Control modem

Control frames are carried by a 16-tone MFSK modem in the codec band. Each
symbol is one tone held for a fixed interval; the tone index is one hex nibble.

- tone(k) = 800 + 80 * k  Hz, for k in 0..15
- symbol length: 200 samples at the 16 kHz codec rate
- lead-in: 64 codec samples of silence before the first symbol

A frame on the wire is a byte stream, high nibble first:

```
0xA5 0x5A  LEN  <LEN payload bytes>  CKSUM
```

`CKSUM` is the XOR of `LEN` and every payload byte. The payload is a sequence
of TLV records:

```
TYPE  LEN  <LEN value bytes>
```

### Opcodes

| type | name           | value                                   |
|------|----------------|-----------------------------------------|
| 0x10 | DEBUG_PING     | none. Replies PONG.                     |
| 0x01 | SELECT_PROFILE | 1 byte region id. Binds a cal region.   |
| 0x02 | SET_CAL_VECTOR | 1 byte count, then count int16 samples. |

`SELECT_PROFILE` on the factory calibration region (id 0x0E) echoes the region
header back as `CAL ECHO`. `SET_CAL_VECTOR` writes a calibration vector into the
bound region.

## Safety interlock

`SELECT_PROFILE` and `SET_CAL_VECTOR` are engineering class opcodes. The firmware
scans the audible control band (300 Hz to 3400 Hz) for an engineering tone
signature and quarantines any capture that carries one with `SAFETY LOCKOUT`,
no decoding. The vendor considers the engineering class unreachable from the
room for this reason.

`DEBUG_PING` is not an engineering opcode and is always serviced.

## Defensive profile

The only field-serviceable setting is the parametric EQ, read from `eq.cfg`.
Each line is one band:

```
type  f0  Q  gain_dB
```

`type` is one of `peak`, `notch`, `lowshelf`, `highshelf`. Up to 8 bands are
applied in order, ahead of the analog front end. The shipped profile is flat.
