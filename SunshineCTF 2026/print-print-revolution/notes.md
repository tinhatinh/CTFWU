# notes.md - print-print-revolution

Input: `files/revolution` (14520 B, sha256 `918483831ef0b27d0cfb8afa9e0341f38d0a296931ccc5f73ef80f5d610f8fa5`)
Service: `nc chal.sunshinectf.games 26002`
Định dạng cờ: `sun{...}` (host là sunshinectf.games - KHÔNG phải `H7CTF{}`)

## S0 - Triage
`ET_EXEC` (no PIE), Full-ish RELRO, NX bật, stripped, `.text` chỉ 0x4ea byte.
Import duy nhất: `write strlen strcspn read setvbuf __libc_start_main` -> **không có
fopen/open**, nên cờ không thể do chính binary đọc ra.
`.rela.plt` = 0x78 -> 5 slot PLT.

## S1 - Dich nguoc renderer (0x401330) - KET QUA CHINH
Format string TU CHE, khong phai printf cua libc. Grammar:

| Directive | Y nghia |
| --- | --- |
| `%%` | in ra `%` (rbp = 0x402004) |
| `%<n>$s` | `write(1, (char*)arg[n], strlen(arg[n]))` -> **DOC tuy y** |
| `%<n>$p` / `%<n>$x` | in `0x%016lx` cua arg[n] -> **LEAK tuy y** |
| `%<n>$w` | `*(char*)arg[n] = arg[n+1]`, in `ok` (0x402006) -> **GHI tuy y** |
| `%s %p %w` | nhu tren dung bo dem tang dan ebx |

Bo dem arg: arg 1..5 = `rsi,rdx,rcx,r8,r9` tai lenh goi renderer; arg 6+k =
8 byte tai `buf[8k]`, va `buf` chinh la input cua ta (`read(0, buf, 0x1ff)`).
`buf` = rsp cua main sau `sub rsp,0x200`; leak no qua `%70$p` (o luu rbx tai
`buf+0x200`).

**Ham va_arg (0x4012c0) la STATELESS**: no `movdqu` `ap` len xmm va chi tang
offset trong ban sao, khong ghi nguoc. Nen `%<n>$w` lay cap (arg n, arg n+1)
chu khong phai (arg n, arg 2n+1) - day la loi ban dau khien phep ghi that bai
(ghi dung `......` vao o dam).

## S2 - Phep ghi: da chung minh
`%8$w` ghi duoc 8 byte tuy y. Chung minh: ghi gadget vao 0x404068 (.bss trung
gian) roi doc ra bang `%8$s` -> khớp. Ghi thang vao `strlen@GOT` cung khop.

## S3 - RELRO khong che GOT
`PT_GNU_STACK` thieu, `PT_GNU_RELRO` = [0x403dc0, 0x404000). Cac slot ham nam o
`.got.plt` 0x404000..0x404027 -> **NGOAI vung RELRO nen van ghi duoc**:
`write=0x404000 strlen=0x404008 strcspn=0x404010 read=0x404018 setvbuf=0x404020`.
Gia tri tai 0x404000. la 0x401030. (stub lazy) -> lazy binding, chua fix.

## S4 - Gadget `syscall` khong can file libc
Doc `write@GOT` -> d/c that cua write trong libc. Doc 0x40 byte dau cua write
(tim bang cach doc moi 1 byte, 20 dia chi/goi) -> thay `0f 05` o
**write+0x12**. Moi connection ASLR doi nen phai leak lai, chi ~4 goi.

## S5 - Hai call site dung duoc cho `syscall`
| Site | rdi | rsi | rdx | rax | rsp |
| --- | --- | --- | --- | --- | --- |
| `call strcspn@plt` (0x40112a) | buf | rbp=0x402022 | 0x1ff | **so byte vua read** | buf-8 |
| `call strlen@plt` (0x4015a0) | = arg n | r15 | - | **= arg n** | buf-0x128 |

Renderer = 6 lenh push + `sub 0xe8` + return address -> renderer_rsp = buf-0x120.

## S6 - Da loai: co cache trong env/argv/auxv
`%111$s..%116$s` doc ra toan bo env: `HOSTNAME HOME=/root TERM PATH
DEBIAN_FRONTEND PWD=/ctf`; argv chi co `/home/revolution/revolution`.
auxv: `AT_UID=AT_EUID=AT_GID=AT_EGID=1337`, `AT_SYSINFO_EHDR`, `AT_BASE`,
`AT_EXECFN`. **Khong co co o day.**

