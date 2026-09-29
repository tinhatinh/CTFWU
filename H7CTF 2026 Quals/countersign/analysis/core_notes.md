# countersign — core primitives: transcribed pseudocode + verified models

Artifact: `unpacked/countersign` (ELF x86-64 PIE, stripped, 22768 B).
Disassembly: `cs.asm` = `objdump -D -M intel --section=.text` (regenerated; 2113 insns, 0x1140–0x368d).
`.text` 0x1140 size **0x2552** (not 0x2e00) → 0x1140–0x3692. `.rodata` 0x4000/0x10e. `.data` 0x6070/0x10.
`.bss` 0x6080 size **0x70e80** (462464 B) → 0x6080–0x76f00.

## 0. Method + verification status (read this first)

No network was used; the ELF was never executed. Ground truth was obtained by
**emulating the disassembly text**: a purpose-built x86-64 subset interpreter
(`C:\tmp\csrev\emu.py`, ~25 mnemonics + the handful of SSE ops used) that loads
the real `.text`/`.rodata`/`.data` at their VMAs and stubs `open/read/close/memset/
getenv/strncpy/fgets/puts/printf/snprintf`. Every formula below marked **[V]** was
confirmed by executing the binary's own instructions under that interpreter and
comparing against an independent Python model. Marked **[R]** = read off the
disassembly only.

Corrections to the assumptions in the brief (all [V]):
* `0x17c0` is **not** a rolling/MAC primitive — it is a 6-byte append to a byte log.
* `0x1af0` is the MAC (a SipHash-shaped ARX), not a helper.
* `0x1810` is a bytecode interpreter, `0x1d50` is the authenticated chain step.
* `0x16c0` is glibc/crt boilerplate (`deregister_tm_clones`), not challenge code.
* `0x76ee0` is not the MAC key; the MAC key is raw urandom at `0x76ef0`/`0x76ef8`.

Caveat: the emulator is my code. It self-checks by reproducing (a) the 40-entry
u16 table from a hand-written rejection-sampling model, (b) 51/51 stored entry
MACs from a hand-written MAC model, (c) the 6-byte append semantics over 200
random cases, (d) the VM opcode table over 1600 random programs. It found two
genuine traps that pure reading had me get wrong (op 7 rotate amount is an
**immediate**, and `ch` high-byte handling).

## 1. Data map

| addr | size | contents |
|---|---|---|
| 0x460a0 | 0x10 | scratch (`movaps xmm0` store @0x2cee, read back @0x2e26) |
| 0x460b0 | 8 | scratch qword (@0x2ce7) |
| **0x460c0** | **0x50 = 40 × u16** | random-permutation table `T[]`, distinct, non-zero [V] |
| 0x46104 / 0x4610a / 0x4610c / 0x4610e | 2 | = T[34] T[37] T[38] T[39] (alias addresses used as cursors) |
| 0x46110 | — | end-of-table sentinel pointer (r9 @0x2077), **no data here** |
| 0x462c0 | 8 | PRNG state A (written 0x2123, overwritten 0x2c0e) |
| 0x462c8 | 8 | PRNG state B, resumable (0x26d9, 0x2ad1, 0x3003, 0x35a6) |
| 0x462d0 | 2 | T[39] — terminal/sink node id |
| 0x462d2 | 2 | T[38] |
| **0x462d4** | 2 | T[0] = **walk start node id** (read by GET 0x128e and RUN 0x1525) |
| 0x462d8 | 4 | record count `nrec` (=40 for the 40-entry table) [V] |
| **0x462e0** | nrec × **0x30c** | record array (capacity to 0x76f00 = 256 records) [V] |
| 0x60a0 | 0x12+ | GET serialization header (0x60a0 magic `CSGN`, +4 ver=2, +6 nrec, +8 start, **+0xa = qword 0x76ee0**) |
| **0x76ee0** | 8 | `seed` = 2nd urandom read; also = NONCE output |
| **0x76ef0 / 0x76ef8** | 8+8 | MAC key `k0,k1` = **raw** first 16 urandom bytes |

## 2. `0x1fa0` — boot: image/key generation (one function, 0x1fa0–0x35d7, 1255 insns)

Called once from `main` @0x116d; returns 0 = ok, non-zero → `main` prints
"boot error" (0x4022) and exits 1. Frame `sub rsp,0x10488` (canary at rsp+0x10478).

