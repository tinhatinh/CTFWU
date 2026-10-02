# Manifest Destiny - Pwn (Medium)

**Flag:** `H7CTF{a2b24085-c670-4a87-93cb-293cfec6196c}`

## Đề bài

Hệ thống mô phỏng môi trường Terminal của tập đoàn Sparrow Freight, quản lý các bản kê khai hàng hoá (manifest) và được giới hạn truy cập cho tài khoản admin. Trong kịch bản, người chơi đóng vai trò một người dùng thông thường. Tuy nhiên, hệ thống thiết kế tính năng tiếp nhận ý kiến phản hồi (feedback) và hiển thị trực tiếp dữ liệu này.
Mục tiêu là khai thác hệ thống, nâng cấp đặc quyền (privilege escalation) lên mức "management" (quản lý) để truy cập tài liệu mật manifest.

## Phân tích ban đầu

Giải nén tệp `manifest.zip`, trích xuất tệp thực thi chính (binary), cùng thư viện `libc.so.6` (phiên bản glibc 2.39, môi trường Ubuntu 24.04) và trình nạp (loader) đi kèm.
Phân tích thông tin tập tin bằng công cụ `scripts/triage.cjs`:

```text
Định dạng: ELF 64-bit, type=ET_EXEC (Địa chỉ cố định, không PIE), trình nạp interpreter=/lib64/ld-linux-x86-64.so.2
Chế độ: PIE=no (tắt)  RELRO=yes (bật)  STACK=non-exec (Bảo vệ cấm thực thi bộ nhớ NX: bật)
Từ khóa phát hiện: admin
```

Thông tin đáng chú ý nhất trong báo cáo phân tích là chế độ `no PIE` (Position Independent Executable bị tắt): Biến cấu hình phân quyền được đặt tại một địa chỉ cố định. Vì vậy, để chiếm quyền hệ thống thông qua lỗ hổng Format String, chỉ cần một lệnh ghi (write) duy nhất - không cần rò rỉ (leak) bộ nhớ hoặc sử dụng kỹ thuật nhảy ROP.

Phân tích 3 khối hàm chức năng:

```c
Hàm main:      Đọc đầu vào fgets(16) -> sử dụng atoi;  Lựa chọn 1 -> Gọi hàm feedback(), Lựa chọn 2 -> Gọi hàm view_manifest(), Lựa chọn khác -> Return.
Hàm feedback:  Khởi tạo biến cục bộ char buf[] tại toạ độ rbp-0xd0; Gọi lệnh xoá memset; Lấy dữ liệu read(0, buf, 0xc7);
               In ra màn hình printf("You said: ");  Tiếp tục gọi printf(buf);      <-- Lỗ hổng Format String rõ ràng nằm ở đây.
Hàm view_manifest:
               Lệnh kiểm duyệt if (!is_admin) in ra puts("[!] admin clearance required.");
               Ngược lại (nếu qua ải) thì gọi fopen(flag_file,"r"); Lấy fgets(128); Hiển thị cờ printf("[manifest] clearance code: %s", buf);
```

Mục tiêu: Cập nhật biến cờ `is_admin` định dạng `DWORD`, đặt tại địa chỉ `0x40407c` (phân đoạn bộ nhớ `.bss`).

Phân tích cấu trúc không gian ngăn xếp (layout): Khi hàm `feedback` được gọi, nó thực hiện các lệnh: `push rbp; mov rbp,rsp; sub rsp,0xd0`. Quá trình này cấp phát bộ đệm `buf` nằm tại đỉnh stack `rsp`. 
Khi hệ thống chạy lệnh `call printf`, theo quy ước ABI, 6 đối số (parameter) đầu tiên được truyền qua thanh ghi (`rdi` chứa chuỗi định dạng; `rsi/rdx/rcx/r8/r9` chứa các vararg từ 1 đến 5). Từ đối số vararg thứ 6, dữ liệu được truyền qua stack (nằm tại địa chỉ trả về return address) - chính xác tại địa chỉ `buf+0`.

