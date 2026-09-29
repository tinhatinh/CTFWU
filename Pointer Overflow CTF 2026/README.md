# Pointer Overflow CTF 2026 (POCTF 2026)

Event site: [pointeroverflowctf.com](https://pointeroverflowctf.com) · CTFtime: [Pointer Overflow CTF](https://ctftime.org/ctf/963/)
Organizer: University of Wisconsin-Stevens Point cybersecurity curriculum (director: C. R. Johnson).
Kickoff: Sunday, September 27, 2026, 09:00 CDT. Online, global participation.

Flag format: `POCTF{...}`. Flags are unique per team, so the body is a team token, not readable text; a flag copied from another team's writeup will not validate.

## Rules that change how we work (from rules.html)

- **Flags are team-specific.** A flag valid for one team is not valid for another, and the contest site validates against our team only. A flag read out of someone else's writeup is not a candidate answer.
- **Challenge content is team-specific too**: ciphertext, image variants and other prompt values are generated per team. Comparing challenge text across teams is misleading. Our own challenge page is the source of truth, so `de.md` must be copied from our instance, not a cached copy.
- Challenges may be released in waves, and some may close early. Note the release/closure time shown on the challenge page in `de.md`.
- Two shapes: jeopardy-style standalone puzzles, and narrative tracks with staged sequences (Forensics and Game Hacking are named as narrative tracks), where later stages depend on earlier output. Keep those cases ordered in `_wip/` until the chain is known.
- Submit only through the challenge page on the contest site. Admins are reachable via the contest Discord channel (`@CTF-Admin`).

## Solved Challenges

| Challenge | Category | Difficulty | Flag |
|-----------|----------|------------|------|
| [letters-never-sent](letters-never-sent/writeup.md) | Crypto | Medium (95 pts, 248 solves) | `POCTF{2.612.ORSMSQU6A7IQJGUC.PQ4FI6SPWLYJYQGBQK66AWTILP}` |
| [read-me-my-fortune](read-me-my-fortune/writeup.md) | EXP | Medium (200 pts) | `POCTF{127.612.IB2GGFAM2XGX6RDT.TEENFQ3KNWVEA3MCHJNFWFODQI}` |
| [everything-left-open](everything-left-open/writeup.md) | Forensics | Easy-Medium (100 pts) | `POCTF{109.612.I777LWHDFNCWRJ2S.JB6P5ZRASWPVYKKKHXKAPSQFWT}` |
| [the-apparatus-invocation](the-apparatus-invocation/writeup.md) | Misc | Easy (100 pts) | `POCTF{3.612.H5VA2OHFE333SO62.EAIOF76YB2L4XMZTFSV4CPOEOX}` |
| [where-the-light-fails-to-fall](where-the-light-fails-to-fall/writeup.md) | OSINT | Hard (400 pts) | `POCTF{99.612.WTT7UHE5X3JIJMKQ.TO6LBQYYORFL6LLPF6Q22SRR2P}` |
| [excavation](excavation/writeup.md) | RE | Easy-Medium (100 pts) | token `2VE5EKXUA5IV2R57` (submit endpoint returns no `POCTF{...}` string) |
| [invisible-text](invisible-text/writeup.md) | Steg | Hard (200 pts) | `POCTF{PIEMPAOSMHDLEGRT}` |
| [shape-of-query](shape-of-query/writeup.md) | Web | Hard (300 pts) | `POCTF{81.612.EB7ZOZUZT7FJHWR2.YQXWHGRFYSBYU46VGKVYD22DNN}` |

**Total: 8 solved**

## In Progress

| Directory | Status |
|-----------|--------|

Unstarted and unsolved cases live in [`_wip/`](_wip/). One subfolder per challenge, using the same layout as a finished case, and `notes.md` carries the hypothesis log while the flag is still missing.

## Challenge Structure

```
<challenge>/
  de.md          Original challenge description + verified metadata
  writeup.md     Solution: initial analysis → eliminated hypotheses → exploit chain → flag
  notes.md       Step-by-step investigation log (including dead ends)
  flag.txt       Captured flag string
  exploit.py     Reproducible solve script
  analysis/      Exploratory scripts for each phase
  files/         Original challenge artifacts (unmodified)
```

Template for new challenges: [`../_template/`](../_template/)

```bash
bash ../_template/new_case.sh "Pointer Overflow CTF 2026" <ten-bai> [file-de] --wip
```

Before solving a challenge: save the challenge page text verbatim into `de.md`, screenshot the card into `files/de.png`, download every artifact into `files/`, and record the size plus SHA-256 of each artifact while the instance is still live.
