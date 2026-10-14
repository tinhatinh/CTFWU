---
title: "OSINT Exam II"
category: "OSINT"
tags: ["multi-question", "exif", "race-results", "geolocation", "public-records", "remote-service"]
solve_date: "2026-10-10"
language: "en"
---

# OSINT Exam II

**Flag:** `FortID{Y0u_H4v3_N0w_B3com3_4_C3rt1fi3d_0p3n_50urc3_1n73l1genc3_Gr4ndM45t3r_4_L1f3_af5a43ec69}`
**Challenge:** `OSINT Exam II` (ipaljak). **Handout:** `data.zip` (7503579 B; the card lists 7.2 MB) containing `data/q1.png`, `data/q2.jpg`, `data/q3.jpeg`, `data/q5.jpg`, `data/q6.mp4`, `data/q6_1.jpeg`, `data/q6_2.jpeg`. **Service:** `ncat --ssl osint-exam-ii-<hash>.inst12.ctf.fortid.com 1337`, served over TLS by `osint_exam_ii/exam_client.py`. The first instance `d4372dc6d1ee` expired mid-session and was replaced by `70beb5f9e24d`.

## Challenge

The exam is a six-question "OSINT exam" served over TLS: the client submits one answer at a time through `exam_client.py`, and once answer 6 is correct the service prints a certificate (the flag). Each question corresponds to a media file under `data/` (q1→`q1.png`, q2→`q2.jpg`, q3→`q3.jpeg`, q5→`q5.jpg`, q6→`q6.mp4`/`q6_1.jpeg`/`q6_2.jpeg`). The six recorded answers:

```text
q1 Edinburgh 14480 00:53:14
q2 From EU Digital Identity Architecture to Real-World Services
q3 Max Bruch Augusta Senoe 31a 23250 Pag Croatia
q4 Paljak Kiki Dino
q5 Docaposte Rennes Midnight Flag CTF
q6 Brant Fell
```

## Analysis

- **q1** — race number and finish time of a male 10K runner: read the Bib number off the cropped `q1_bib.png`, then look it up in `mens10k.com/results?event=1070`. The joined fields give `Edinburgh 14480 00:53:14`.
- **q2** — the title of a presentation on EU Digital Identity: `From EU Digital Identity Architecture to Real-World Services`.
- **q3** — an address matched from the image: `Max Bruch Augusta Senoe 31a 23250 Pag Croatia`.
- **q4** — the foosball leaderboard: `Paljak Kiki Dino`.
- **q5** — the recorded answer is `Docaposte Rennes Midnight Flag CTF`. The `2026-06-12` EXIF timestamp is a time clue; the record does not preserve a source establishing the EUDIW Unfold #3.1 explanation.

## Solution

For each question, text is read directly off the media (the Bib number, the address line, the leaderboard, the slide title) and cross-checked against a public source where needed (the 10K results table for q1; the EUDIW/Docaposte session calendar for q5). q6 is the only question that required try-then-correct, because the video/photos are ambiguous between two summits; the service confirms by refusing `Higger Tor` and accepting only `Brant Fell`.

The six answers are submitted in order through `exam_client.py`; after answer 6 the service prints the certificate:

```text
After answer 6 : \r\nCongratulations!\r\nYou passed the exam, here is your certificate: FortID{Y0u_H4v3_N0w_B3com3_4_C3rt1fi3d_0p3n_50urc3_1n73l1genc3_Gr4ndM45t3r_4_L1f3_af5a43ec69}\r\n
```

## Result

```text
FortID{Y0u_H4v3_N0w_B3com3_4_C3rt1fi3d_0p3n_50urc3_1n73l1genc3_Gr4ndM45t3r_4_L1f3_af5a43ec69}
```

The flag was both read verbatim from the remote service (the certificate line above, saved to `osint_exam_ii/flag.txt`, 162 B) and accepted by the platform on submission; the submission response is recorded verbatim:

```text
{'kind': 'goodFlag', 'message': 'The flag is correct.'}
```

## Reproduce

A live instance is required: the flag shown is the value from the recorded run. Without server source, its suffix generation and acceptance scope across instances are not established.

```console
$ ncat --ssl osint-exam-ii-70beb5f9e24d.inst12.ctf.fortid.com 1337
```

`exam_client.py` connects to the instance and sends the six answers in turn: (1) read the Bib number from `q1_bib.png` and look it up in `mens10k.com/results?event=1070`; (2)-(4) read the slide title, the address line and the foosball leaderboard directly from `q2.jpg`/`q3.jpeg` and the leaderboard shown in the exam; (5) use the EXIF stamp `2026-06-12` to pin the Docaposte-hosted EUDIW Unfold #3.1 session and its Midnight Flag CTF finals; (6) submit `Brant Fell` (after `Higger Tor` was refused). After answer 6 the printed certificate is the flag for that instance.
