# Countersign - Rev (Insane)

**Flag:** `H7CTF{011c87d4-b5c8-405d-923a-33dbed3e5bf7}` · **Files:** `countersign.zip` (ELF x86-64 PIE, stripped, 22 KB) + `note.txt` · Service: `nc pwn.h7tex.com 43708`

## Challenge

> Countersign is the attestation core of a licensed firmware module. Slide a pass under
> the glass and the clerk stamps whatever you hand him, but the core itself only ever
> walks a route it can vouch for. Find the input that walks it all the way to the flag.

`note.txt` describes a 4-command protocol, one command per line:

```
GET            stream program image of this instance as hex
NONCE          instance's nonce
MINT <hex>     debug stamp for at most 16 bytes
RUN <hex>      đưa vào core 24 byte input, in ra những gì core nhả ra
```

and states that the image and the signing material are freshly generated for each instance. Only later did I
understand that sentence fully: it changes per connection, not per instance. The job is to find the 24 input bytes
that make the core traverse the whole graph and emit the flag.

## Analysis

The machine has no pwntools and no ghidra/r2, so everything was done with `objdump -d` + `readelf` plus
self-written tooling (`fd.py` prints vma ranges, `records.py` parses the image). The binary has only a handful of
functions, no anti-debug and no self-decryption; the difficulty is that it is stripped, so function names had to be
invented by reading the bodies.

Function map (re-read several times; the places I originally mislabelled are listed under
"Error Analysis"):

| Address | Role |
|---|---|
| `0x1fa0` | boot: opens `/dev/urandom`, reads 16 bytes, derives a 26-byte key (`0x22e0`, splitmix64), loads the image, generates a signature for every edge |
| `0x1810` | `exec_program`: straight-line VM over 8 u32 registers |
| `0x1d50` | `emit`: picks the next edge and verifies its countersignature |
| `0x1af0` | the stamp function (SipHash-shaped): `stamp(domain, msg, len, out)`, domain `0x45` for edges, `0x4d` for `MINT` |
| `0x1eb0` | hex parser |
| `0x1240` | serializer used by `GET` (gives us the exact record layout) |
| `0x1410`/`0x1496` | `MINT` / `RUN` handlers |

### The `RUN` loop

This is the part I read wrong for the longest time. Its real shape:

```asm
1519:  xor eax,eax ; mov ecx,8  ; lea rdi,[rsp+0x20]
1525:  movzx esi, WORD PTR [0x462d4]      ; entry tag
152c:  rep stos DWORD PTR [rdi],eax       ; regs = 0   (8 u32)
152e:  lea rbp,[rsp+0x80] ; mov ecx,0x20 ; rep stos   ; buf = 0 (128 byte)
154f:  mov DWORD PTR [rsp+0x1c],0         ; printflag = 0
1553:  ...                                ; <- đầu vòng lặp, ba lệnh xóa ở TRÊN vòng
158e:  cmp si, WORD PTR [rdx]             ; tìm record theo tag
15b6:  call 1810                          ; exec_program(rec, regs, buf, input24, &printflag)
15bb:  cmp DWORD PTR [rsp+0x1c],0
15c5:  jne  1635                          ; printflag != 0 -> in buf, DUNG   <== THẮNG
15c7:  test eax,eax
15c9:  jne  15ea                          ; ret == 1 -> "denied"
15cb:  cmp BYTE PTR [rdi+0x208],0
15d2:  je   15ea                          ; no edges -> \"denied\"
15d4:  ... call 1d50                      ; emit -> tag kế tiếp
15e0:  sub r13d,1 ; jne 1553              ; tối đa 0x30d40 = 200000 bước
```

Three decisive points:

1. `printflag` is checked before the return value of `exec_program`. A record containing a print opcode
   wins even if it ends with a deny opcode.
2. The `rep stosd` sits outside the loop (`jne 1553` jumps back past them). The registers survive the
   whole walk; they are not cleared on every step.
3. The second argument of `emit` is `rsp+0x20`, which is precisely the register file, not some other region.
   The register file is only 8 u32.

