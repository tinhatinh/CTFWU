# Safe House - Pwn (Hard)

**Flag:** `sun{n3gat1ve_h4ndl3s_0pen_s3cret_d00rs}`
**Tác giả:** Oreomeister
**Target:** `nc chal.sunshinectf.games 26007` · **Files:** `service` (18504 B, sha256 `40c8993c1a853f62...`)

## Đề bài

> "Safe house nhận báo cáo và lưu note cho thực địa. Vượt qua quầy lễ tân để vào hầm." 

Bài cung cấp một cờ duy nhất.

## Phân tích ban đầu

Tệp thực thi là một ELF kiến trúc x86-64, không sử dụng cơ chế bảo vệ địa chỉ (no PIE), được kích hoạt NX, hoàn toàn vắng bóng stack canary ở các hàm nằm trên đường dẫn của chuỗi ROP. GNU_RELRO bao phủ toàn bộ vùng `.got` (nghĩa là không thể thực hiện thủ thuật ghi đè GOT), và binary đã bị loại bỏ thông tin gỡ lỗi (stripped). 

Mô hình dịch vụ được thiết kế với hai tiến trình liên lạc với nhau thông qua một cặp socket (socketpair); trong đó, chỉ có tiến trình cha mới trực tiếp nhận đầu vào (input) từ phía người chơi.

## Kiến trúc phần mềm

Quá trình khởi tạo trong hàm `main` tại `0x401290`:

1. Thiết lập giao tiếp: Khởi tạo kênh nối `socketpair(AF_UNIX, SOCK_STREAM, 0, sv)`.
2. Sinh khoá bảo mật: Tạo khoá mã hoá `key = prng(getpid())` (với hạt giống hằng số `0x45d9f3b` qua hai bước dịch chuyển XOR-shift), sau đó lưu tại địa chỉ `0x405060`. Đây là khoá XOR duy nhất áp dụng cho mọi bản tin trao đổi giữa tiến trình cha và con. Khoá này sẽ thay đổi qua mỗi lần kết nối nhưng giữ nguyên trong suốt vòng đời của một tiến trình.
3. Rẽ nhánh bằng `fork()`:
   - **Tiến trình cha (Front Desk):** Gán socket bằng `dup2(sv[0], 3)`, thiết lập quy tắc bảo mật seccomp cực kỳ nghiêm ngặt (`PR_SET_NO_NEW_PRIVS` kèm theo `seccomp(2)` chứa 21 lệnh BPF). Sau đó, nó đi vào vòng lặp vô tận, đọc từng byte từ `stdin` cho đến khi gặp ký tự xuống dòng `\n` vào một vùng đệm 1024 byte, rồi tiến hành so khớp 4 byte lệnh cơ bản: `PING`, `HELP`, `NOTE`, `RELAY`, `SUBMIT`, `QUIT`.
   - **Tiến trình con (Vault):** Gán socket qua `dup2(sv[1], 3)`. Nó mở tệp rỗng `/dev/null` rồi ánh xạ đè lên hai luồng tiêu chuẩn 0 (stdin) và 1 (stdout) qua `dup2`, đồng thời phớt lờ tín hiệu đứt gãy đường truyền `signal(SIGPIPE, SIG_IGN)`. Trọng tâm nhất, nó mở trực tiếp tệp `flag.txt` và ghi cấu trúc `{state=2, fd}` vào một bảng hệ thống nằm tại `0x405080`. Mỗi mục trong bảng này dài 0x40c byte; toàn bộ các phần tử còn lại phía sau đều mặc định trỏ về `/dev/null`. Tiến trình Vault hoàn toàn không bị áp đặt bất kỳ quy tắc seccomp nào.
