# Mic Drop - Hardware (Medium)

**Flag:** `H7CTF{7f0cb1b6-34ee-46c0-945b-1f069dff2a29}`

## Challenge

The AV bridge in the online meeting room has been taken over, and it is still live-streaming the room.
The attacker rides that very live feed to smuggle secrets out, while "nobody in the meeting room hears
anything unusual". The target is an instance running `mediamtx` (MediaMTX), given as an HTTPS URL.

The task: read the data the attacker sends out.

## Analysis

`curl -I /` returns `Server: mediamtx`, so this is a media streamer rather than a web app. MediaMTX serves
HLS at the route `<path-name>/index.m3u8`, while the `/v3/...` API here is closed (301 then 404). Trying a list of
path names that fit the meeting-room context, `/boardroom/index.m3u8` returns 200 with `application/vnd.apple.mpegurl`:

```
#EXT-X-STREAM-INF:BANDWIDTH=186669,...,CODECS="mp4a.40.2"
main_stream.m3u8
```

`main_stream.m3u8` is a live playlist, the `*_main_segN.ts` segments are ~6.9 s long, and the sliding window keeps ~7
segments. Downloading 7 segments gives 47.85 s of AAC mono 48 kHz audio.

Two questions to answer in order: is the data in the container or in the signal? and if it is in the signal, in what
modulation form?

## Solution

**Step 1 - Looking at the spectrum by eye.** `ffmpeg -lavfi showspectrumpic` gives a spectrum image (saved as `analysis/spectrogram.png`).
Nine energy bursts are visible at once, each ~1.7 s, repeating at a steady ~5.68 s spacing, sitting entirely inside
0.8-2.5 kHz. Perfect periodicity like that is the signature of a message replayed continuously on a live feed, not
room noise.

**Step 2 - Reading the burst structure** (`analysis/bursts.py`). Each burst opens with a pure 1200 Hz tone for ~160 ms,
then two energy groups appear at once around 1200 Hz and 2200 Hz, with sidebands from the constant keying.
1200/2200 Hz is exactly the mark/space pair of the Bell 202 standard - classic half-duplex AFSK - and the 160 ms of
pure tone at the head of each burst is the mark carrier (preamble) before any data.

**Step 3 - Measuring the baud instead of guessing.** Compare the two bands' energy over bit windows at different baud
rates and count transition density (`analysis/afsk.py`):

```
baud  300: 508 bits, 268 transitions, trans/bit=0.528
baud  600: 1018 bits, 272 transitions, trans/bit=0.267
baud 1200: 2038 bits, 274 transitions, trans/bit=0.134
```

The signal changes state almost every bit at 300 baud and falls by exactly the factor at the higher bauds, i.e.
**300 baud is the real rate**; 1200 is only the Bell 202 default. The arithmetic checks out too:
43 characters × 10 bits (8N1) = 430 bits = 1.43 s, plus the 160 ms preamble ≈ 1.6 s, exactly the burst length.

**Step 4 - Demodulating.** For each bit, compare the amplitudes after a ±120 Hz bandpass around 1200 Hz and 2200 Hz,
`mark > space` is 1; slice the bit stream on start bits, pack 8 bits LSB-first into ASCII:

```
H7CTF{7f0cb1b6-34ee-46c0-945b-1f069dff2a29}
```

**Step 5 - Cross-verification.** Decoding all 9 bursts: the 8 complete bursts yield the identical string, and the
9th is cut mid-way (`...dff`) precisely because the capture window ends in the middle of it. A coincidental decode
cannot repeat verbatim 8 times; this is also evidence that the message is looped out over the live feed.

## Result
```bash
python exploit.py https://web-021fc06a681e8dca.web.h7tex.com/boardroom 60   # khi instance còn chạy
python exploit.py files/352f5b477507_main_seg15.ts                          # re-run from the saved segment
```

Actual output of the second command (a 159.048 B TS segment already saved in `files/`):

```
[*] offline TS files/352f5b477507_main_seg15.ts: 159048 B
[*] 6.85 s of PCM at 48000 Hz
[*] 1 burst(s)
      0.98-  2.68s  'H7CTF{7f0cb1b6-34ee-46c0-945b-1f069dff2a29}'
[+] flag: H7CTF{7f0cb1b6-34ee-46c0-945b-1f069dff2a29}   (agreed by 1/1 bursts)
```

The flag was captured while the instance was still alive, from 7 directly downloaded segments (47.85 s of audio, 9
bursts); by the time the script was repackaged for a check the instance had been stopped, so only the saved artifact
could be run. The 8/9 identical-burst verification comes from `analysis/afsk.py` run over that 47.85 s of audio (see
`notes.md` H6).
