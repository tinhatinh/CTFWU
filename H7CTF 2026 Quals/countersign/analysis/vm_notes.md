# countersign - attestation core: function transcription

Artifact: `analysis/unpacked/countersign` (Linux ELF x86-64, PIE, stripped, `.text` 0x1140-0x3692,
`.rodata` 0x4000-0x410e, `.bss` 0x6080-0x76f00).
Method: `objdump -D -M intel` only (fresh `analysis/full_text.asm`; `cs.asm` is byte-identical in
mnemonics - compared programmatically, 0 mismatches). **No network, no execution.**
All addresses are vma == file offset for `.text`/`.rodata` (verified with `readelf -S`).

Cross-check material used (all local, from teammate captures): `grab.out` (a real `GET` image,
first 200 bytes), `oracle_results.txt` + `mint_vectors.txt` (4386 `MINT` replies).

---

## 0. Corrections to the premises I was handed

| handed to me | actual | evidence |
|---|---|---|
| jump-table entries are offsets "relative to the table's own end" | relative to the table **start** `0x406c` (`r11 = lea` target, `add rdx,r11`) | `0x1826: lea r11,[rip+0x283f] -> 0x406c`; `0x1855/0x1859` |
| record array at `0x462e8` | array base is **`0x462e0`**; `0x462e8` = record0 + 8 = `code[0]` (the GET loop walks it with an 8-byte bias) | `0x12b4 lea r13,[rip+0x4502d] -> 0x462e8`, `0x12e1 mov [rdi-8],ax`; `0x1544 lea r14 -> 0x462e0` |
| `0x462d4` = "current entry id", updated by the walk | `0x462d4` is **written exactly once** at startup and is only ever the *starting* id. The walk's running id lives in `esi` of the RUN loop | xref: write only at `0x217f`; reads at `0x128e`, `0x1525` |
| `0x22e0` = 6-byte stamp fn (8-round xor-shift-ADD-Multiply over 128 tables + 26-byte key) | **false**. `0x22e0` is one instruction (`imul rax,rax,0x30c`) in the middle of `0x1fa0`. The real stamp function is **`0x1af0`**. There are no 0x46ee0 tables, no 26-byte key, and no 8-round loop | raw bytes `0x22e0: 4a 63 c5`... `imul`; xref shows **zero** references to `0x46ee0` |
| `0x23f0` = a "checksum-like function", `0x10000f`/`0x6000600` constants | `0x23f0`/`0x2403` are two `imul`s of a SplitMix64 finalizer inside `0x1fa0`. The constants `0x10000f`/`0x6000600` **do not exist anywhere in the binary** (grep: no match) | `0x23f0: imul rax,r15` (r15=0xbf58476d1ce4e5b9), `0x2403: imul rax,r10` (r10=0x94d049bb133111eb) |
| `0x1ee0` = a startup-randomising function | `0x1ee0` is inside the **hex parser `0x1eb0`** (the whitespace skip, `bt` on mask `0x400009`). It randomises nothing | `0x1eb0..0x1f07` is one function ending in `ret` |
| "199 fixed records" | captured instance reports `count = 40`; the generator's chain loop is bounded by `0x4610a` (12 iterations x 3 records) + preamble + tail | GET header byte 6-7 = `28 00` = 40 |
| `record.done` byte | there is no `done` byte. `record+0x208` (called `n` below) does double duty: table length **and** the "this record can continue the walk" test | `0x15cb cmp BYTE [rdi+0x208],0` ; `0x1d95 test al,al` |
| `>0xf` halts and sets the completion flag | `>0xf` merely advances pc by 1 (same as opcode 0). Setting the flag is **opcode 0xe**; halting-with-return-1 is **opcode 0xf** | `0x184d ja 0x1877` ; `0x1870 mov [rbp],1` ; `0x1860 mov eax,1;ret` |

`0x5010`/`0x5018` - confirmed not referenced by any program instruction (ld.so artifacts).

## 1. Data map (all `.bss`, filled at startup by `0x1fa0`)

```
0x460a0  24 bytes  witness register state regs[0..5] captured during the startup self-walk
                   (written at 0x2ce7/0x2cee; never read from bss, but the *generator* re-reads
                    it through r14=0x460a0 at 0x2e3d to bake witness words into tail records)
0x460c0  80 bytes  40 distinct, non-zero random u16 = the "key" / id pool  [0x460c0 .. 0x46110)
                   0x460c0 = start id, 0x460c2..0x46109 = chain ids (read 3 u16 per iteration),
                   0x4610a = loop terminator, 0x4610c = FLAG-record id, 0x4610e = decoy id
0x462c0   8 bytes  splitmix state snapshot - write-only (dead)
0x462c8   8 bytes  running splitmix state used to seed the entry-`x` streams (read at
                   0x2a94, 0x2fac, 0x3139; written at 0x26d9, 0x2ad1, 0x3003, 0x35a6)
0x462d0   2 bytes  = u16 @0x4610e (decoy id)      - write-only
0x462d2   2 bytes  = u16 @0x4610c (FLAG-record id) - write-only
0x462d4   2 bytes  start id = u16 @0x460c0        - written once @0x217f, read @0x128e, @0x1525
0x462d8   4 bytes  record count (int)             - written @0x2834/@0x2dac, read @0x1268/@0x1553
0x462e0  stride 0x30c record array (see §2)
0x60a0   18 bytes  GET response header scratch
0x76ee0   8 bytes  nonce (public: printed by NONCE, embedded in the GET header)
0x76ef0/8  16 bytes SECRET stamp key (2 qwords, never transmitted, never used by any other fn)
```

## 2. Record layout (0x30c = 780 bytes, base `0x462e0`)

Verified field-by-field against the captured GET image (record 0: `0b48 ff 00 660d fc00 ...`).

