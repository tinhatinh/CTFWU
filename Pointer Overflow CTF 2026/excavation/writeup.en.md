# Excavation (RE-100) - Pointer Overflow CTF 2026

Flag / accepted answer: `2VE5EKXUA5IV2R57`

```
POST /challenges/excavation/submit  {"flag":"2VE5EKXUA5IV2R57"}
{"correct":true,"message":"Correct."}
```

## 1. What the challenge gives

Four `.sav` files from a fictional RPG: three sample files from different stored runs, and one `team.sav` generated specifically for the team and "carrying a 16-character token". No file-reading tool, no format. The format has to be inferred from the four files themselves.

## 2. Initial analysis

The first 12 bytes of all four files are identical:

```
9e e1 c7 21 | 02 00 | 02 00 | d2 01 00 00     sample1
9e e1 c7 21 | 02 00 | 02 00 | 59 03 00 00     sample2
9e e1 c7 21 | 02 00 | 02 00 | 78 04 00 00     sample3
9e e1 c7 21 | 02 00 | 02 00 | 66 05 00 00     team
```

The last four bytes of the header are a u32 little-endian and equal the file size exactly: 466, 857, 1144, 1382. So the body starts at offset 12, while the header is not encoded.

Autocorrelation over the body (counting the ratio `body[i] == body[i+L]`) shows a very clear peak at multiples of 8:

```
sample1  lag 8 = 0.058, lag 16 = 0.043, lag 24 = 0.044, còn lại <= 0.015
team     lag 8 = 0.045, lag 16 = 0.048, lag 24 = 0.047, còn lại <= 0.008
```

That is the signature of an 8-byte repeating XOR key.

## 3. Directions tried and ruled out

**One shared key for all four files.** The `team.sav` key only gets the other files to 10-17% alphabetic bytes, while it itself reaches 72%. Each file has its own key:

```
sample1  bff366a0192308a7
sample2  8ee28d4183df8c1b
sample3  e62903e8dcf7b038
team     1337df4e77c16cc7
```

**The plaintext is plain text.** After XOR with the key, `team.sav` still has 260/1370 bytes outside the printable range, and they are spread evenly over all 8 columns (28 to 36 bytes per column). So no key column is wrong, and the file genuinely contains binary fields.

**The key rotates per record.** This is the easiest direction to get wrong, because the "strange" bytes are interleaved into the readable text. But the records of the same item in two different files match each other byte for byte over stretches longer than 60 bytes:

```
sample1: 21 20 37 72 55 53 54 45 44 00 53 50 49 52 49 54 0d 4d ... 4c 45 00 57 45 49 47 48 54 0e
team   : 21 20 37 72 55 53 54 45 44 00 53 50 49 52 49 54 0d 4d ... 4c 45 00 57 45 49 47 48 54 0e
```

The key is right and the plaintexts coincide, so those odd bytes are real data in the file.

**The token is a 16-character run inside the text.** `re.finditer(rb'[A-Z0-9]{16,}')` and `[A-Za-z0-9_]{14,}` return no match at all on any of the four files.

**The token is the last 14 bytes of the final location record.** All four files end with exactly 14 bytes:

```
sample1  00 00 00 00 00 00 fd ff ff ff 8a 3a 82 c6
sample2  30 fd ff 79 05 00 d6 ff ff ff 9c 45 62 ea
sample3  c6 07 00 75 f3 ff e0 ff ff ff c0 51 d5 eb
team     fc fa ff 60 02 00 9f ff ff ff 5f 53 9d 05
```

They are binary fields (a negative `i32`, a `ff ff ff` sentinel, four checksum bytes), a constant length of 14, and they do not encode 16 characters. This direction is wrong.

## 4. The crux: two layers, not one

One detail breaks every "plain text" reading: the **first** letter of each word is lowercase while the rest are uppercase (`mIDDLE RANK OF A DISCONTINUED ORDER`). The stopgap `byte < 0x20 -> byte + 0x20` makes the text read through, but the string lengths stay meaningless.

The genuinely decisive step was examining the 6 bytes standing in front of every string. The alphabet in the file is ASCII already XORed with `0x20`, so `space` becomes `0x00`, `-` becomes `0x0d`, `.` becomes `0x0e`, `'` becomes `0x07`, `:` becomes `0x1a`, and **the length bytes have bit 5 flipped as well**:

```
'/' = 0x2f  ^0x20 = 15   "Obsidian censer"            15 byte
 0x05       ^0x20 = 37   "Fingerprints of five different hands."   37 byte
 0x3c       ^0x20 = 28   "Warm regardless of the room."            28 byte
 0x28       ^0x20 =  8   "K. Ansen"                   8 byte
```

