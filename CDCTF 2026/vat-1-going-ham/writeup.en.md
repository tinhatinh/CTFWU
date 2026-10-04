# Verbal Authentication Transmissions 1/5: Going HAM - OSINT + Crypto (500 pts)

**Flag:** `cdctf{N4T0_comms}`
**Files:** `captured_radio.mp3`, 584028 B, sha256 `36a9039cd0dfe8416da8acc64a6cd1d4222da5e0312617cb72aff74cadca1d07`

## Problem Description

The challenge ships a single audio file, `captured_radio.mp3`, described as an intercepted
transmission between two Crimson Offense field operatives who are "passing an encoded flag".
The card is worth 500 points, tagged OSINT + Crypto, authored by `b0b`, with flag format
`cdctf{Ex4mpl3_flag}`. There is no remote service and no hint; every fact lives inside 97
seconds of audio.

## Initial Analysis

`file` reports an MP3 with an ID3v2.4 tag, MPEG-2 layer III, 48 kbps, 24 kHz, mono. `exiftool`
shows the tag is 34 bytes holding only the `TSSE = Lavf61.7.103` frame, so the file was produced
by ffmpeg and carries no descriptive metadata. Walking the MP3 frames
(`analysis/mp3_frame_walk.py`) finds 2026 frames, all 288 bytes, plus 8 out-of-frame gaps of
exactly 44 bytes each and a 144-byte tail. Dumping those regions: one gap is a second ID3v2.4
tag inserted mid-stream, the rest are frame payloads that lost their header during re-encoding,
and the tail is a `FFF3` frame whose payload is all `0x55` (a padded silent frame). No surplus
byte carries meaning, so the container angle closes immediately.

The spectrum is what actually orients the challenge. Three spectrogram bands
(`analysis/spectrogram_0-1200Hz.png`, `analysis/spectrogram_0-6000Hz.png`) show a ~100 Hz harmonic
comb moving over time together with travelling formants, i.e. the source is a human voice.
Autocorrelation over 60 ms frames measures a median f0 of 103.9 Hz with 884/1617 voiced frames.
The challenge is not a digital mode, it is a voice call.

## Ruled-Out Approaches

Before committing, these channels were tested and rejected (full log in `notes.md`):

1. **Container stego**: every anomalous byte region is explained by the ffmpeg encoder, entropy
   6.494/8, zero flag-pattern hits. Rejected.
2. **RTTY/AFSK, SSTV, FT8**: no stationary tone pair, no line structure. Rejected.
3. **DTMF**: energy at the four low and four high keypad frequencies all sits below the
   broadband reference, no cell stands out. Rejected.
4. **Morse / on-off keying**: the silences are phrase boundaries, and the carrier is continuously
   amplitude modulated rather than switched. Rejected.

## Exploitation Chain

**Step 1 - Turn audio into text.** Decode to WAV and run Whisper on CPU. The `base` model
(beam 5) captures the content but collapses digit runs:

```bash
ffmpeg -y -i files/captured_radio.mp3 -acodec pcm_s16le -f wav audio.wav
python analysis/asr_base.py
```

```text
copy wilco eagle 2 flag is 636 4637 467 bravo correction flag is 636 4637 4667 bravo
4-0-3-4-5-4-3-0-5 Foxtrot 6-36 Foxtrot 6- delta 6- delta 7-3-7- delta. Repeat.
```

Re-running with `small`, `beam_size=10`, `temperature=0.0`, `word_timestamps=True` and an
`initial_prompt` preloaded with the NATO alphabet plus the digit words, restricted to the
45-83 s window, yields one token per character (`files/transcript_small_flagpart.txt`):

```text
[  4.64- 10.72] Copy Wilco. Eagle two. Flag is six three six four six three seven four six seven bravo.
[ 11.16- 16.80] Correction. Flag is six three six four six three seven four six six seven bravo four echo three
[ 16.80- 22.82] four five four three zero five foxtrot six three six foxtrot six delta six delta seven three seven
[ 22.82- 34.42] Delta. Repeat. Flag is 63646374667 Bravo for Echo 3454305 Foxtrot 636 Foxtrot 6 Delta 6 Delta
```

**Step 2 - Identify the alphabet in use.** The flag is spelled with the NATO alphabet, but only
four code words appear, and they are exactly the hex letters: `bravo`, `echo`, `foxtrot`, `delta`
map to `B E F D`. The number words are plain hex digits. The 34 tokens form 17 bytes.

The pivot is the word `Correction`. The first reading drops one `6` (`...four six seven bravo`),
producing an 11-character hex string, odd, so no byte can be assembled. The second reading
restores it (`...four six six seven bravo`) to 12 characters, and `63 64 63 74 66 7B` is
`cdctf{`. The author planted a transmission error in the speech so that the solver has to pick
the corrected reading, and the broadcast confirms itself with the third `Repeat` pass.

**Step 3 - Decode and cross-check the readings.**

```python
DIGITS = {"zero":"0","one":"1","two":"2","three":"3","four":"4",
          "five":"5","six":"6","seven":"7","eight":"8","nine":"9"}
LETTERS = {w: w[0].upper() for w in ("alpha bravo charlie delta echo foxtrot golf hotel "
           "india juliett kilo lima mike november oscar papa quebec romeo sierra tango "
           "uniform victor whiskey xray yankee zulu").split()}

hexs = "".join(DIGITS.get(w, LETTERS.get(w, w)) for w in tokens)
flag = bytes.fromhex(hexs).decode("ascii")
```

**Verification:** `exploit.py` extracts all three readings from the transcript with one regex and
exits 0 only when at least two independent readings agree on a string matching
`^cdctf\{[A-Za-z0-9_]+\}$`. The `Correction` and `Repeat` readings match byte for byte; the first
reading is rejected precisely because its hex length is odd. Length 34 is even, all 17 bytes are
printable ASCII, and the prefix and closing `}` obey the stated format.

## Flag

```bash
python exploit.py files/transcript_small_flagpart.txt
```

```text
[*] transcript_small_flagpart.txt: 3 lan doc co duoc phat song
[1] 11 ky tu hex (le) -> khong ghep duoc thanh byte: 6364637467B
[2] 17 byte -> 'cdctf{N4T0_comms}'  <- co hop le
[3] 17 byte -> 'cdctf{N4T0_comms}'  <- co hop le
[*] lan doc dau tien thieu mot chu so '6' nen hex le: do la loi ma phat song tu sua bang tu 'Correction'
[+] 2 lan doc doc lap (Correction + Repeat) trung nhau: cdctf{N4T0_comms}
[+] da luu flag.txt
```

## Reproduce

```bash
python exploit.py files/transcript_small_flagpart.txt
```

To replay from the original audio, follow `de.md`: decode to WAV, run `analysis/asr_small.py` to
regenerate the transcript, then run the command above. The ASR step needs the Whisper `small`
model (weights are downloaded, not committed); the decoding step is stdlib only.
