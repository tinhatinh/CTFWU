# Verbal Authentication Transmissions 5/5: You get all that? - OSINT + Crypto (500 pts)

**Flag:** `cdctf{8u88l3_848813_fl4g_pa55ing}`
**Files:** `captured_cred_call.mp3` (151244 B, sha256 `687fecc9b0868355f0af53b347d8a3a5e918522d936cda0cd46d89504799f803`), `cred_call_transcript.txt` (254 B, sha256 `41eb65db34be1d35090b7d694d2bd065d1afbee97d57172f3aa9ead6aab00fea`)

## Challenge

The challenge ships an automated voice call placed to one of Jeffery Barrett's employees,
plus its transcript. The message says a credential is being shared and that it has been
"encoded for ease of verbal transmission". The payload is 17 pronounceable gibberish words
separated by periods. The card is worth 500 points, tagged OSINT + Crypto, authored by `b0b`,
with flag format `cdctf{ex4mp13_f14g}`. There is no remote service.

## Analysis

The provided transcript contains all 17 word groups needed by the decoder. Use it directly rather than transcribing the audio again. The accompanying MP3 is 24 kHz mono with tag `TSSE = Lavf61.7.100`.

The structure of the 17 words announces the algorithm. Every word is `CVCVC`. The alphabet is
contained in 21 letters: exactly the 6 vowels `a e i o u y`, and 15 of the 17 consonants
`b c d f g h k l m n p r s t v z x` (missing `d` and `p`). The first group starts with `x` and
the last group ends with `x`. That triple - "6 vowels + 17 consonants + `x` clamping both
ends" - is the signature of **BubbleBabble**, the spoken-aloud fingerprint format OpenSSH
generates in `fingerprint_bubblebabble` (`sshkey.c`).

## Analysis note

Container, spectral and ASR experiments are preserved in `notes.md`. The solution below only needs the supplied transcript.

## Solution

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

All 85 letters match, including the 16 dashes, confirming the transcript agrees with the re-encoded bytes (the early
guess that `z` was a mis-read `x` was wrong). The plaintext also explains itself:
`8u88l3_848813` is `bubble_babble`, the tail `fl4g_pa55ing` is `flag_passing`, and the prefix
`cdctf{` plus the closing `}` obey the stated format. One side property of the code acts as a
safety valve: some character errors produce indices outside 0..3. This structural check does not detect every possible alteration.

## Result

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
