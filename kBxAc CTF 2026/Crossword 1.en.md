---
title: "Crossword 1"
category: "Crypto"
tags: ["substitution-cipher", "crossword", "image-analysis", "monoalphabetic-substitution"]
solve_date: "2026-10-10T10:40:00+07:00"
language: "en"
points: 100
---

# Crossword 1

**Author:** ayushch  
**Prompt:** *Fill this FOOT…* — the description line is truncated in the supplied data; the flag format is `kBxAc{...}`, and the football theme is confirmed by the solved grid itself. The full flag-construction rule is given in `instructions (1).txt`.  
**Flag:** printed in full below, 616 characters. Submission response not recorded.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `crossword1.zip` | 23,991 | `869fc3a85fc6c8c8a4b0e8e54f125f983df107b93fceabf78300c4c0f8a68e86` |
| `crossword.png` (inside ZIP) | 30,097 | `02eef3e60df6b12a7429055c592db0fb52f763c7268d74f628a113361c942ae8` |
| `instructions (1).txt` | 1,006 | `1cc1b70a9a507046a4182924039d140ce800c2ec49fc93b01f7b1b41f919ae34` |

`instructions (1).txt` has the same SHA-256 as the instruction file shipped with **Crossword 2**: both challenges share one rule set and differ only in grid difficulty.

## Statement and flag construction

Every letter in the grid was replaced by **a randomly assigned number between 1 and 26**, not the standard `1=A, 2=B, ...` mapping. The number-to-letter bijection has to be recovered by solving the intersecting words.

Once solved: read letters **left to right within each row**, drop empty cells, keep rows **top to bottom**, join rows with `_`, then wrap the result in `kBxAc{...}`. The statement's own example shows that a row holding several words is still concatenated into a single run.

## Image analysis

`crossword.png` is a strictly binary `1480×1520` image: no ancillary chunks, no data after `IEND`, and only two pixel values (0 and 255). The lattice is **37 columns × 38 rows** at a 40 px pitch; each cell is a `36×36` white box holding one or two black digits. **572 cells** carry data.

Cropping every cell as a `38×38` window on the 40 px lattice and grouping raw bytes with `Counter` yields **exactly 27 patterns**: one blank pattern occurring 834 times plus 26 digit patterns. Each pattern corresponds to one numeric value, so the whole problem reduces to identifying 26 classes — no per-cell digit reading is required.

## Identifying the 26 values

Splitting the dark strokes of each cell into connected components reveals how many digits it holds: **183 single-digit cells** and **389 two-digit cells**. Collecting every stroke gives 20 glyph shapes, i.e. 10 digits × 2 renderings: 28 px tall glyphs serve the single-digit cells and 21 px tall glyphs the two-digit cells.

The heavier weight is **not a hidden signal**. The 183 single-digit cells match exactly the number of cells carrying values 1–9, and no single-digit cell takes a value ≥ 10. The font simply draws a one-digit number larger so it fills the cell.

The decisive constraint is that every value must lie in 1–26. The tens digit can only be `1` (207 cells) or `2` (182 cells); after a tens `2` the units digit is capped at 0–6. Counting each units glyph by the tens digit that precedes it:

```text
digit  after-tens-1  after-tens-2   total
  0             3             16       19
  1             8              2       10
  2            16             38       54
  3            28              2       30
  4            13             45       58
  5             9             30       39
  6            37             49       86
  7            20              0       20
  8            40              0       40
  9            33              0       33
```

Exactly three glyphs never follow a tens `2` — they are `{7,8,9}`, because `27`, `28` and `29` are all invalid. The three are separable by shape: `7` is a top bar with a leftward diagonal, `8` is two closed loops pinched in the middle, `9` is a closed loop with a right-side descender. The remaining seven glyphs are `{0,1,2,3,4,5,6}`, where `0` is recognised by the diagonal inside its oval (a slashed zero).

Substituting the glyph-to-number table into the grid yields letter runs under an unknown key. The longest runs are the anchors, using their repeated-letter patterns and crossing constraints: the 12-cell run matches `CHAMPIONSHIP` (pattern `ABCDEFGHIBFE`), the 13-cell run matches `COUNTERATTACK`, and the 10-cell run with pattern `ABCCDCCEBF` matches `POSSESSION`; `MIDFIELDER`, `SUBSTITUTE` and `REFEREE` also fit the crossing constraints. The single 15-cell run matches nothing in any dictionary because it is actually two adjacent words in the same column: `PENALTY` + `SHOOTOUT`.

## Substitution key

```text
1=W  2=D  3=E  4=K  5=Z  6=J  7=S  8=M  9=U  10=V  11=G  12=P  13=L
14=B 15=Y 16=C 17=H 18=R 19=O 20=F 21=Q 22=I 23=X 24=T 25=N 26=A
```

