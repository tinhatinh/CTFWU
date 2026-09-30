# Dockside Ticket Office — Pwn (Beginner)

**Flag:** `CSSCTF{us3_4ft3r_fr33_d0cks1d3}` · **Files:** `dockside_ticket` (16664 B, sha256 `b275a7c2…49dd`)

## Đề bài

Thiết bị bán vé ra cảng cho phép tạo, huỷ, sửa và dùng vé. Vé đã huỷ lẽ ra không dùng được
nữa, nhưng thiết bị cũ quản lý bộ nhớ vé không an toàn. Mục tiêu: biến một vé đã huỷ thành
lối vào khẩn cấp.

## Phân tích ban đầu

ELF 64-bit, không PIE, partial RELRO, NX, not stripped. Sáu hàm tự giải thích tên:
`create_ticket`, `cancel_ticket`, `edit_ticket`, `use_ticket`, và hai đích `open_gate` /
`deny_access`.

`create_ticket` cấp phát một chunk 0x28 byte, ghi chuỗi `"GUEST"` ở đầu và — đây là điểm
then chốt — **một con trỏ hàm ở offset 0x20**, khởi tạo là `deny_access`:

```asm
40137c:  mov    edi,0x28
401381:  call   malloc@plt
401386:  mov    QWORD PTR [rip+0x2cdb],rax      # active_ticket = chunk
401394:  mov    DWORD PTR [rax],0x53455547       # "GUEST"
4013a7:  lea    rdx,[rip-0x178]                  # deny_access
4013ae:  mov    QWORD PTR [rax+0x20],rdx         # con tro ham
```

## Các hướng đã loại

1. **Overflow stack / ghi đè return address**: `edit_ticket` ghi đúng 0x28 byte vào vùng
   malloc, không tràn sang đâu cả; và binary có `__stack_chk_fail`. Loại vì không cần.
2. **Ghi đè GOT (partial RELRO)**: không có chỗ nào cho ta ghi vào GOT, và cũng không cần
   vì có con trỏ hàm ngay trong chunk. Loại.
3. **Double free**: không có đường nào free hai lần mà không tạo lại vé (`create_ticket`
   chặn khi `active_ticket` còn khác 0). Loại.

## Chuỗi khai thác

**Bước 1 - Chỉ ra con trỏ không bị xoá.** `cancel_ticket` chỉ có `free` và một `puts`:

```asm
4013e8:  mov    rax,[rip+0x2c79]        # active_ticket
4013f2:  call   free@plt
401401:  call   puts@plt                # "Ticket cancelled."
```

Đếm trong toàn binary thì `active_ticket` chỉ được ghi **một lần duy nhất**, ở
`create_ticket+0x2f`. Vậy sau khi huỷ, biến toàn cục vẫn trỏ vào chunk đã giải phóng.

**Bước 2 - Ghi vào chunk đã giải phóng.** `edit_ticket` chỉ kiểm tra con trỏ khác 0 rồi
`read(0, active_ticket, 0x28)`; 40 byte ta gửi đi nằm trọn trong chunk, nên byte 32..39
(chính là con trỏ hàm) trở thành tuỳ ý:

```python
payload = b"A" * 32 + struct.pack("<Q", 0x40125F)   # dung 40 byte, vua khit read(0x28)
```

**Bước 3 - Kích hoạt.** `use_ticket` gọi thẳng con trỏ đó, không thẩm tra gì:

```asm
401492:  mov    rdx,QWORD PTR [rax+0x20]
40149b:  call   rdx
```

Vì không PIE nên địa chỉ `open_gate` cố định, không cần leak.

**Bước 4 - Kiểm chứng đích nhảy.** `open_gate` in ba chuỗi, chuỗi thứ ba lấy từ
`0x402088`; ánh xạ `.rodata` (vaddr 0x402000 ↔ file offset 0x2000) cho ra đúng xâu cờ:

```
0x402008 -> 'Ticket scanned.'
0x402060 -> 'Emergency harbour access granted.'
0x402088 -> 'CSSCTF{us3_4ft3r_fr33_d0cks1d3}'
```

Chuỗi này cũng được đọc nguyên văn từ dữ liệu của file, không phải suy ra.

**Lưu ý về môi trường.** Máy phân tích là Windows: không có distro WSL nào chạy được
(`wsl -l` chỉ liệt kê `docker-desktop`, đang tắt) và angr hỏng ở bước nạp `rustylib`,
nên chưa chạy thật binary để lấy output. Lời giải trên là chứng minh tĩnh, và
`exploit.py` vẫn dùng được ngay trên Linux hoặc với remote:

```bash
python exploit.py --run ./dockside_ticket
python exploit.py --host <challenge> --port <port>
```

## Flag

```
CSSCTF{us3_4ft3r_fr33_d0cks1d3}
```

## Reproduce

```bash
python exploit.py --run ./dockside_ticket     # tren Linux
python exploit.py --payload                   # chi in byte payload
```
