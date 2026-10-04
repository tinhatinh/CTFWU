# Crypto Cat Caticus Catanius (3/5) - Crypto (498 points)

**Flag:** `cdctf{any monoalphabetic sub'stitution cipher can be cracked through sta'tistical analysis given su'fficient cipher text for the numbers to be figured out mathematically and such}` · **Files:** `files/ciphertext.txt`, 180 bytes, sha256 `742a5555bc13ed0d6336b29673baba2dca97ebfc77ad905989ca4015083233ed`
**Event:** CDCTF 2026 (Crimson Defense CTF) · **Author:** alex

## Problem Description

Part 3/5 of the Crypto Cat series: 179 characters printed on the card, no download, no instance. The
ciphertext keeps spaces, the `{}` pair and three apostrophes, so the word shape (token lengths, brace
positions) is readable straight off the problem statement.

## Initial Analysis

- 151 letters, 22 distinct, Index of Coincidence = 0.0580. English under a single alphabet measures
  about 0.066; a multi-alphabet Vigenère flattens toward 0.045. 0.0580 motivates testing a single alphabet, but IC alone is inconclusive for this short sample.
- Two tokens repeat verbatim: `wezmrf` (6 letters) at tokens 4 and 13, `kr` (2 letters) at tokens 6 and
  19. The gaps are 59 and 75 letters, gcd = 1.
- If the repeated words represent the same plaintext at the same key phase, a Vigenère period would divide both 59 and 75, leaving L = 1. This assumption motivates testing monoalphabetic substitution; it does not exclude every polyalphabetic cipher.
- The apostrophes initially suggested contractions. The recovered words are `sub'stitution`, `sta'tistical`, and `su'fficient`; preserve those apostrophes when copying the plaintext.

## Rejected Approaches

All figures come from `analysis/triage_poly.py` (`analysis/triage_poly.out`).

1. **Vigenère / variant Beaufort / Beaufort with a key repeating over letters.** The `cdctf` crib on the
   first five letters gives `K[0..4] = u,z,u,w,g`; adding the `can't` and `we'll` readings at letter
   positions 22-25 and 83-86 leaves exactly L = 13 alive for all three conventions. 13 does not divide
   59, contradicting the repeat measurement. Rejected.
2. **Key advancing on every character** (counting spaces, braces, quotes). The repeats sit 70 and 90
   characters apart, under the same-phase assumption, L must divide 10, i.e. L ∈ {2, 5, 10}. Rerunning the same cribs in that index
   space returns an empty list of surviving periods from 1 to 20, for all three conventions. Rejected.
3. **Autokey** (primer + plaintext and primer + ciphertext, m = 1..8, all three conventions). No
   candidate reached two common English words. At m = 3 the plaintext-autokey opens with `cdctf{one`
   and then decays into `eucdwswqybrqvt`. Rejected.
4. **IC per candidate key length** shows no single spike: L = 9 and 18 give 0.0767 and 0.0776, but 18
   does not divide 59, and L = 8 and 16 are within the noise band for a 151-letter sample. Not
   evidence, and already covered by (1) and (2). Rejected.

## Exploitation Chain

**Step 1 - Flag-format crib.** The first token `wcwpl{qgj` has shape `ABACD{`, which matches `cdctf{`,
giving the first four mappings `w→c, c→d, p→t, l→f`.

**Step 2 - Grow through the short tokens.** Those four turn the 2-4 letter words into near-complete
frames: `pmr` = `t?e` → `the` (m→h, r→e), `ph` = `t?` → `to` (h→o), `lhf` = `f?r` → only `for` (f→r),
`prdp` = `te?t`.

```text
pmr -> the    ph -> to    lhf -> for    prdp -> te?t
```

**Step 3 - The repeated word locks the table.** `wezmrf` = `c?pher` under `r→e, m→h`, so it has to be
`cipher`, giving `e→i` and `z→p`. From there `leovfrc` = `f?gur?d` → `figured` (o→g, v→u),
`wfqwyrc` = `cr?ck?d` → `cracked` (q→a, y→k), and `pmfhvom` = `through` re-checks everything.

**Step 4 - Fill the remaining letters with word frames.** The eight unmapped letters (`g,n,u,k,s,t,d,j`)
close one at a time: `sqpmrsqpewquuj` = `?athe?atic???` is only `mathematically` (s→m, u→l, j→y),
`shghquzmqkrpew` = `?o?oa?pha?etic` is only `monoalphabetic` (g→n, k→b), `qgc` = `a.d` → `and`
(confirms g→n), `oetrg` = `gi.e?` → `given` (t→v), `nvwm}` = `?uch` → `such`, and `prdp` = `te?t` →
`text` (d→x; `test` is impossible because plain `s` already belongs to cipher `n`).

**Step 5 - Verification.** The table holds 22 injective mappings, which is exactly what a bijection over
the alphabet demands: the ciphertext omits four letters (`a,b,i,x`) and the plaintext must omit four as
well, measured as `j,q,w,z`. Re-encrypting the plaintext through the inverse table reproduces all 179
characters of the card, all 24 tokens are English words, and no character is left undecoded.

```text
[*] ban tho dung 22 chu cai phan biet, bang so chu cua ban ma (22): True
[+] round-trip: ma hoa lai ban tho bang bang the nguoc tai tao dung 179 ky tu cua de -> True
```

Final table (`analysis/table.out`, printed from the dict inside `exploit.py`). Top row is the
ciphertext letter, bottom row the plaintext letter:

```text
ma : . . d x i r n o . y b f h s g t a e m v l u c . k p
co : a b c d e f g h i j k l m n o p q r s t u v w x y z
```

And the reverse direction:

```text
co : q k w c r l o m e . y u s g h z . f n p v t . d j .
ma : a b c d e f g h i j k l m n o p q r s t u v w x y z
```

## Flag

```bash
python exploit.py files/ciphertext.txt
```

```text
[*] ciphertext.txt: 151 chu cai, 22 chu phan biet, IC = 0.0580
    tan suat top 6: p:17 q:13 r:13 e:13 w:12 g:9
[*] tu lap lai 'wezmrf': cach 59 chu cai, 70 ky tu
[*] tu lap lai 'kr': cach 75 chu cai, 90 ky tu
[*] bang the 22 anh xa, don anh, 22 chu cai trong ban ma duoc phan anh het
    chu vang trong ban ma: abix | chu vang trong ban tho: jqwz
[*] ban tho dung 22 chu cai phan biet, bang so chu cua ban ma (22): True
[+] round-trip: ma hoa lai ban tho bang bang the nguoc tai tao dung 179 ky tu cua de -> True
[+] plaintext: cdctf{any monoalphabetic sub'stitution cipher can be cracked through sta'tistical analysis given su'fficient cipher text for the numbers to be figured out mathematically and such}
[+] da luu flag.txt
```

## Reproduce

```bash
python exploit.py files/ciphertext.txt
```

`analysis/triage_poly.py` carries the polyalphabetic rejection (IC per key length, repeat distances,
cribs in both index spaces, autokey sweep); its output is stored as `analysis/triage_poly.out`. There is
no downloaded artifact, `files/ciphertext.txt` is a verbatim copy of the card text including the three
apostrophes. If the grader rejects the apostrophes, the stripped variant is
`cdctf{any monoalphabetic substitution cipher can be cracked through statistical analysis given sufficient cipher text for the numbers to be figured out mathematically and such}`.