```
+0x000 u16  id            record identifier (from the 0x460c0 pool)
+0x002 u8    slot          register index tested on entry; 0xff = "no test" (set together with
                            bitidx as one WORD store 0xffff at 0x2346/0x27e5/0x2d56/0x2dbf)
+0x003 u8    bitidx        bit index tested (generator emits 0..31; `bt` masks mod 32)
+0x004 u16   alt_id        "next id" returned when nothing matches (0x1e9a)
+0x006 u16   code_len      <= 0x204 (code area is +0x008 .. +0x207)
+0x008 u8    code[code_len]
+0x208 u8    n             table length; also the "walk may continue" flag (0 == stop)
+0x20c       entry[0]
             ...           16 bytes per entry, i = 0 .. n-1, entry i at +0x20c + 16*i
+0x308..    unused tail of the record
entry (16 bytes, 13 used - exactly the 13 bytes GET emits per entry, 0x1340-0x1382):
  +0x00 u8   bit      required value of that bit (generator emits 0, 1, or 0xff)
  +0x02 u16  tgt      next record id
  +0x04 u32  x        per-link nonce/tag salt (splitmix-derived)
  +0x08 u32  stamp_lo  expected stamp, bytes 0..3
  +0x0c u16  stamp_hi  expected stamp, bytes 4..5
```

GET stream (`0x1261`-`0x13d4`): `u32 magic "CSGN"`, `u16 ver`(=2), `u16 count`, `u16 start_id`,
`u64 nonce`, then per record: `id,slot,bitidx,alt_id,code_len` (8B) + `code[code_len]` + `n` +
`n` x 13-byte entries; every byte printed as `%02x`, then `\n`. Capture decoded cleanly:
`CSGN ver=2 count=40 start_id=0x480b nonce=0x81c7ad957a5c8aa9` == the `NONCE` reply `81c7ad957a5c8aa9`
(same session) - this is the strongest confirmation of the header/layout reading.

## 3. The VM - `0x1810`

```c
/* rdi=record, rsi=regs(u32*), rdx=input(24B), rcx=flagbuf(128B), r8=state(u32*) */
int vm(record *R, u32 *regs, u8 *in, u8 *flagbuf, u32 *state)
{
    if (R->code_len == 0) return 0;                     /* 0x1810 cmp WORD[rdi+6],0 / 0x1ae5 */
    r9  = R;  r12 = in;  rbp = state;  r8 = regs;       /* 0x181b-0x1834 */
    r11 = 0x406c;  eax = 0;                             /* 0x1826 (table), 0x1823 (pc) */
  loop:                                                    /* 0x1840 */
    r10d = eax + 1;                                       /* next pc */
    op   = R->code[eax];                                  /* 0x1847 */
    if (op > 0xf) { eax = r10d; goto advance; }           /* 0x184d -> 0x1877: NOP-advance */
    jmp  *(int *)(r11 + op*4) + r11;                      /* 0x1855-0x185c */
  advance:                                                /* 0x1880 */
    if ((u16)R->code_len > eax) goto loop;
    return 0;                                             /* 0x1889-0x188d (ran off the end) */
}
```

Jump table (`0x406c`, 16 x int32 LE, **target = 0x406c + entry**, all deltas negative; the table
start `0x406c` is the `lea r11` target at `0x1826`, so entries are table-**start**-relative, not
end-relative). Arithmetic written out (entry[i] = int32 LE at 0x406c+4i,
handler = 0x406c + entry[i]):

```
op 0: 0xffffd80b = -0x27f5   0x406c-0x27f5 = 0x1877     op 8: 0xffffd914 = -0x26ec -> 0x1980
op 1: 0xffffda2c = -0x25d4   0x406c-0x25d4 = 0x1a98     op 9: 0xffffd8f4 = -0x270c -> 0x1960
op 2: 0xffffda54 = -0x25ac   0x406c-0x25ac = 0x1ac0    op10: 0xffffd944 = -0x26bc -> 0x19b0
op 3: 0xffffda04 = -0x25fc   0x406c-0x25fc = 0x1a70    op11: 0xffffd8d4 = -0x272c -> 0x1940
op 4: 0xffffd9dc = -0x2624   0x406c-0x2624 = 0x1a48    op12: 0xffffd8a4 = -0x275c -> 0x1910
op 5: 0xffffd9b4 = -0x264c   0x406c-0x264c = 0x1a20    op13: 0xffffd82c = -0x27d4 -> 0x1898
op 6: 0xffffd98c = -0x2674   0x406c-0x2674 = 0x19f8    op14: 0xffffd804 = -0x27fc -> 0x1870
op 7: 0xffffd964 = -0x269c   0x406c-0x269c = 0x19d0    op15: 0xffffd7f4 = -0x280c -> 0x1860
```
(bytes dumped from `.rodata` 0x406c..0x40af; every handler lands inside `0x1810`..`0x1af0`,
which is itself a consistency check. Script: `analysis/jtbl.py`.)

### Opcode table

`D = code[pc+1]` (destination register index, u8, **no bound check** - index up to 255 reaches
`regs+1020`), `S = code[pc+2]`, `imm32 = LE u32 at code[pc+2]` (unaligned).

