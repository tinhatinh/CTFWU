# Verbal Authentication Transmissions 3/5: Pretty Good Passphrase - OSINT + Crypto (500 pts)

English translation of `writeup.md`. Same commands, same numbers.

**Flag:** `cdctf{pr3t7y_g00d_piv4cy_fl4G}`
**Files:** `voicemail.mp3` (3964752 B, sha256 `437d7631ee3ee3aaf15ddb54383609b3f550c4feb5bbd08814c87ccd0b4e613a`), `VAT_key` (2096 B, sha256 `28715250c107ef4a3b2bbe611df4a457256c865c091087a0eaf3a6e0875fd03a`)

## Challenge

The author's friend meant to send a PGP-encrypted message but left an automated voicemail
instead. The challenge ships `voicemail.mp3`, 660.792 s long, plus `VAT_key`, a PGP private key,
and the passphrase `Password123!`. The task is to rebuild the message that was read out and then
decrypt it.

## Initial analysis

`ffprobe` reports MPEG layer III v2, 48 kbps, 24 kHz, mono, `duration=660.792000`, no ID3
carrying content. The container matches every other part of the VAT series, i.e. the file came
out of a TTS engine.

Energy-based segmentation gives 432 speech bursts spaced 1.585 s apart, each 0.36-0.88 s long.
Every burst has an F0 of 80-140 Hz with formants up to 12 kHz, so this is speech, not a numeric
mode. Repeats of the same word are near bit-identical copies (correlation 1.000), which is what a
word-clipping TTS produces.

Whisper `base.en` returns 419 tokens with two striking properties: every initial letter falls in
`a`-`k`, and the **syllable count alternates 2 - 3 - 2 - 3 exactly with the word position**. The
restricted initials rule out a NATO-style spelling alphabet, while the even/odd syllable rhythm is
the signature of the **PGP Word List**: 256 two-syllable words for bytes at even positions and 256
three-syllable words for odd positions, designed precisely for reading bytes over a voice channel.

So each word is one byte, and a word's index within the parity-correct list is the byte value. The
byte stream is the whole ASCII armor text, including CR, LF and the CRC line.

## Ruled out

1. **The given passphrase is wrong**: `--export-secret-keys` printed `Bad passphrase`, but the two
   failing keyIDs do not belong to this challenge's keyring. Signing and then verifying returns
   `Good signature`. Ruled out.
2. **Stego in the container or in low bits of the PCM**: no magic beyond `LAME`, and all eight bit
   planes yield 8-17% printable bytes. Ruled out.
3. **DTMF, stable tones, data in the spectrum**: no stable tone above 2.5 kHz. Ruled out.
4. **A spelling alphabet**: clustering finds ~351 distinct words across 413 slices, far too many
   for a 16/26/64 symbol table. Ruled out.
5. **Template matching with a local TTS**: best `espeak-ng` correlation is 0.043 (different
   engine), and `edge-tts` installs but every voice dies on `ClientConnectorDNSError` for
   `speech.platform.bing.com`. Ruled out.
6. **Skip the audio and find the ciphertext elsewhere**: `gpg --list-packets VAT_key` shows only
   five packets, no user attribute and no comment/URI signature subpacket. Ruled out.

## Exploit chain

**Step 1 - Force parity with a Viterbi decode.** For each token the state is the current parity; a
word that is an exact hit in the parity-correct list scores 3, a close match scores 1, and two
adjacent tokens may be merged into one word to repair cases like `dogs led` and `eight ball`. On
the 419 tokens of `base.en` the decode matches 246 cells exactly and yields:

```text
-----BEGIN PGP MESSAGE-----

hIwDyHr/VfQJfJEBA/wLRYGn0HpRTthSYqEDJICRMtgAMmeEVkQVzYpzk1gvL9zk
0tfMYkBYFE8txo9+qk7EKJ?T2lBnRL?3oRcdcYswYe6gt+hkRzUKUu8y73woSZoh
...
xmJMn57j6YcQOO5bzw==
=uQhg
-----END PGP MESSAGE---
```

Line breaks land every 64 base64 characters, so the word count and the alignment are already
right; only two `?` cells remain, which whisper heard as `escamo` and `imbecile`.

**Step 2 - Localise the remaining errors with three independent oracles.** Packet structure of the
253 decoded bytes: `PKESK tag=0x84 len=140 ver=3 keyid=c87aff55f4097c91 algo=1 mpi=1020 bit` then
`SEIP tag=0xd2 len=109 ver=1`. The keyID matches the challenge's encryption subkey exactly, and
`len=109` equals `253 - 142 - 2`, so everything up to byte 144 is clean. Sweeping all 64x64
combinations for the two `?` cells through `gpg` returns `Wrong secret key used` for all 4096, so
another error still sits inside the RSA region.

