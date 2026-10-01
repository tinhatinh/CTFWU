# Đề bài - dockside-ticket

## Nguyên văn đề

```text
Dockside Ticket Office
75
Beginner
The dockside ticket office manages temporary harbour access tickets.

You can create, cancel, edit, and use a ticket.

A cancelled ticket should no longer be usable, but this old terminal may not handle
ticket memory safely.

Can you turn a cancelled ticket into emergency harbour access?

Flag Format: CSSCTF{}
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/dockside_ticket` (copy từ: `/c/Users/Administrator/Downloads/dockside_ticket`) |
| Kích thước | 16664 byte |
| SHA-256 | `b275a7c289d1bf36b0c14562325838c0c2a6cf75edd363e72745a5b493ae49dd` |
| Loại file | ELF 64-bit LSB executable, x86-64, dynamically linked, not stripped |
| Mitigation | không PIE, partial RELRO, NX, có `__stack_chk_fail` (nhưng không cần overflow stack) |
| Hàm đáng chú ý | `create_ticket`, `cancel_ticket`, `edit_ticket`, `use_ticket`, `open_gate`, `deny_access` |
| Nhiệm vụ | làm ticket đã cancel vẫn "use" được và vào nhánh emergency access |
| Định dạng cờ | `CSSCTF{...}` |
| Điểm / độ khó / tác giả | 75 / Beginner (ngay trên thẻ đề) |
| Trạng thái nộp | cờ đọc nguyên văn từ `.rodata` của chính file đề (0x402088), chưa chạy binary và chưa có xác nhận bảng điểm; xem ghi chú môi trường trong `writeup.md` |

## Hướng giải (tóm tắt)

`cancel_ticket` gọi `free()` nhưng không gán lại con trỏ toàn cục, nên `edit_ticket` vẫn
`read()` 40 byte vào chunk đã giải phóng và `use_ticket` gọi con trỏ hàm ở offset 0x20 của
chunk đó. Ghi địa chỉ `open_gate` (0x40125f, binary không PIE) vào vị trí ấy rồi chọn menu 4.

## Chạy lại lời giải

```bash
python exploit.py --run ./dockside_ticket        # Linux
python exploit.py --payload                      # chi xuat byte payload
```

Kết quả: `CSSCTF{us3_4ft3r_fr33_d0cks1d3}` (đã lưu trong `flag.txt`).