## S7 - Da loai: SROP
`%<n>$s` voi arg = 15 tai site `strlen` (va `read()` tra 15 byte tai site
`strcspn`) goi `rt_sigreturn` voi frame ngay duoi rsp. Da thu:
- frame tai buf-8 (site strcspn): **lien tuc tra ve loi, tien trinh SONGLI** in
  tiep `score> `. Thu 2 layout gregs (frame+0x30 va frame+0xb0), thu sua
  fpstate (zero / xfeatures=3 / compacted / magic1), thu tro fpstate hop le ->
  khong thay doi.
- frame tai buf-0x128 (site strlen): **tien trinh CHET**. Da chung minh hijack
  strlen@GOT that (arg=1 -> syscall write, arg=39 -> getpid, ca hai SONGLI; neu
  khong hijack thi `strlen(1)` da segfault).
- Quet 8 gia thuyet offset gregs khac nhau: chet tat.
- Stack duoc map den tan buf+0xf70 nen `access_ok` khong phai ly do.

**Ket luan hop ly nhat: seccomp chan `rt_sigreturn` (SECCOMP_RET_ERRNO -> song
o site strcspn; KILL -> chet o site strlen).** Day la tin hieu hai site hanh
xu khac nhau voi CUNG mot frame.

## S8 - Con lai (huong di tiep theo)
ROP thuan toi `execve`, khong dung SROP. Da co du: `pop rdi; ret` @0x4014a1,
`pop r15; ret` @0x4014a0, `pop rbp; ret` @0x40129d, 13 x `ret`, gadget
`syscall`, va `mov rdx,rax` @0x4015ad / `mov rsi,rbp` @0x401120 /
`lea rdx,[rsp+2]` @0x40154a de dieu khien rdx/rsi gian tiep.
Vat can giai quyet: rax cho syscall dau tien = so byte cua template, nen
chuoi phai duoc dat truoc vao buf bang `%w` roi chi goi mot template ngan.
Theo ghi nho runtime: co shell la `cat /ctf/flag.txt` duoc ngay (file
`root:<user>` 640).

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.

## S9 - SUA LAI S7/S5 (bang phep do tuyet doi)
Phep do: hook `strcspn@GOT` -> gadget `syscall`, gui DUNG 1 byte. Ket qua:
`0x404010` doc ra dung gadget, `%w` tra `ok`, va sau khi gui 1 byte thi van
nhận `A\nscore> `. **Nghia la hook CHAY THAT** (syscall 1 = write voi
rdi = dia chi buf -> EBADF), va **tien trinh SONGLI sau mot syscall bi tu choi**.
-> KET LUAN: `write` duoc seccomp cho phep; `syscall` gadget quay ve dung;
   moi suy luan truoc do rang "hook khong chay" la SAI.

## S10 - Chuoi ROP da chay, execve thi khong
`vdso+0xa14` = `xor edx,edx; xor ecx,ecx; xor esi,esi; xor edi,edi;
xor r8d..r11d; ret` (**khong dong rax**). Chuoi
`pop rdi;ret` (0x4014a1) -> `vdso+0xa14` -> `pop rdi;ret` -> path -> `syscall`
da duoc chung minh chay den noi: bien lanh (ket thuc bang `ret` ve 0x40114f)
tra lai `score> ` binh thuong.
   nhung khi ket thuc bang `execve` (rax=59, rdi="/bin/sh" hoac
"/home/revolution/revolution", rsi=rdx=0) thi **ca ba bien the deu chet ket noi
gian tiep sau do**, ke ca duong dan co that. Khac hanh vi cua `write` bi EBADF
(tien trinh song). -> **`execve` bi seccomp giết (SECCOMP_RET_KILL)**, khong phai
loi chain. Cung khop voi viec `rt_sigreturn` bi tu choi o ca hai call site.

## S11 - Dieu can biet con lai
Trong vDSO con co `0f 05` tai **vdso+0xa47** (ngay sau `mov eax,0xe4`), va
khong tim thay `0f 05 c3` o dau ca. Chuoi da len duoc nhieu syscall lien tiep
vi libc `write` ket thuc bang `ret` nen rsp van nam trong chuoi.
Cac syscall da do duoc: `write`(1) -> cho phep. Chua do: `open`(2), `read`(0),
`close`(3), `lseek`(8). Neu `open` duoc cho phep thi co the doc flag bang
chuoi `open -> (rax=fd) -> ...` ma khong can execve; do la buoc tiep theo.