### 2.1 entropy (0x1fcd–0x2037)
```
fd   = open("/dev/urandom", O_RDONLY)            ; 0x1fa4 lea rdi,[rip+0x206a] # 4015
read(fd, &bss[0x76ef0], 16)  -> k0, k1           ; 0x1fdf,0x1fea   (128-bit MAC key, raw)
read(fd, [rsp+0x3c0], 8)     -> seed; [0x76ee0]=seed ; 0x1ff9,0x2008,0x2060
read(fd, [rsp+0x3c8], 8)     -> s2               ; 0x2017,0x2026
close(fd)                                        ; 0x2037
r14 = seed ^ 0xa5a5a5a5a5a5a5a5                  ; 0x2046,0x2067,0x206f
memset([rsp+0x470], 0, 0x10000)                  ; 0x2050/0x206a/0x2072  = u8 seen[65536]
```
Each read must return exactly the requested count, else jump 0x3662 (close + error).
Total secret entropy = **32 bytes / 256 bits**: 128 bits MAC key (never transmitted,
never derived) + 64 bits `seed` (**transmitted**) + 64 bits `s2` (never transmitted).

### 2.2 stream A → `T[40]` (0x2077–0x2111) [V]
```
mix33(z): z ^= z>>33; z *= 0xff51afd7ed558ccd; z ^= z>>33; z *= 0xc4ceb9fe1a85ec53; z ^= z>>33
          ; 0x20c9–0x20e9  (Murmur3 finalizer, but all shifts are >>33, not >>30)
st = s2                                  ; rbp = [rsp+0x3c8]  @0x2058
repeat:
    st += 0x2545f4914f6cdd1d             ; 0x20c3 (rdi)
    v  = mix33(st) & 0xffff              ; 0x20ec test ax,ax
    if v == 0        -> retry            ; 0x20ef
    if seen[v]       -> retry            ; 0x20f4  (byte map at rsp+0x470)
    *u16cursor++ = v ; seen[v] = 1       ; 0x20fe/0x2106, cursor r8 = 0x460c0 → end r9 = 0x46110
until cursor == 0x46110                  ; 0x210e  ⇒ exactly 40 values
[0x462c0] = st                           ; 0x2123  (later overwritten @0x2c0e)
```
`T` = 40 **distinct, non-zero** u16 ⇒ a partial random permutation of [1,65535].
Alias reads: T[0]→0x462d4 (start), T[38]→0x462d2, T[39]→0x462d0 (sink/default).

### 2.3 record 0 prelude (0x2113–0x224f) [V]
`rec[T-index]` layout, stride 0x30c, `memset(rec,0,0x30c)` @0x218e:
```
rec+0x00 u16  id       = T[i]
rec+0x02 u8   sel      ; 0xff = unconditional node, else index into the register file
rec+0x03 u8   bit      ; bit position tested in regfile[sel]  (0..31)
rec+0x04 u16  default  = T[39]  (sink)      ; every node's fallback
rec+0x06 u16  plen     ; byte length of the program below (log counter, see §4)
rec+0x08      program bytes (up to 0x30c-8 = 772 B, NO bound check in the appender)
rec+0x208 u8  nent      ; number of transition entries
rec+0x20c + j*0x10  entry j :
        +0x00 u8  sel   ; selector this entry answers to (0x00 / 0x01 / 0xff)
        +0x02 u16 val   ; NEXT NODE ID
        +0x04 u32 imm   ; per-edge salt/nonce, MAC-input only, unused by the VM
        +0x08 u32 mac0  \  48-bit tag, stored contiguously as u32+u16
        +0x0c u16 mac1  /
        +0x0e (2 B pad)
```
rec0 header writes: `rec+0 = T[0]` (0x21a2), `rec+2 = 0xffff` (0x21a7).
Prelude program, for i=0..5: one `0x17c0` append (op 1, dst=i, imm=0) @0x21bb, then 4
hand-written 9-byte groups @0x21d3–0x2236 → `plen = 6*(6+4*9) = 252` (0x2240 `add edi,0x24`).
Emitted text (verified by disassembling the generated bytes) [V]:
```
for i in 0..5:  r[i] = 0
                for j in 0..3:  r[6] = in[4i+j];  r[6] = ROTL32(r[6], r[8j] & 31);  r[i] |= r[6]
```
i.e. `r[i] = OR_j ROTL32(in[4i+j], r[8j])`, with r[8]/r[16]/r[24] left at their
initial 0 and r[0] being block 0's own result (rotate amount taken mod 32).

