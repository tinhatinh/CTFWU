---
title: "Cubism"
category: "Reverse"
tags: ["linux-elf", "static-analysis", "quirc", "qr-code", "constraint-solving", "voxel-projection"]
solve_date: "2026-10-10"
language: "en"
---

# Cubism

**Flag:** `FortID{TH3_Cub3_15_47_th3_54m3_T1M3_4_SyMb0l_0F_51MP11C1tY_4nd_C0mpl3Xi7y}`
**Service:** `ncat --ssl cubism-e41328dc5075.inst7.ctf.fortid.com 1337`. **Artifact:** `handout.zip` (18065 B), containing `checker` (34888 B, stripped ELF64 PIE) and `server.py` (1383 B).

## Challenge

`server.py` invites the player to "submit a cubist painting": it calls `sys.stdin.buffer.readline(SIDE_LENGTH + 2)` exactly `SIDE_LENGTH * SIDE_LENGTH = 441` times, joins the lines into one block and feeds it to the stdin of the `checker` binary. `checker` prints nothing — stdout and stderr are discarded and it runs with `env={}` — so every acceptance condition (line length, alphabet, voxel budget) lives inside the binary. If `checker` returns exit code 0, the server prints the flag from the `FLAG` environment variable.

The objective is to find a voxel set in a `21×21×21` lattice whose projections pass the check implemented in `checker`.

## Analysis

This section is entirely static analysis: `checker` was decompiled with Ghidra headless (a script that decompiles every function, output kept as `decomp.c` in the working directory, not shipped with this writeup); `checker` was not executed on the analysis machine. The binary is stripped and exposes only 17 unresolved libc symbols, so internal functions are referred to by address.

The input parsing constraints, taken from `decomp.c`:

```c
if ((int)pcVar18 != 0x15) goto LAB_001012b9;      /* mỗi dòng phải dài đúng 21 */
if (puVar19[lVar6] == '#') { puVar15 = puVar15 + 1; uVar13 = 1; }
else { if (puVar19[lVar6] != '.') goto LAB_001012b9; uVar13 = 0; }
...
if ((undefined *)0xf4 < puVar15) goto LAB_001012b9;   /* tổng '#' tích luỹ <= 244 */
```

`LAB_001012b9` is the rejection branch. All three nested loops are bounded by `0x15`, and the image buffer advances in steps of `0x1b9 = 441`, so the data is treated as a `21 × 21 × 21` lattice.

Once a layer completes, the checker builds the QR image:

```c
iVar3 = FUN_00101760(puVar17, 0x15c, 0x15c);         /* 0x15c = 348 */
lVar6 = FUN_001039b0(puVar17, pcVar18, puVar16 + -0x156c);
lVar6 = (*(code *)PTR_memset_00108f98)(lVar6, 0xff, 0x1d910);
```

`0x1d910 = 121104 = 348²` bytes of white background (`0xff`), with dark modules drawn as `12×12` pixel blocks. For `21` data modules, this matches a 4-module quiet zone: `(21 + 2*4) * 12 = 348`. The decoder's jump table sits at `0x6050` (`DAT_00106050`), its case-label array at `0x6070..0x6088` holds 6 entries, and `if ((uint)in_R9 < 6)` bounds the index to 6 values: the checker processes **six images**, one per viewing direction.

The presence of `quirc/lib/identify.c` together with `("row[x] == from", ...)` in `.rodata` shows that **quirc** is statically linked in. At the end of the function:

```c
in_R8 = "%s %s %s %s %s %s";
(*(code *)PTR___snprintf_chk_00108f60)(puVar19, 0x600, 1, 0x600);
pcVar18 = "SIMON SAYS GIVE ME THE FLAG";
iVar3 = (*(code *)PTR_strcmp_00108fb0)(puVar19);
if (iVar3 == 0) { (*(code *)PTR_puts_00108f80)("Correct!"); ... return 0; }
```

The six decoded payloads (one 256-byte slot each) are joined with `"%s %s %s %s %s %s"` and `strcmp`'d against `"SIMON SAYS GIVE ME THE FLAG"`, a string that really exists in `.rodata`. That target string contains six words, so the six faces must decode to `SIMON`, `SAYS`, `GIVE`, `ME`, `THE`, `FLAG` in the order of the checker's face counter.