```
op  mnem   operands            pc+=  handler  semantics (exact)
 0  NOP    -                   1     0x1877   nothing (same path as op>0xf)
 1  MOVI   rD, imm32            6     0x1a98   regs[D] = imm32
 2  MOV    rD, rS               3     0x1ac0   regs[D] = regs[S]
 3  ADD    rD, rS               3     0x1a70   regs[D] += regs[S]           (32-bit wrap)
 4  XOR    rD, rS               3     0x1a48   regs[D] ^= regs[S]
 5  AND    rD, rS               3     0x1a20   regs[D] &= regs[S]
 6  OR     rD, rS               3     0x19f8   regs[D] |= regs[S]
 7  ROL    rD, imm_byte         3     0x19d0   regs[D] = rotl32(regs[D], S & 31)   (cl not masked
                                     rol [r8+rsi*4],cl                             by hand: x86 masks)
 8  SHR    rD, imm_byte         3     0x1980   if S > 31: regs[D] = 0  else regs[D] >>= S
                                     cmp cl,0x1f; ja; shr edx,cl        -> zero-extension, no rotate
 9  ADDI   rD, imm32            6     0x1960   regs[D] += imm32
 a  XORI   rD, imm32            6     0x19b0   regs[D] ^= imm32
 b  ANDI   rD, imm32            6     0x1940   regs[D] &= imm32
 c  LBI    rD, in[S]            3     0x1910   t = (S <= 0x17) ? in[S] : 0 ; regs[D] = t
 d  FLAG   -                    1     0x1898   getenv("FLAG") -> flagbuf
 e  SETDONE -                   1     0x1870   *state = 1            (0x1870, then falls into advance)
 f  HALT   -                    1     0x1860   return 1 from vm()
 >f NOP    -                   1     0x1877   (dispatched at 0x184d, never reaches the table)
```

Operand order for 2/3/4/5/6: **`D` is `code[pc+1]`, `S` is `code[pc+2]`** - confirmed twice:
(a) raw bytes at `0x1a70`: `movzx ecx,[r9+r10+8]` (r10 = pc+1) then `movzx edx,[r9+rdx+8]`
(rd = pc+2) then `add DWORD [r8+rcx*4], edx`; (b) the captured record-0 program decodes to
self-consistent `LBI r6,in[j]; ROL r6,8*j; OR r(i),r6` only under this order (§8).

`op 0x8 SHR` is *not* the x86 `shr` semantic: `xor edx,edx; cmp cl,0x1f; ja skip; mov edx,[rsi];
shr edx,cl; skip: mov [rsi],edx` (0x199c-0x19a7) ⇒ shifts >= 32 produce 0, and the value is read
only when `cl <= 0x1f`.

`op 0xd FLAG` (`0x1898`, raw-verified): spills `r8/r9/r10d` to `[rsp+0x18/0x10/0xc]`,
`rdi = 0x4010` ("FLAG"), `getenv`; `rsi = (rax ? rax : 0x4004)` where `0x4004 = "unavailable"`;
zeroes **128 bytes** at `rbx` (8 x `movups`, offsets 0..0x70) then
`strncpy(rbx, src, 0x7f)` (`edx = 0x7f` at 0x18c7); reloads `r8`,`r9`,`r11 = 0x406c`,`r10d`
(0x18f1-0x1902) and jumps to `0x1877` (pc += 1, no return). So opcode 0xd is the only `getenv`
user and the only handler that touches the 128-byte flag buffer.

## 4. RUN loop (`main`, `0x1519`-`0x1610`)

```c
u32  regs[32];                    /* [rsp+0x20], 128 B; only regs[0..7] zeroed @0x1519-0x152c */
u8   in[24];                      /* [rsp+0x40]  == regs[8..13] aliased! */
u8   flagbuf[128];                /* [rsp+0x80] == regs[24..] region */
u32  state = 0;                   /* [rsp+0x1c] */
/* 0x1519: zero 8 dwords @rsp+0x20 ; 0x154b: rep stosd 0x20 dwords @rsp+0x80 */
esi  = *(u16*)0x462d4;             /* 0x1525 start id */
budget = 0x30d40;                  /* 0x153b */
do {
    for (i = 0; i < count; i++) if (rec[i].id == (u16)esi) break;   /* 0x1553-0x1591 */
    if (i == count) goto denied;                    /* id not found */
    rc = vm(&rec[i], regs, in, flagbuf, &state);    /* 0x15b6 (rdi=rec, rsi=regs, rdx=in,
                                                       rcx=&flagbuf, r8=&state) */
    if (state != 0) goto print_flag;                /* 0x15bb  <-- SUCCESS test, checked FIRST */
    if (rc != 0)    goto denied;                    /* 0x15c7 op 0xf executed => hard stop */
    if (rec[i].n == 0) goto denied;                 /* 0x15cb */
    esi = link(&rec[i], regs);                      /* 0x15d9 call 0x1d50 ; 0x15de mov esi,eax */
} while (--budget);                                  /* 0x15e0/0x15e4 */
denied:   puts("denied")            /* 0x15ea-0x160b, string built from immediates
                                       0x696e6564 @0x100 + 0x646569 @0x103 => "denied\0" */
print_flag: snprintf(tmp,256,"%s",flagbuf); puts(tmp)   /* 0x1635-0x1651, fmt "%s" @0x4062 */
```

Note `regs`, `in` and `state` are **not** reset per step: the chain is a sequence of programs
sharing one 32-register file (only the first 8 registers are pre-zeroed, and the 24-byte input
aliases regs[8..13]).

## 5. `0x1d50` - step emitter / link verifier