4. Hàm mã hoá `0x401be0(buf, len, edx=key)`: Nhiệm vụ XOR dữ liệu với 4 byte khoá được mã hoá theo định dạng big-endian, lặp lại theo chu kỳ 4 byte.
5. Hàm gửi dữ liệu `0x401d50(edi=kênh, rsi=data, edx=len)`: Xây dựng một phần đầu bản tin (header) với cấu trúc `[kênh][len_be16][0]`, áp dụng phép XOR, đẩy `write(3, header, 4)` lên luồng, rồi tiếp tục copy, mã hoá XOR và ghi `write(3, payload, len)`. Hàm tiện ích này được gọi từ cả hai phía nhờ vào việc nó chỉ thao tác độc lập trên mô tả tệp (file descriptor) số 3.

Tập hợp lệnh của Front Desk bao gồm: 
- `NOTE <0..7> <text>`: Ghi chú thông tin vào bảng tại `0x40a180` (mỗi mục cấp 0x40 byte, hàm `strncpy` giới hạn copy tối đa 0x3f byte).
- `RELAY <1..4>`: Điều hướng về địa chỉ `0x401f70`.
- `SUBMIT <size>`: Điều hướng về địa chỉ `0x401ed0`.

Đặc điểm của giao thức AF_UNIX kết hợp kiểu `SOCK_STREAM` là truyền dữ liệu dạng chuỗi byte thuần túy, không giữ lại ranh giới giữa các bản tin (record boundary). Nhờ vậy, một lệnh `read(3, buf, n)` đơn lẻ hoàn toàn có khả năng lấy được đồng thời cả header lẫn nội dung tải trọng (payload) của câu trả lời.

## Hai lỗ hổng định mệnh

**1. Tràn bộ đệm stack tại Front Desk (`0x401ed0`, trình xử lý lệnh `SUBMIT`)**

```asm
strtol(size); bl = size & 0xff
if (bl) { write(1,"GO\n",3); read(0, rsp, bl); write(1,"OK\n",3); }
add rsp,0x40; pop rbx; ret
```

Khuôn bộ nhớ (frame) được cấp phát là `sub rsp,0x40` tương đương 64 byte, khiến địa chỉ trả về (return address) bị đặt ở độ lệch 0x48. Tuy nhiên, hàm `read` lại sẵn sàng tiếp nhận lên tới 255 byte dữ liệu mà không hề bị stack canary cản trở. Khả năng tấn công ROP mở ra ngay trước mắt, nhưng rào cản là binary đã bật cả NX lẫn GNU_RELRO nên không thể áp dụng thủ thuật ghi đè bảng GOT. Mọi thứ trở nên gian nan hơn khi kho ROP gadget trong vùng `.text` quá đỗi nghèo nàn: chỉ tồn tại lác đác `pop rdi` và `pop rsi`, hoàn toàn vắng bóng các gadget tối quan trọng như `pop rdx`, `syscall`, hay bất kỳ lệnh nào can thiệp được vào con trỏ stack `rsp`.

**2. Lỗi chỉ số mảng âm tại Vault (`0x4019c0`, thao tác xử lý mã 3)**

```c
if (len <= 3) -> "short"
idx = *(int32*)data            // Phép dịch movsxd CHẤP NHẬN SỐ ÂM
if (idx > 15) -> "range"       // Chỉ chặn giới hạn cận trên
e = 0x4060b0 + idx*0x40c
if (e.state == 2) { pread(e.fd, buf, 0x400, 0); trả kết quả về fd 3 }
```

Gốc toạ độ `0x4060b0` thực chất trỏ vào phần tử thứ 4 của bảng quản lý fd. Điều kỳ diệu xảy ra khi truyền vào `idx = -4`, con trỏ sẽ lùi thẳng về đúng vị trí `0x405080` – tức là lấy chính xác phần tử điều khiển tệp `flag.txt`. Lỗ hổng nghiêm trọng này cấp quyền đọc trực tiếp cờ từ hệ thống tệp tin, với điều kiện duy nhất là ta phải chạm được vào bộ máy bên trong tiến trình Vault. Tuy nhiên, lệnh `write` trả về kết quả cho ta lại đòi hỏi thanh ghi `rdx` phải đóng vai trò là tham số quyết định chiều dài dữ liệu.

