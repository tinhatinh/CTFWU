# Polyglot - Reverse Engineering (500)

**Flag:** not confirmed yet. Proven prefix `cdctf{SecretOfComp`; suggested submission
`cdctf{SecretOfCompartmentalized}` · **Points:** 500 · **Author:** reep236
**Files:** `Polyglot1.zip` (2313 B, sha256 `f96c6082004222a2c8356d24e0edfb92f8256c5f9986a7d099b5b11089d88555`)

## Challenge

Three files: a "protocol" written in Haskell, 32 question lines, and 32 recovered answer lines that are
each missing part of their content. The information to recover is the module `Secrets` exporting `KEY`,
which `Program1.hs` imports. "far depths of Glasgow, Scotland" points at GHC and at the Glaswegian
dialect. Flag format `cdctf{ABunchOfTitleCaseWords}`.

## Initial analysis

`Program1.hs` is type-level programming (`DataKinds`, `TypeFamilies`, `UndecidableSuperClasses`) and reads
`import Secrets (KEY)` with `KEY` as a `Symbol`. Running it is not possible here: no GHC on the box and no
`Secrets.hs`, so the semantics get reimplemented and inverted instead.

The core is the `LocaleSet` instance. For state `n` and character `c`:

```haskell
locales _ _ =  locale  (Proxy @(Mod (n * CharToNat c) M1))
            :  locales (Proxy @(Mod (n * CharToNat c) M2)) (Proxy @(UnconsSymbol cs))
```

`type M1 = 6`, `type M2 = 7`, `data Locale = Alpha | Beta | Gamma | Delta | Epsilon | Zeta`, and
`dialect = zipWith6 mkForms (locales @1 ls) ... (locales @6 ls)` with `mkForms` person place thing time
method reason. Six chains seeded `n = 1..6`, each step emitting `out = (n * ord c) mod 6` and advancing
`n' = (n * ord c) mod 7`, one chain per column Who/Where/What/When/How/Why through the `\case` in `respond`.

Since the mod-7 part only multiplies, chain j is always `(j * P) mod 7` with `P = ∏ ord(c) mod 7`, so one
mod-7 variable tracks all six chains. `respond` consumes one input line per `Forms`, so the line count
equals `len(KEY)`: `len(KEY) = 32` and the flag body is 25 characters.

The data itself confirms the reading: every answer line has exactly 3 fragments and the category of each
fragment matches the question order on that line. Over 96 slots that is not a coincidence.

## Ruled out

1. **Homoglyph or byte-level stego**: no byte above 0x7F in any of the three files; trailing-space
   histogram is uniform (one per answer line because every variant ends with a space, zero in questions).
   Ruled out.
2. **Hidden zip entries or ADS**: `unzip -l` shows only the folder plus the three files, no comment;
   `dir /r` shows only `Zone.Identifier` added by the browser. Three downloads share md5
   `55e1ce98f5df3c1b44b73f1b6b392531` even after the organizers said the challenge was updated, so the
   attachment did not change. Ruled out.
3. **Question order of lines 21-32 encoding the tail**: lines 1-20 are exactly the 20 3-subsets of the six
   columns in a canonical order, lines 21-32 are the reversed first 12. Pattern, no payload. Ruled out.
4. **The "living chain" branch that would keep the tail constrained**: `python exploit.py files/Polyglot1.zip --alive` (`analysis/alive.log`) shows forbidding a `≡ 0 (mod 7)` char at
   position 18 leaves 528 feasible strings at indices 12-17 and all are consonant junk (`CHCECL`,
   `CHmEmv`); scanning death positions 18, 20, 22, 24, 26, 28, 30 against both a 10k and a 370k word list
   yields no meaningful phrase. Ruled out, so the English branch forces `p` at position 18.
5. **Dictionary search without the flag wrapper**: searching TitleCase dictionary phrases under the raw
   constraints gives zero hits, because positions 1-3 are pinned to lowercase `cdc`. The mistake was
   assuming the body starts at position 1.
6. **Using GHC as an oracle**: no `ghc`, `runghc` or `stack` installed, and `import Data.List (zipWith6)`
   is not even part of base. Ruled out; the hand-written model plus a self-test is enough.

## Exploit chain

**Step 1 - Rebuild the semantics and test the parser.** `exploit.py` simulates `locales` for all six
chains and inverts it into constraints, asserting each fragment sits in the column its question asked.

```bash
python exploit.py files/Polyglot1.zip --selftest
```

```
[selftest] plant = 'GlesgaWeeFreeMenPureDeadlyBampot'
[selftest] KEY cai dat luon nam trong tap kha dung o ca 32 vi tri: True
[selftest] so vi tri bi ep cung 1 chu: 6
```