```c
/* rdi = record R, rsi = regs */
u16 link(record *R, u32 *regs)
{
    u8 bit;                                                       /* 0x1d63 movzx ebp,BYTE[rdi+2] */
    if (R->slot == 0xff) bit = 0xff;                              /* 0x1d78 cmp/je */
    else { bit = (u8)((regs[R->slot] >> (R->bitidx & 31)) & 1); }  /* 0x1d7e-0x1d89 bt edx,eax; setb */
    if (R->n == 0) return R->alt_id;                              /* 0x1d8d/0x1d97 -> 0x1e9a */
    for (entry *e = &R->tab[0]; e != &R->tab[R->n]; e++) {        /* 0x1da5..0x1dc7, 16B stride,
                                                                     rbx=R+0x214=&e->stamp_lo,
                                                                     r13=R+0x224+16*(n-1) */
        if (e->bit != bit) continue;                              /* 0x1dcd cmp BYTE[rbx-8],bpl */
        u8 buf[9];                                                /* 0x1ddc lea rsi,[rsp+0xc] */
        *(u16*)(buf+0) = R->id;                                   /* 0x1dd3 + SSE 0x1e03-0x1e2c */
        *(u16*)(buf+2) = e->tgt;                                  /* 0x1dd7 -> xmm1 */
        buf[4] = bit;                                             /* 0x1de9 mov BYTE[rsp+0x10],bpl */
        *(u32*)(buf+5) = e->x;                                    /* 0x1de6/0x1df4 mov DWORD[rsp+0x11] */
        stamp(0x45, buf, 9, out /*[rsp+6], 6 bytes*/);            /* 0x1df8/0x1e16 mov edx,0x9,
                                                                     0x1e36 call 0x1af0 */
        if (*(u32*)out != e->stamp_lo) continue;                  /* 0x1e3b-0x1e41 */
        if (*(u16*)(out+4) != e->stamp_hi) continue;              /* 0x1e47-0x1e50 */
        return e->tgt;                                            /* 0x1e70 mov eax,r12d */
    }
    return R->alt_id;                                             /* 0x1e90 -> 0x1e9a */
}
```
It **prints nothing** (the only output of the whole RUN path is `denied` or the flag buffer, in
`main`). It returns the next id, which `main` puts in `esi` - **not** written to `0x462d4`.

Ordering of checks, exactly as executed: `slot==0xff` -> bit extraction -> `n==0` -> per-entry:
`e->bit == bit` (first match only, no look-ahead: a stamp mismatch falls through to the *next*
entry, 0x1dc0) -> 4-byte compare -> 2-byte compare. All entries failing -> `alt_id`.

The 4 SSE instructions at `0x1e03-0x1e30` build `buf[0..3]` = `id`(u16 LE) followed by `tgt`(u16
LE) - verified two ways: (i) raw-byte decode `66 0f 6e c0 / 66 0f 6f d0 / 66 0f 6e c8 / 66 0f 60 d1
/ 66 0f 60 c1 / 66 0f 70 d2 41 / 66 0f 60 c2 / 66 0f 7e 44 24 0c` gives
`A = id | (id_hi<<16)`, `B = tgt | (tgt_hi<<16)`, `X = punpcklbw(A,B)`,
`buf[0..3] = movd(punpcklbw(X, pshufd(X,0x41)))` = `[A0,A2,B0,B2]` = `[id_lo,id_hi,tgt_lo,tgt_hi]`;
(ii) the generator's stamping pass writes the *same* buffer with plain stores - `mov WORD[rsp+0x3f0],di`
(id, 0x304a) and `mov WORD[rsp+0x3f2],si` (tgt, 0x2adb/0x2aed), `mov BYTE[rsp+0x3f4],dl` (bit),
`mov DWORD[rsp+0x3f5],eax` (x), `mov edx,0x9`, `mov edi,0x45`. Both paths must agree, so the
layout is confirmed.

## 6. `0x1af0` - the 6-byte stamp (the real one)

```c
/* rdi = tweak byte (dil), rsi = data, rdx = len, rcx = out6 */
void stamp(u8 tweak, const u8 *data, u64 len, u8 out[6])
{
    u8  buf[64];                       /* [rsp] ; only [rsp+1..+0x1f] pre-zeroed (0x1b14/0x1b1d) */
    buf[0] = tweak;                    /* 0x1b19 mov [rsp],dil */
    c = len & 63;                      /* 0x1b22 and ecx,0x3f */
    if (c) for (k=0;k<c;k++) buf[k] = data[k];     /* 0x1b27-0x1b36 -> overwrites buf[0] */

    s0 = *(u64*)0x76ef0;  s1 = *(u64*)0x76ef8;     /* 0x1b38/0x1b3f  THE SECRET (128 bit) */
    u64 A=0x736f6d6570736575ULL, B=0x646f72616e646f6dULL,
        C=0x6c7967656e657261ULL, D=0x7465646279746573ULL;   /* 0x1b49/0x1b61/0x1b53/0x1b77 */
        /* BE-ascii: "somepseu" "dorandom" "lygenera" "tedbytes"
           = "some pseudo randomly generated bytes" */
    u64 x = B ^ s1;                    /* rax  (0x1b71) */
    u64 a = A ^ s0;                    /* rsi  (0x1b6b) */
    u64 b = s1 ^ D;                    /* rdx  (0x1b81) */
    u64 c4 = s0 ^ C;                   /* r12  (0x1b6e/0x1b74) */
    u64 tail = len << 56;              /* 0x1b5d shl rbx,0x38 */

    if (len > 7) {                     /* 0x1b84 cmp r8,7 / jbe 0x1d42 */
        /* absorb up to TWO 8-byte words; r10 is SET to 0x10 (never incremented) at 0x1ba9,
           and the guard is len>=16 then len>=24, so word2 is re-read as word1 -> a len>=24
           call would loop forever @0x1bbf.  All callers use len<=16 (MINT caps at 16, the
           verifier uses 9), so the reachable input domain is len in 0..16. */
        u64 w = *(u64*)buf;            /* word0, via rbp=rsp-8 (0x1b94), [rbp+r10] r10=8 */
        b ^= w; ROUND(x,a,b,c4); ROUND(x,a,b,c4); a ^= w;     /* 0x1bc9, 0x1ba2 */
        if (len >= 16) { w = *(u64*)(buf+8);
                         b ^= w; ROUND(x,a,b,c4); ROUND(x,a,b,c4); a ^= w; }
        /* rbx keeps len<<56 until the OR below (0x1b5d shl rbx,0x38) */
        u64 rcx = ((len - 8) & ~7ULL) + 8;       /* 0x1c10 lea rcx,[r8-8]; and rcx,~7; add rcx,8 */
        u64 nt  = len - rcx;                     /* 0x1c1e sub r8d,edi */
        tail |= pack_le(buf[rcx .. rcx+nt-1]);  /* 0x1c40-0x1c59 */
    } else {                           /* len <= 7: no absorption at all (0x1d42) */
        tail |= pack_le(buf[0 .. len-1]);        /* rcx=0, nt=len */
    }
    b ^= tail;                         /* 0x1c5b / 0x1bc9-equivalent for the last block */
    ROUND(x,a,b,c4); ROUND(x,a,b,c4);   /* 0x1c63 twice, edi gate 0x1c97/0x1d38 */
    a ^= tail;                         /* 0x1ca0 */
    c4 ^= 0xff;                        /* 0x1ca3 xor cl,0xff - flips the low byte of the 4th word
                                          (rcx still aliases the c4 written by the last ROUND) */
    for (i=0;i<4;i++) ROUND2(x,a,b,c4);        /* 0x1cac-0x1ce6 */
    x ^= c4; x ^= rdi;                         /* 0x1ce8/0x1ced  (rdi = rotl21 of the last rdx) */
    for (k=0;k<6;k++) out[k] = (u8)(x >> (8*k));   /* 0x1d00-0x1d19: 6 bytes, LE bytes of x */
}

#define ROTL(v,n)  (((v)<<(n))|((v)>>(64-(n))))
/* ROUND = the 15-instruction block 0x1bcc-0x1c00 (main loop) : */
void ROUND(u64*x,u64*a,u64*b,u64*c4){
    *a += *x;              *x = ROTL(*x,13);  u64 t = *c4 + *b;
    *x ^= *a;              *b = ROTL(*b,16);  *b ^= t;
    *a  = ROTL(*a,32);     t += *x;           *x = ROTL(*x,17);
    *a += *b;              *b = ROTL(*b,21);  *x ^= t;
    t   = ROTL(t,32);      *b ^= *a;          *c4 = t;
}
/* ROUND2 = 0x1cac-0x1ce0, the same permutation with (x,a,b,t) held in (rax,rsi,rdx,rcx) and
   rdi as the rotl21 temp; note the 4th word is rcx itself, i.e. it is NOT re-copied from r12
   inside the tail loop. */
```