### 2.4 stream B + node/edge generation (0x2255 → 0x35d7)
rec0's first entry is seeded at 0x2263/0x2271 (`sel=0xff`, `nent=1`, `val=T[1]`), then a
12-iteration loop @0x23a0 (cursor `r8` walks `0x460c2, +6` each pass, terminates at
`0x4610a` @0x2375–0x2388) consumes `T` in triples and writes 3 records per iteration
(stride arithmetic `0x924 = 3*0x30c`, @0x2312/0x2319/0x2328).
Per-iteration mixing (0x23ae–0x251a) is **standard splitmix64** on a state advanced by
`0x2e2ac13ef8e8d8d2`:
```
mix(z): z ^= z>>30; z *= 0xbf58476d1ce4e5b9; z ^= z>>27; z *= 0x94d049bb133111eb
        ; 0x23e4/shr 0x1e, 0x23f0 imul r15, 0x23f7/shr 0x1b, 0x2403 imul r10  (×6, unrolled)
        ; NOTE: the standard final `z ^= z>>31` is NOT applied here; each consumer
        ; applies it lazily at the point of use (see the derived scalars below).
rbp0 = 0x2e2ac13ef8e8d8d2 + (seed ^ 0xa5a5a5a5a5a5a5a5)      ; 0x2298,0x22a2
out_m = mix(rbp0 + Km),  m = 1..6                            ; Km @0x23ae,0x23c2,0x2427,0x245b,0x248f,0x24c3
   K1=0x700cb87a8661a343 K2=0x0e44323405ac1f58 K3=0xac7babed84f69b6d
   K4=0x4ab325a704411782 K5=0xe8ea9f60838b9397 K6=0x8722191a02d60fac
rbp += 0x2e2ac13ef8e8d8d2                       ; 0x235f–0x2372, once per iteration
```
Derived scalars, each of the form `a = out ^ (out>>31)` [V]:
`sel8 = a(K5) & 3` @0x254c–0x2560 (rec+2), `bit8 = a(K6) & 0x1f` @0x2559–0x2576 (rec+3),
and `a(K1) % 30 + 1` (reciprocal `0x8888888888888889`/`shr 4`, 0x25c8–0x25e3) feeds a
program operand byte; the same pattern repeats at 0x2657. Node programs are
emitted through `0x17c0` (0x26b8, 0x26d4, 0x2801, 0x28fd, 0x2e7b) plus direct byte
stores (0x257d–0x2643); edges and their tags via `0x1af0` (0x2b3a, 0x307d).
`0x1810`/`0x1d50` are also called once during generation (0x2ca3, 0x2cc0) as a
self-check walk with a private regfile at `[rsp+0x1b0]` and step limit 200000 (0x2c35).
`nrec` is published at 0x2834/0x2dac; PRNG state B is persisted to `0x462c8` so that
later stages resume the same stream.

### 2.5 what the image actually is [V]
For `nrec = 40`: **125 serialized entries, exactly 51 of which carry a MAC that
verifies**. Structure recovered from an emulated generation:
* 25 pass-through nodes (`rec+2 == 0xff`) with 1 valid entry (selector 0xff);
* 13 decision nodes (`rec+2 ∈ {0x00,0x01,0x02,0x03,0x06}`) with exactly 2 valid
  entries, selector `0x00`/`0x01`;
* 2 empty sinks (rec37=T[38], rec38=T[39]).
⇒ 25·1 + 13·2 = **51** live edges. So the image is a 40-node authenticated decision
DAG: start = `T[0]` (rec0), the walk consumes one register bit per decision node,
sink = `T[39]` (rec38). Node programs mix `in[0..23]` into `r[0..7]`; `r[6]` is the
prelude accumulator, and the terminal node (rec39) tests `bit 0 of r[6]`.
The remaining **74 entries are decoys**: their 6-byte `mac` fields come from a stream
that is **invariant under a change of the MAC key and under a change of `s2`, and
changes only when `seed` (0x76ee0) changes** — i.e. decoy bytes = PRNG(seed). Proved by
three differential generations (only-key / only-s2 / only-seed varied): 74/125 mac
fields byte-identical across key change, 0/125 across seed change, and the valid/invalid
*position pattern* identical in all three.
Consequence: the 128-bit key is **not** needed to know which edges are live — but a
client-side reimplementation of stream B is. (Whether the decoy stream is reproducible
from the transmitted `seed` alone is the one thing I did **not** finish; see §8.)
Key recovery from the oracle: the tag is 48 bits truncated, the key is 128 raw random
bits, the primitive has no known related-key weakness here ⇒ infeasible; and MINT only
signs attacker-chosen messages, so it is not a verification oracle.