## S12 - KET LUAN CHINH (sau khi sua phep do seccomp bi sai)
Phep do truoc do (S10) **sai o cho**: chuoi < 40 byte thi o noi tiep sau syscall
(buf[0x20]) khong du cho ghi -> `ret` cua libc pop phai 0 -> crash. Voi chuoi
day du 5 slot, ket qua dao nguoc hoan toan:

| Syscall goi ra | Ket qua |
| --- | --- |
| 39 getpid | song (in `score> `) |
| 102 getuid | song |
| 257 openat | song |
| **59 execve (rdi="/bin/sh", rsi=0, rdx=0)** | **song, TUC LA execve TRA VE LOI** |
| 15 rt_sigreturn | chet/ bi tu choi |

-> **`execve` bi chan kieu SECCOMP_RET_ERRNO (khong giết, khong cho chạy)**,
nên không có shell. File syscall (`open`/`openat`) KHONG bi chan (goi ra loi
tham so van song). Van de cian lai chi la: **lam sao dat rax = 2 (open) va
rsi = dia chi path**, vi:
  - rax cua syscall DAU TIEN = so byte cua template (>= 40 cho chuoi day du),
    nen khong the goi thang open(2)/read(0).
  - gadget `pop rsi; ret` / `pop rdx; ret` / `pop rax; ret` khong ton tai trong
    binary cung khong thay o vDSO; scan libc ±0x30000 (stride 4) van chua thay.
  - `mov rsi,r15` @0x4015a5 buoc rdi=1 va rdx=rax; `mov rsi,rbx` @0x401168 buoc
    rdi=0 va rdx=0x1ff; `mov rdx,rax` o ca hai -> xung dot voi truong flags.

## S13 - Huong duy con lai (chua lam)
Trong container, pid cua dich thuong rat nho. Chuoi 2 syscall vut trong 39 byte:
  buf[0x00]=vdso+0xa14 (zero) ; buf[0x08]=syscall (rax=39 -> getpid, rax=pid)
  buf[0x10]=pop rdi;ret ; buf[0x18]=&"/ctf/flag.txt" ; buf[0x20]=syscall
Syscall THU HAI co ma = pid. Neu pid == 2 thi do chinh la
`open("/ctf/flag.txt", O_RDONLY, 0)` vi rsi/rdx van bang 0 tu gadget zero.
Do la buoc tiep theo, chua chay.

## S14 - NGUYEN NHAN THAT: `multi_write` de hai phep ghi deo len nhau
`%<n>$w` lay cap (arg n, arg n+1) = HAI O LIEN KIEP trong buf. Khi `multi_write`
phat sinh n = first + i (tang 1), thi o value cua write i TRUNG o target cua
write i+1. Ket qua: write 0 ghi CON TRO DUONG DAN vao strcspn@GOT (thay vi
`pop rdi; ret`) -> tien trinh nhay vao stack (NX) -> chet.

**Day chinh la ly do doan S10 va S12 ket luan sai** rang rt_sigreturn bi
seccomp giết va execve tra loi: chuoi ROP da hong truoc khi toi duoc syscall,
nen moi bien the deu cho cung mot hien tuong. Sau khi sua (n = first + 2i,
moi phep ghi chiem dung 16 byte), control "khong syscall" song, va:

| execve duong dan | ket qua |
| --- | --- |
| /bin/sh | **SONG SUIT** - shell im lang cho lenh |
| /home/revolution/revolution | `score> ` (that bai, roi chay lai vong lap) |
| /nonexistent | `score> ` |

-> **execve duoc phep, khong co seccomp chan.** `/bin/sh` ton tai. Toan bo
gia thuyet seccomp o S12 la sat gia do phep do hong.

## S15 - KET THUC
cmd: `python exploit.py`
evidence: buf/vdso/write/syscall leak OK; 2 phep ghi `ok`; sau chuoi 59 byte
thì `cat /ctf/flag.txt` tra ve dung dong co.
result: OK - co: `sun{cust0m_fmtstr_n0_t00ls_4ll0wed}`

---

**Bai hoc do luong:** khi mot chuan bien the cung cho RA MAT KET NOI, thi
"giot" nam o ngoai cac bien the do - o day la ban than chuoi ROP. Phai co
control chay chuoi ma khong goi syscall (doi o syscall thanh `ret` ve vong lap)
truoc khi ket luan bat ky dieu gi ve syscall bi chan.