**Exact constants / loop bounds / indexing, all from raw bytes:**
rotl amounts 13 (`0x1bd3`.. via `rol rax,0xd`), 16 (`rol rdx,0x10`), 32 (`rol rsi,0x20`),
17 (`rol rax,0x11`), 21 (`rol rdx,0x15`), 32 (`rol rcx,0x20`); 2 rounds per absorbed word;
4 tail rounds (`mov r8d,4` `0x1ca6`); output 6 bytes (`cmp rdx,6` `0x1d15`).
**Input length:** `rdx` bytes, of which `len & 63` are copied, but the absorption reads at most
`buf[0..15]` -> effectively `len in 0..16` (and only `len<=16` is ever exercised).
**Output length: exactly 6 bytes** - matches 4385/4386 observed `MINT` replies being 12 hex chars
(the one 8-byte outlier, `mint_vectors.txt` line 1, is a capture stream-sync artifact).

No table, no key array: the only key material is the 16 secret bytes at `0x76ef0`. The 26-byte-key
/ 128-table model is not in this binary.

**Two consequences worth flagging:**
* The `tweak` argument (`0x45` 'E' for links, `0x4d` 'M' for MINT, `0x4d` also at `0x14d5`) is
  **dead**: it lands in `buf[0]` which any `len>=1` copy overwrites, and for `len==0` `buf` is
  never read at all (only `tail = 0<<56`). So `MINT <9 hex-bytes>` returns *exactly* the stamp the
  link verifier expects - a legal stamp oracle over the secret.
* MINT's own output proves the stamp is length-sensitive only through `tail = len<<56` and the
  absorbed words.

## 7. `0x1eb0` / `0x1ee0` / `0x23f0` (the non-functions)

`0x1eb0(rdi = string, rsi = out bytes) -> esi = bytes produced`: hex parser. Skips leading
whitespace by `mov r8d,0x400009` + `bt r8,rcx` on `ch-0x0a` (`0x1ee0` is this skip loop, chars
0x0a..0x20); `0x1f10`-`0x1f8f` fold `0-9`,`a-f`(and `A-F`, via `-0x57`/`-0x37` variants) into
`dl = hi<<4 | lo` with `cmp cl,9`/`cmp ecx,5` range gates, rejects (`mov esi,-1; return`) on any
non-hex byte, requires an even number of digits (`test dl,dl @0x1f4a` -> second nibble must exist),
`mov BYTE [r9+rsi],dl`. Callers: `0x142e` (MINT, `cmp eax,0x10; ja -> puts "bad"` @0x404b) and
`0x14a3` (RUN, `cmp eax,0x18; jne -> puts "need 24 bytes"` @0x4054).

`0x23f0` / `0x2403`: `imul rax,r15` / `imul rax,r10` - the two multiplies of a **SplitMix64
finalizer** applied to `rbp + K`:
```
h = rbp + K;  h ^= h>>30;  h *= 0xbf58476d1ce4e5b9;  h ^= h>>27;  h *= 0x94d049bb133111eb;
h ^= h>>31;
```
with `K` = `0x700cb87a8661a343` (0x23ae), `0x0e44323405ac1f58` (0x23c2), `0xac7babed84f69b6d`
(0x2427), `0x4ab325a704411782` (0x245b), `0xe8ea9f60838b9397` (0x248f), `0x8722191a02d60fac`
(0x24c3) and `rbp` advancing by `0x2e2ac13ef8e8d8d2` per record (0x235f/0x2372). Results land in
`[rsp+0x50/0x48/0x40/0x30/0x60/0x58]` and feed code bytes and `entry.x`. `0x23f0` is "called"
only by `jmp 0x23f0`-free fallthrough - i.e. it is not a function and has no call sites (grep of
all `call` targets: 0x1030-0x1100 plt, 0x16c0, 0x17c0, 0x1810, 0x1af0, 0x1d50, 0x1eb0, 0x1fa0 only).

## 8. `0x1fa0` - what is actually random at startup (and what is per-connection)