Applying `^ 0x20` to the entire body puts everything back in normal form: ordinary Title Case text, space decoding to space, and the binary fields turning into sensible small numbers. As it turns out, the body is encoded with **two** layers:

```
body = struct ^ 0x20 ^ key[i % 8]
```

## 5. The reversed format

12-byte header, not encoded:

```
u8[4]  magic 9e e1 c7 21
u16    0x0002
u16    0x0002
u32    kích thước file (LE)
```

The body is a sequence of records, and each record describes its own length through its prefixes:

```
record nhân vật   01  u32  u8 namelen  name  ...  u16 item_count  u8 0
record item       10  u8 idx  u8 a  u8 b  u8 namelen  name  u16 desclen  desc
record nhật ký    02/03  u8 0  u8 idlen  "S<run>D<n>"  u16 desclen  text
record vị trí     04  u32  u8 5  u32 size  u8 namelen  name  14 byte cuối
```

Points to remember when writing the parser yourself: the name string length is `u8`, the description string length is `u16 LE`, and both have bit 5 flipped.

The item count matches the number stored in the character record:

| file | item_count | `0x10` records parsed |
|---|---|---|
| sample1 | 5 | 5 |
| sample2 | 10 | 10 |
| sample3 | 13 | 13 |
| team | 16 | 16 |

## 6. Token

The challenge had already said it: *"The flag for this challenge is a little different"*, and the log of `team.sav` contains the line *"I notice its voice most in the items I've collected in a particular order. First things first, I think."*

Take the first letter of each item name in the exact inventory order:

```
sample1  Talcum-stained token, Obsidian censer, Rusted spirit-medallion,
         Cracked seance disc, Hair-braid amulet
         -> TORCH

sample2  Silver-thread bandage, Ivory dial-plate, Lead-bound envelope,
         Vessel-key, Ember-in-glass, Rusted spirit-medallion, Marrow-quill pen,
         Obsidian censer, Obsidian censer, Needle of the Bureau
         -> SILVERMOON

sample3  Needle, Ivory, Ghost-key, Hair-braid, Talcum, Ember, Needle,
         Doubling mirror, Silver, Silver, Obsidian, Obsidian, Needle
         -> NIGHTENDSSOON          ("NIGHT ENDS SOON")
```

All three samples are meaningful English, so the rule was proven with the author's own data rather than guessed at. `team.sav` has 16 items and yields exactly 16 characters:

```
 0 2-star runic band        -> 2      8  Ash-glazed lantern        -> A
 1 Vessel-key               -> V      9  5-knot cord               -> 5
 2 Ember-in-glass           -> E     10  Ivory dial-plate          -> I
 3 5-knot cord              -> 5     11  Vessel-key                -> V
 4 Ember-in-glass           -> E     12  2-star runic band         -> 2
 5 Knotted willow charm     -> K     13  Rusted spirit-medallion   -> R
 6 Xylophone plate          -> X     14  5-knot cord               -> 5
 7 Uncoiling rope           -> U     15  7-day candle              -> 7
```

```
2VE5EKXUA5IV2R57
```

The three items whose names begin with a digit (`2-star runic band`, `5-knot cord`, `7-day candle`) appear only in `team.sav`, not in the three sample files. Those are items the author added so that digits could be encoded in the team's token.

Submitting the token:

```
$ curl -s -X POST https://pointeroverflowctf.com/challenges/excavation/submit \
    -H 'Content-Type: application/json' -b cookies.txt \
    -d '{"flag":"2VE5EKXUA5IV2R57"}'
{"correct":true,"message":"Correct."}
```

The wrapped form `POCTF{2VE5EKXUA5IV2R57}` was rejected (`Incorrect. Keep working.`), and the endpoint returns no flag string to record. The challenge page displays `>> ACK :: Correct.`.

## 7. Reproduce

```
cd excavation
python exploit.py
```

`exploit.py` recovers the 8-byte key of all four files by itself (no key is entered by hand), strips the `^0x20` layer, parses the `0x10` records and prints the acrostic. Keys are selected by a byte-distribution model learned from the best-decoding file itself, so `sample3` also comes out with the correct key (`e62903e8dcf7b038`) instead of being off by one byte as a crude scoring pass would leave it.

The intermediate files in `analysis/`: `*.pt` is the body after the first XOR layer, `*.dec` is the provisional reading produced by the `+0x20` rule for control bytes only, `*.true` is the real struct after both layers.