The self-test plants a known key, generates answers with the same model, then re-runs the filter: the
planted key stays inside the feasible set at all 32 positions, so the later "no more data" conclusions do
not come from a broken probe.

**Step 2 - Tighten constraints with a forward and backward DP.** Keep only mod-7 states that a completable
path actually passes through (fwd ∩ bwd), then count the characters still legal per position.

```bash
python exploit.py files/Polyglot1.zip
```

```
lines = 32  ->  len(KEY) = 32

Ung cu vien cua tung vi tri (chu cai, sau bua backward):
  pos  1  states 1   1 cai: c
  pos  2  states 1   1 cai: d
  pos  3  states 23   2 cai: Wc
  pos  4  states 2   8 cai: DJPVhntz
  pos  5  states 123456   8 cai: BHNZflrx
  pos  6  states 45   3 cai: EQo
  pos  7  states 2   1 cai: S
  pos  8  states 5   1 cai: e
  pos  9  states 1   7 cai: EKQWcou
  pos 10  states 123456   8 cai: BHNZflrx
  pos 11  states 2   1 cai: e
  pos 12  states 6   2 cai: Jt
  pos 13  states 3   9 cai: CIOUagmsy
  pos 14  states 123456   8 cai: BHNZflrx
  pos 15  states 3   2 cai: Cm
  pos 16  states 5   2 cai: Eo
  pos 17  states 2   2 cai: Cm
  pos 18  states 1   8 cai: FLRXdjpv
  pos 19  states 0123456  52 cai: ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz

Ky tu kha dung o vi tri 18 ma cung chia het cho 7: Fp
Tu vi tri 19 tro di, ca 52 chu cai deu kha dung -> duoi KEY khong bi file nay rang buoc.
```

Positions 1-3 pin `cdc`, position 7 pins `S`, position 8 pins `e`, and positions 4-6 admit `t`, `f`, `{`,
so `KEY` is the whole flag string rather than just the body. Over the alphabet, the only readable
18-character start is `cdctf{SecretOfComp`: `Se`+`cr`+`e`+`t` = `Secret`, `O`+`f` = `Of`, then `C`+`o`+`m`+`p`
opens a `Comp*` word.

**Step 3 - Show the ambiguity with the data itself.** The mod-7 state is absorbing: once `P = 0` every
column answers Alpha whatever the character, and `p` (112) at position 18 makes `P = 0`. Four keys with
different tails all reproduce the 32 lines, while two deliberately wrong strings break immediately:

```bash
python exploit.py files/Polyglot1.zip "cdctf{SecretOfCompartmentalized}"
```

```
KEY = 'cdctf{SecretOfCompartmentalized}' (32 ky tu, du 32 dong)  khop 32/32 dong | TAI TAO DU TOAN BO SO DONG DA KIEM
```

```
KEY = 'cdctf{SecretOfCompartmentalised}' (32 ky tu, du 32 dong)  khop 32/32 dong | TAI TAO DU TOAN BO SO DONG DA KIEM
KEY = 'cdctf{SecretOfCompoundSentences}' (32 ky tu, du 32 dong)  khop 32/32 dong | TAI TAO DU TOAN BO SO DONG DA KIEM
KEY = 'cdctf{SecretOfComprehensiveness}' (32 ky tu, du 32 dong)  khop 32/32 dong | TAI TAO DU TOAN BO SO DONG DA KIEM
KEY = 'cdctf{WrongPhraseEntirelyWrong}' (31 ky tu, ph bao 31/32 dong)  khop 17/31 dong | lech dong 7,8,9,10,11,12,13,15,16,17,18,19,20,21
```

All 52 letters being legal from position 19 onward means the rest of the body is a phrase, not a protocol
output. The author then confirmed it: reep236 said the flag was too long after moving dev to testing, his
verification script missed inputs that still passed, and the checker was rewritten as a regex anchored at
the end of the ambiguous region, so any tail after `cdctf{SecretOfComp` is accepted.

## Flag

Region proven from the data:

```
cdctf{SecretOfComp
```

Submission under the author's updated checker:

```
cdctf{SecretOfCompartmentalized}
```

## Reproduce

```bash
python exploit.py files/Polyglot1.zip
python exploit.py files/Polyglot1.zip --selftest
python exploit.py files/Polyglot1.zip "cdctf{SecretOfCompartmentalized}"
python exploit.py files/Polyglot1.zip "cdctf{WrongPhraseEntirelyWrong}"
python exploit.py files/Polyglot1.zip --alive
python exploit.py files/Polyglot1.zip --invariant
```

Real output of the first three lives in `analysis/regions.log`, `analysis/selftest.log`, `analysis/verify.log`.