One function `0x1fa0..0x35d7` (`sub rsp,0x10488`, canary at `rsp+0x10478`). Called once from
`main` at `0x116d`; `if (eax) -> puts "boot error" (@0x4022); return 1`.

Three `/dev/urandom` reads (`open @0x1fd2` on `0x4015 "/dev/urandom"`, exact-length checked):
```
read(fd, 0x76ef0, 16)  -> SECRET stamp key (2 qwords). != 16 bytes => -1 => "boot error"
read(fd, rsp+0x3c0, 8) -> nonce; stored to 0x76ee0; printed by NONCE; in the GET header (PUBLIC)
read(fd, rsp+0x3c8, 8) -> splitmix seed for the 40-u16 id pool (PRIVATE, never stored globally)
```
Then:
1. `0x2050-0x2072`: `memset(rsp+0x470, 0, 0x10000)` = a 64 KiB "already used" bitmap;
   `r14 = nonce ^ 0xa5a5a5a5a5a5a5a5` (0x2067, used later).
2. `0x20c0-0x2111` **u16 pool**: state (rbp, seeded from the 2nd read) `+= 0x2545f4914f6cdd1d`,
   murmur3-finalize (`^= >>33; *= 0xff51afd7ed558ccd; ^= >>33; *= 0xc4ceb9fe1a85ec53; ^= >>33`),
   take the low 16 bits, reject 0 and duplicates (bitmap at `rsp+0x470+val`), store to
   `0x460c0 .. 0x4610f` - **40 distinct non-zero u16**. `0x462c0 = final state` (dead).
3. `0x2113-0x215e`: `0x462d2 = u16@0x4610c` (FLAG record id), `0x462d0 = u16@0x4610e` (decoy id),
   `0x462d4 = u16@0x460c0` (start id, also staged at `[rsp+0x86]`).
4. `0x2165-0x227c` **preamble record** (index 0, id = `0x460c0`): `memset(rec,0,0x30c)`,
   `slot = bitidx = 0xff` (`mov WORD[rec+2],0xffff` @0x21a7), 6 x `MOVI r(i),0` (`call 0x17c0`
   @0x21bb), then for i = 0..5, j = 0..3: `LBI r6,in[4i+j] ; ROL r6,8j ; OR r(i),r6`
   (`code[+0]=0xc,code[+1]=6,code[+2]=4i+j, code[+3]=7,code[+4]=6,code[+5]=8j,
     code[+6]=6,code[+7]=i,code[+8]=6`) - this is exactly what the captured record 0 decodes to.
   `code_len += 0x24` per i (`0x2240`) => 0xd8, later extended by `0x17c0`.
   Its single table entry: `bit = 0xff` (0x2263), `n = 1` (0x2271), `tgt = u16@0x460c2` (0x228c).
   **This is only the state at build time** - later passes extend every record's table (§12).
5. `0x2293-0x237c` chain loop over the id pool: `r8` walks `0x460c2 -> 0x4610a` in steps of 6
   (3 u16 per iteration, 12 iterations x 3 records); `rbp = 0x2e2ac13ef8e8d8d2 + r14`
   (0x22a2) seeds the SplitMix64 stream of step 7's constants; 3 records per iteration get ids
   from consecutive pool words, `slot`/`bitidx` = `(mix & 3)` and `(mix & 0x1f)`
   (`0x2549-0x2576`), and `n`/entries written at `+0x208/+0x20c/+0x21c/...` (0x22fa-0x237c).
   `0x1fa0` writes **every byte of the array**: `memset(rec,0x30c)` @0x251f/0x27b3 then field
   stores - so the randomised region is `0x462e0 .. 0x462e0 + 0x30c*count` (count = 40 gives
   `0x462e0 + 0x79e0 = 0x4dcc0`; the 199-record figure would end at `0x6c134`), i.e.
   id/slot/bitidx/alt_id/code_len/code/
   n/entry.bit/entry.tgt/entry.x, **plus** entry.stamp which is written by the stamping pass.
6. `0x23a0-0x2f61` code bodies: e.g. `ADD r5,r4 ; ROL r5, 1+(h % 30)` (0x2841-0x28bb, the `%30`
   via `mul 0x8888888888888889; shr rdx,4; imul rax,rdx,30; sub`), then `call 0x17c0` appends
   `XORI r4, h32` (0x26b8/0x26d4/0x2801/0x28fd); `MOV r7,r(i); XORI r7, witness[i]` per register
   (0x2e3d-0x2eba, witness read from `0x460a0+i*4`); `MOV r7,r6; SHR r7,s; OR r6,r7` x4 with
   s in {16,8,4,2} (0x2ec9 `mov DWORD[rsp+0x3bb],0x2040810`, 0x2ef1-0x2f5f).
   0x17c0 signature: `(record, op=esi, reg=edx, imm32=ecx)` -> writes
   `[op,reg,imm0..imm3]` at `code[code_len]`, `code_len += 6` (raw-verified 0x17c0-0x180a).
7. `0x2b69-0x2bf3` **witness input**: splitmix (`state += 0x2545f4914f6cdd1d`, murmur3 finalizer)
   seeded with `rbx + 0x4a8be9229ed9ba3a`, 24 bytes -> `[rsp+0x3d0]`. This is the 24-byte input
   that satisfies the chain.
8. `0x2a32-0x2b58` + `0x2fac-0x3093` stamping passes: for every record and every entry, compute
   `entry.x` from the `0x462c8` splitmix state (`+= 0x9e3779b97f4a7c15`, finalizer
   `>>30/*0xbf58..>>27/*0x94d0..>>31`), store it at `entry+4`, build the 9-byte buffer
   `[id,tgt,bit,x]` and `stamp(0x45, buf, 9, &entry.stamp_lo)` - i.e. **the expected stamps are
   computed by the same `0x1af0` that verifies them**.
