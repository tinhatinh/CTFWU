# Mad Libs — Pwn (Medium)

## Đề bài

`Fill in the blanks! Our Mad Libs game prints back whatever you type. It's just a simple word game... right?`

Target `nc chal.sunshinectf.games 26001`, kèm `mad_libs`, `libc.so.6`, `ld-linux-x86-64.so.2`.
499 điểm, 38 solves, tác giả Oreomeister.

## Phân tích ban đầu

Binary 14584 byte, ELF 64-bit PIE, stripped. Mitigation: PIE, NX, canary, RELRO một phần
(không có `BIND_NOW`), libc là Ubuntu glibc 2.39.

`main` nằm tại `0x11c9`, dịch ngược ra được đúng một vòng lặp:

```c
for (i = 0; i <= 7; i++) {
    printf("(%d) > ", i + 1);
    if (fgets(buf, 0x100, stdin) == NULL) break;
    printf(buf);                  // <= format string
}
```

Buffer nằm ở `[rbp-0x110]` tức rộng 272 byte, trong khi `fgets` chỉ đọc 256 byte, nên không có
overflow, không với tới return address. Chương trình chỉ có duy nhất một primitive, là `printf(buf)`
với `buf` hoàn toàn do ta chọn, lặp lại 8 lần.

`.rela.plt` cho biết vị trí GOT, và vì RELRO chỉ một phần nên vùng này ghi được:

```
0x4000 puts   0x4008 __stack_chk_fail   0x4010 printf   0x4018 fgets   0x4020 setvbuf
```

## Chuỗi khai thác

### Bước 1, định vị stack

Gửi `%1$p %2$p ...` rồi đọc lại. Slot 8 in ra đúng 8 byte đầu của chính chuỗi ta gửi
(`0x2432252070243125` = `"%1$p %2$"`), nghĩa là vùng varargs bắt đầu ngay tại buffer:
slot `k` tương ứng `buf[8*(k-8)]`. Như vậy chỉ cần đặt một địa chỉ vào `buf` là có ngay
đọc/ghi tùy ý bằng `%k$s` / `%k$hhn`.

Tiếp tục quét các slot phía trên buffer. Hai lần quét liên tiếp cho kết quả giống hệt nhau, tức
là ổn định:

```
40 0x7fffa7bb40e0 (stack)   41 0x2ef1945964c7bb00 (canary)   42 0x7fffa7bb4160 (stack)
47 0x60de6e4031c9           52 0x60de6e405db8
```

12 bit thấp của slot 47 là `0x1c9`, khớp chính xác `main` tại `0x11c9`. Đó là con trỏ `main` mà
`__libc_start_call_main` để lại. Vậy PIE base = slot 47 - 0x11c9, và kết quả luôn chia hết cho
0x1000, đúng tính chất của một base.

### Bước 2, leak libc qua chính GOT

Không cần đoán symbol nào nằm ở slot 1 (các slot 1-7 là giá trị còn lại trong thanh ghi, không ổn
định giữa các lần chạy). Thay vào đó dùng đúng cái GOT: `printf` đã được gọi ở lần in prompt đầu
tiên, nên `printf@GOT` đã resolve thành địa chỉ thật trong libc.

Định dạng chuỗi đọc: prefix phải dài đúng 8 byte để địa chỉ rơi vào `buf[8:16]` tức slot 9:

```
"%9$s" + "AAAA" + p64(base + 0x4010)
```

`%9$s` in ra 6 byte của con trỏ rồi dừng (2 byte cao là NUL). `libc_base = ptr - 0x600f0`.

Trước khi tin con số này, tôi đặt một đáp án đã biết để kiểm: đọc tiếp `libc_base + 0x1cb42f` và yêu
cầu nó in ra đúng chuỗi `/bin/sh`. Nếu base sai, bước này fail và exploit dừng, không leo thang trên
một địa chỉ vô nghĩa.

### Bước 3, ghi GOT

`printf = 0x600f0` và `system = 0x58740` trong libc, cách nhau `0x79b0` (dưới 16 MB). Nghĩa là 3 byte
cao của hai địa chỉ giống hệt nhau, và GOT đang sẵn chứa 3 byte cao đúng. Nên chỉ cần ghi 3 byte
thấp, không phải 8:

```
%hhn vào base+0x4010, +1, +2 với giá trị = 3 byte thấp của system
```

Bộ dựng chuỗi format tính delta cho từng byte (`d = (muốn - đã in) mod 256`), xếp các đích theo giá
trị tăng dần để không phải quay vòng, rồi đệm cho đủ 40 byte để ba địa chỉ nằm đúng slot 13, 14, 15.
Tôi kiểm bộ dựng này bằng cách mô phỏng printf với 500 bộ ba byte ngẫu nhiên: cả 500 đều ghi đúng
(`analysis/selftest_fmt.py`).

### Bước 4, shell

Sau khi GOT trỏ sang `system`, lời gọi `printf(buf)` kế tiếp trở thành `system(buf)`. Chỉ cần gửi
`/bin/sh` làm nội dung buffer, vì `buf` chính là tham số đầu tiên.

```
uid=1337(mad_libs) gid=1337(mad_libs)
/ctf/flag.txt:  -rw-r----- 1 root mad_libs 27
```

## Flag
```
sun{f1ll_iN_th3_g0T_eNtry}
```

```bash
python exploit.py                  # mặc định: ls -l /ctf; cat /ctf/*; env | grep -i flag
python exploit.py 'cat /ctf/flag.txt'
python analysis/selftest_fmt.py    # mô phỏng printf, kiểm bộ dựng chuỗi %hhn
```

Cờ nằm ở `/ctf/flag.txt` (27 byte, chủ `root:mad_libs`, chế độ `-rw-r-----`). Script chỉ dùng
stdlib, tự nối vào `chal.sunshinectf.games:26001`, tự dò lại base ở mỗi lần chạy (5 lượt thử),
tự kiểm `libc_base` bằng chuỗi `/bin/sh` trước khi ghi GOT, và ghi `flag.txt` khi bắt được chuỗi
cờ trong output.
