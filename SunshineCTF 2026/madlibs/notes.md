# Log giả thuyết

## Đọc binary

H1. Có overflow buffer để ghi đè return address.
`result: DEAD` buffer ở `[rbp-0x110]` (272 byte) còn `fgets` chỉ đọc 256 byte, nên không chạm tới
saved rbp (`rbp+0`) hay return address (`rbp+8`). Không có đường ROP trực tiếp.

H2. Primitive duy nhất là format string `printf(buf)` với buf do người dùng kiểm soát.
`result: LIVE` đúng một lời gọi `printf(buf)` trong vòng lặp 8 lần.

## Dò stack

H3. Tìm slot chứa con trỏ để leak.
`result: WIN` gửi `%1$p..%7$p`: slot 1 và 4 là con trỏ vào vùng data của libc (`0x...2a1`,
`0x...2c3`), slot 2 là `0xfbad2088` (flags của `stdout`). Nhưng các slot 1-7 là giá trị còn lại
trong thanh ghi, **không ổn định giữa các lần chạy**, nên không dùng làm leak chính.

H4. Buffer nằm ngay trong vùng varargs.
`result: WIN` slot 8 in ra đúng 8 byte đầu của chuỗi gửi lên (`%1$p %2$`), nên slot k tương ứng
`buf[8*(k-8)]`. Đây là chìa khóa: chỉ cần định dạng prefix đúng 8 byte là đặt được địa chỉ tùy ý
vào slot 9.

H5. Quét slot 40-56 để tìm con trỏ ổn định.
`result: WIN` hai lần dò liên tiếp cho kết quả **giống hệt nhau**:

```
40 0x7fffa7bb40e0 (stack)   41 0x2ef1945964c7bb00 (canary)   42 0x7fffa7bb4160 (stack)
45 0x7fffa7bb41e8 (stack)   47 0x60de6e4031c9                52 0x60de6e405db8
```

Slot 47 có 12 bit thấp là `0x1c9`, khớp `main` tại `0x11c9` -> **PIE base = slot47 - 0x11c9**,
và page-aligned. Slot 52 = `base + 0x3db8` (trong vùng RELRO) củng cố thêm.

H6. Chỉ số leak nằm ở 49.
`result: DEAD -> sửa thành 47` lần dump đầu bị `fgets` cắt (chuỗi 287 ký tự > 256), nên các
specifier cuối bị dồn sang iteration sau và mình đọc nhầm chỉ số. Gửi `%49$p` đơn lẻ trả về giá trị
random, xác nhận 49 sai.

## Leak libc

H7. Dùng GOT làm kênh leak.
`result: WIN` vì partial RELRO và `printf` đã được gọi ít nhất một lần trước format string đầu
tiên, nên `printf@GOT` đã resolve. Đọc `base + 0x4010` bằng `%9$s` cho ra 6 byte của địa chỉ libc
printf -> `libc_base = ptr - 0x600f0`.

H8. Tin ngay libc base vừa tính.
`result: KHÔNG DÙNG` đã thêm bước tự kiểm: đọc `libc_base + 0x1cb42f` và yêu cầu in ra đúng
`/bin/sh`. Base sai thì dừng, không leo thang.

## Ghi

H9. Ghi full 8 byte vào `printf@GOT` bằng `%hhn`.
`result: DEAD (không cần)` `printf` và `system` cách nhau `0x79b0` (< 16 MB) nên 3 byte cao của
chúng giống hệt nhau; chỉ cần ghi 3 byte thấp, và GOT giữ nguyên phần cao vốn đã đúng.

H10. Đệm format string bằng NUL để tránh in ra byte của địa chỉ.
`result: DEAD -> sửa` đệm 4 byte NUL làm địa chỉ bị đẩy sang offset 11 thay vì 8, slot 9 đọc phải
chỗ khác và tiến trình segfault. Cách đúng: prefix dài **đúng 8 byte** (`"%9$s"` + `"AAAA"`), địa
chỉ nằm ở `buf[8:16]`; các byte địa chỉ in thừa nằm **sau** phần dữ liệu cần đọc nên không ảnh
hưởng parsing.

H11. Bộ dựng `%hhn` tự tính delta đúng.
`result: WIN` `analysis/selftest_fmt.py` mô phỏng printf và kiểm 500 bộ 3 byte ngẫu nhiên, tất cả
đều ghi đúng giá trị mong muốn.

## Chạy thật

H12. `Conn.send` luôn nối newline.
`result: WIN (lỗi trước đó)` bản đầu chỉ nối `\n` khi payload là `str`, còn mọi payload là `bytes`,
nên `fgets` không bao giờ trả về và mọi read trả rỗng.

H13. Kết quả leak có lúc rác.
`result: WIN` một lần chạy trả `0x1041414141f0` (lẫn byte `A` của padding) do gói tin bị lệch. Ba
lần liên tiếp sau đều page-aligned. Xử lý bằng vòng retry 5 lần ở tầng kết nối, cộng điều kiện
chặn `base % 0x1000`.

## Cờ

```
sun{f1ll_iN_th3_g0T_eNtry}
```

Cờ nằm ở `/ctf/flag.txt`, chủ `root`, group `mad_libs`, mode `0640` -> chỉ đọc được sau khi có RCE
thật, không phải qua đọc file trực tiếp.