### The `exec_program` VM

Jump table at `0x406c`, indexed table-relative:
`handler = 0x406c + (int32)*(uint32*)(0x406c + 4*op)`. Get one digit wrong and you get a fake handler and a
wrong table throughout.

```
0  NOP              1  MOVI  rD, imm32 (6B)  2  MOV   rD, rS
3  ADD rD,rS        4  XOR rD,rS             5  AND rD,rS      6  OR rD,rS
7  ROL rD, K        8  SHR rD, K   (K>31 -> 0)
9  ADDI rD,imm      10 XORI rD,imm           11 ANDI rD,imm
12 LBI  rD, in[k]   (k <= 0x17, ngược lại lấy 0)
13 strncpy(buf, getenv("FLAG") ?: "unavailable", 0x7f)
14 printflag = 1
15 return 1
```

For every opcode 2..8 and 12: `rD = code[pc+1]`, `rS/K/k = code[pc+2]`. Only for `ROL` and `SHR`
is the second operand a constant rather than a register index. `op > 15` just does `pc += 1`. The loop
stops when `pc >= pay_len`, so code truncated in the middle of a 6-byte instruction still runs normally.

There is no branch opcode. Each record is a branch-free function that takes registers and returns registers.

### `emit`

```c
bpl = (rec->sel_reg == 0xff) ? 0xff
    : (regs[rec->sel_reg] >> (rec->sel_bit & 31)) & 1;   // bt r32 lấy bit modulo 32
for (i = 0; i < rec->k; i++) {
    if (e[i].sel != bpl) continue;
    if (stamp6(tag || target || bpl || tweak) != (e[i].sig_lo, e[i].sig_hi)) continue;
    return e[i].target;                 // only walks paths that can be PROVED
}
return rec->dflt;                       // luôn trỏ về "deny sink"
```

Each input step controls exactly one bit, and that bit selects the edge. An edge carrying a forged signature is
skipped even when its `sel` matches. That is what "the core only ever walks a route it can
vouch for" means.

### Record layout

Derived from the serialize loop inside `GET` itself:

```
wire:  tag u16 | sel_reg u8 | sel_bit u8 | dflt u16 | L u16 | code[L] | k u8 | k * 13B
edge:  sel u8 | target u16 | tweak u32 | sig_lo u32 | sig_hi u16
mem:   stride 0x30c, code @ +8 (512B), k @ +0x208, edge[j] @ +0x20c + 16j
```

### The four kinds of record

Boot `entry=30137`, 40 records, 129 edges. Classified by payload length:

* 252 bytes, the entry record: `MOVI r*,0` then four times `LBI r6,in[k]; ROL r6,K; OR r*,r6`.
  Meaning `r0..r5 = 6 little-endian words of the 24-byte input`. A 1-1 pairing between the input and the
  starting state.
* 12 bytes: `XORI r4,K; ADD r5,r4; ROL r5,s`. Touches only `r4, r5`.
* 30 bytes: `ADD r0,r1; ROL r0,s1; XOR r2,r0; ADD r3,r2; ROL r3,s2; XOR r1,r3;
  ADDI r0,A; XORI r2,B`. Touches only `r0..r3`.
* 117 bytes, the "fold": `r6 = (r0^C0) | (r1^C1) | ... | (r5^C5)` then
  `r6 |= r6>>16; r6 |= r6>>8; r6 |= r6>>4; r6 |= r6>>2; r6 |= r6>>1`.
  Collapses every bit down into bit 0, so `bit0(r6) == 0 <=> r6 == 0 <=> r_i == C_i for every i`.
  Its `sel=0` edge leads straight to the winning record.
* The winning record: payload `0d 0e 0f` = GETFLAG, PRINT, HALT. Because `printflag` is checked before
  `ret`, the HALT does not matter.
* The deny sink: payload `0f` = HALT. Every other record has a `dflt` pointing back to it.

## Solution

