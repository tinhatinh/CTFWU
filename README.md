# CTF Writeups

My own writeups from competitive CTF events. I play with **R3:TURИ**
([CTFTime team 449538](https://ctftime.org/team/449538)): minhduc26122913, k4tpr02k5, Tikilazada,
tinhatinh, Lizamort1 - their solutions live in their own repos, this one is only mine.

**Rendered site:** <https://tinhatinh.github.io/CTFWU/> (Jekyll + [Chirpy](https://github.com/cotes2020/jekyll-theme-chirpy), deployed by GitHub Actions).

## Site

The archive layout below is the source of truth. The site is assembled into a staging tree so the
1.3 GB of challenge artifacts in this repo never reach `_site`:

```bash
python tools/build_site.py              # writes _site_src/ and _site_src_en/, 55 posts each
```

`_site_src/` (Vietnamese) and `_site_src_en/` (English) are generated and git-ignored - never edit
them. The generator reads each `<Event>/<slug>/writeup.md` and `writeup.en.md`, takes the publish
date from `tools/solve_times.json` (the moment the flag was written during the contest; an entry
with no clock time means the file was copied in bulk, so only the day is evidenced), reads the
category from the event's `README.md` table, generates the `competitions` and `about` tabs, copies
referenced images to `assets/writeups/<event>/<case>/`, and wraps every body in `{% raw %}` because
writeups quote Liquid syntax (`{{7*7}}`, `{% ... %}`) that Jekyll would otherwise try to execute.
GitHub Actions runs it before building, so the site cannot drift from the archive.

## Competitions

| Event | Date | Writeups | Categories |
|-------|------|----------|------------|
| [H7CTF 2026 Quals](H7CTF%202026%20Quals/) | Sep 2026 | 29 | Pwn · Crypto · Web · Web3 · Hardware · Forensics · Mobile · Cloud · AI · Rev · OSINT · Misc |
| [SunshineCTF 2026](SunshineCTF%202026/) | Sep 2026 | 18 | Pwn · Web · Crypto · Forensics · Misc |
| [Pointer Overflow CTF 2026](Pointer%20Overflow%20CTF%202026/) | Sep 2026 | 8 | Crypto · EXP · Forensics · Misc · OSINT · RE · Steg · Web |

**Total: 55 writeups**

## Structure

Each challenge directory follows a consistent layout:

```
<challenge-name>/
  writeup.md     Solution walkthrough with exploitation chain and flag
  writeup.en.md  English edition: prose translated, every fenced block byte-identical to the Vietnamese
  de.md          Original challenge description and verified metadata
  notes.md       Step-by-step investigation log (including dead ends)
  flag.txt       Captured flag string
  exploit.py     Reproducible solve script (reads artifacts from argv)
  analysis/      Exploratory scripts for each investigation phase
  files/         Original challenge artifacts (unmodified)
```

## Conventions

- Flags are recorded only when they appear verbatim in command output. No guessing.
- Every claim in `writeup.md` traces back to a command logged in `notes.md`.
- Dead-end hypotheses are preserved in the "Eliminated hypotheses" section — these are often the most educational parts.
- Solve scripts are self-contained and can be re-run against a live instance.
- Flag prefixes vary between challenges (even within the same event). Always verify before scanning.

## Quick Navigation

<details>
<summary><b>H7CTF 2026 Quals - 29 challenges</b></summary>

| Challenge | Category | Difficulty | Flag |
|-----------|----------|------------|------|
| [arcel-bomb](H7CTF%202026%20Quals/arcel-bomb/) | Pwn | Medium | `H7CTF{0b79ca94-…}` |
| [countersign](H7CTF%202026%20Quals/countersign/) | Rev | Insane | `H7CTF{011c87d4-…}` |
| [deep-freeze](H7CTF%202026%20Quals/deep-freeze/) | Forensics | Hard | `H7CTF{bf3a8e98…}` |
| [deputy](H7CTF%202026%20Quals/deputy/) | Cloud | Hard | 4 flags |
| [dog-whistle](H7CTF%202026%20Quals/dog-whistle/) | Hardware | Insane | `H7CTF{3c48f268-…}` |
| [echo-chamber](H7CTF%202026%20Quals/echo-chamber/) | AI | Medium | `H7CTF{174f034a-…}` |
| [genesis](H7CTF%202026%20Quals/genesis/) | Web3 | Medium | `H7CTF{346df380-…}` |
| [ghost-on-the-bus](H7CTF%202026%20Quals/ghost-on-the-bus/) | Hardware | Medium | `H7CTF{10d9b516-…}` |
| [hear-no-evil](H7CTF%202026%20Quals/hear-no-evil/) | Hardware | Medium | 2 flags |
| [justified](H7CTF%202026%20Quals/justified/) | Web | Medium | `WEBVERSE{d5f607…}` |
| [kick-the-can](H7CTF%202026%20Quals/kick-the-can/) | Hardware | Medium | `H7CTF{6360cbb3-…}` |
| [kintsugi-vault](H7CTF%202026%20Quals/kintsugi-vault/) | Rev | Hard | `H7CTF{9df8f215-…}` |
| [loose-ends](H7CTF%202026%20Quals/loose-ends/) | Pwn | Hard | `H7CTF{4d0e9693-…}` |
| [loose-lips](H7CTF%202026%20Quals/loose-lips/) | Crypto | Hard | 2 flags |
| [manifest-destiny](H7CTF%202026%20Quals/manifest-destiny/) | Pwn | Medium | `H7CTF{a2b24085-…}` |
| [merged](H7CTF%202026%20Quals/merged/) | Web | Medium | `WEBVERSE{8ba2f5…}` |
| [meridian-pay](H7CTF%202026%20Quals/meridian-pay/) | Mobile | Hard | 3 flags |
| [mic-drop](H7CTF%202026%20Quals/mic-drop/) | Hardware | Medium | `H7CTF{7f0cb1b6-…}` |
| [open-sesame](H7CTF%202026%20Quals/open-sesame/) | Hardware | Hard | `H7CTF{f6091c17-…}` |
| [owners-draw](H7CTF%202026%20Quals/owners-draw/) | Crypto | Medium | `H7CTF{786dff67-…}` |
| [papers-please](H7CTF%202026%20Quals/papers-please/) | Pwn | Easy | `H7CTF{b66621cc-…}` |
| [patient-exfil](H7CTF%202026%20Quals/patient-exfil/) | Forensics | Medium | `H7CTF{6787b86c…}` |
| [radio-silence](H7CTF%202026%20Quals/radio-silence/) | Hardware | Medium | `H7CTF{6780856d-…}` |
| [shared-blood](H7CTF%202026%20Quals/shared-blood/) | Crypto | Medium | `H7CTF{a727587f-…}` |
| [splice](H7CTF%202026%20Quals/splice/) | Web | Hard | `WEBVERSE{fcb61c…}` |
| [take-two](H7CTF%202026%20Quals/take-two/) | Crypto | Hard | `H7CTF{63b0dde3-…}` |
| [tapeout](H7CTF%202026%20Quals/tapeout/) | Misc | Hard | `H7CTF{afd4beac-…}` |
| [trace-amounts](H7CTF%202026%20Quals/trace-amounts/) | Hardware | Medium | `H7CTF{48333086-…}` |
| [trompe-loeil](H7CTF%202026%20Quals/trompe-loeil/) | Web3 | Hard | `H7CTF{0bba5486-…}` |

</details>

<details>
<summary><b>SunshineCTF 2026 - 18 challenges</b></summary>

| Challenge | Category | Difficulty | Flag |
|-----------|----------|------------|------|
| [cache-money](SunshineCTF%202026/cache-money/) | Pwn | Hard | `sun{s4fe_l1nk…}` |
| [code-breaker](SunshineCTF%202026/code-breaker/) | Crypto/Pwn | Hard | `sun{cr4ck_tHe…}` |
| [cookiecorp](SunshineCTF%202026/cookiecorp/) | Web | Medium | `sun{c00kie_ja…}` |
| [groundhog_day](SunshineCTF%202026/groundhog_day/) | Web | Hard | `sun{s1x_m0r3_…}` |
| [homemaker](SunshineCTF%202026/homemaker/) | Pwn | Hard | `sun{the_futur…}` |
| [madlibs](SunshineCTF%202026/madlibs/) | Pwn | Medium | `sun{f1ll_iN_t…}` |
| [my-eyes-burn](SunshineCTF%202026/my-eyes-burn/) | Misc | Medium | `sun{praisethesun}` |
| [nas-coal](SunshineCTF%202026/nas-coal/) | Forensics | Medium | `sun{yup_issa_gem}` |
| [planetary-probe](SunshineCTF%202026/planetary-probe/) | Web | Hard | `sun{bl1nd_psq…}` |
| [print-print-revolution](SunshineCTF%202026/print-print-revolution/) | Pwn | Hard | `sun{cust0m_fm…}` |
| [robocall](SunshineCTF%202026/robocall/) | Pwn | Hard | `sun{you_must_…}` |
| [safe-house](SunshineCTF%202026/safe-house/) | Pwn | Hard | `sun{n3gat1ve_…}` |
| [sitecheck](SunshineCTF%202026/sitecheck/) | Web | Hard | `sun{fr4gm3nt3…}` |
| [suntrail](SunshineCTF%202026/suntrail/) | Misc | Medium | `sun{qwerty_sucks}` |
| [total_recall](SunshineCTF%202026/total_recall/) | Pwn | Medium | `sun{r3caLl_ev…}` |
| [vecnet](SunshineCTF%202026/vecnet/) | Web | Hard | `sun{k33p_your…}` |
| [welcome-call](SunshineCTF%202026/welcome-call/) | Forensics | Medium | `sun{thankyouforplaying}` |
| [you-cut-me-off](SunshineCTF%202026/you-cut-me-off/) | Forensics | Medium | `sun{totallyoriginalchallengeidea}` |

</details>

## Tools Used

Solves are built with minimal dependencies - most use only Python stdlib (`socket`, `struct`, `hashlib`) or Node.js with `ethers.js` for Web3 challenges. No `pwntools` - all exploit scripts run on any OS including Windows.

## License

Educational use. Challenge descriptions and flag strings remain the property of their respective CTF organizers.