## 3. `0x1af0` — the MAC [V] (called from 0x14d5 MINT, 0x1e36 chain-step, 0x2b3a, 0x307d)

```
void mac(rdi = tag/*DEAD*/, rsi = msg, edx = len, rcx = out /*6 bytes*/)
sub rsp,0x30; canary [rsp+0x28]
buf[0] = tag; zero buf[1..0x1f]                       ; 0x1b14–0x1b1d  (32-byte buffer)
n = len & 0x3f; for i<n: buf[i] = msg[i]              ; 0x1b22–0x1b36  (clamps copy to 63)
v0 = k0 ^ 0x736f6d6570736575                          ; 0x1b38/0x1b49/0x1b6b   (rsi)
v1 = k1 ^ 0x646f72616e646f6d                          ; 0x1b3f/0x1b61/0x1b71   (rax)
v2 = k0 ^ 0x6c7967656e657261                          ; 0x1b6e/0x1b74          (r12)
v3 = k1 ^ 0x7465646279746573                          ; 0x1b81                 (rdx)
; "somepseudorandomlygeneratedbytes" — SipHash c/d IV, keys k0=[0x76ef0] k1=[0x76ef8]
mfin = (len & 0xff) << 56                             ; 0x1b46,0x1b5d  (rbx)
if len >= 8:  for off in {8,16}: v3 ^= LE64(buf[off-8:off]); 2×ROUND; v0 ^= LE64(buf[...])
              ; 0x1b84,0x1bbf,0x1bc4,0x1bc9,0x1bcc–0x1bfd, loop ctrl 0x1ba0–0x1bbd
tail:  nb = len - (((len-8) & ~7) + 8)  /* if len>=8 */ ; 0x1c10–0x1c1e
       for i<nb: mfin |= buf[(len-nb)+i] << (8i)          ; 0x1c40–0x1c59
v3 ^= mfin; 2×ROUND; v0 ^= mfin; v2 = (v2 ^ 0xff); 4×ROUND ; 0x1c5b–0x1ce8
h = v0 ^ v1 ^ v2 ^ v3                                   ; 0x1ce8–0x1ced
out[i] = (h >> (8i)) & 0xff  for i in 0..5              ; 0x1d00–0x1d19   ⇒ 48-bit tag
```
The single round, transcribed from 0x1bcc–0x1bfd (identical code at 0x1c63–0x1c94 and in
the finalisation body 0x1cac–0x1ce6) and confirmed bit-exact against 900 random states:
```
ROUND(v0,v1,v2,v3):
    p = (v0 + v1) & M64            ; 0x1bcc
    q = ROTL64(v1,13) ^ p          ; 0x1bcf,0x1bd7
    s = (v2 + v3) & M64            ; 0x1bd3
    t = ROTL64(v3,16) ^ s          ; 0x1bda,0x1bde
    n0 = ROTL64(p,32) + t          ; 0x1be1,0x1bec
    u = s + q                      ; 0x1be5
    n1 = ROTL64(q,17) ^ u          ; 0x1be8,0x1bf3
    n2 = ROTL64(u,32)              ; 0x1bf6,0x1bfd
    n3 = ROTL64(t,21) ^ n0         ; 0x1bef,0x1bfa
    return n0,n1,n2,n3
```
**Verified Python** (all lengths 0..23, random keys, byte-exact vs the emulated `0x1af0`):
```python
M64=(1<<64)-1
def rotl(x,b): b&=63; return ((x<<b)|(x>>(64-b)))&M64 if b else x
def R(v0,v1,v2,v3):
    p=(v0+v1)&M64; q=rotl(v1,13)^p; s=(v2+v3)&M64; t=rotl(v3,16)^s
    n0=(rotl(p,32)+t)&M64; u=(s+q)&M64
    return n0, (rotl(q,17)^u)&M64, rotl(u,32), (rotl(t,21)^n0)&M64
def mac(k0,k1,msg,out=6):                       # needs len(msg)<24
    v=[k0^0x736f6d6570736575,k1^0x646f72616e646f6d,k0^0x6c7967656e657261,k1^0x7465646279746573]
    off=0
    for base in (8,16):
        if len(msg)<base: break
        m=int.from_bytes(msg[off:off+8],'little'); v[3]^=m
        for _ in range(2): v=R(*v)
        v[0]^=m; off=base
    b=(len(msg)&0xFF)<<56
    for i,c in enumerate(msg[off:]): b|=c<<(8*i)
    v[3]^=b
    for _ in range(2): v=R(*v)
    v[0]^=b; v[2]^=0xff
    for _ in range(4): v=R(*v)
    return (v[0]^v[1]^v[2]^v[3]&M64).to_bytes(8,'little')[:out]
```
Notes [V]: the `tag` argument is **dead** — it lands only in `buf[0]`, which the copy
loop overwrites for `len>0`; verified `mac(...)` is identical for tag 0x45/0x4d/0x00/0xff.
Therefore **MINT (≤16 bytes, tag 0x4d @0x14d0) is a direct signing oracle for the exact
9-byte chain-edge messages**. Two latent bugs, unreachable from the shipped callers:
the block loop can never advance past a 2nd block (`mov r10d,0x10` @0x1ba9 is a constant,
threshold fixed at 24 @0x1bb2) ⇒ `len >= 24` **hangs**; and the clamp is 63 bytes into a
32-byte stack buffer @0x1b22–0x1b36.
Width: input = arbitrary bytes (`edx`), output = **6 bytes / 48 bits**.
**Not** established to be bit-identical to published SipHash-2-4 — see §8.

