# Verbal Authentication Transmissions 4/5: What the helly - OSINT + Crypto + Password Cracking (500 pts)

English translation of `writeup.md`. Same commands, same numbers.

**Flag:** `cdctf{idontcare1}`
**Files:** `OTP_CODES_VAT.mp3` (448848 B, sha256 `56c3bbfa042f4e6ae46e577152260d9f1414ae199f09c0c0c3dcba7897d5e11c`)

## Challenge

A 74.808 s audio clip believed to carry the S/Key OTP codes of a Crimson Offense operative. The
codes are stale, but the original password behind them should be recoverable, and that password
is supposedly reused elsewhere. Three parameters are given: `n=8`, hashes are folded, no seed.
Card: 500 pts, OSINT + Crypto + Password Cracking, author `b0b`, format `cdctf{password}`.

## Analysis

`ffprobe` reports MPEG layer III v2, 48 kbps, 24 kHz, mono, no content-bearing ID3 tag. Same
container style as the other parts of the VAT series, i.e. TTS output, so the payload is the
spoken words rather than stray bytes or a modem mode.

Whisper `base` and `small` (one word per segment, `analysis/asr_base_run.log`,
`analysis/asr_small_run.log`) give 8 `CODE n` blocks of six words: 48 tokens. Against the
2048-word RFC 1760 dictionary (1-4 letters, `files/skey_dictionary.txt`) 44 of the 48 merged
tokens are dictionary words; the rest are 5-6 letters long and therefore definitely mishearings.
Six words per code is the signature of the S/Key six-word format: 6 x 11 bits covering a 64-bit
value plus 2 spare bits.

Three things had to be pinned: how 64 bits become six words, what the chain step function is, and
the password. The first two are falsifiable from data, so they were settled before any guessing.

## Approaches tried

1. **Data outside the speech**: uniform MP3 frames, no ID3, no secondary channel. Rejected.
2. **Dictionary-constrained ASR**: Vosk with a 2048-word grammar on the 1.1 s slices returned no
   candidate at all for 49/49 slices (`analysis/asr_vosk_grammar_attempt.txt`), and the log shows 19
   distinct dictionary words dropped by the acoustic model (931 `Ignoring word missing in
   vocabulary` lines). Rejected in favour of three unconstrained transcripts.
3. **A literal RFC 1760/2289 chain**: `step(v) = fold(MD5(8 raw bytes))`. Tested over every pair of
   readable codes, `k = 1..7`, with MD4, MD5, SHA1 and both byte orders: no match. Rejected.
4. **A false negative worth recording**: the first version of that test compared six whole words,
   so the 2 checksum bits inside the last word produced exactly one mismatch for every pair, and a
   tolerance of one word threw away the true model. The test only means something once the
   comparison is on the 64-bit value with the checksum bits dropped.

## Solution

**Step 1 - Pin the encoding with RFC vectors.** Parse Appendix C of RFC 2289 (27 vectors of
pass phrase + seed + count -> hex -> six words, kept verbatim in
`analysis/rfc2289_test_vectors.txt`) and check one implementation against them:

```python
def fold_md5(data):                      # 128 -> 64 bit: XOR first half with second half
    d = hashlib.md5(data).digest()
    return int.from_bytes(d[:8], "big") ^ int.from_bytes(d[8:16], "big")

def parity(v):                           # sum of the 32 two-bit pairs, keep 2 low bits
    return sum((v >> (2 * i)) & 3 for i in range(32)) & 3

def to_words(v):                         # 64 bits + checksum -> 6 indices of 11 bits
    x = (v << 2) | parity(v)
    return [WORDS[(x >> (55 - 11 * i)) & 0x7FF] for i in range(6)]
```

`python analysis/skey_kat.py` prints `27/27 vector khop ca hex lan sau tu` (27/27 vectors match in
both hex and words), on condition that the seed is lower-cased before being concatenated with the
pass phrase. The same script then runs the checksum test on each heard code: 5 codes have all six
words in the dictionary (3, 4, 5, 6, 7) and 4 of them are checksum-valid (3, 4, 5, 7); code 6 wants
`WATS` where the audio gave `WAVE`. Two conclusions: the display encoding is the standard one, and
the transcript still contains errors, so it cannot be treated as absolute evidence.

**Step 2 - Find the real step function.** Sweep 65 combinations (4 hashes, 4 fold styles, 5 input
forms) and ask whether `step^k(code A)` reproduces `code B`, allowing one word of slack:

```text
ma dung duoc 6 tu (lam bang chung): [3, 4, 5, 6, 7]
so ket hop hash/nap/input da thu: 65
  KHOP  step^1(Code4) ~ Code3  lech=[]   [md5 / xor-nua / chuoi-hex]
  KHOP  step^2(Code5) ~ Code3  lech=[]   [md5 / xor-nua / chuoi-hex]
  KHOP  step^1(Code5) ~ Code4  lech=[]   [md5 / xor-nua / chuoi-hex]
mo hinh RFC (8 byte tho): khong co
```

So `step(v) = fold(MD5("%016x" % v))`: the hashed input is the 16-character lowercase hex string of
the previous value, not its 8 raw bytes. The script also walks codes 2 and 1 forward from code 3
(`GLEN YAWL PEW RUNG BUOY BODY`, `BAIT GAUR OS TACT TIP DUD`), which proves the slots
`GLIN/YALL/RUN` and `BATE/GOWER` are ASR errors rather than real words. With `n=8` and no seed the
chain runs from `code8 = fold(MD5(password))` to `code1 = step^7(code8)`.

**Step 3 - Scan the wordlist through bit masks.** Each code exposes part of its 64-bit value:
slots 1-5 carry 11 bits each, slot 6 carries 9 (its last 2 bits are the checksum). The confidence
per code is `[53, 42, 64, 64, 64, 64, 64, 53]` bits. For a candidate `P`, compute
`v = fold(MD5(P))`, walk 8 steps and at each step test `(v & mask) == value` for every mask of at
least 53 bits. A 53-bit mask already gives roughly 1e-8 expected collisions over 14.3M candidates,
and every hit is expanded back into 8 codes and required to match at least 3 codes exactly.

```text
[*] wordlist C:/Tools/rockyou.txt: 14344391 dong, 14 tien trinh, so bit chac cua tung ma: [53, 42, 64, 64, 64, 64, 64, 53]
[*] mask hit b'idontcare1': 39/48 o khop, 3/8 ma khop het
Code 3    GRUB TRY BABY MUFF GRIM ACME             GRUB TRY BABY MUFF GRIM ACME             == KHOP
Code 4    CUB CUTS GAIN SLUM MUST ELM              CUB CUTS GAIN SLUM MUST ELM              == KHOP
Code 5    RUST HERB BAIL SAVE IFFY DO              RUST HERB BAIL SAVE IFFY DO              == KHOP
[*] 39/48 o tu khop voi transcript, 3/8 ma khop tuyen doi
[+] cdctf{idontcare1}
```

The full scan took 2 m 47 s on 14 processes (`real 2m46.994s` in `analysis/crack_rockyou.log`). The
string is line 39260 of rockyou. The eight codes rebuilt from the password agree with the audio on
39 of 48 slots; the remaining 9 are all near-homophone pairs (`BATE/BAIT`, `GOWER/GAUR`,
`GLIN/GLEN`, `YALL/YAWL`, `RUN/RUNG`, `NO/NOLL`, `HOLD/HOLT`, `WORT/WERT`, `LOSE/LOS`), i.e.
listening errors, not chain errors.

**Step 4 - Check the accompanying PGP key.** `gpg --import` was attempted with the recovered password on `VAT_key` (iterated-and-salted SHA1 S2K, protect-count 65011712, AES-256), and reported `secret key imported`. Successful import alone does not demonstrate that the passphrase unlocks the private key; signing or decryption is needed to verify that.

## Result

```text
cdctf{idontcare1}
```

## Reproduce

```bash
python analysis/skey_kat.py           # 27/27 RFC 2289 vectors + checksum screen
python analysis/chain_model_scan.py   # 65 combinations, only md5/xor-halves/hex-string matches
python exploit.py --selftest          # planted chain: proves the filter can find a positive
python exploit.py --crack C:/Tools/rockyou.txt 14
python exploit.py --verify idontcare1 # rebuild all 8 codes from one string
```

`--selftest` prints `planted duoc bat = True, ba mat khau sai duoc loai = True, round-trip 6-tu = True`,
so the filter is demonstrated to catch a positive before the negative result of the earlier chain
test is trusted. ASR is not on the path to the flag: `files/transcript_asr.txt` already stores the
spoken words, and the commands that produced it are in `de.md` (they need Whisper and Vosk models,
which are not committed). The 140 MB wordlist is not committed either; pass any other list to
`--crack`.
