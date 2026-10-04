# notes.md - soupos-0-welcome-to-the-kitchen

## N1 - Login va nop co mien phi
cmd: tren noVNC: `cook` / `soup`
evidence: shell `cook@soupOS:/>` len; the de ghi ro `Free flag ... cdctf{soupOS_is_better_than_arch}`
result: OK - nop duoc, kenh submit hoat dong

## N2 - Handout co phai source that khong
cmd: `tar -tzf soupos-handout.tar.gz | wc -l`; `grep -n 'FLAG[1-4]' soupos/src/challenge.c`
evidence: 121 muc; 4 dinh FLAG bi che thanh `REDACTED_STAGE_n`, con lai la source day du
(`shell.c`, `soupyc.c`, `usermode.c`, `users.c`, `alphasoup.c`, `paging.c`, `fat.c`)
result: OK - doc source thay vi reverse-engineer binary

## N3 - Bon cho "tin nham" nam dau
cmd: `python exploit.py files/soupos-handout.tar.gz`
evidence: 8/8 mau tim thay (xem output trong writeup): `may()` trong shell, `vfs_open` trong soupyc,
`users_check` so hash, `kmalloc` cho FLAG3, `memcpy(... buf + p_offset ...)`, `if (i >= a->len)`,
`sc_state.after_hook`
result: OK - ban do chain cho stage 1-4, dung de thu tu toi uu (stage 1 → 2 → 3 → 4)

## N4 - Mot handout cho ca 5 the
cmd: `cmp "soupos-handout.tar.gz" "soupos-handout (3).tar.gz"`; `cmp symbols.txt "symbols (3).txt"`
evidence: khong khac nhau (kich thuoc va sha256 giong het: `c9fc07e2…92a1e7`, `1e1aad7e…04b7d9`)
result: OK - khong can tai lai handout o stage sau; chi khac nhau o URL instance

## N5 - Harness local
cmd: `gcc -O0 -w -idirafter ../soupos/src -o soupctest.exe stubs.c main.c ../soupos/src/soupyc.c ../soupos/src/vfs.c ../soupos/src/alphasoup.c`
evidence: lan dau dung `-I` thi build that bai vi handout co `src/stdio.h` remap `printf` sang
`doom_printf`; doi sang `-idirafter` thi chay
result: OK - moi lenh soupyc deu duoc chay thu o local truoc khi yeu cau nguoi choi go