## 4. `0x17c0` — transcript appender [V] (0x21bb, 0x26b8, 0x26d4, 0x2801, 0x28fd, 0x2e7b)
```
append6(rdi = rec, esi = a, edx = b, ecx = c):     ; a,b = low bytes only, c = u32 LE
    w = rec.len16                                  ; movzx edx,WORD [rdi+6]  @0x17c3
    rec.buf[w+0] = a & 0xff                        ; 0x17cf
    rec.buf[w+1] = b & 0xff                        ; 0x17da
    rec.buf[w+2..w+5] = c little-endian            ; 0x17e5,0x17f0,0x17fd,0x1802
    rec.len16 = (w + 6) & 0xffff                   ; 0x1806,0x180a
```
No length check; buffer is `0x30c-8 = 772 B`, `len` is u16. Verified against a Python
model on 200 random (buffer, w, a, b, c) cases. Not a MAC/rolling function.

## 5. `0x1810` — the VM / interpreter [V] (0x15b6 RUN, 0x2ca3 self-check)
```
int run(rdi = rec, rsi = regfile/*u32[]*/, rdx = in24, rcx = outbuf128, r8 = haltflag)
    if rec.len16 == 0: return 0                    ; 0x1810–0x1815, 0x1ae5
    pc = 0
    loop: op = rec.buf[pc]                         ; 0x1847
          if op > 0xf: pc += 1; goto advance       ; 0x184d→0x1877
          jmp table[0x406c + op*4] + 0x406c        ; 0x1855–0x185c
    advance: if (u16)rec.len16 > pc: goto loop     ; 0x1880–0x1887
             else return 0                          ; 0x1889
```
Register operands are **raw bytes 0..255 with no bound check**; the caller's regfile is
32 B = `r[0..7]` (`rep stosd`, ecx=8 @0x151b/0x152c), so `r[i]` for i≥8 aliases the
stack (input buffer at lower addresses, out buffer at rsp+0x80). Latent, not reachable
from a server-generated image (all emitted indices ≤ 24) [R].

Opcode table (jump table at 0x406c decoded; semantics confirmed op-by-op by isolated
execution, and a Python model matched the emulator on 1600 random programs):

