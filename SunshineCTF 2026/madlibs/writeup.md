# Mad Libs - Pwn (Medium)

## Đề bài

`Fill in the blanks! Our Mad Libs game prints back whatever you type. It's just a simple word game... right?`

Mục tiêu được cung cấp qua địa chỉ `nc chal.sunshinectf.games 26001`, kèm theo các file `mad_libs`, `libc.so.6`, và `ld-linux-x86-64.so.2`.
Bài có trị giá 499 điểm với tổng cộng 38 lượt giải thành công, tác giả là Oreomeister.

## Phân tích

File thực thi là một ELF 64-bit PIE đã bị loại bỏ thông tin gỡ lỗi (stripped) với kích thước 14584 byte. Các cơ chế bảo vệ được bật bao gồm PIE, NX, stack canary, và Partial RELRO (không sử dụng `BIND_NOW`). Thư viện C được cung cấp là Ubuntu glibc 2.39.

Hàm `main` nằm tại offset `0x11c9` và khi được dịch ngược sẽ lộ ra một vòng lặp đơn giản:

```c
for (i = 0; i <= 7; i++) {
    printf("(%d) > ", i + 1);
    if (fgets(buf, 0x100, stdin) == NULL) break;
    printf(buf);                  // <= Lỗ hổng Format String
}
```

Buffer tại `[rbp-0x110]` dài 272 byte. `fgets(buf, 0x100, stdin)` đọc tối đa 255 byte dữ liệu rồi thêm NUL, nên lời gọi này không tràn buffer. Primitive được dùng là `printf(buf)` với format string do input điều khiển; vòng lặp cho phép tám lần nhập.

Bảng thông tin `.rela.plt` chỉ ra vị trí của bảng GOT. Vì chương trình chỉ biên dịch với Partial RELRO, các địa chỉ hàm trong bảng GOT hoàn toàn có thể bị ghi đè:

```
0x4000 puts   0x4008 __stack_chk_fail   0x4010 printf   0x4018 fgets   0x4020 setvbuf
```

## Lời giải

### Bước 1: Khảo sát và định vị stack

gửi thử chuỗi định dạng `%1$p %2$p ...` để phân tích bộ nhớ. Kết quả trả về cho thấy tham số ở vị trí số 8 (slot 8) trỏ chính xác vào 8 byte đầu tiên của chuỗi đầu vào (`0x2432252070243125` tương đương với chuỗi `"%1$p %2$"`). Điều này khẳng định vùng tham số biến đổi (varargs) bắt đầu ngay tại vùng đệm đầu vào: tham số thứ `k` sẽ tương ứng với con trỏ lưu tại `buf[8*(k-8)]`. Nhờ đó, ta hoàn toàn có thể đọc hoặc ghi tùy ý vào bất kỳ địa chỉ nào bằng cách đặt trực tiếp địa chỉ đó vào `buf` và sử dụng các chỉ thị như `%k$s` để đọc, hoặc `%k$hhn` để ghi.

Tiếp tục quét các giá trị trên stack ở các vị trí nằm ngoài `buf`. Hai lần quét độc lập cho ra những kết quả nhất quán, minh chứng cho sự ổn định của vùng nhớ này:

```
40 0x7fffa7bb40e0 (stack)   41 0x2ef1945964c7bb00 (canary)   42 0x7fffa7bb4160 (stack)
47 0x60de6e4031c9           52 0x60de6e405db8
```
Giá trị ở slot 47 có 12 bit thấp `0x1c9`, khớp offset `main` là `0x11c9`. Tính PIE base bằng giá trị slot 47 trừ `0x11c9`, rồi kiểm tra kết quả căn trang `0x1000` và đối chiếu leak tiếp theo.

### Bước 2: Trích xuất địa chỉ thư viện libc thông qua GOT

Không cần phải dò đoán ý nghĩa của các con trỏ nằm ở những slot đầu tiên (các slot 1-7 chỉ chứa giá trị tàn dư trong thanh ghi và không ổn định). Thay vào đó, mục tiêu lý tưởng nhất là đọc trực tiếp từ bảng GOT: hàm `printf` đã được gọi ít nhất một lần để in dấu nhắc lệnh, do đó mục `printf@GOT` đã được phân giải thành địa chỉ thực tế trong bộ nhớ libc.

