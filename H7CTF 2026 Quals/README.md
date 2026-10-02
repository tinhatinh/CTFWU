# H7CTF 2026 Quals

Writeups for challenges solved at [ctf.h7tex.com](https://ctf.h7tex.com).  
Flag format: `H7CTF{uuid}` or `H7CTF{hex}`; WebVerse Labs challenges (web category partner) use `WEBVERSE{…}` and are played at [ctf.webverselabs-pro.com](https://ctf.webverselabs-pro.com).

## Solved Challenges

| Challenge | Category | Difficulty | Flag |
|-----------|----------|------------|------|
| [arcel-bomb](arcel-bomb/writeup.md) | Pwn | Medium | `H7CTF{0b79ca94-3b66-4509-9365-34d224d5cfe2}` |
| [countersign](countersign/writeup.md) | Rev | Insane | `H7CTF{011c87d4-b5c8-405d-923a-33dbed3e5bf7}` |
| [deep-freeze](deep-freeze/writeup.md) | Forensics | Hard | `H7CTF{bf3a8e98115450c654b4}` |
| [deputy](deputy/writeup.md) | Cloud | Hard | 4 flags (see writeup) |
| [dog-whistle](dog-whistle/writeup.md) | Hardware | Insane | `H7CTF{3c48f268-6761-422b-9df0-e652f6b2c4d0}` |
| [echo-chamber](echo-chamber/writeup.md) | AI | Medium | `H7CTF{174f034a-b318-49db-a3eb-24192b3d7ce2}` |
| [genesis](genesis/writeup.md) | Web3 | Medium | `H7CTF{346df380-9ca8-41a7-8853-5a6f23c601ad}` |
| [ghost-on-the-bus](ghost-on-the-bus/writeup.md) | Hardware | Medium | `H7CTF{10d9b516-d19b-4895-9634-45b27a7591c3}` |
| [hear-no-evil](hear-no-evil/writeup.md) | Hardware | Medium | 2 flags (see writeup) |
| [justified](justified/writeup.md) | Web | Medium | `WEBVERSE{d5f60724dc9f1197140001fa4b24198e}` |
| [kick-the-can](kick-the-can/writeup.md) | Hardware | Medium | `H7CTF{6360cbb3-73fc-4ba5-a9e6-0229a3b1a008}` |
| [kintsugi-vault](kintsugi-vault/writeup.md) | Rev | Hard | `H7CTF{9df8f215-6ef3-4ee2-a336-42d628680738}` |
| [loose-ends](loose-ends/writeup.md) | Pwn | Hard | `H7CTF{4d0e9693-88bd-4749-87d8-c64dd2ef80ab}` |
| [loose-lips](loose-lips/writeup.md) | Crypto | Hard | 2 flags (see writeup) |
| [manifest-destiny](manifest-destiny/writeup.md) | Pwn | Medium | `H7CTF{a2b24085-c670-4a87-93cb-293cfec6196c}` |
| [merged](merged/writeup.md) | Web | Medium | `WEBVERSE{8ba2f569dafeedea7f4f6848757e1917}` |
| [meridian-pay](meridian-pay/writeup.md) | Mobile | Hard | 3 flags (see writeup) |
| [mic-drop](mic-drop/writeup.md) | Hardware | Medium | `H7CTF{7f0cb1b6-34ee-46c0-945b-1f069dff2a29}` |
| [open-sesame](open-sesame/writeup.md) | Hardware | Hard | `H7CTF{f6091c17-1155-4d06-8a90-b826fd758185}` |
| [owners-draw](owners-draw/writeup.md) | Crypto | Medium | `H7CTF{786dff67-75cd-4d4e-8b74-55edb1353aad}` |
| [papers-please](papers-please/writeup.md) | Pwn | Easy | `H7CTF{b66621cc-c85c-4042-b908-0d3dd36a71e5}` |
| [patient-exfil](patient-exfil/writeup.md) | Forensics | Medium | `H7CTF{6787b86cc777f426b9c0}` |
| [radio-silence](radio-silence/writeup.md) | Hardware | Medium | `H7CTF{6780856d-db42-4cfa-8b56-c62109d8417c}` |
| [shared-blood](shared-blood/writeup.md) | Crypto | Medium | `H7CTF{a727587f-67d5-4246-b7c3-e57798659fac}` |
| [splice](splice/writeup.md) | Web | Hard | `WEBVERSE{fcb61c06cbb7cd020a371730b71521fe}` |
| [take-two](take-two/writeup.md) | Crypto | Hard | `H7CTF{63b0dde3-3edd-4a95-92d3-4e8c26e38483}` |
| [tapeout](tapeout/writeup.md) | Misc | Hard | `H7CTF{afd4beac-e86e-409b-907d-b519bb748599}` |
| [trace-amounts](trace-amounts/writeup.md) | Hardware | Medium | `H7CTF{48333086-d56b-41f5-b24b-a1d53fb122ec}` |
| [trompe-loeil](trompe-loeil/writeup.md) | Web3 | Hard | `H7CTF{0bba5486-eebc-4ee8-a3de-a55e80c787f1}` |

**Total: 29 solved**

## Incomplete / In Progress

| Directory | Status |
|-----------|--------|
| `fleetlink` | Has artifacts, no writeup yet |
| `help-yourself` | Has artifacts, no writeup yet |
| `public-domain` | Has artifacts, no writeup yet |
| `signed-sealed-delivered` | Has artifacts, no writeup yet |
| `_wip/*` | Partial work - scripts and captures exist but no flag obtained |

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
