# notes.md - maintenance-log

Input: `files/chall` (14480 B, sha256 `de630ba8…b118e3`) + `files/Dockerfile` + `files/flag.txt`
Dịch vụ: `nc 34.116.80.78 7312`
Định dạng cờ đề yêu cầu: `CSSCTF{...}`

## H1 - overflow buffer `report()` đè return address
cmd: `objdump -D -M intel files/chall > analysis/full.asm` rồi đọc `0x40139a`
evidence: `memset(rbp-0x50,0,0x50); read(0, rbp-0x50, 0x50)` - số byte đọc đúng bằng
kích thước buffer, và buffer kết thúc sát ngay slot saved rbp. Với `X = rbp_main`,
`P = X-0x70`, 80 byte phủ `X-0x70..X-0x21`, còn return address của `report()` nằm ở
`X-0x18`: thiếu 8 byte nữa mới tới.
result: DEAD - không có đường tràn thẳng vào return address.

## H2 - bỏ qua canary vì service "fortified" như vendor nói
cmd: `grep -n "fs:0x28" analysis/full.asm`
evidence: canary xuất hiện ở `io_setup` (0x4011be), `grant` (0x401276), `main` (0x401421);
**không** xuất hiện ở `report` (0x40139a) và `operator` (0x401348).
result: DEAD - claim của vendor là chi tiết đánh lạc hướng; hai hàm ta bắn vào không
những không có canary mà `grant()` còn `exit(0)` trước khi `main` kịp check.

## H3 - `operator()` ret vào chuỗi ROP đặt ở đầu buffer `report()`
cmd: tính lại frame: `push rbp` của `operator` lưu `rbp_report = X-0x20` tại địa chỉ `X-0x80`
evidence: epilogue `operator()` là `leave; ret`, nên `ret` pop qword tại `X-0x78` - đó
chính là return address `0x401407` mà `call operator()` vừa push, ta không ghi tới.
Byte thứ 33 chỉ sửa được **giá trị** saved rbp (`X-0x20`), không sửa được rsp của `ret` này.
result: DEAD - pivot không xảy ra trong `operator()`; phải đợi đến `leave; ret` của
chính `report()`. (Trước đó tôi ghi `rbp_op = X-0x70` trong docstring `exploit.py`,
lệch 8 byte, và chuỗi ROP đặt theo mô hình đó sẽ không bao giờ chạy.)

## H4 - pivot qua saved rbp bị hỏng, chuỗi ROP nằm trong buffer 80 byte
cmd: `python analysis/selftest.py`
evidence: mô hình bộ nhớ phẳng theo đúng thứ tự prologue/epilogue cho:
`rbp = (X-0x20 & ~0xFF) + z`, `ret` lấy rip từ qword `A = rbp+8`. Muốn `A` rơi vào
buffer tại offset `O` thì `z = O + L - 88` với `L = (X-0x20) & 0xFF`, và `O` phải bội
của 16 để `grant()` nhận rsp `%16 == 8`, `O <= 40` để 40 byte chuỗi nằm gọn trong 80
byte. Chạy 16 giá trị `X mod 256`: 12 ra `FLAG`, 4 case `L ∈ {0,16,32,48}` bị `plan()`
loại đúng như dự đoán; control "không có ROP" và control "z lệch 1 byte" đều fail.
result: OK (offline) - còn 4/16 stack alignment không gọi được buffer -> chấp nhận
kết nối lại để lấy địa chỉ stack mới (ASLR mỗi lần exec).

## H5 - đánh thật trên dịch vụ
cmd: `python exploit.py --probe` rồi `python exploit.py`
evidence: probe cho `P = 0x7fff1b7b6720` (`P % 16 = 0`), flow chạy đúng như mô hình. Lần 1:
`P = 0x7ffdd96ba300` -> `offset=16 z=0x8`, server in
`[+] Access Granted! Here is your flag:` / `CSSCTF{Duh_m4t3_1_4m_sl33py}`.
Chạy lại lần 2 để chứng minh tái lập: `P = 0x7ffda1427b30` -> `offset=0 z=0x28`, cùng cờ.
Cờ khác hẳn `files/flag.txt` (`CSSCTF{definetely_not_flag}`) nên đây là cờ thật trên server.
result: OK - cờ: `CSSCTF{Duh_m4t3_1_4m_sl33py}`

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