## Chuỗi khai thác

**Bước 1 - Sử dụng gadget từ nhánh báo lỗi.** 
Nếu điều kiện `size & 0xff == 0` xảy ra, trình xử lý lập tức in `"ERR bad size\n"` (thông qua `mov edx,0xd`) rồi thực thi lệnh ret. Khi đó, luồng chạy không hề gọi `read` và cũng không báo `"OK\n"`, dẫn đến thanh ghi `rdx` được cố định một cách khéo léo thành giá trị `13` tại thời điểm lệnh ret kích hoạt. Để tạo ra số 0 hoàn hảo đó, chuỗi `"256"` được lồng vào bộ nhớ NOTE nhằm đảm bảo phép tính `bl = 0`.

**Bước 2 - Bố trí mìn dữ liệu.** 
Cài cắm lệnh `NOTE 0 = int32(-4)` (vì dãy số này không chứa bất kỳ byte null 0 nào, hàm `strncpy` sẽ sao chép trọn vẹn), đồng thời thiết lập `NOTE 3 = "256"`.

**Bước 3 - Thi công chuỗi ROP.** 
Mỗi vòng lặp là một lời gọi `SUBMIT 255` đi kèm với đoạn mã tải trọng chính xác 255 byte (`bl` vừa đóng vai trò thanh ghi `rdx`, vừa là giới hạn số byte lệnh `read` sẽ nuốt vào tải trọng, do đó kích thước tải trọng bắt buộc phải bằng đúng biến `bl`):

```text
pad(0x48)
pop rdi -> NOTE3("256") ; 0x401ed0                 # ghim cứng rdx = 13
[vòng đầu] pop rdi=3 ; pop rsi=NOTE0 ; 0x401d50    # gửi lệnh: op=3, len=13, data=int32(-4)
pop rdi=3 ; pop rsi=REPLY ; read@plt               # rút dữ liệu: read(3, REPLY, 13)
pop rdi=1 ; pop rsi=REPLY ; write@plt              # đẩy dữ liệu: write(1, REPLY, 13) -> đổ thẳng ra socket của ta
0x4014d0                                           # luân chuyển về màn hình nhắc lệnh
```

Vòng lặp đầu tiên sẽ rút thành công 13 byte khởi đầu; các vòng lặp tiếp theo kiên trì rút phần còn lại. Chỉ cần chạy đúng 4 vòng, ta đã thu hoạch trọn vẹn 4 byte header kết hợp với 40 byte payload.

**Bước 4 - Phá mã (decrypt) ngoại tuyến.** 
Cấu trúc nguyên bản (plaintext) của phần đầu bản tin luôn tuân theo công thức `[00][L>>8][L&0xff][00]`. Do đó, đối với mọi offset và mọi độ dài `L` khả dĩ, ta có thể đảo ngược toán học để tìm ra `key = ct ^ plaintext_suy_đoán`. Khi đã nắm trong tay khoá, phần việc còn lại chỉ là giải mã toàn bộ khối dữ liệu và rà quét chuỗi `sun{`. Toàn bộ thao tác này không hề đòi hỏi phải biết trước giá trị PID của tiến trình trên server.

```bash
$ python -u exploit4.py -4
[+] key=23b2f0a0  L=40
[+] b'sun{n3gat1ve_h4ndl3s_0pen_s3cret_d00rs}\n'
[+] CO: sun{n3gat1ve_h4ndl3s_0pen_s3cret_d00rs}
```

**Bước 5 - Kiểm chứng độ tin cậy.** 
Kịch bản khai thác đã được chạy lại 3 lần độc lập qua 3 kết nối hoàn toàn khác nhau. Mỗi lần sinh ra một khoá bảo mật riêng biệt nhưng vẫn luôn đánh cắp thành công và cùng trả về một lá cờ duy nhất.

## Flag
```
sun{n3gat1ve_h4ndl3s_0pen_s3cret_d00rs}
```