9. `0x2c03-0x2cf5` **self-walk at startup**: finds the record whose id == `[rsp+0x86]` (= start
   id), runs the VM with regs at `[rsp+0x1b0]` and the witness 24 bytes at `[rsp+0x3d0]`, calls
   `0x1d50`, and repeats up to `0x30d40` times; when the returned id equals `u16@0x4610a` it
   snapshots 24 bytes of the register file to `0x460a0..0x460bf` (0x2ce7/0x2cee). So `0x460a0`
   holds the witness's *register* state, which the tail records then reference.
10. Tail records `0x2d0b-0x2e00`: FLAG record = `{id=u16@0x4610c, slot/bitidx=0xff,
    alt=u16@0x4610e, code = 0d 0e 0f (FLAG;SETDONE;HALT), n=0}`; decoy = `{id=u16@0x4610e,
    slot/bitidx=0xff, code = 0f (HALT), n=0}`; plus the witness-compare / bit-spread records.
    `count` is then committed to `0x462d8` (0x2834, 0x2dac). Captured value: 40.

Per-connection vs reproducible: ids and the 40-u16 pool come from the **private** 8-byte seed;
`slot`, `bitidx`, code bytes, shift amounts and `entry.x` come from streams seeded with the
**public** nonce (`rbp = 0x2e2ac13ef8e8d8d2 + (nonce ^ 0xa5a5a5a5a5a5a5a5)`, and `0x462c8`);
stamps come from the **private** 16-byte key. Nothing is randomised lazily per `RUN` - the whole
image is built once at `0x116d`, so a `GET` is the exact image that `RUN` uses.

## 9. Success path

`0x1635`/`0x1651`: `snprintf([rsp+0x100], 0x100, "%s" /*0x4062*/, [rsp+0x80])` then `puts` at
`0x1608`. Reached **only** when `[rsp+0x1c] != 0` (0x15bb), i.e. the VM executed opcode `0xe`
(SETDONE, `0x1870`) during the current step. The record that does that is the FLAG record
(`code = 0d 0e 0f`), whose id is `u16@0x4610c` (also parked at the dead global `0x462d2`).
Because the `state != 0` test precedes both the `rc != 0` test (0x15c7) and the `n == 0` test
(0x15cb), the FLAG record's `n = 0` and its `HALT` return value do **not** block the print.
So the condition for the walk to emit the flag is exactly:
* starting at `id = 0x462d4`, repeatedly: run the record's program on the **shared** register
  file, then take the first table entry with `entry.bit == bit(regs[slot],bitidx)` whose stored
  stamp equals `stamp(0x45, id||tgt||bit||x, 9)`; and
* land on a record whose program executes `0xe` (in practice the one with `code = 0d 0e 0f`)
  within `0x30d40` steps, with every intermediate record having `n != 0` and a matching entry.
Anything else prints `denied` (`0x15ea`). The flag itself comes from the environment variable
`FLAG` (`getenv` at `0x18ae`), truncated to 127 chars; unset => the literal `"unavailable"`
(`0x4004`) - so an empty reply of `unavailable` would mean the env var is missing, not that the
walk failed.

## 10. Verification ledger

Byte/constant-verified (I dumped the raw bytes or matched independent data):
* every jump-table word (`0x406c..0x40af`) and all 16 handler addresses; handler bodies decoded
  from raw bytes for all 16 opcodes (`objdump --start-address=0x1910 --stop-address=0x1af0`);
* record layout + GET header against the captured 200-byte image (id/slot/bitidx/alt/code_len of
  record 0, nonce == NONCE reply, code bytes disassemble cleanly with the derived table);
* the generator's emitted preamble bytes (`0x21d3-0x2236`) == the captured record-0 program;
* the 9-byte stamp buffer layout, twice-derived (SSE raw bytes in `0x1d50` vs the plain stores in
  the stamping pass at `0x2adb/0x2aed/0x2b27/0x2b33` and `0x304a/0x301b/0x306a/0x3076`);
* `stamp()` rotl constants 13/16/17/21/32/32/32, `mov edx,0x9`, `mov edi,0x45/0x4d`, output
  `cmp rdx,6`, the four magic qwords (= "somepseudorandomlygeneratedbytes"), secret reads from
  `0x76ef0/0x76ef8`;
* 6-byte stamp output length against 4386 observed MINT replies (4385 x 6 bytes);
* splitmix/murmur constants: 0x2545f4914f6cdd1d, 0xff51afd7ed558ccd, 0xc4ceb9fe1a85ec53,
  0xbf58476d1ce4e5b9, 0x94d049bb133111eb, 0x9e3779b97f4a7c15, 0x2e2ac13ef8e8d8d2,
  0x4a8be9229ed9ba3a, 0xa5a5a5a5a5a5a5a5, 0x8888888888888889 (%30), the six K constants;
* `denied` assembled from immediates `0x696e6564` + `0x646569` (0x15ea/0x15fd) -> "denied";
* §12: the whole record/entry layout + the advance table validated against **three** complete
  served images already present in the directory (`image.txt`, `imgA.bin`, `imgG.bin`, captured by
  the teammate - I fetched nothing): exact byte consumption, `count=40`, zero misaligned pc, zero
  illegal opcodes, `entry.bit` confined to {0x00,0x01,0xff}, all 126 `tgt`/`alt_id` resolving.
* command keywords and format strings from `.rodata` (`FLAG`,`/dev/urandom`,`unavailable`,
  `GET`,`%02x`,`NONCE`,`%016llx\n`,`MINT `,`bad`,`RUN `,`need 24 bytes`,`%s`,`QUIT`,`?`).

Read off the disassembly only (not independently re-derived):
* the exact record-count arithmetic (I confirmed count==40 empirically from the capture and the
  12 x 3 chain loop bound at `0x4610a`, but did not fully unwind the unrolled `+3/+6` updates);
* the precise semantics of the tail/gadget records (`0x2e36-0x2f61`) - I read their emitted byte
  patterns, not their intended algebraic role;
