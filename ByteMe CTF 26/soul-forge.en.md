---
title: "Soul Forge"
category: "Crypto"
tags: ["two-time-pad", "keystream-reuse", "crib-dragging", "xor"]
solve_date: "2026-10-09"
language: "en"
---

# Soul Forge

**Flag:** `OWASP{s0ul_f0rge_pr1m3s_4r3_n3v3r_r4nd0m}`
**Artifacts:** two hex blobs `T1` (57 bytes) and `T2` (77 bytes), embedded directly in the workspace scripts; no standalone artifact file.

## Challenge

The statement (Easy, 100 points) is just the two hex blobs and a request to recover the content:

```text
T1 = 5945b2affe943fcc07714e6fdf6a4bc19ebd9232b30a543ef09deeded7be581938adb099bd2c81134999a63d456aaef68addd2275899652d26
T2 = 5945b2affe943fcc07714e6fc16a5bc09aaeed32c6097d088080f29cc5b7270d6db2b2918039815104cfa3070361bdda858dd67d4caf747c668621b710e6e1e2397af4e35719fb59c817dd62cd
```

Flag format is `OWASP{...}`; no remote service is involved.

## Analysis

Lengths: `T1` is 57 bytes, `T2` is 77 bytes. XORing byte by byte over the overlapping region gives:

```text
D = 0000000000000000000000001e00100104137f0075032936701d1c4212097f14551f02083d1500424d56053a460b132c0f50045a1436115140
identical prefix: 12 bytes
```

The first 12 bytes of `D` are zero, meaning `T1` and `T2` start with 12 identical bytes. If both messages share one keystream — `C1 = P1 ^ K`, `C2 = P2 ^ K` — then `C1 ^ C2 = P1 ^ P2`, and a zero byte means the two plaintexts agree at that position. Whether the keystream is a short repeating key was tested: scanning periods 1..56 under the constraint that every decrypted byte stays printable, `soulforge_repeating.py` prints nothing, i.e. no period from 1 to 56 is feasible; the looser measurement in `soulforge_period.py` also shows no standout period (highest ratio 0.370 at period 30 of `T1`). The workable model is therefore a one-time pad reused twice, `D = P1 ^ P2`.

`D` also marks the positions where the two plaintexts agree: the indices with `D[i] = 0` are `[0..11, 13, 19, 38]`.

Crib dragging: the flag starts with `OWASP{`, so sliding that 6-character string across `D` and keeping the alignments whose partner side is entirely printable bytes leaves 21 offsets:

```text
all-printable alignments: 21
  off= 0 other=b'OWASP{'
  off= 1 other=b'OWASP{'
  off= 2 other=b'OWASP{'
  off= 3 other=b'OWASP{'
  off= 4 other=b'OWASP{'
  off= 5 other=b'OWASP{'
  off= 6 other=b'OWASP{'
  off= 7 other=b'OWASPe'
  off= 8 other=b'OWASN{'
  off= 9 other=b'OWAMPk'
  off=10 other=b'OW_S@z'
  off=12 other=b'QWQRTh'
  off=14 other=b'_VE@/{'
  off=16 other=b'KD>S%x'
  off=17 other=b'\\(A&SR'
  off=18 other=b'0W4PyM'
  off=20 other=b':The f'
  off=21 other=b'L~w#Mg'
  off=22 other=b'fa1NL9'
  off=33 other=b'PUInE{'
  off=34 other=b'M_|FP9'
```

Printability alone is not enough to choose: offsets 0..6 are degenerate solutions inside the zero region of `D`, where both plaintexts are simply equal, and offsets 27 and 50 are dropped by the same script because they are not ASCII. Among the surviving candidates, only offset 20 produces text that reads as English — `:The f`. That is what pins the flag position, and it is also the single step in the chain that relies on a language judgement rather than on arithmetic.

Expanding `P2[20:]` into `:The forge remembers every sacrifice.` and computing `P1 = D ^ P2` over the overlap yields 37 consecutive characters of the flag. A hard limit of the data is already visible at this step: `T1` is 57 bytes and the flag starts at index 20, so the derivable region ends at the 37th character, while the recorded flag is 41 characters long — the last four characters fall outside any region the artifact describes. This is spelled out in the Solution and Result sections.

## Solution

