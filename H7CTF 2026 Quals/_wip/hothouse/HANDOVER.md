# Hothouse — ghi chú dở dang (chuyển cho đồng đội)

Đã dừng ở đây, chưa `FIRE` lần nào (budget FIRE 1 lần còn nguyên).

## Binary

`files/hothouse.zip` → ELF x86-64, **no PIE**, NX, stripped. `main @ 0x401290`.
`analysis/full.asm` = objdump `-D -M intel` đầy đủ.

## Layout bộ nhớ

- `mmap(0, 0x2000, RW)` → `[0x4e62a8] = base`.
- `mprotect(base+0x1000, 0x1000, RWX)` → `[0x4e62a0] = base+0x1000` = **fabric page**
  (vừa là dữ liệu vừa là code; `FIRE` gọi thẳng vào đó).
- `0x4e5aa0` : **substrate** 1024 bit (128 byte), mỗi byte `& 1`.
- `0x4e5ea0` : **seed lattice** 32×32 byte.
- `0x4e62a8` : base của vùng mmap (fabric = base+0x1000).

## Lệnh

| Lệnh | Handler / budget | Ghi chú |
|---|---|---|
| `SEED r c` | counter `0x4e5a98 ≤ 0xfff` | đặt `byte lattice[r*32+c] = 1` |
| `INCUBATE` | counter `0x4e5a90 ≤ 0x3f` | chạy `0x403800`, 7 thế hệ |
| `PROBE r c` | counter `0x4e5a88 ≤ 0x4e1f` | in byte `fabric[r*4 + (c>>3)]`; **r signed (`movsxd`) → đọc được dưới trang** |
| `RENDER` | – | in lattice 32×32 dạng `#`/`.` |
| `FIRE` | counter `0x4e5a80`, **dùng 1 lần** | cài seccomp rồi `call [0x4e62a0]` |

## Quy tắc sinh (`0x403800`)

Bảng hàng xóm `0x4ad280` = 6 cặp (row,col): `(-1,0),(1,0),(0,1),(0,-1),(-1,1),(1,-1)`.

`new[r][c] = XOR` của 6 ô trong-lattice, ngoài lattice coi là 0; **sau đó XOR với substrate
từng ô**; rồi pack 32×32 bit xuống 128 byte fabric: `fabric[r*4+(c>>3)]` bit `(c&7)`.

Suy ra (đây là điểm mấu chốt vì substrate ngẫu nhiên theo kết nối):

```
fabric_observed = M · seed  XOR  s0
```

với `s0` = nội dung fabric **trước** `INCUBATE` (đọc được bằng 128 lệnh `PROBE`,
còn dư 19874 trong budget 20000). Nên: đọc `s0` trước khi seed, rồi giải
`M·x = target XOR s0`.

`analysis/ca.py` mô phỏng đúng hình thức (đã khớp dạng quy tắc), `analysis/matrix.py`
dựng ma trận GF(2) 1024×1024 bằng cách truyền basis vector qua 7 thế hệ — **chưa chạy**,
và còn một vòng lặp chết dòng 15–18 cần xoá.

## seccomp của FIRE (12 lệnh cBPF)

Cho phép: `openat(257)`, `read(0)`, `write(1)`, `mmap(9)`, `exit(60)`, `exit_group(231)`.
Kiến trúc `0xc000003e`, còn lại `KILL_PROCESS` (`0x80000000`).
**Không có syscall nào khác**, không `execve`.

## Đường đi còn lại

1. `getenv("FLAGPATH")` được copy vào `base + (rand % 0xf40) + 0x40`, tức **ngay dưới**
   fabric page trong vùng RW → shellcode quét ngược từ `base+0x1000` tìm xâu `"fl"`.
2. Shellcode gói trọn trong **1 trang fabric 128 byte**: `openat(AT_FDCWD=-100, path,
   O_RDONLY)` → `read(fd, buf, n)` → `write(1, buf, n)` → `exit_group(0)`. Địa chỉ vùng
   RW phía dưới suy ra từ chính trang fabric (`FIRE` làm `call [0x4e62a0]`, nên RIP
   = base+0x1000; lấy `lea rip-relative` rồi trừ đi là định vị được `base+0x40..0xf80`).
   `PROBE r` với `r` âm là cách kiểm tra nhanh nội dung vùng đó trước khi viết shellcode.
3. Giải hệ GF(2) rồi phát `SEED` cho từng bit bật (budget 4095, nhiều hơn 1024 nên đủ).
4. `INCUBATE`, đối chiếu fabric bằng `PROBE`, rồi `FIRE`.
