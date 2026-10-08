# Kintsugi Vault - Rev (Hard)

## Summary

`vmrun` is a custom 14-opcode VM; each guardian (`.shard`) holds a 256-byte opcode substitution table that acts as
the "decryption key" plus a 649-byte program. That program reads an 8-byte key from the command line, mixes it with
3 `LUT` layers + a linear XOR mixing pass, then compares 8 registers against 8 constants. The vault's 32-byte seed
is simply the 8 key bytes of the 4 guardians concatenated in chain order. The work required:

1. read the shard format and the ISA from `vmrun` (a static, stripped binary that cannot run on a machine without
   Docker/WSL, so a Python reimplementation was mandatory),
2. recover the decode table of the guardians whose table is not transparent ("the lost glue"),
3. run the program backwards to derive the key, accepting both values of the bits cleared by `ANDI`,
4. try every assembly order, checking against `pubkey.bin` through the Ed25519 problem,
5. sign the nonce and submit it to `POST /attest`.

Result: `seed = f860622f78adc147 0aba129efad830d8 1b091cc9cc9b71ee a4b10c57af5dd7af` (with the sample handout) and
for the instance's real handout it is
`185087fcdd31641e 58f77177f104cded f29bb38be31bf782 8dd0b1fab65c4746`,

```
H7CTF{9df8f215-6ef3-4ee2-a336-42d628680738}
```

The decisive detail is in section 7: the handout on the challenge page is the author's sample; the instance
serves its own copy at `GET /handout.tar.gz`.

## Shard format

```
0x000  4   'KSHD'
0x004  1   version = 01
0x005  1   flags;  bit0 == 1  -> decode table is inside the file (starting guardian)
                          == 0 -> BẮT BUỘC đưa file bảng ở tham số thứ 3
0x007  1   keylen = 08
0x008  2   u16 tablelen = 0x100
0x00a  2   u16 proglen  = 0x289 = 649
0x00e 16   content id (= tên file)      <- vmrun NEVER checks this
0x01e  4   (unused)                 <- vmrun NEVER checks this
0x022 16   \"next\" id is obfuscated    <- vmrun NEVER checks this
0x032 256  decode table: raw opcode -> số thứ tự handler
0x132 256  sbox (LUT), always a permutation, always transparent
0x232 649  chương trình
```

The only checks inside `main` (0x402fd0): `size > 0x31`, the magic, and
`size >= 0x132 + tablelen + proglen` (`truncated shard`). An external table file only needs to be
`> 0xff` bytes and is then copied wholesale, all 256 bytes, onto the stack (0x4030cb); it is never combined with the
file's bytes and its content is never validated. Important conclusion: we are completely free to invent decode
tables, as long as they make the program run correctly.

Key: 16 hex characters, case-insensitive, decoded with SSE and written as 8 consecutive bytes
at `rsp+0x58`.

## ISA

Dispatch: `op = table[prog[pc]]`. `op == 0` -> HALT, prints `OK`, exit 0. `op > 13` -> `bad opcode`,
exit 2. `pc >= proglen` also counts as success. The jump table at `0x486ba8` (signed, table-relative int32)
gives:

| op | mnemonic | length | semantics |
|----|----------|--------|------------|
| 0 | HALT | 1 | halt, accept |
| 1 | KEY | 3 | `rA = (u32)mem8[0x58 + B]` (B 0..7 is the key, B >= 8 reads straight into the decode table!) |
| 2 | MOVI | 6 | `rA = imm32` |
| 3 | MOV | 3 | `rA = rB` |
| 4 | XOR | 3 | `rA ^= rB` |
| 5 | ADD | 3 | `rA = (rA + rB) mod 2^32` |
| 6 | MUL | 3 | `rA = (rA * rB) mod 2^32` |
| 7 | AND | 3 | `rA &= rB` |
| 8 | OR | 3 | `rA |= rB` |
| 9 | ROL | 3 | `rA = rol32(rA, B & 31)` - B is an imm8, not a register |
| 10 | LUT | 3 | `rA = (u32)sbox[rB & 0xff]` (clears the upper 24 bits) |
| 11 | CMP | 6 | if `rA != imm32` -> print `FAIL`, exit 1 |
| 12 | ANDI | 6 | `rA &= imm32` |
| 13 | XORI | 6 | `rA ^= imm32` |