| op | size | semantics | handler |
|---|---|---|---|
| 0x0 | 1 | nop | 0x1877 |
| 0x1 | 6 | `r[b1] = imm32` | 0x1a98 |
| 0x2 | 3 | `r[b1] = r[b2]` | 0x1ac0 |
| 0x3 | 3 | `r[b1] = r[b1] + r[b2]` | 0x1a70 |
| 0x4 | 3 | `r[b1] ^= r[b2]` | 0x1a48 |
| 0x5 | 3 | `r[b1] &= r[b2]` | 0x1a20 |
| 0x6 | 3 | `r[b1] \|= r[b2]` | 0x19f8 |
| 0x7 | 3 | `r[b1] = ROTL32(r[b1], b2 & 31)` — **rotate amount is the immediate byte**, not `r[b2]` (0x19e2 loads only the byte, 0x19e8 `rol …,cl`) | 0x19d0 |
| 0x8 | 3 | `r[b1] = (b2 > 31) ? 0 : r[b1] >> b2` (explicit zero, unlike x86 `shr`) | 0x1980 |
| 0x9 | 6 | `r[b1] += imm32` | 0x1960 |
| 0xa | 6 | `r[b1] ^= imm32` | 0x19b0 |
| 0xb | 6 | `r[b1] &= imm32` | 0x1940 |
| 0xc | 3 | `r[b1] = (b2 <= 0x17) ? in24[b2] : 0` — the only input read, 24 bytes | 0x1910 |
| 0xd | 1 | `strncpy(outbuf128, getenv("FLAG") ?: "unavailable", 0x7f)`; zeroes the 128 B first | 0x1898 |
| 0xe | 1 | `*haltflag = 1` (accept marker) | 0x1870 |
| 0xf | 1 | `return 1` (main maps this to "denied") | 0x1860 |

op 0xd: `lea rdi,[rip+0x2771] # 4010` = `"FLAG"`, default `[rip+0x274a] # 4004` =
`"unavailable"`; `cmovne rsi,rax` @0x18cc picks the env value when set.
Operand reads may run past `plen` (the `count > pc` test is at 0x1880, after the body) —
the trailing bytes are inside the 0x30c record and are zeroed by `memset`.

## 6. `0x1d50` — authenticated chain step [V] (0x15d9 RUN, 0x2cc0 self-check)
```
u16 step(rdi = rec, rsi = regfile):
    sel = rec.sel8                                 ; 0x1d63  [rec+2]
    if sel != 0xff:  sel = (regfile[sel] >> rec.bit8) & 1   ; 0x1d7e,0x1d81 bt/setb  [rec+3]
    if rec.nent == 0: return rec.default16         ; 0x1d8d,0x1e9a   [rec+0x208], [rec+4]
    for j in 0..nent-1:                            ; entries at rec+0x20c, stride 16, scan 0x1dcd
        e = &rec+0x20c + j*16
        if e.sel8 != sel: continue
        msg = u8[8] = { lo(id16), hi(id16),        ; 0x1dee–0x1e30 (SSE byte permute,
                        lo(e.val16), hi(e.val16),   ;   movdqa/punpcklbw/pshufd/movd)
                        sel,                        ; 0x1de9
                        LE32(e.imm32) }             ; 0x1df4
        mac6 = mac(k0,k1,msg)                      ; 0x1e36, tag = 0x45
        if LE32(mac6[0..3]) != e.u32@+8: continue   ; 0x1e3b–0x1e41
        if LE16(mac6[4..5]) != e.u16@+12: continue  ; 0x1e47–0x1e50
        return e.val16                             ; 0x1e70
    return rec.default16                           ; 0x1e9a
```
Verified: the 9-byte message is exactly `id||val||sel||imm` (byte order confirmed by
reproducing 51/51 stored tags), and `id = rec+0` (the *current* node), so a tag binds an
edge to its source node, its selector, its successor and its nonce. A failing MAC makes
the scan **continue**, which is what makes the 74 decoys harmless-but-confusing.
Return width: **u16 node id**. Input: 1 bit of the register file (or the 0xff sentinel).

## 7. helpers not in the brief, and `0x16c0`
* `0x16c0` (called from `0x1758`) = **`deregister_tm_clones`**: compares `&bss[0x6080]`
  to itself, then calls `[0x5fc8]` (`_ITM_deregisterTMCloneTable`) if non-NULL. Same for
  `0x16f0` (`register_tm_clones`, called by `frame_dummy` @0x1780 = `.init_array[0]`),
  `0x1730` = `__do_global_dtors_aux` (`.fini_array[0]`, guarded by byte `0x6098`).
  crt-file boilerplate; **no challenge role**. [V] trivially (only the two `lea/cmp/ret` paths)
