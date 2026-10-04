# Verbal Authentication Transmissions 5/5: You get all that? - OSINT + Crypto (500 pts)

**Flag:** `cdctf{8u88l3_848813_fl4g_pa55ing}`
**Files:** `captured_cred_call.mp3` (151244 B, sha256 `687fecc9b0868355f0af53b347d8a3a5e918522d936cda0cd46d89504799f803`), `cred_call_transcript.txt` (254 B, sha256 `41eb65db34be1d35090b7d694d2bd065d1afbee97d57172f3aa9ead6aab00fea`)

## Problem Description

The challenge ships an automated voice call placed to one of Jeffery Barrett's employees,
plus its transcript. The message says a credential is being shared and that it has been
"encoded for ease of verbal transmission". The payload is 17 pronounceable gibberish words
separated by periods. The card is worth 500 points, tagged OSINT + Crypto, authored by `b0b`,
with flag format `cdctf{ex4mp13_f14g}`. There is no remote service.

## Initial Analysis

The audio is a 24 kHz mono file produced by ffmpeg (`TSSE = Lavf61.7.100`). The container is
clean: the ID3 tag is 34 bytes, the body is 151200 bytes, and the sum is exactly
`25.20 s * 48000 / 8`, so no byte is appended past the stream. The spectrum is a human voice
(energy below 500 Hz sits 25.40 dB above the 4-11 kHz band and varies 91.05 dB per frame),
and there is no pixel grid of a spectrogram stego. Whisper `small` recovers only the intro
sentence inside the first 9.4 s and returns 0 tokens for the code words, which confirms the
complaint in the problem text: a machine cannot hear them either. Working conclusion: the
payload lives in the transcript, and the audio is only a rendering of it.

The structure of the 17 words announces the algorithm. Every word is `CVCVC`. The alphabet is
contained in 21 letters: exactly the 6 vowels `a e i o u y`, and 15 of the 17 consonants
`b c d f g h k l m n p r s t v z x` (missing `d` and `p`). The first group starts with `x` and
the last group ends with `x`. That triple - "6 vowels + 17 consonants + `x` clamping both
ends" - is the signature of **BubbleBabble**, the spoken-aloud fingerprint format OpenSSH
generates in `fingerprint_bubblebabble` (`sshkey.c`).

## Ruled-Out Approaches

Before committing, these channels were tested and rejected (full log in `notes.md`):

1. **MP3 container stego**: the ID3 holds only `TSSE`, the bitrate arithmetic accounts for
   every body byte, and the `PK` runs at offsets 44887/96286/120669 are coincidental compressed
   content. Rejected.
2. **Spectrogram stego**: no frame in the 1-4 kHz band is near fully white and no long plateau
   exists; the low band is continuously modulated harmonics. Rejected.
3. **DTMF / AFSK / Morse**: only 18 human utterances from 9 s onward, no tone cell stands out. Rejected.
4. **Transcribing the audio**: Whisper `small` yields 0 tokens for the 17 words, so the audio
   adds no data; the transcript is the only source. Rejected as an input channel, but the
   transcript is still validated through the cipher itself.
5. **Classical ciphers over the 85 letters** (homophonic Polybius, one character per word):
   654 parameter sets (position subset, letter-to-digit rule, endian, alphabet, ASCII offset)
   produced 0 candidate containing a flag trace, while the same engine does find `cdctf` in a
   synthetic control built with that scheme. Rejected.

## Exploitation Chain

**Step 1 - Turn the structure into BubbleBabble parameters.** The function emits `x`, then per
round prints 5 characters derived from one byte pair, with `-` between rounds:

```python
rounds = len(data) // 2 + 1
idx0 = (((data[2*i] >> 6) & 3) + seed) % 6      # vowel
idx1 = (data[2*i] >> 2) & 15                    # consonant
idx2 = ((data[2*i] & 3) + seed // 6) % 6        # vowel
idx3 = (data[2*i+1] >> 4) & 15                  # consonant before the '-'
idx4 = data[2*i+1] & 15                         # consonant after it, = first char of next group
seed = (seed * 5 + data[2*i] * 7 + data[2*i+1]) % 36
```

17 groups means `rounds = 17`, so the data is 32 or 33 bytes long. The even-length branch
forces the third character of the last group to be `x` (idx1 = 16); the actual last group is
`lizyx` whose third character is `z` (consonant index 15), so the length must be odd:
**33 bytes**, and the final byte is taken from that very group.

**Step 2 - Follow the seed to invert.** The two vowel indices do not hand over raw bits; they
give `(2 bits + seed) mod 6` and `(2 bits + seed//6) mod 6`. Because a 2-bit value only spans
0..3, that addition has a unique inverse once `seed` is known, and `seed` depends only on byte
pairs already decoded in earlier rounds. That yields a single sequential solution starting from
`seed = 1`:

```bash
python exploit.py files/cred_call_transcript.txt
```

```text
[*] cred_call_transcript.txt: 17 word 5 chu cai
[*] word dau tien bat dau bang 'x' = True, word cuoi ket thuc bang 'x' = True
[*] so byte = (rounds-1)*2 + 1 = 33, rounds = len/2 + 1 = 17
[*] hex stage-1 : 63646374667b387538386c335f3834383831335f666c34675f70613535696e677d
[+] giai ma    : cdctf{8u88l3_848813_fl4g_pa55ing}
```

**Step 3 - Verify with the encoding round trip.** `exploit.py` re-encodes the 33 recovered
bytes with BubbleBabble's own forward function and compares character by character against the
transcript:

```text
[*] BubbleBabble re-encode : ximok-gemul-ganol-ruvul-hevaf-murof-felyf-metuf-myvaf-cusih-zynok-sitek-lulol-bemef-hatok-norek-lizyx
[+] vong lap khop 85/85 ky tu: True
```

All 85 letters match, including the 16 dashes, so no transcript letter was misheard (the early
guess that `z` was a mis-read `x` was wrong). The plaintext also explains itself:
`8u88l3_848813` is `bubble_babble`, the tail `fl4g_pa55ing` is `flag_passing`, and the prefix
`cdctf{` plus the closing `}` obey the stated format. One side property of the code acts as a
safety valve: if any character had been altered, the mod-6 addition would produce an index
outside 0..3 in the following round and the chain would break there.

## Flag

```bash
python exploit.py files/cred_call_transcript.txt
```

```text
[*] cred_call_transcript.txt: 17 word 5 chu cai
[*] word dau tien bat dau bang 'x' = True, word cuoi ket thuc bang 'x' = True
[*] so byte = (rounds-1)*2 + 1 = 33, rounds = len/2 + 1 = 17
[*] hex stage-1 : 63646374667b387538386c335f3834383831335f666c34675f70613535696e677d
[+] giai ma    : cdctf{8u88l3_848813_fl4g_pa55ing}
[*] BubbleBabble re-encode : ximok-gemul-ganol-ruvul-hevaf-murof-felyf-metuf-myvaf-cusih-zynok-sitek-lulol-bemef-hatok-norek-lizyx
[+] vong lap khop 85/85 ky tu: True
[+] da luu flag.txt
```

## Reproduce

```bash
python exploit.py files/cred_call_transcript.txt
```

The script is stdlib only and reads the transcript stored in `files/`; the audio is not needed.
To re-check the audio side (container, spectrum, utterance timing, ASR) run the four scripts in
`analysis/` listed in `de.md`; `analysis/asr_check.py` needs the Whisper `small` weights, which
are downloaded on first use.