Two geometric consequences drive the solution:

- The six orthographic projections of one voxel set form **three pairs of opposite faces**, and each pair is a mirror image of itself. A projected image only has to be constructed once; the other three follow by mirroring.
- Mirroring does not make the problem easier: the data in the mirrored image has to decode to a *different* word of the same target string, so every single face must be a QR version 1 symbol that **decodes two different ways**.

To answer "what does a mirrored image produce", quirc was cloned and built as a standalone harness (`oracle/harness.c`, which reads a raw `348×348` image by default), together with a Python model that reproduces the decode path of `lib/decode.c` exactly (`qrmodel.py`: `reserved_cell`, the `read_data` order, `mask_bit`, `read_format`, the `block_syndromes` convention and the segment decode loop). Two observations from that oracle:

- quirc reads a mirrored image as the **transpose** of the original — unlike a rotated image — because its corner ordering and module sampling direction map the mirror onto a transpose permutation of the 208 data modules.
- An image that is not a valid QR symbol is rejected with `QUIRC_ERROR_DATA_ECC` rather than with a locator error, so the binding constraint is the Reed–Solomon code, not QR detection.

For each face the constraints are linear over GF(2): 208 unknown data modules, two readings that use those same 208 variables in two different orders, each reading contributing `56` Reed–Solomon equations (version 1, 26 codewords, `26 - 19 = 7` error-correction codewords times 8 bits), for `56 + 56` in total. Discretising by the `(ECC level, mask)` pair of the two readings gives the **308 format classes** that were enumerated and verified during the face search.

## Solution

Three faces were selected, each carrying one consecutive word pair of the target string: `(SIMON, SAYS)`, `(GIVE, ME)`, `(THE, FLAG)`. This assignment is confirmed by the service accepting the final painting.

For each format class, both messages are pushed into the same 208-variable space: the free part of the segment (12/13/14-bit lengths) and alternative segment encodings let the two words occupy disjoint variable sets, avoiding a direct contradiction. The system of `56 + 56` parity equations plus the forced-bit equations is solved by Gauss elimination over GF(2); a particular solution is then optimised by exhaustive Gray-code search over the kernel when the kernel is small, and by greedy flips otherwise.

The three resulting faces have `203 / 214 / 212` dark modules. The last step is a covering problem: find a voxel set `V ⊆ 21³` with `|V| ≤ 244` whose three projections match those three faces exactly, i.e. every dark module on a projection must be "supported" by a real voxel in the lattice. The solve used a repeated greedy fill combined with descent over the free space of the GF(2) system (`joint.py`, `cover*.py`, `descend*.py`), accepting a candidate only after the exact cover was verified.

The result is `painting.txt` (9702 B): 441 lines, 21 characters each, exactly 244 `#`. Local verification:

```python
from pathlib import Path
import numpy as np

raw = Path("painting.txt").read_bytes()
rows = [r for r in raw.split(b"\n") if r]
assert len(rows) == 441 and {len(r) for r in rows} == {21}
assert set(raw.replace(b"\n", b"")) <= {ord("."), ord("#")}
print("lines:", len(rows), "chars/line:", len(rows[0]), "hashes:", raw.count(b"#"))

grid = np.array([[1 if c == 35 else 0 for c in r] for r in rows], dtype=np.uint8)
vol = grid.reshape(21, 21, 21)          # 21 lớp, mỗi lớp 21 dòng
proj = [(vol.sum(axis=a) > 0) for a in (0, 1, 2)]
print("voxels:", int(vol.sum()))
print("projection black modules:", [int(p.sum()) for p in proj])
```

```text
lines: 441 chars/line: 21 hashes: 244
voxels: 244
projection black modules: [203, 214, 212]
```

The projection counts match the three solved faces, and `hashes: 244` sits exactly at the `0xf4` ceiling. Submitting the solution directly:

```bash
(timeout 70 ncat --ssl cubism-e41328dc5075.inst7.ctf.fortid.com 1337 < painting.txt > ncat_out.txt)
```

`ncat_out.txt` received 480 B:

```text
   A painting is more than the sum of its blocks.

Welcome, artist.
Submit your cubist painting below.
The curator will begin after the final row.

The curator smiles.
Correct!

Enjoy your flag: FortID{TH3_Cub3_15_47_th3_54m3_T1M3_4_SyMb0l_0F_51MP11C1tY_4nd_C0mpl3Xi7y}
```

The cube construction is instance-independent: the solution is only a voxel set satisfying the static constraints of `checker`, and `server.py` mixes no instance data into the check. Only the final read needs a live instance.

## Result

```text
FortID{TH3_Cub3_15_47_th3_54m3_T1M3_4_SyMb0l_0F_51MP11C1tY_4nd_C0mpl3Xi7y}
```

The flag was read directly from the challenge service. No submission response recorded.

## Reproduce

Requires Linux or MSYS for `binutils`/Ghidra, Python 3 with `numpy`, a C build toolchain for quirc, and `ncat` (nmap) with `--ssl` support.

Recover the static constraints from the artifact:

```console
$ unzip handout.zip
$ file handout/checker
$ strings -a handout/checker | grep -E "SIMON|%s %s"
$ readelf -hW handout/checker | grep -E "Type|Entry"
```

```text
checker: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, BuildID[sha1]=ced39f5ad5ffd3108c2d9118b11ffe8089b38792, for GNU/Linux 3.2.0, stripped
%s %s %s %s %s %s
SIMON SAYS GIVE ME THE FLAG
```

Build the quirc oracle and probe the mirrored-image behaviour:

```console
$ git clone https://github.com/dlbeer/quirc
$ cc -Iquirc/include -c quirc/lib/*.c -o /dev/null   # kiểm tra header
$ cc -Iquirc/include quirc/lib/*.c oracle/harness.c -o oracle/harness
$ python -c "import qrcode" # qrmodel.py cần thư viện qrcode để sinh ảnh chuẩn đối chiếu
```

Write `oracle/harness.c` (about 1.9 KB, not shipped with this writeup) following this description: `main(argc, argv)` takes a raw image path, a width and a height (defaults `img.raw`, `348`, `348`) plus a `d` flag to dump the grid; the function does `quirc_new` → `quirc_resize(q, w, h)` → `quirc_begin` → `fread` of exactly `w*h` bytes → `quirc_end`, then for each index `i < quirc_count(q)` calls `quirc_extract(q, i, &code)` and `quirc_decode(&code, &data)`, printing `payload_len`/`ecc_level`/`mask`/`data_type` and the payload, or the `quirc_decode_error_t` code when decoding fails. Build and run: `cc -Iquirc/include quirc/lib/*.c oracle/harness.c -o oracle/harness`, then `harness img.raw 348 348 d`.

Generate the solution. The names below are scripts written during the solve and are **not** shipped with this writeup; the handout contains only `checker` and `server.py`. Their roles are listed so the pipeline can be rewritten: `qrmodel.py` is the decoder model following `lib/decode.c`, `solve_face.py`/`fastsolve.py` solve the GF(2) system for one face under one format class, `genfaces.py` produces many low-weight faces per word pair, `joint.py` optimises the three faces jointly, and `cover*.py` plus `descend*.py` search for a voxel cover `<= 244`. Every parameter needed to rebuild it is in the Analysis section (QR version 1, the `(ECC level, mask)` pair for each reading, `56 + 56` parity equations, mirrored images read by quirc as transposes, the 244-voxel ceiling); the final output is `painting.txt`. Because the solution does not depend on the instance, an accepted painting can always be constructed offline and submitted afterwards.

Check `painting.txt` with the Python block from the Solution section, then submit:

```bash
(timeout 70 ncat --ssl cubism-e41328dc5075.inst7.ctf.fortid.com 1337 < painting.txt > ncat_out.txt)
cat ncat_out.txt
```

If the instance hostname changed, only the host in the `ncat` command needs editing; `painting.txt` does not change because the solution does not depend on the instance.