* `0x1eb0` (called from `0x142e` MINT, `0x14a3` RUN) = hex decoder:
  `int hexdecode(rdi = str, rsi = out) -> outlen`, pairs of hex digits → `out[i]`,
  **skips** `\n \r space` (mask `0x400009` @0x1eb6 tested by `bt` 0x1ee0, skip path 0x1ee6),
  stops at NUL, digits/`a-f`/`A-F` else **returns -1** (0x1f00), `cmp esi,0x3f` caps output
  at 64 bytes (0x1f36). Odd trailing nibble is dropped. Callers check the length
  (`cmp eax,0x10; jbe` @0x1433 for MINT, `cmp eax,0x18; je` @0x14a8 for RUN ⇒ exactly 24).

## 8. `main` (0x1140–0x168f) command → globals touched
Dispatch 0x11e2–0x122c on the first bytes of a 0x2000-byte `fgets` line at rsp+0x200
(`EG`=GET, `NONC`=NONCE, `MINT`, `RUN `=0x204e5552, `QUIT`=0x54495551, else `"?"` 0x406a).
* **GET** 0x1240: builds header at 0x60a0 = `"CSGN"`, ver `2`, `nrec` (0x462d8),
  start `T[0]` (0x462d4), **qword `seed` = [0x76ee0]** @0x129c–0x12a3 → then per record
  (0x12d0–0x1393): 8-byte hdr (id, sel, bit, default, plen) + `plen` program bytes +
  `nent` byte (rec+0x208) + `nent`×**13 bytes** (sel, val, imm, mac[6]) — every
  MAC is transmitted. Bytes printed `%02x` @0x13b0–0x13c8. **The seed leaves the box.**
* **NONCE** 0x13e0: `printf("%016llx\n", [0x76ee0])` — the seed again, second channel.
* **MINT** 0x1410: hex-decode ≤16 B → `mac(tag=0x4d, msg, len, rsp+0x80)` @0x14be–0x14d5 →
  prints 6 bytes @0x14f0. Reads key at 0x76ef0/f8 only.
* **RUN** 0x1496: hex-decode exactly 24 B → zero regfile (rsp+0x20, 32 B) and out buffer
  (rsp+0x80, 128 B), `id = T[0]`, limit 200000 @0x1519–0x154b; loop 0x1553: find record
  whose `id` matches → `run()` @0x15b6 → if halt flag (rsp+0x1c) set: `snprintf("%s",
  rsp+0x80)` @0x1635 and print ⇒ **the flag only escapes via op 0xd + op 0xe**; else if
  `run()` returned 0 and `nent != 0`: `id = step()` @0x15d9 and repeat. Any other exit
  prints `"denied"` @0x15ea. Touches 0x462d4, 0x462d8, 0x462e0[…], 0x76ef0, 0x76ef8.

## 9. Could NOT determine
1. **Bit-exact relation to published SipHash-2-4.** Same IV, same key mixing, same
   `len<<56` encoding, same 2+4 round counts, same rotation constants {13,16,17,21,32} —
   but the round is *not* a register-renaming of either SIPROUND form I can write down
   (tested all 24 permutations against the executed block). I have no authoritative
   test vector offline (no network), and my two candidate canonical forms disagree with
   each other, so I can neither confirm nor deny equivalence. Treat §3's `mac()` as the
   spec — it is byte-exact against the binary, which is what matters.
2. **Client-side reproducibility of the decoy stream.** Proven: decoy tag bytes are
   invariant under key change and under `s2` change, and vary with `seed`. Not proven:
   that they can be regenerated from the transmitted `seed` alone, because the node
   `imm` values also shift when the key changes (so the key feeds at least some
   generator draws) and I did not finish separating those streams.
3. **Exact per-record roles of the 6 splitmix outputs** (which of K1..K6 chooses
   `sel` vs `bit` vs `nent` vs successor vs decoy count) and the ordering of the
   3-records-per-iteration block at 0x22fa–0x2388 — I verified the *results* through the
   emulator but did not hand-map every field to its source word.
4. **Whether the accept node is always reachable / how many bits of the 24-byte input
   are actually constrained.** I confirmed the DAG shape (51 live edges, 13 bit tests,
   `r[6] bit 0` at the terminal) but did not solve or symbolically execute a full walk,
   and so never exercised `main`'s accept path end-to-end (my `main` harness was built
   but I did not get a halting run before stopping).
5. `0x460a0`/`0x460b0` (scratch, 0x2cee/0x2ce7) and `0x3554–0x359d` (unexecuted under my
   seed) — cold/error paths, unread.