```python
T1 = bytes.fromhex("5945b2affe943fcc07714e6fdf6a4bc19ebd9232b30a543ef09deeded7be581938adb099bd2c81134999a63d456aaef68addd2275899652d26")
T2 = bytes.fromhex("5945b2affe943fcc07714e6fc16a5bc09aaeed32c6097d088080f29cc5b7270d6db2b2918039815104cfa3070361bdda858dd67d4caf747c668621b710e6e1e2397af4e35719fb59c817dd62cd")

N = min(len(T1), len(T2))
D = bytes(a ^ b for a, b in zip(T1, T2))
print("len T1, len T2, overlap :", len(T1), len(T2), N)
print("D =", D.hex())
print("identical prefix:", next(i for i in range(N) if D[i] != 0), "bytes")

crib = "OWASP{"
hits = [(o, bytes(D[o + j] ^ ord(crib[j]) for j in range(len(crib))))
        for o in range(N - len(crib) + 1)
        if all(32 <= (D[o + j] ^ ord(crib[j])) < 127 for j in range(len(crib)))]
print("all-printable alignments:", len(hits))
for o, cand in hits:
    print("  off=%2d other=%r" % (o, cand))

off = 20
p2 = ":The forge remembers every sacrifice."
p1 = bytearray(b"?" * len(T1))
for j, ch in enumerate(p2):
    i = off + j
    if i >= len(T1):
        break
    p1[i] = D[i] ^ ord(ch)
recovered = "".join(chr(b) for b in p1)
print("P1 =", repr(recovered))
print("chars derived:", len(recovered) - recovered.count("?"))

recorded = "OWASP{s0ul_f0rge_pr1m3s_4r3_n3v3r_r4nd0m}"
got = recovered[off:]
print("derived from artifact :", repr(got), len(got), "chars")
print("recorded flag         :", recorded, len(recorded), "chars")
print("derived is prefix of recorded:", recorded.startswith(got))
print("outside the overlap   :", repr(recorded[len(got):]))
print("max chars reachable   :", len(T1) - off)
```

```text
len T1, len T2, overlap : 57 77 57
D = 0000000000000000000000001e00100104137f0075032936701d1c4212097f14551f02083d1500424d56053a460b132c0f50045a1436115140
identical prefix: 12 bytes
all-printable alignments: 21
  off= 0 other=b'OWASP{'
  off= 1 other=b'OWASP{'
  off= 2 other=b'OWASP{'
  off= 3 other=b'OWASP{'
  off= 4 other=b'OWASP{'
  off= 5 other=b'OWASP{'
  off= 6 other=b'OWASP{'
  off= 7 other=b'OWASPe'
  off= 8 other=b'OWASN{'
  off= 9 other=b'OWAMPk'
  off=10 other=b'OW_S@z'
  off=12 other=b'QWQRTh'
  off=14 other=b'_VE@/{'
  off=16 other=b'KD>S%x'
  off=17 other=b'\\(A&SR'
  off=18 other=b'0W4PyM'
  off=20 other=b':The f'
  off=21 other=b'L~w#Mg'
  off=22 other=b'fa1NL9'
  off=33 other=b'PUInE{'
  off=34 other=b'M_|FP9'
P1 = '????????????????????OWASP{s0ul_f0rge_pr1m3s_4r3_n3v3r_r4n'
chars derived: 37
derived from artifact : 'OWASP{s0ul_f0rge_pr1m3s_4r3_n3v3r_r4n' 37 chars
recorded flag         : OWASP{s0ul_f0rge_pr1m3s_4r3_n3v3r_r4nd0m} 41 chars
derived is prefix of recorded: True
outside the overlap   : 'd0m}'
max chars reachable   : 37
```

**Limit:** with the recorded crib at offset 20, the script recovers 37 of the 41 flag characters. `T1` ends at index 56, so the final `d0m}` is outside the recovered range and comes from the saved flag. The crib is assumed input; it is not uniquely established by the two ciphertexts.

## Result

```text
OWASP{s0ul_f0rge_pr1m3s_4r3_n3v3r_r4nd0m}
```

The first 37 characters follow directly from the two blobs through `P1 = (T1 ^ T2) ^ P2` with the crib anchored at offset 20; the final 4 characters come from the flag recorded in the event files and cannot be derived from the artifact, because `T1` ends before them. No remote service ships with this challenge. No submission response recorded.

## Reproduce

Python 3, standard library only. Save the block in the Solution section as `soulforge_crib.py` and run:

```console
$ python soulforge_crib.py
```

The blobs and crib are embedded in the script. It recovers only the first 37 characters; the `d0m}` suffix is a saved value, not derived from the two blobs.
