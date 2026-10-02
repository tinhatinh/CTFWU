# Countersign - decision log (kiem chung truc tiep, khong tin agent)

De: `nc pwn.h7tex.com 43708`.  **DA CO CỜ:** `H7CTF{011c87d4-b5c8-405d-923a-33dbed3e5bf7}`
(xem `flag.txt`, bang chung trong `analysis/livewin.txt`).

## Ket luan cu DA SAI - giu lai de khong lap lai

| Y cu (cũ) | That |
|---|---|
| `emit` in co khi `next == 0`; khong link nao co `nx==0` nen khong the in co | `emit` KHONG in gi ca. No chi tra ve tag ke tiep. In co la do **op 14** trong chuong trinh cua record (`RUN` kiem `[rsp+0x1c]` TRƯỚC khi kiem gia tri tra ve). |
| Bang opcode: ops 3/4/5 co `rD = code[i+2]` | **`rD = code[i+1]` cho MOI op 2..8.** Da doi chieu tung body. |
| `ROL/SHR` lay chi so thanh ghi | Byte lenh thu 3 cua `ROL`(7) va `SHR`(8) la **HANG SO**, khong phai chi so reg. |
| Op 14/15 = "SETPRINT" | Op 13 = `strncpy(buf128, getenv("FLAG"), 0x7f)`. Op 14 = `printflag=1` (RUN in ra buf roi dung). Op 15 = **return 1 → denied**. |
| Register file = 32 u32, reset moi buoc | **8 u32 tai `rsp+0x20`, KHONG reset giua cac buoc** (lenh `rep stosd` nam NGOAI vong lap 0x1553). `rsp+0x80` la buf 128 byte cua op13, `rsp+0x40` la 24 byte input. |
| "Co the tu supply edge qua RUN" / "alt_id o `rec+0x20a` la an so" | `rec+4` (tren wire) chính là `rec+0x20a`... sai nhan: `emit` doc `WORD[rec+4]` = **dflt**, nam tren wire. Khong co an so nao ca. |
| `GET` tra 3076 byte co dinh | Do dai image **doi theo instance** (da thay 2998/3063/3076/3089). Cong thuc `18 + Σ(9 + L + 13k)` van dung. |
| Can Unicorn de lay ground truth | Khong can. Doc ky `cs.asm` la du; Unicorn lam nan chi vi PLT/stack-canary ma khong cho them thong tin. |

## Model THAT (da doi chieu tung lenh voi `cs.asm`)

### `RUN` = vong lap `0x1496..0x1610`
```
hexparse(sau "RUN ") -> phai dung 24 byte (khong -> "need 24 bytes")
regs[8 u32] = 0 ; buf128 = 0 ; printflag = 0          # chi reset MOT LAN
tag = *(u16*)0x462d4                                  # entry, gan luc boot
lap toi da 0x30d40 = 200000 buoc:
    rec = record dau tien co tag (khong thay -> "denied")
    ret = exec_program(rec, regs, buf128, input24, &printflag)
    if printflag:  puts(buf128); DUNG                  # 0x15bb  <-- THANG
    if ret == 1 :  "denied"                            # 0x15c7
    if rec.n_link == 0: "denied"                       # 0x15cb
    tag = emit(rec, regs)                              # 0x1d50
"denied"
```

### `exec_program` `0x1810` - VM straight-line, khong co lenh nhan
Bang nhay tai `0x406c`, `handler = 0x406c + int32(0x406c + 4*op)`.  `op > 15`: `pc += 1`.
Vong lap dung khi `pc >= pay_len` (khong can `pc == pay_len`, nen code thieu 1-2 byte
dang 6-byte van chay binh thuong).

```
0  NOP(1)          1  MOVI rD,imm32(6)   2  MOV  rD,rS(3)
3  ADD rD,rS(3)    4  XOR  rD,rS(3)      5  AND  rD,rS(3)     6  OR rD,rS(3)
7  ROL rD,K(3)     8  SHR  rD,K(3) (>31 -> 0)
9  ADDI rD,imm(6)  10 XORI rD,imm(6)     11 ANDI rD,imm(6)
12 LBI rD,in[k]  (k <= 0x17, nguoc lai 0)
13 strncpy(buf, getenv("FLAG") ?: "unavailable", 0x7f)
14 printflag = 1        15 return 1
```
`rD = code[pc+1]`, `rS/K/k = code[pc+2]` cho TAT CA op 2..8 va 12.