* which of the 3 candidate `slot`-selection folds is used where (the `&3` / `&0x1f` masks at
  `0x2549-0x2576` are verified, their input qword provenance is inferred from the stack slots);
* `0x1af0`'s behaviour for `len >= 24` (unreachable through the protocol; my reading says it
  re-absorbs `buf[8..15]` forever because `0x1ba9` sets rather than increments `r10`).

## 11. Still unknown / open

1. **Which entries are actually signed** - see §12: in the served image the FLAG record is never
   the first bit-matching entry of any record, so stamp validity (not the bit) must be what
   selects the edge. I cannot decide statically which entries carry a genuine stamp: that needs
   either the 16 secret bytes or one `MINT` probe per candidate edge.
2. `0x460a0` (24-byte witness) is write-only in bss and not in the GET range - the witness itself
   is not retrievable; only its baked-in `XORI` immediates leak through the tail records.
3. `0x462d0`/`0x462d2` (FLAG/decoy ids) are write-only globals; they leak only via the image
   (`0x4610c`/`0x4610e` are also outside the GET range).
4. Whether the ids' high byte matters is moot (it is included in the stamp input), but note
   `cmp si, WORD [rdx]` matches the **first** record with that id, and the pool guarantees distinct
   u16 -> ids are unique by construction.
5. The remote-side meaning of "the walk completes" is answered statically (§9); the concrete
   24-byte answer for the live instance still has to be derived from a full GET (bit constraints
   are `bit(regs[slot],bitidx) == entry.bit` with `regs` affine in the six input words).

## 12. Structural findings from three real images (added after the first draft)

`image.txt`, `imgA.bin`, `imgG.bin` (three different sessions) were parsed with the §2 layout by a
throwaway script. Results - all three:

* **the parse consumes the stream exactly** (3037 / 3076 / 3115 bytes, zero leftover),
* `count = 40` in every instance (so the "199 records" figure is wrong; 40 is fixed),
* every program counter lands exactly on `code_len` with **no illegal opcode** (verifies the
  1/3/6 advance table over ~2400 instructions per image),
* `n` distribution `{0:2, 2:13, 3:12, 4:2, 5:10, 6:1}`, `entry.bit` values are only `0x00`,
  `0x01`, `0xff`, all `entry.tgt` and all `alt_id` resolve to real record ids, 126 entries and
  126 distinct stamps, no duplicate `tgt` inside a record,
* opcode census identical across instances: MOVI 6, MOV 12, ADD 48, XOR 24, OR 34, ROL 72, SHR 5,
  ADDI 12, XORI 42, LBI 24, FLAG 1, SETDONE 1, HALT 2,
* exactly two records have `n == 0`: index 37 = `0d 0e 0f` (FLAG;SETDONE;HALT, `slot=0xff`) and
  index 38 = `0f` (HALT decoy, `slot=0xff`). Every record's `alt_id` = the decoy's id (`0x0d66`
  in `image.txt`) => **any failed link drops straight into the HALT record => `denied`**,
* 25 records have `slot == 0xff` with all-`0xff` entry bits (unconditional: `entry[0]` is taken
  whenever its stamp verifies), 14 have `slot in {0,1,2,3}`, `bitidx in 0..31` (bit branch), and
  record 39 has `slot = 6`, `bitidx = 0` - `slot=6`/`bitidx=0` is written explicitly by
  `mov eax,6; mov WORD[rec+2],ax` at `0x2e1b/0x2e2d`, not by the `&3` fold.

Record 39 (`0x2e36`-`0x2f61` builder) is the **witness gate**; its program is

```
for i in 0..5:  MOV r7,r(i) ; XORI r7, witness[i] ; OR r6,r7        ; r6 |= regs[i] ^ witness[i]
then:           MOV r7,r6 ; SHR r7,16 ; OR r6,r7 ; SHR 8 ; OR ; SHR 4 ; OR ; SHR 2 ; OR ; SHR 1 ; OR
```
so `bit0(regs[6]) == (the six input words are NOT all equal to the witness words)`; its entries
are `00>rec26, 01>rec38(deny), 00>..., 01>..., 01>..., 00>rec37(FLAG)` - i.e. the *equality*
branch is entry 0, and the FLAG edge (entry 5) is shadowed by it under "first bit match wins".

That shadowing is the crux: in `image.txt` the FLAG record has in-edges only from `rec6.entry[2]`
(`bit=0xff`, shadowed by `rec6.entry[0]` which has the same bit) and `rec39.entry[5]` (`bit=0x00`,
shadowed by `rec39.entry[0]`). So if *every* entry carried a genuine stamp, **the FLAG record
would be unreachable and the challenge unsolvable**. Therefore the stamps are not mere validation
but the real selector: per record, the walk takes the first entry that satisfies *both*
`entry.bit == bpl` and `stamp(0x45, id||tgt||entry.bit||entry.x, 9) == entry.stamp`, and the
generator signs only the edges of the true path (the decoy entries keep the shape but their stored
stamp does not reproduce). Combined with §6 this yields a cheap, legal probe:

```
for each record R, each entry e:
    MINT <hex16( R.id_le2 || e.tgt_le2 || byte(e.bit) || e.x_le4 )>   -> 6 bytes
    accept the edge iff the reply == e.stamp
```
i.e. `MINT` is a *signed-edge oracle* for the whole graph; `entry.x` (already in the image) is the
nonce that makes each stamp unique, and the flag path is then whatever chain of accepted edges
leads to the `0d 0e 0f` record. Nothing about this needs the secret key.

Caveat, stated plainly: the "decoy stamps do not verify" step is a **reductio from the served
data plus the §5 rule**, not something I could execute or mint here (no network, no emulation).
The alternative explanation would be a misread of `0x2a32`/`0x2fac` (which do appear to stamp
entries `0..n-1` for each record they cover); one `MINT` per candidate edge settles it in seconds.
