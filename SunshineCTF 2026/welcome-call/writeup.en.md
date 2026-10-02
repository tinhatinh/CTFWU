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

After verifying no steganography in RTP fields, the audio content was analyzed directly.

## Exploit Chain

Decode the G.711 mu-law payload to PCM:

```python
pcm = audioop.ulaw2lin(payload, 2)
```

`ffmpeg -f mulaw -ar 8000 -i payload.raw` gives a matching result: `corr(audioop, ffmpeg) = 1.0000`.
(Also: because `width=1` was passed the first time, I mis-measured the audio length as 7.78 s instead of 15.56 s.)

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