### `emit` `0x1d50` - day la "countersign"
```
bpl = (rec.sel_reg == 0xff) ? 0xff : (regs[rec.sel_reg] >> (rec.sel_bit & 31)) & 1
for i in 0..n_link-1:                    # link tai rec+0x20c+16i
    if link[i].sel != bpl: continue
    if stamp6(tag||target||bpl||tweak) != (sig_lo, sig_hi): continue   # 0x1af0, edi=0x45
    return link[i].target                # chi duoc buoc tren duong CHUNG minh duoc
return rec.dflt                          # tuc tac = tag cua "deny sink"
```
`bt r32, r32` lay bit theo **modulo 32**, nen `sel_bit = 29/23/...` van hop le.

### Layout
```
image = 18 hdr ("CSGN", u16 ver, u16 nrec, u16 entry, 8 byte) + Σ record
record (wire)  = tag u16 | sel_reg u8 | sel_bit u8 | dflt u16 | L u16 | code[L] | k u8 | k*13
record (mem)   = stride 0x30c; code @ +8 (512 byte); n_link u8 @ +0x208;
                 link[j] @ +0x20c+16j: sel u8@0, target u16@2, tweak u32@4, sig u32@8, sighi u16@12
wire link 13B  = sel | target u16 | tweak u32 | sig u32 | sighi u16
```

### Bon vai tro record (boot `img_live.bin`, entry 30137)
* `252 byte` (entry): `MOVI r*,0` + 4 lan `LBI r6,in[k]; ROL r6,K; OR r*,r6`
  → **r0..r5 = 6 word LE cua 24 byte input** (song anh 1-1 voi input).
* `12 byte`: `XORI r4,K; ADD r5,r4; ROL r5,s` → chi dong **r4, r5**. Nghich dao duoc.
* `30 byte`: `ADD r0,r1; ROL r0,s1; XOR r2,r0; ADD r3,r2; ROL r3,s2; XOR r1,r3;
  ADDI r0,A; XORI r2,B` → chi dong **r0..r3**. Nghich dao duoc.
* `117 byte` ("fold"): `r6 = OR_{i=0..5}(r_i ^ C_i)` roi `r6 |= r6>>16|>>8|>>4|>>2|>>1`
  → **bit0(r6)==0 <=> r0..r5 == C0..C5** (6 hang so XORI). Link `sel=0` cua no tro
  thang den record `0d 0e 0f` = GETFLAG|PRINT|HALT.
* `3 byte` `0d 0e 0f` = in co. `1 byte` `0f` = deny sink (moi record khac co `dflt` chi ve day).

## CACH GIAI

Toan bo walk **tinh tien** theo input, nen khong the brute force 2^192. Nhung:
1. Input <-> (r0..r5) la **song anh**, va
2. Moi record trung gian la **ham nghich dao duoc** tren registers.

→ **DI NGUOC**: dat (r0..r5) = (C0..C5) o cua record fold, toi lui tung canh
nguoc cua do thi, moi buoc `pre = invert(rec.ops, post)`.  O moi buoc KIEM
`step(rec, post)` thuan cung cho ra dung canh ay (neu khong thi loai) - day la
dieu kien "first matching valid link", rat manh vi no quyet dinh nhanh.
Den entry `30137` thi `input = pack(r0..r5)`; chay `walk()` thuan de xac nhan.

So canh hop le lay bang cach **goi `MINT` tren cung ket noi**:
`MINT(tag||target||sel||tweak)[:6] == link.sig` ↔ chu ky dat.  Trong boot cua toi
co **51/129** link hop le - 78 link kia la chu ky gia, va chinh viec chung BI BOC BO
tao ra duong dan (vi du: record fold nam sau `23316`/`41275` chi vi link `sel=255`
dau tien cua chung chu ky xau).

## ORACLE / CHI PHI
* Moi thu sinh lai theo **tung ket noi** (nonce doi 150/150). Nen: GET → 129 MINT
  → solve → RUN **tren cung 1 socket**.
* ~102 ms/lenh; 129 MINT ~13.5 s; solve < 0.1 s; tong < 20 s / lan nop.
* Khong co budget lenh.  `RUN` tra ve "denied" cho moi input sai (khong co du lieu
  trung gian), nen khong the leo duong (hill-climb) - bat buoc phai giai bang mo hinh.
* 3/3 lan `RUN` lien tiep cung input deu ra co → khong may mo.

## File
`core.py` (mo hinh VM + emit + run), `back.py` (tim duong nguoc), `records.py`
(parse image), `session.py` (client 1 ket noi), `solve_live.py` (driver),
`diag.py` (luu image + bang chu ky), `imgE/img_live.bin`, `valid_live.json`,
`cs.asm` (objdump -d), `unpacked/`.  `emuhw.py` = Unicorn harness, BO (khong can).
