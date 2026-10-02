# Đề bài - prince-walk

## Nguyên văn đề

```text
prince walk
50
One year after The Severance silenced the Quantum Nexus Network, your terminal receives a transmission from the Kuiper Belt Relay. Hidden inside it is an abandoned Polaris Logistics recovery channel. With the old factions racing to claim the rebooting network, you follow the signal before someone else does. PRINCE WALK The channel opens into PRINCE WALK, an old planetary survey simulation damaged by The Severance. Your avatar starts at (1, 1), while the last surviving recovery beacon flickers as a distant star at (999999, 999999). Somewhere beneath this impossible landscape lies the route back to the relay-you just need to reach it.

Flag Format: CSSCTF{...}

附件引用:
- 文件: C:\Users\Administrator\Downloads\prince_walk
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/prince_walk` (copy từ: `/c/Users/Administrator/Downloads/prince_walk`) |
| Kích thước | 92384 byte |
| SHA-256 | `2d0c95f718b84f07d94173def6753a105260a8d1a46e92cac9d8352e84ee5812` |
| Loại file | ELF 64-bit LSB pie executable, x86-64, dynamically linked, stripped |
| Entropy | 7.416/8, do một khối 66560 byte trong `.rodata` từ `0x4a80` |
| Imports đáng chú ý | `isatty`, `tcgetattr`, `tcsetattr`, `ioctl`, `poll`, `prctl`, `raise`, `sigaction`, `strcmp` |
| Bảng landmark | `.data.rel.ro` tại `0x16be0`, mỗi bản ghi 32 byte `{i32 x, i32 y, title*, desc*, u32, u32 achievement}` |
| Nhiệm vụ | Lấy chuỗi chỉ được in ra khi tới toạ độ `(999999, 999999)` |
| Định dạng cờ | `CSSCTF{...}` |

## Hướng giải (tóm tắt)

Không cần chơi game. Khối 66560 byte trong `.rodata` là 8320 bản ghi hai từ 32 bit đã được làm trắng, và chỉ có đúng một hàm chạm tới nó: `FUN_00102c52`, hàm này mở đầu bằng kiểm tra `x == 999999 && y == 999999`. Chuỗi khoá sinh từ chính toạ độ đó bằng `rol` và `lowbias32`, một bảng 16 từ bị biến đổi sau mỗi byte phát ra, và payload mang theo độ dài cùng checksum FNV-1a để tự xác thực. Viết lại đúng hàm đó bằng Python rồi chạy là thu được plaintext.

## Chạy lại lời giải

```bash
python exploit.py files/prince_walk
```

Kết quả: `CSSCTF{P12INC3_0R_P1NC3?}` (đã lưu trong `flag.txt`).
