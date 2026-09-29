# Welcome Call — Forensics (Medium)

**Flag:** `sun{thankyouforplaying}`
**Files:** `welcomecall.pcap` (181952 B, sha256 `7e0effd30dbd6fd0…`)

## Challenge

"I just got a call from the flag factory, they said they were looking for their favorite CTFer?"
A single pcap file.

## Initial Analysis

The capture is one VoIP session: SIP `INVITE` from `192.0.2.10` to `sip:board@192.0.2.20`, answered by
`100 Trying` / `180 Ringing` / `200 OK` / `ACK`. The SDP both sides agree on:

```
m=audio 4000 RTP/AVP 0        a=rtpmap:0 PCMU/8000   a=ptime:20   a=sendonly   (caller)
m=audio 4002 RTP/AVP 0        a=rtpmap:0 PCMU/8000   a=ptime:20   a=recvonly   (board)
```

So it is a single G.711 mu-law 8 kHz audio stream, 20 ms per packet, with sound in only one direction.
The machine has no tshark, so `scapy` is used to read the pcap and stitch the payload together by hand.

Before listening to the content, the "data disguised as voice" hiding places were ruled out:

| check | result |
| --- | --- |
| sequence number | 778 packets, 0 gaps |
| RTP timestamp | delta always 160 samples |
| SSRC | single value `48271739` |
| telephone-event (PT 101) | absent -> no DTMF |
| Goertzel 697/770/852/941 x 1209/1336/1477 on the audio | no tone pairs |
| LSB bits 0/1/7 of the mu-law payload | noise |
| ASCII strings in the pcap | `xor`/`rot`/`HINT` are only coincidences: mu-law bytes during silence fall right in the 0x60-0x7E range, producing up to 3733 fake "ASCII runs" |

So the flag has to be in the audio content.

## Where I fooled myself (the most important part)

The first version had a mu-law decoder I wrote myself. Only when cross-checking it against the stdlib
did I find it wrong for all 256 codes  -  for example code `0x00` gave `-126943` while the correct value is `-32124` (off by about 4x and overflowing int16).

The chain of consequences:

- The WAV that came out was garbage, but garbage whose amplitude and spectrum *resemble a human voice*, so the spectrogram looked perfectly reasonable.
- Whisper on that garbage produced hallucinations that looked very "believable": `"I was a dead man"` repeated 7 times, and another pass repeating `"a girl in law"`. I nearly concluded "just an ordinary voice call, nothing here".
- Every conclusion about metadata/stego still held (they only use the raw payload), but every conclusion about the *audio content* made before the decoder was fixed was worthless.

Fixed it by using what already exists and cross-checking two independent sources:

```python
pcm = audioop.ulaw2lin(payload, 2)     # width là độ rộng mẫu ĐẦU RA; truyền 1 sẽ ra 8-bit
```

`ffmpeg -f mulaw -ar 8000 -i payload.raw` gives a matching result: `corr(audioop, ffmpeg) = 1.0000`.
(Also: because `width=1` was passed the first time, I mis-measured the audio length as 7.78 s instead of 15.56 s.)

## Exploit Chain

With correct audio, the spectrogram shows continuous harmonics + formants, a fundamental around
~100-125 Hz, 32 sound clusters: it really is a human voice. But whisper `base`/`small`, beam=5, with a
CTF prompt, language auto-detect, speed sweeps of 0.6x-4x all yield consistently meaningless text
-> the signal itself was transformed, this is not a model failure.

The deciding measurement is the onset/offset asymmetry of the sound clusters. Forward-playing human
speech has a sharp attack and a slow decay, so the start of a cluster must be stronger than its end.
Measured over the 32 clusters:

```
năng lượng trung bình 1/3 đầu cụm = 0.0539
năng lượng trung bình 1/3 cuối cụm = 0.0649   -> ratio 0.83
```

Sign reversed -> the audio is time-reversed. Apply `x[::-1]` and only then transcribe:

```
Welcome to Bsides Orlando. The flag that you are looking for is Sun with a left curly
bracket. Thank you for playing right curly bracket. All lowercase, no spaces.
Thank you and have a good one.
```

The flag is *spoken as a description*: the prefix `sun`, then "left curly bracket", then the content
"thank you for playing", then "right curly bracket", with the constraint "all lowercase, no spaces":

```
sun{thankyouforplaying}
```

This matches the pattern of the same author's challenge in this series (`sun{praisethesun}`), so the
prefix `sun{` is consistent.

## Flag
```
$ python solve_call.py
[2] RTP: 778 packets, 124480 payload bytes, 0 sequence gaps, 0 bad timestamps
[3] mu-law expansion via stdlib audioop
    15.56 s of audio; corr(audioop, ffmpeg) = 1.0000
[5] transcription: Welcome to B-Sides Rolando. The flag ... Sun with a left curly bracket.
    Thank you for playing right curly bracket. All lowercase, no spaces. ...
[+] FLAG: sun{thankyouforplaying}
```