The four rarest letters (`Z`, `J`, `X`, `W`) account for only 12 cells and were pinned by `EQUALIZER`, `INJURY`, `JERSEY`, `EXTRATIME`, `FIXTURE`, `WHISTLE`, `SWEEPER`, `WINGER`, `FORWARD`, `DRAW` and `YELLOWCARD`.

## Solver (Python 3 + Pillow)

Run from a directory containing `crossword1.zip`. Because several tile classes share a frequency (38, 16, 3, 2), `labels` is ordered by the **lexicographic order of the raw tile bytes** so the assignment stays deterministic rather than frequency-based.

```python
from PIL import Image
from collections import Counter
from io import BytesIO
import zipfile

# number -> letter, recovered from the intersecting crossword words
number_to_char = {1:'W',2:'D',3:'E',4:'K',5:'Z',6:'J',7:'S',8:'M',9:'U',10:'V',11:'G',
                  12:'P',13:'L',14:'B',15:'Y',16:'C',17:'H',18:'R',19:'O',20:'F',21:'Q',
                  22:'I',23:'X',24:'T',25:'N',26:'A'}

# the 26 tile classes, in lexicographic order of their raw tile bytes
labels = [5,7,9,8,3,2,6,1,4,25,20,23,22,26,21,24,15,17,10,19,18,13,12,16,11,14]

with zipfile.ZipFile('crossword1.zip') as z:
    im = Image.open(BytesIO(z.read('crossword.png'))).convert('L')
    W, H = im.size
    tiles = [[im.crop((c*40, r*40, c*40+38, r*40+38)).tobytes() for c in range(W//40)]
             for r in range(H//40)]
    counts = Counter(t for row in tiles for t in row)
    blank = counts.most_common(1)[0][0]
    uniq = sorted(t for t in counts if t != blank)
    assert len(uniq) == 26, len(uniq)
    tile_to_char = {t: number_to_char[n] for t, n in zip(uniq, labels)}
    rows = [''.join(tile_to_char[t] for t in row if t != blank) for row in tiles]
    flag = 'kBxAc{' + '_'.join(r for r in rows if r) + '}'
    print(flag)
    print('rows', sum(1 for r in rows if r), 'letters', sum(len(r) for r in rows), 'len', len(flag))
```

Output:

```text
rows 38 letters 572 len 616
```

## Validation

The result holds **38 row segments**, **37 underscores** and **572 letters** — matching the grid's data-cell count exactly, so no cell was duplicated or dropped.

All 96 maximal runs (50 across, 46 down) of length ≥ 4 are valid football terms: `CHAMPIONSHIP`, `COUNTERATTACK`, `MIDFIELDER`, `GOALKEEPER`, `QUARTERFINAL`, `TOURNAMENT`, `SUBSTITUTION`, `YELLOWCARD`, `WORLDCUP`, `CENTREBACK`, `ADVANTAGE`, `TARGETMAN`, `PLAYMAKER`, `EQUALIZER`… No cell is left outside a valid word, so neither a misread digit nor a wrong key could pass unnoticed.

SHA-256 of the **flag string as UTF-8, without a trailing newline**:

```text
01b9b0086a3089c0ab567ca77b20ad9807fdc34345025ec4e338447de8a6d30c
```

## Full flag (not truncated)

```text
kBxAc{WHISTLESCOMEBACK_OFULLBACKMEP_UUIVCHAMPIONSSCREST_SCOUTNENCTET_HSEHMATCHHCROSSA_LASWEEPERGKTISD_KILMALCENTREBACKII_INHANDBALLRERENU_CLEATSNEYOCPGRGM_KHRMSOEE_OBOOTSPASSINJURYTIME_FTHKTM_HALFTIMEGIERA_CCOUNTERCHAMPIONSHIP_OFFSIDEFAPQCOH_RORLEAGUECAPTAINJERSEY_NRWINGERKDAQNCEE_EMOEELUCOUNTERATTACK_RAREKSEMIFINALSOS_TLXIPZRVSFO_IDTACKLEETPOSSESSION_SOCCERKREFEREEPLUBX_NUATRELBATTACK_TPTCOACHDEFENSESRU_RHIUIAYTRD_ACADEMYBRACEFINALMIDFIELDER_NTENYATTF_STGOALPENALTYUE_FROMLDSUBSTITUTION_EIAEFLVHEDRIBBLE_RCLNOOAYOUTHE_KPTHROWINOACREDCARD_ANCHORWCTTBALLE_SSAAAFOULEDRAWK_SPITCHRRGUEABII_IDDETINJURYNET_S_TACTICS}
```

## Conclusion

The key point is that the constraint "every value lies in 1–26" identifies the three largest digits `{7,8,9}` on its own, turning an open-ended cryptogram into a finite classification table. The substitution key is **not** the answer: the statement asks for **every letter** in the grid, row by row, including the six cells that belong only to the three-letter words `KIT` (column 31, rows 33–35) and `NET` (row 35, columns 29–31) in the lower-right corner — runs shorter than every other word and easy to drop if only the long words are extracted.