**Step 1 - Ruling out the forward direction.** The walk is deterministic in the input, `RUN` only returns `denied`
(no step count, nothing to hill-climb on), and the input is 192 bits. There is no oracle to probe bit by bit.

**Step 2 - Walking backwards from the fold record.** The state entering the fold record is forced to be
`(C0..C5)`, and those six constants are read directly from its payload (six `XORI r7, imm` instructions).
Every record on the path (12-byte and 30-byte) is invertible: `ADD` becomes `-`,
`XOR`/`XORI` becomes itself, `ROL` becomes `ROR`, `ADDI` becomes `-`. So step back from the fold record to
the entry record, each step `pre = invert(rec.program, post)`; at the entry record,
`input = pack('<I', r0..r5)`.

At each step the forward condition must also be checked: does `step(rec, post)` really select the edge we are
stepping back over? Because `emit` takes the *first matching* edge, this condition is extremely strong and prunes
almost every branch. Path search takes under 0.1 seconds. The root of the path search is the fold record itself - we
cannot step back through it, because it uses `MOV`/`OR`/`SHR` and loses information.

**Step 3 - Classifying edges with `MINT`.** To check the forward constraint we must know which edges carry a valid
signature, because `first_match` depends on it. The signing key is per-connection so it cannot be computed offline,
but `MINT` is an absolute signing oracle: it takes at most 16 bytes and returns a 6-byte stamp, which is exactly
`(sig_lo, sig_hi)`. The edge's message is

```
MINT( tag(u16) || target(u16) || sel(u8) || tweak(u32) )[:6] == edge.sig
```

On my boot: 51/129 edges valid, 78 edges carrying forged signatures. Those forged edges are not noise - it is precisely
`emit` skipping them that opens the winning path. For instance the fold record sits right behind the 12-byte records
with `sel_reg=0xff`, and their first edge (which always matches on `sel`) is a forged edge, so the core jumps to the
second edge.

**Step 4 - Merging into one connection.** Because the image, the signing key and the solution only agree within a single session:

```
connect -> GET (image) -> 129 x MINT (phân loại edge) -> solve (ngược) -> RUN
```

~13.5 seconds for the 129 `MINT` commands, ~0.42 s/command overall, under 20 s total per submission.

**Step 5 - Verification.** The Python model (`analysis/core.py`, reimplementing the VM + `emit` + the `RUN`
loop) run forward on the input just found yields `(win, 52312, 26)`, matching the real `RUN`, and three
consecutive `RUN` calls on the same socket all return the same flag string. The actual walk is 26 records long.

## Result
```bash
python solve_live.py
```

```
$ python solve_live.py
[*] nonce: a02b52f22ef6817d
[*] image 3076 byte entry=43250
[*] 129 link, 51 hop le (13.5s)
[?] fold 24915 seed={'0x0': '0xe53bf802', ... '0x5': '0xf1551421'} -> emit idx=3 (can 3)
[+] duoi dai 26
[*] solve 0.0s -> a8a5d7f6053e442d785c81c2e7f137825c6181553d2a6d52
[*] model forward: ('win', 52312, 26)
[!] RUN a8a5d7f6053e442d785c81c2e7f137825c6181553d2a6d52 -> H7CTF{011c87d4-b5c8-405d-923a-33dbed3e5bf7}
[*] thu them 2 lan nua:
       H7CTF{011c87d4-b5c8-405d-923a-33dbed3e5bf7}
       H7CTF{011c87d4-b5c8-405d-923a-33dbed3e5bf7}
```

## Files

```
exploit.py            standalone: connect, GET, probe MINT, solve, RUN
flag.txt
analysis/core.py      VM model + emit + run (cross-checked every instruction)
analysis/back.py      tim duong nguoc
analysis/records.py   parse image
analysis/session.py   client mot ket noi
analysis/solve_live.py
analysis/diag.py      luu image + bang chu ky ve file
analysis/img_live.bin, analysis/valid_live.json
analysis/cs.asm       objdump -d
analysis/unpacked/    binary goc (khong bao gio sua)
```

