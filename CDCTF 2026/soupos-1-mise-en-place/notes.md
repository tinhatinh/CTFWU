# notes.md - soupos-1-mise-en-place

Handout: `files/soupos-handout.tar.gz` (214.924 B, sha256 `c9fc07e2…92a1e7`), `files/symbols.txt`
(`1e1aad7e…04b7d9`). Instance: noVNC, `cook`/`soup`.

## H1 - File cờ nằm ở đâu, bị chặn bởi cái gì
cmd: `serve /` (trên máy), rồi `cd`
evidence: `serve /` → `No soup for you: 'serve /'` (shell không nhận tham số cho `serve`,
`cmd_serve(void)` ở `shell.c:545`); `cd` in danh sách root bowl có `FLAG1.TXT`
result: OK - file tồn tại; quyền bị chặn bởi `may()` trong shell, không phải bởi VFS

## H2 - Đường nào kiểm quyền
cmd: `grep -n "may(" soupos/src/shell.c`; `grep -n "vfs_open" soupos/src/soupyc.c`
evidence: `shell.c:595 if (!may(path,'r')) { deny(path); return; }` cho `pour`;
`soupyc.c:1460 vfs_open(a[0].sval, flags)` không có `may()` nào ở trước
result: OK - hai đường dẫn, một phép kiểm → đi đường soupyc

## H3 - Đọc bao nhiêu byte là đủ
cmd: `grep -n 'SVAL_LEN' soupos/src/soupyc.c`
evidence: `#define SVAL_LEN 48`; `read()` chặn `want > SVAL_LEN-1` → tối đa 47
result: OK - phải truyền đúng 47; cờ stage 1 dài 42 ký tự + `\n` vừa khít

## H4 - Lỗi gõ khi nhập lệnh
cmd: `soup -c pour read(open("/FLAG1.TXT),47)`
evidence: `soupyc: parse error (line 1): expected ')'`
result: DEAD - thiếu một nháy đóng; đã tái lập đúng thông báo lỗi trong harness trước khi gõ lại

## H5 - Có cần nháy cho `soup -c` không
cmd: `sed -n '618,634p' soupos/src/shell.c`
evidence: `cmd_soup` làm `code = args + 2` rồi bỏ khoảng trắng, không cắt theo nháy
result: OK - `soup -c code` và `soup -c "code"` tương đương; chọn bản không nháy để đỡ lỗi gõ

## Kiểm chứng cuối

`exploit.py files/soupos-handout.tar.gz` in ra 5 bằng chứng từ source thật (may(), cmd_pour,
soupyc open, read builtin, fat_chmod FLAG1.TXT) rồi mới in lệnh cần gõ. Cờ capture verbatim lần đầu ở
stage 3 (vòng quét kernel memory đọc luôn `.rodata`).
