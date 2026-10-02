# notes.md - dockside-ticket

Input: `files/dockside_ticket` (16664 B, sha256 `b275a7c289d1bf36b0c14562325838c0c2a6cf75edd363e72745a5b493ae49dd`)
ELF 64-bit, ET_EXEC (không PIE), partial RELRO, NX, not stripped. Không có remote kèm theo.
Định dạng cờ: `CSSCTF{}`

## H1 - Bug nằm ở đâu
cmd: `objdump -d -M intel files/dockside_ticket > analysis/disasm.txt` rồi đọc 6 hàm
evidence:
- `create_ticket` @0x401357: `if (active_ticket) puts("A ticket already exists.")` ngược lại
  `malloc(0x28)`, ghi `"GUEST"` ở +0 và **`deny_access` vào +0x20** (con trỏ hàm).
- `cancel_ticket` @0x4013c3: `free(active_ticket)` rồi chỉ `puts("Ticket cancelled.")`.
- `edit_ticket` @0x401408: `if (!active_ticket) puts("No active ticket.")` ngược lại
  `read(0, active_ticket, 0x28)` -> 40 byte attacker kiểm soát.
- `use_ticket` @0x401466: `rdx = [active_ticket+0x20]; call rdx` - gọi thẳng, không kiểm tra gì.
result: PENDING -> UAF, chốt ở H2.

## H2 - Con tro con trỏ co bi xoa sau khi free khong
cmd: `grep -n "404068" analysis/disasm.txt`
evidence: toàn binary chỉ có **một** lệnh ghi vào `active_ticket`, ở `create_ticket+0x2f`
(401386, lưu kết quả malloc). Chín chỗ còn lại đều là đọc. Không có chỗ nào gán NULL.
=> sau `cancel_ticket`, con trỏ vẫn trỏ vào chunk đã giải phóng và `edit_ticket`/`use_ticket`
vẫn coi là hợp lệ.
result: OK - use-after-free chắc chắn, không cần thêm điều kiện.

## H3 - Ghi bao nhieu byte va con tro nam dau
cmd: `python - <<'PY' ... tinh offset ... PY`
evidence: chunk 0x28 = 40 byte; `create_ticket` ghi con trỏ tại `rax+0x20` = byte 32..39.
Payload `b"A"*32 + p64(0x40125f)` dài đúng 40 byte, vừa khít `read(0, ptr, 0x28)`.
Không PIE nên địa chỉ hàm đích cố định, không cần leak.
result: OK.

## H4 - Dich cua con tro in ra gi
cmd: `python - <<'PY' ... doc .rodata theo vaddr ... PY`
evidence: `open_gate` @0x40125f gọi ba lần `puts`: 0x402008 `"Ticket scanned."`,
0x402060 `"Emergency harbour access granted."`, 0x402088 -> file offset 0x2088 chứa
chuỗi `CSSCTF{us3_4ft3r_fr33_d0cks1d3}`.
result: OK - cờ: `CSSCTF{us3_4ft3r_fr33_d0cks1d3}`

## Nhanh khong chay duoc binary tren may nay
- `wsl.exe -l -v`: chỉ có distro `docker-desktop` (Stopped), không có Ubuntu nào để chạy ELF.
- angr 10.0.0 cài sẵn nhưng thiếu `claripy`; cài claripy 9.3.6 xong thì
  `from .rustylib import claripy` báo `ImportError: DLL load failed while importing rustylib`.
  Không thử lần ba.
- Docker Desktop có binary nhưng đang tắt, cần bật + pull image -> hỏi trước khi làm.
=> Lời giải ở đây là chứng minh tĩnh: chuỗi cờ được đọc nguyên văn từ `.rodata` đúng tại
địa chỉ mà nhánh cướp được truyền cho `puts`. Khi nào chạy được Linux, dùng
`python exploit.py --run ./dockside_ticket` để lấy cờ từ output thật.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