Để đọc địa chỉ này, ta thiết kế một chuỗi format đặc biệt. Phần tiền tố (prefix) cần dài chính xác 8 byte để đẩy địa chỉ cần đọc vào khối 8 byte thứ hai (tức là `buf[8:16]`), tương ứng với slot 9:

```
"%9$s" + "AAAA" + p64(base + 0x4010)
```

Chỉ thị `%9$s` sẽ in ra 6 byte giá trị của con trỏ và dừng lại (do 2 byte cao nhất là ký tự NUL). Từ đó, địa chỉ cơ sở của thư viện libc được xác định bằng công thức `libc_base = ptr - 0x600f0`.

Để xác thực con số này, một phép thử được thực hiện bằng cách đọc dữ liệu tại `libc_base + 0x1cb42f`, nơi chứa chuỗi `/bin/sh` cố định trong thư viện. Nếu phép toán base sai, bước này sẽ thất bại và chuỗi khai thác tự động dừng lại, tránh việc tiếp tục tấn công một cách mù quáng vào các vùng nhớ không hợp lệ.

### Bước 3: Ghi đè bảng GOT

Tra cứu trong thư viện libc, ta có `printf = 0x600f0` và `system = 0x58740`. Khoảng cách giữa hai hàm này chỉ là `0x79b0` (nhỏ hơn 16 MB). Điều này có nghĩa là 3 byte cao của hai địa chỉ này hoàn toàn giống nhau, và bảng GOT hiện tại đã chứa sẵn 3 byte cao chính xác đó. Nhờ vậy, ta chỉ cần ghi đè 3 byte thấp của địa chỉ thay vì phải ghi lại toàn bộ 8 byte:

```
Dùng %hhn ghi vào base+0x4010, base+0x4011, base+0x4012 các giá trị tương ứng với 3 byte thấp của hàm system.
```

Một bộ dựng chuỗi format tự động sẽ đảm nhiệm việc tính toán delta cho từng byte (`d = (giá trị mong muốn - số ký tự đã in) mod 256`), sắp xếp các địa chỉ đích theo thứ tự tăng dần của giá trị cần ghi để tránh tình trạng tràn số đếm, và cuối cùng đệm thêm các ký tự rác để đảm bảo ba địa chỉ đích nằm gàng tại các slot 13, 14 và 15.
Bộ dựng này được kiểm chứng bằng cách mô phỏng kỹ thuật printf với 500 bộ ba byte ngẫu nhiên, kết quả cho thấy cả 500 trường hợp đều được ghi vào bộ nhớ chính xác (`analysis/selftest_fmt.py`).

### Bước 4: Gọi shell hệ thống

Sau khi mục `printf@GOT` bị ghi đè thành địa chỉ của hàm `system`, mọi lời gọi `printf(buf)` tiếp theo trong vòng lặp sẽ trở thành `system(buf)`. Lúc này, ta chỉ cần gửi chuỗi `/bin/sh` làm đầu vào, nó sẽ trở thành tham số đầu tiên truyền cho lệnh system.

```
uid=1337(mad_libs) gid=1337(mad_libs)
/ctf/flag.txt:  -rw-r----- 1 root mad_libs 27
```

## Kết quả
```
sun{f1ll_iN_th3_g0T_eNtry}
```

```bash
python exploit.py                  # Chế độ mặc định: chạy ls -l /ctf; cat /ctf/*; env | grep -i flag
python exploit.py 'cat /ctf/flag.txt'
python analysis/selftest_fmt.py    # Chạy mô phỏng printf để kiểm tra độ tin cậy của bộ dựng %hhn
```

Cờ nằm trong file `/ctf/flag.txt` (độ dài 27 byte, thuộc quyền sở hữu `root:mad_libs` với chế độ quyền `-rw-r-----`). Exploit script được viết hoàn toàn bằng thư viện tiêu chuẩn (stdlib), tự động kết nối đến `chal.sunshinectf.games:26001`, tự dò tìm PIE base mỗi lần chạy (giới hạn 5 lượt thử), tự xác minh `libc_base` bằng cách đối chiếu chuỗi `/bin/sh` trước khi can thiệp vào GOT, và tự động trích xuất nội dung `flag.txt` khi nhận diện được chuỗi cờ trong kết quả trả về.