The second oracle is the armor CRC24. The CRC routine was validated first by detach-signing a
scratch file with this very key and comparing the `=` line `gpg` emits against the
hand-written function: `gpg crc: X+0T mine: X+0T MATCH`. With a trustworthy CRC, the
"one additional wrong cell" hypothesis leaves only 4 candidates, and all four still fail RSA.

The third oracle is the recogniser itself: rerun whisper with `condition_on_previous_text=False`.
The library default conditions decoding on text already emitted, which both triggers infinite
repetition (`gossamer german gossamer german ...` in `medium.en`) and lowers accuracy. With it off,
`small.en` and `medium.en` each return exactly 417 words.

**Step 3 - Merge the three transcripts.** They disagree on 8 cells and the gaps cancel out: `base`
cannot resolve cells 86 and 94 while the other two both give `W` and `P` (the words `Eskimo` and
`embezzle`, which `base` rendered as `escamo` and `imbecile`); `small` is blank at 229, 247 and
329 where `base` and `medium` both give `i`, `i`, `Y`. Majority vote is enough:

```output
[*] asr_base: 419 token -> 415 tu, body 340, o chua doc duoc [86, 94]
[*] asr_medium: 423 token -> 417 tu, body 340, o chua doc duoc [227]
[*] asr_small: 423 token -> 417 tu, body 340, o chua doc duoc [229, 247, 329]
[*] hop nhat 3 ban nghe: 340 ky tu base64, 8 o co bat dong
      pos 41: tXX -> X
      pos 65: tXX -> X
      pos 86: ?WW -> W
      pos 94: ?PP -> P
      pos 227: W?W -> W
      pos 229: ii? -> i
      pos 247: ii? -> i
      pos 329: YY? -> Y
```

**Step 4 - Verification.** The CRC24 read from the audio equals the CRC24 recomputed over the 253
bytes, so an independent 24-bit check passes, and `gpg` then decrypts with a valid MDC:

```output
[*] 253 byte, CRC doc tu audio = uQhg (b90860), CRC24 tinh lai tu body = b90860 KHOP
[*] kiem cau truc packet:
      PKESK tag=0x84 len=140 ver=3 keyid=c87aff55f4097c91 algo=1 mpi=1020 bit
      SEIP  tag=0xd2 len=109 ver=1
[*] gpg:
gpg: encrypted with rsa1024 key, ID C87AFF55F4097C91, created 2026-10-03
      "Crimson Offense b0b (baller) <b0b@crimson.offense>"
[+] plaintext: 'Good work: cdctf{pr3t7y_g00d_piv4cy_fl4G}\n'
```

## Flag

```bash
python exploit.py files/voicemail.mp3
```

```
[*] 253 byte, CRC doc tu audio = uQhg (b90860), CRC24 tinh lai tu body = b90860 KHOP
[*] kiem cau truc packet:
      PKESK tag=0x84 len=140 ver=3 keyid=c87aff55f4097c91 algo=1 mpi=1020 bit
      SEIP  tag=0xd2 len=109 ver=1
[*] gpg:
gpg: encrypted with rsa1024 key, ID C87AFF55F4097C91, created 2026-10-03
      "Crimson Offense b0b (baller) <b0b@crimson.offense>"
[+] plaintext: 'Good work: cdctf{pr3t7y_g00d_piv4cy_fl4G}\n'

FLAG: cdctf{pr3t7y_g00d_piv4cy_fl4G}
```

## Reproduce

```bash
python exploit.py files/voicemail.mp3
```

`exploit.py` needs only the standard library plus `gpg` on PATH. It reads the three transcripts in
`analysis/`, runs the parity-forced Viterbi against `files/pgp_wordlist.txt`, merges them, checks
the CRC24 and decrypts with `files/VAT_key`. To regenerate a transcript from scratch:

```bash
python -c "import whisper,json;w=whisper.load_model('small.en').transcribe('voicemail.mp3',language='en',fp16=False,word_timestamps=True,condition_on_previous_text=False);json.dump([[round(x['start'],3),round(x['end'],3),x['word']] for s in w['segments'] for x in s['words']],open('analysis/asr_small.json','w'))"
```

Caveat when calling the Git-Bash build of `gpg` from Python on Windows: `GNUPGHOME` and
`--homedir` must use the MSYS form (`/c/Users/...`). A `C:\Users\...` path is parsed as relative
and produces a bogus `Wrong secret key used` that looks exactly like a failed decryption.
