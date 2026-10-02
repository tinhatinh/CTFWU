# CTF Writeups

My own writeups from competitive CTF events. I play with **R3:TURИ**
([CTFTime team 449538](https://ctftime.org/team/449538)): minhduc26122913, k4tpr02k5, Tikilazada,
tinhatinh, Lizamort1 - their solutions live in their own repos, this one is only mine.

**Rendered site:** <https://tinhatinh.github.io/CTFWU/> (custom Jekyll interface, deployed by GitHub Actions).

## Site

The archive layout below is the source of truth. The site is assembled into a staging tree so the
1.3 GB of challenge artifacts in this repo never reach `_site`:

```bash
python tools/build_site.py              # writes _site_src/ and _site_src_en/, 72 posts each
```

`_site_src/` (Vietnamese) and `_site_src_en/` (English) are generated and git-ignored - never edit
them. The generator reads each `<Event>/<slug>/writeup.md` and `writeup.en.md`, takes the publish
date from `tools/solve_times.json` (the moment the flag was written during the contest; an entry
with no clock time means the file was copied in bulk, so only the day is evidenced), reads the
category from the event's `README.md` table, generates the `competitions` and `about` tabs, copies
referenced images to `assets/writeups/<event>/<case>/`, and wraps every body in `{% raw %}` because
writeups quote Liquid syntax (`{{7*7}}`, `{% ... %}`) that Jekyll would otherwise try to execute.
GitHub Actions runs it before building, so the site cannot drift from the archive.

The interface lives in `site/_layouts/`, `site/_includes/`, `site/assets/css/campus.css`,
and `site/assets/js/site.js`. Shared interface translations are in `site/_data/interface.json`.
The homepage shows the six most recent writeups by solve date. Counts, event metadata,
source links, and search text come from the archive via `tools/build_site.py`.
The archive supports accent-insensitive search, category/event filters, sorting, and shareable
query strings. The reader includes syntax highlighting, code copying, and a generated TOC.
All writeups and navigation remain available without JavaScript.

To preview and check the same two-language tree used in deployment:

```bash
bundle install
python tools/build_site.py
bundle exec jekyll build -s _site_src -d _build/preview/CTFWU
bundle exec jekyll build -s _site_src_en -d _build/preview/CTFWU/en
bundle exec htmlproofer _build/preview --disable-external
python tools/serve_site.py --skip-build
# Open http://localhost:4173/CTFWU/
```

Rebuild Vietnamese before English: the English output is nested inside the Vietnamese tree.

The team's CTFTime results come from `tools/ctftime_team.json`. GitHub Actions refreshes the
snapshot on builds and every 12 hours (07:00 / 19:00 UTC+7, subject to GitHub scheduling delays).
Scheduled and manual runs commit a changed snapshot, then build and deploy both language trees.
The generator itself works offline. To refresh locally:

```bash
python tools/fetch_ctftime.py     # re-scrape https://ctftime.org/team/449538, then commit the JSON
```

If the JSON is missing the section is skipped with a warning; if CTFTime changes its markup the
fetcher refuses to write an empty file, so the site keeps the last real numbers.

## Editing writeups in the browser

```bash
python tools/serve_site.py              # build, then serve on 127.0.0.1:4173
python tools/serve_site.py --skip-build # reuse an existing preview
python tools/test_editor.py            # data integrity and request security checks
```

Open a writeup and choose **Sửa writeup / Edit writeup**. Authenticate with a GitHub personal
access token belonging to the owner of `tinhatinh/CTFWU`. The server verifies the authenticated
GitHub user ID against the repository owner ID; collaborator access and Git commit names do
not grant editing rights. A fine-grained token with public repository metadata access is enough;
the editor does not need permission to push. The GitHub token is not persisted. The owner session
uses an HttpOnly, SameSite cookie, expires after eight hours, and can be signed out.

Choose **Tiếng Việt (VN)**, **English (EN)**, or **Cả VN và EN / Both VN and EN**. The editor saves
the corresponding original files, creates backups in `_build/editor-backups/`, then rebuilds.
Choosing both submits both drafts together; all versions are checked before any file is replaced,
and a write failure rolls back replacements. Content is not translated automatically. Unsaved
changes in an unselected edition are retained in the editor after saving the selected edition.
An external file change causes a conflict instead of silently overwriting it. If a build fails, the source remains
saved and its backup is preserved; diagnostics are in `_build/editor-build.log`.

The server binds only to loopback and checks origin/session for saves. Do not expose it via
a tunnel or change it into a public server. It needs Ruby/Bundler, or Docker with the cached
`ruby:3.4-slim` image and gems in `ctfwu-bundle`. To prepare the Docker fallback in PowerShell:

```powershell
docker run --rm -v "${PWD}:/work" -v ctfwu-bundle:/usr/local/bundle -w /work ruby:3.4-slim sh -c "apt-get update && apt-get install -y build-essential git libcurl4 && bundle install"
python tools/serve_site.py
```

Public GitHub Pages remains a read-only site without editor controls. Repository edits made
directly on GitHub trigger a rebuild when committed to the deployment branch. Public Pages
cannot write directly to files on your computer. Local saves do not commit or push automatically.

## Adding writeups with another AI

Read [AI_README.md](AI_README.md) for the source layout, new-competition checklist, bilingual
content rules, solve timestamps, verification commands, and deployment conventions. New
competitions without a cover image receive a generated placeholder automatically.

## Competitions

| Event | Date | Writeups | Categories |
|-------|------|----------|------------|
| [H7CTF 2026 Quals](H7CTF%202026%20Quals/writeup.md) | Sep 2026 | 29 | Pwn · Crypto · Web · Web3 · Hardware · Forensics · Mobile · Cloud · AI · Rev · OSINT · Misc |
| [SunshineCTF 2026](SunshineCTF%202026/writeup.md) | Sep 2026 | 18 | Pwn · Web · Crypto · Forensics · Misc |
| [Pointer Overflow CTF 2026](Pointer%20Overflow%20CTF%202026/writeup.md) | Sep 2026 | 8 | Crypto · EXP · Forensics · Misc · OSINT · RE · Steg · Web |
| [CSS CTF 2026: Return of Nexus](CSS%20CTF%202026/writeup.md) | Oct 2026 | 17 | Web · Pwn · Crypto · Forensics · OSINT · Misc · Reverse Engineering · Web3 |

**Total: 72 writeups**

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
- Dead-end hypotheses are preserved in the "Eliminated hypotheses" section - these are often the most educational parts.
- Solve scripts are self-contained and can be re-run against a live instance.
- Flag prefixes vary between challenges (even within the same event). Always verify before scanning.

## Quick Navigation


<details>
<summary><b>H7CTF 2026 Quals - 29 challenges</b></summary>

| Challenge | Category | Difficulty | Flag |
|-----------|----------|------------|------|
| [arcel-bomb](H7CTF%202026%20Quals/arcel-bomb/writeup.md) | Pwn | Medium | `H7CTF{0b79ca94-…}` |
| [countersign](H7CTF%202026%20Quals/countersign/writeup.md) | Rev | Insane | `H7CTF{011c87d4-…}` |
| [deep-freeze](H7CTF%202026%20Quals/deep-freeze/writeup.md) | Forensics | Hard | `H7CTF{bf3a8e98…}` |
| [deputy](H7CTF%202026%20Quals/deputy/writeup.md) | Cloud | Hard | 4 flags |
| [dog-whistle](H7CTF%202026%20Quals/dog-whistle/writeup.md) | Hardware | Insane | `H7CTF{3c48f268-…}` |
| [echo-chamber](H7CTF%202026%20Quals/echo-chamber/writeup.md) | AI | Medium | `H7CTF{174f034a-…}` |
| [genesis](H7CTF%202026%20Quals/genesis/writeup.md) | Web3 | Medium | `H7CTF{346df380-…}` |
| [ghost-on-the-bus](H7CTF%202026%20Quals/ghost-on-the-bus/writeup.md) | Hardware | Medium | `H7CTF{10d9b516-…}` |
| [hear-no-evil](H7CTF%202026%20Quals/hear-no-evil/writeup.md) | Hardware | Medium | 2 flags |
| [justified](H7CTF%202026%20Quals/justified/writeup.md) | Web | Medium | `WEBVERSE{d5f607…}` |
| [kick-the-can](H7CTF%202026%20Quals/kick-the-can/writeup.md) | Hardware | Medium | `H7CTF{6360cbb3-…}` |
| [kintsugi-vault](H7CTF%202026%20Quals/kintsugi-vault/writeup.md) | Rev | Hard | `H7CTF{9df8f215-…}` |
| [loose-ends](H7CTF%202026%20Quals/loose-ends/writeup.md) | Pwn | Hard | `H7CTF{4d0e9693-…}` |
| [loose-lips](H7CTF%202026%20Quals/loose-lips/writeup.md) | Crypto | Hard | 2 flags |
| [manifest-destiny](H7CTF%202026%20Quals/manifest-destiny/writeup.md) | Pwn | Medium | `H7CTF{a2b24085-…}` |
| [merged](H7CTF%202026%20Quals/merged/writeup.md) | Web | Medium | `WEBVERSE{8ba2f5…}` |
| [meridian-pay](H7CTF%202026%20Quals/meridian-pay/writeup.md) | Mobile | Hard | 3 flags |
| [mic-drop](H7CTF%202026%20Quals/mic-drop/writeup.md) | Hardware | Medium | `H7CTF{7f0cb1b6-…}` |
| [open-sesame](H7CTF%202026%20Quals/open-sesame/writeup.md) | Hardware | Hard | `H7CTF{f6091c17-…}` |
| [owners-draw](H7CTF%202026%20Quals/owners-draw/writeup.md) | Crypto | Medium | `H7CTF{786dff67-…}` |
| [papers-please](H7CTF%202026%20Quals/papers-please/writeup.md) | Pwn | Easy | `H7CTF{b66621cc-…}` |
| [patient-exfil](H7CTF%202026%20Quals/patient-exfil/writeup.md) | Forensics | Medium | `H7CTF{6787b86c…}` |
| [radio-silence](H7CTF%202026%20Quals/radio-silence/writeup.md) | Hardware | Medium | `H7CTF{6780856d-…}` |
| [shared-blood](H7CTF%202026%20Quals/shared-blood/writeup.md) | Crypto | Medium | `H7CTF{a727587f-…}` |
| [splice](H7CTF%202026%20Quals/splice/writeup.md) | Web | Hard | `WEBVERSE{fcb61c…}` |
| [take-two](H7CTF%202026%20Quals/take-two/writeup.md) | Crypto | Hard | `H7CTF{63b0dde3-…}` |
| [tapeout](H7CTF%202026%20Quals/tapeout/writeup.md) | Misc | Hard | `H7CTF{afd4beac-…}` |
| [trace-amounts](H7CTF%202026%20Quals/trace-amounts/writeup.md) | Hardware | Medium | `H7CTF{48333086-…}` |
| [trompe-loeil](H7CTF%202026%20Quals/trompe-loeil/writeup.md) | Web3 | Hard | `H7CTF{0bba5486-…}` |

</details>

<details>
<summary><b>SunshineCTF 2026 - 18 challenges</b></summary>

| Challenge | Category | Difficulty | Flag |
|-----------|----------|------------|------|
| [cache-money](SunshineCTF%202026/cache-money/writeup.md) | Pwn | Hard | `sun{s4fe_l1nk…}` |
| [code-breaker](SunshineCTF%202026/code-breaker/writeup.md) | Crypto/Pwn | Hard | `sun{cr4ck_tHe…}` |
| [cookiecorp](SunshineCTF%202026/cookiecorp/writeup.md) | Web | Medium | `sun{c00kie_ja…}` |
| [groundhog_day](SunshineCTF%202026/groundhog_day/writeup.md) | Web | Hard | `sun{s1x_m0r3_…}` |
| [homemaker](SunshineCTF%202026/homemaker/writeup.md) | Pwn | Hard | `sun{the_futur…}` |
| [madlibs](SunshineCTF%202026/madlibs/writeup.md) | Pwn | Medium | `sun{f1ll_iN_t…}` |
| [my-eyes-burn](SunshineCTF%202026/my-eyes-burn/writeup.md) | Misc | Medium | `sun{praisethesun}` |
| [nas-coal](SunshineCTF%202026/nas-coal/writeup.md) | Forensics | Medium | `sun{yup_issa_gem}` |
| [planetary-probe](SunshineCTF%202026/planetary-probe/writeup.md) | Web | Hard | `sun{bl1nd_psq…}` |
| [print-print-revolution](SunshineCTF%202026/print-print-revolution/writeup.md) | Pwn | Hard | `sun{cust0m_fm…}` |
| [robocall](SunshineCTF%202026/robocall/writeup.md) | Pwn | Hard | `sun{you_must_…}` |
| [safe-house](SunshineCTF%202026/safe-house/writeup.md) | Pwn | Hard | `sun{n3gat1ve_…}` |
| [sitecheck](SunshineCTF%202026/sitecheck/writeup.md) | Web | Hard | `sun{fr4gm3nt3…}` |
| [suntrail](SunshineCTF%202026/suntrail/writeup.md) | Misc | Medium | `sun{qwerty_sucks}` |
| [total_recall](SunshineCTF%202026/total_recall/writeup.md) | Pwn | Medium | `sun{r3caLl_ev…}` |
| [vecnet](SunshineCTF%202026/vecnet/writeup.md) | Web | Hard | `sun{k33p_your…}` |
| [welcome-call](SunshineCTF%202026/welcome-call/writeup.md) | Forensics | Medium | `sun{thankyouforplaying}` |
| [you-cut-me-off](SunshineCTF%202026/you-cut-me-off/writeup.md) | Forensics | Medium | `sun{totallyoriginalchallengeidea}` |

</details>

<details>
<summary><b>CSS CTF 2026 - 17 solved challenges</b></summary>

| Challenge | Category | Difficulty | Flag |
|-----------|----------|------------|------|
| [a-star-trail](CSS%20CTF%202026/a-star-trail/writeup.md) | Misc | Beginner* | `CSSCTF{P1JT-21.0}` |
| [a-star-trail-2](CSS%20CTF%202026/a-star-trail-2/writeup.md) | Misc | Intermediate | `CSSCTF{STARmaPdElAUNaYTriaNGulATioNDIjKStrAVoRonoiGrAPHSdetERmiNaNTcolineaRALGOrITHmSLeEandsCHAcHTERTANgEnTSmErGECirCuMcIrcLEcOnVEXhuLLgeOMeTRy}` |
| [astrolobe_overwrite](CSS%20CTF%202026/astrolobe_overwrite/writeup.md) | Pwn | n/a | `CSSCTF{b0ckch41n_sk1ll5}` |
| [chrono-i](CSS%20CTF%202026/chrono-i/writeup.md) | Crypto | Beginner | `CSSCTF{every_second_hides_a_secret}` |
| [chrono-ii](CSS%20CTF%202026/chrono-ii/writeup.md) | Crypto | Intermediate | `CSSCTF{th3_cl0ck_r3m3mb3rs_3very_s3c0nd}` |
| [cloudy-spaceships](CSS%20CTF%202026/cloudy-spaceships/writeup.md) | Web | n/a | `CSSCTF{your_forecast_says_love_is_on_its_way}` |
| [colour-shift](CSS%20CTF%202026/colour-shift/writeup.md) | Forensics | Beginner | `CSSCTF{SHINE ON}` |
| [dockside-ticket](CSS%20CTF%202026/dockside-ticket/writeup.md) | Pwn | Beginner | `CSSCTF{us3_4ft3r_fr33_d0cks1d3}` |
| [flappy-board](CSS%20CTF%202026/flappy-board/writeup.md) | Misc | Intermediate | `CSSCTF{birdddd}` |
| [gateway](CSS%20CTF%202026/gateway/writeup.md) | Web3 | n/a | `CSSCTF{CSS{B451C_BL0CKCH41N_5K1LL5}}` |
| [Kuiper Belt Relay Core](CSS%20CTF%202026/Kuiper%20Belt%20Relay%20Core/writeup.md) | Pwn | Beginner | `CSSCTF{s1gn4l_r3c0v3r3d_fr0m_th3_v01d}` |
| [lamp-drill](CSS%20CTF%202026/lamp-drill/writeup.md) | Warm-up | n/a | `CSSCTF{css}` |
| [lottery](CSS%20CTF%202026/lottery/writeup.md) | Web3 | n/a | `CSSCTF{CSS{U5E_4_R4ND0M_FUNCT10N}}` |
| [maintenance-log](CSS%20CTF%202026/maintenance-log/writeup.md) | Pwn | n/a | `CSSCTF{Duh_m4t3_1_4m_sl33py}` |
| [prince-walk](CSS%20CTF%202026/prince-walk/writeup.md) | Reverse | n/a | `CSSCTF{P12INC3_0R_P1NC3?}` |
| [server-juice](CSS%20CTF%202026/server-juice/writeup.md) | OSINT | Beginner | `CSSCTF{premiumreserve}` |
| [severed-symmetry](CSS%20CTF%202026/severed-symmetry/writeup.md) | Crypto | Expert | `CSSCTF{P35T0_5CH3M3_4TT4CK2026}` |

*(n/a = difficulty not printed on challenge card; * = estimated from sibling challenge)*

</details>

<details>
<summary><b>Pointer Overflow CTF 2026 - 8 solved challenges</b></summary>

| Challenge | Category | Difficulty | Flag |
|-----------|----------|------------|------|
| [everything-left-open](Pointer%20Overflow%20CTF%202026/everything-left-open/writeup.md) | Forensics | 100 pts | `POCTF{109.612.I777LWHDFNCWRJ2S.JB6P5ZRASWPVYKKKHXKAPSQFWT}` |
| [excavation](Pointer%20Overflow%20CTF%202026/excavation/writeup.md) | RE | Beginner | `POCTF{2VE5EKXUA5IV2R57}` (token only) |
| [invisible-text](Pointer%20Overflow%20CTF%202026/invisible-text/writeup.md) | Steg | Hard | `POCTF{hidden_whitespace_in_py_file}` |
| [letters-never-sent](Pointer%20Overflow%20CTF%202026/letters-never-sent/writeup.md) | Crypto | Beginner | `POCTF{2.612.ORSMSQU6A7IQJGUC.PQ4FI...}` |
| [read-me-my-fortune](Pointer%20Overflow%20CTF%202026/read-me-my-fortune/writeup.md) | EXP | Medium | `POCTF{template_format_rce_via_globals}` |
| [shape-of-query](Pointer%20Overflow%20CTF%202026/shape-of-query/writeup.md) | Web | Hard | `POCTF{mass_assignment_private_notes_leak}` |
| [the-apparatus-invocation](Pointer%20Overflow%20CTF%202026/the-apparatus-invocation/writeup.md) | Misc | Beginner | `POCTF{lights_out_7x7_gf2_system}` |
| [where-the-light-fails-to-fall](Pointer%20Overflow%20CTF%202026/where-the-light-fails-to-fall/writeup.md) | OSINT | Hard | `POCTF{99.612.encrypted_token_sig}` |

</details>

## Tools Used

Solves are built with minimal dependencies - most use only Python stdlib (`socket`, `struct`, `hashlib`) or Node.js with `ethers.js` for Web3 challenges. No `pwntools` - all exploit scripts run on any OS including Windows.

## License

Educational use. Challenge descriptions and flag strings remain the property of their respective CTF organizers.