The register window is 12 32-bit cells at `rsp+0x30..0x57`; `rep stos` clears only the first 8 cells, cells 10/11
overlap exactly the 8 key bytes, cells >= 12 alias straight into the live decode-table region (the program
can rewrite its own dispatch), cells >= 0x4e touch the canary/retaddr. No guardian in the handout uses
those indices - they are latent traps, not a mechanism.

The whole opcode table and every trap were verified by reimplementing the VM (`vm.py`, the `VM` class)
and cross-checking against the painstaking results of two independent reading passes.

## The two guardian lines

Classifying the 7 shards by how they self-decode using the table inside their own file:

- Line A (`f6f11ad1`, `080ec62d`, `3e3a0fc9`, `cfa1fa34`): 3 `LUT` layers + XOR mixing,
  ending in 8 `CMP` instructions whose immediates fit exactly one byte. This is real 64-bit code.
- Line B (`3df10ef4`, `63bafd7f`, `f14ad4e2`): one `KEY -> LUT -> ADD -> ROL -> MUL -> OR ->
  XORI -> CMP` round with a 32-bit immediate. `MUL` and `OR` destroy information, so the check is very weak:
  hand analysis of `3df10ef4` yields about 528 accepted keys. They are the "dead bodyguards"
  in the mesh and carry no seed.

## Recovering the "glue" (the decode table)

`vmrun` refuses to run a line-A shard lacking the bit0 flag unless we hand it a table. The real table does not exist
in the file (their 0x32 region holds only 158..163 distinct values, i.e. random).

The recovery method, using the machine's own properties:

1. Each program uses only ~8 distinct opcodes, and since the real table is a permutation, each raw byte
   must map to a different op.
2. Instruction positions are partly known in advance: the first 8 `KEY` instructions sit at pc = 0,3,...,21 with
   operand `(i,i)`; the trailing 49 bytes are certainly 8 `CMP` instructions on `r0..r7` with one-byte immediates
   followed by one HALT byte. So `KEY`, `CMP`, `HALT` are pinned.
3. Since every opcode is 3 or 6 bytes long, every opcode position satisfies `pc % 3 == 0`; take the 5 raw bytes
   appearing most often at those positions and try every assignment to `{MOV, XOR, LUT, ANDI, XORI}`
   (at most 6720 possibilities), accepting an assignment when: the walk covers the program entirely, it stops at HALT
   on exactly the last byte, there are exactly 8 `CMP` instructions, every register operand is <= 11, and the
   backward run has no contradiction.

For `080ec62d` and `3e3a0fc9` there is also a shortcut: transplanting the entire `(pc, op)` sequence of `f6f11ad1`
onto their positions gives 0 conflicts - meaning these three shards share one program shape. `cfa1fa34` is
out of phase because its leading `XORI/ANDI` round runs 5 passes instead of 4, so the search above had to be used;
its table is
`f7=KEY 79=XORI 4e=ANDI d6=LUT 4c=XOR c1=MOV bc=CMP 44=HALT`.

## Inverting the key

With the correct table, a line-A program has the shape

```
r0..r7 = key[0..7]
vòng 1: (XORI r?, imm) (ANDI r?, mask) xen kẽ trên một vài thanh ghi
lặp 3 lần: LUT r?,r?  ->  16 lệnh XOR trộn  ->  XORI r?, imm
MOV r0,r0 x56          (padding)
CMP r0..r7, byte đích  -> HALT
```

Every step is invertible except `ANDI`: a bit that the mask clears can never influence the result, so it is a free
bit. Running backwards from the 8 `CMP` to the start gives the value of each `key[i]` together with the list of free
bits; each guardian therefore has 16..64 accepted keys rather than just 1.

The fatal trap when enumerating variants: free bits must be forced to both 0 and 1. A loop that only *sets*
the bit (`k[s] |= 1 << b`) misses exactly half of the solution space, and that is why the first seed assembly
returned 0 results even though the algorithm was already correct.

## Assembling the seed

4 pieces of 8 bytes, 24 orderings, the product of the variants (16 x 32 x 32 x 64) - comfortably inside one minute of compute:

```
seed = f860622f78adc147 0aba129efad830d8 1b091cc9cc9b71ee a4b10c57af5dd7af
       f6f11ad1           3e3a0fc9           080ec62d           cfa1fa34
Ed25519_pubkey(seed) = 5a0239a82fba9d2d5c6c5418e237ed8a888baeced6f4c32aa71e7be3805775ee
pubkey.bin           = 5a0239a82fba9d2d5c6c5418e237ed8a888baeced6f4c32aa71e7be3805775ee  -> khớp
```

The oracle here is mathematics, not the server: the public key derived from the seed matching proves that the 4 keys
and their order are the unique correct solution, with no need to wait for the endpoint to respond. The
(seed -> pubkey) pair was verified with two independent implementations: `cryptography` 50.0.1 (OpenSSL) and a
hand-written pure-stdlib `ed25519/ed.py`; both match the 3 vectors of RFC 8032 section 7.1.

Hypotheses eliminated by this oracle (no match): the 8 target `CMP` bytes concatenated; all the
`XORI` immediates; every 32-byte window of every file in the handout; the header's 16-byte field pairs (`id`,
`next`); reversed byte order.

## Attestation - state

Exactly as the README says, the contract is `GET /attest` -> a 24-byte nonce (48 hex characters), then
`POST /attest` with `nonce` and `sig` (hex). Our own signature verifies against `pubkey.bin` (checked locally, with
two independent implementations). And yet the endpoint returned `400 attestation incomplete` for *every* variant
tried - the full list is in `notes.md` K9/K11: several message constructions, every body encoding, every field alias,
40 GET+POST pairs on the same connection, and even `OPTIONS/PUT/PATCH/DELETE` (the app accepts only
`GET, POST, OPTIONS, HEAD`, on the single path `/attest`).

The key point: the server returns the same message for `sig="zz"` (invalid hex), a `sig` of the wrong length, a
missing field, and a nonce that was never issued. That means it offers no oracle whatsoever to distinguish "nonce not
found" from "wrong signature" - so the contract cannot be probed by brute force.

The chain of reasoning then led to a wrong conclusion: "the handout is internally consistent, the signature is valid,
the server refuses flatly => this container is not bound to the artifact we have". Half right: the artifact we had
really was not bound to the instance - but not because the instance was broken.

The key was a request nobody had made: `GET /handout.tar.gz` on the instance itself returns 200 with
318172 bytes, sha256 `6bbfc07a...`, i.e. an artifact set completely different from the static 347257-byte file
(`4ce8375d...`) downloaded from the challenge page. The instance's copy has a different `pubkey.bin`
(`5b0a2f81...`), 7 shards with different content ids, chain start `35e266269ee5...`, timestamps at the instance's boot
time. In other words: the file on the challenge page is the author's sample dump
(`MANIFEST.txt` says `team: team-local` - a signal that was seen but not doubted early enough).

Re-running the exact pipeline (`analysis/live_solve.py <thu_muc>`) on the real artifact:

| guardian | how the table was obtained | key (8 bytes) |
|----------|----------------|--------------|
| `35e266269ee5` (start, flag 0x01) | its own transparent table | `185087fcdd31641e` |
| `80014ce50564` | raw->op assignment search | `58f77177f104cded` |
| `42b1de232bfc` | raw->op assignment search | `f29bb38be31bf782` |
| `aaae515b295d` (flag 0x02) | raw->op assignment search | `8dd0b1fab65c4746` |

```
seed  = 185087fcdd31641e58f77177f104cdedf29bb38be31bf7828dd0b1fab65c4746
sig   = Ed25519_sign(seed, bytes.fromhex(nonce))        # 24 raw bytes, NOT a hex string
POST /attest  nonce=...&sig=...  ->  200
H7CTF{9df8f215-6ef3-4ee2-a336-42d628680738}
```

The entire endpoint investigation in K9-K14 was not wasted: it proved that the server fails *before*
parsing the signature, i.e. its verification key differs from the `pubkey.bin` in the sample handout - which is
exactly the clue leading to the dynamic artifact file. Offline flag recovery was checked further
(`analysis/flag_sweep.py`, 53 byte arrays x ~30 encodings): no flag anywhere in the handout.