Từ cấu trúc này, xác định 2 toạ độ bộ nhớ (offset):
- Vị trí `buf+0` tương ứng với đối số định dạng thứ 6 (Mã cấu trúc: `%6$`)
- Vị trí `buf+8` tương ứng với đối số định dạng thứ 7 (Mã cấu trúc: `%7$`)

## Quá trình khai thác

**Bước 1 - Xác định địa chỉ để định vị bộ đệm buffer.** 
Nhập chuỗi kiểm tra `MARKER-%6$p-%7$p-...` vào hệ thống:

```text
Hệ thống trả về: You said: MARKER-0x252d52454b52414d-0x702437252d702436-...
```

Giải mã khối hex `0x252d52454b52414d` theo quy tắc little-endian, chuỗi trả về gồm 8 ký tự `"MARKER-%"`. Kết quả xác nhận rõ ràng: toạ độ `buf+0` chính xác với tham số offset thứ 6. Phương pháp này giảm thiểu rủi ro khi xác định offset.

**Bước 2 - Chuẩn bị: Đặt địa chỉ mục tiêu vào `buf+8` và thực thi lệnh ghi `%7$n`.**

Cấu trúc payload gồm 16 byte:

```text
Khối độn ("CCCC")  +  Khối thực thi ("%7$n")  +  Địa chỉ p64(0x40407c)
Khoảng: 0..3             Khoảng: 4..7                Khoảng: 8..15
```

**Bước 3 - Lỗi phát sinh: Hàm `%n` ghi giá trị 0.** 
Ở lần thử đầu tiên, khối kích hoạt `%7$n` được đặt ở đầu buffer (Dạng: `"%7$n" + b"AA" + địa_chỉ`). Quá trình không gây lỗi hệ thống (không crash), nhưng biến `is_admin` không thay đổi, hệ thống từ chối truy cập manifest. 
Nguyên nhân của vấn đề bao gồm hai điểm quan trọng:

- Lệnh định dạng `%n` ghi TỔNG SỐ KÝ TỰ đã được lệnh in hiển thị tới thời điểm nó được gọi. Do đặt ở đầu chuỗi, số ký tự đếm được là 0.
- Ngoài ra, phần đệm `b"AA"` (độ dài 2 byte) đã làm sai lệch vị trí địa chỉ, đẩy nó sang offset số 6 thay vì số 8, làm lệch toạ độ `buf+8`.

Phương án điều chỉnh: Đảo ngược cấu trúc. Nhập 4 ký tự đệm (có thể in được, như `CCCC`) ở đầu payload; chuyển khối thực thi `%7$n` sang vị trí offset 4-7. Cấu trúc này đảm bảo địa chỉ mục tiêu nằm đúng tại toạ độ `buf+8`. Khi `%n` thực thi, nó ghi nhận 4 ký tự đệm và ghi giá trị 4 vào bộ nhớ - giá trị lớn hơn 0, đáp ứng điều kiện vòng kiểm duyệt `test eax,eax`.

**Bước 4 - Khai thác quyền hệ thống và đọc Manifest.** 
Thực thi nhánh menu số `2`:

```text
[manifest] clearance code: H7CTF{a2b24085-c670-4a87-93cb-293cfec6196c}
```

## Flag
```bash
python exploit.py pwn.h7tex.com 42506
```

Nhật ký hệ thống:
```text
[*] Hệ thống yêu cầu: Leave feedback for the terminal operators:
[*] Bắn vọng lại: b'You said: CCCC|@@\n\n1) leave feedback\n...'
[*] Trích xuất manifest: [manifest] clearance code: H7CTF{a2b24085-c670-4a87-93cb-293cfec6196c}
[+] FLAG: H7CTF{a2b24085-c670-4a87-93cb-293cfec6196c}
```
