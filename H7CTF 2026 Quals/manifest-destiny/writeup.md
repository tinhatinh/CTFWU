# Manifest Destiny — Pwn (Medium)

**Flag:** `H7CTF{a2b24085-c670-4a87-93cb-293cfec6196c}`

## Đề bài

Hệ thống cung cấp một điểm truy cập Terminal của tập đoàn Sparrow Freight, nơi quản lý các bản kê khai hàng hoá (manifest) và được bảo vệ ngặt nghèo dưới đặc quyền admin. Trong bối cảnh này, người chơi chỉ là một khách vãng lai rảnh rỗi. Thế nhưng, hệ thống terminal này có một tính năng thú vị: nó "rất thích lắng nghe góp ý (feedback) và lưu tâm đến từng lời bạn nói".
Mục tiêu là phải tìm cách bẻ cong hệ thống, nâng cấp đặc quyền (privilege escalation) lên mức "management" (quản lý) để đàng hoàng đọc được tài liệu mật manifest.

## Phân tích ban đầu

Đập hộp file `manifest.zip`, ta gom được tệp thực thi chính (binary), kèm đúng thư viện `libc.so.6` (phiên bản glibc 2.39, chạy trên Ubuntu 24.04) và trình nạp (loader) tương ứng.
Phác hoạ hiện trường bằng công cụ `scripts/triage.cjs`:

```text
Định dạng: ELF 64-bit, type=ET_EXEC (Đứng im tại chỗ, không PIE), trình nạp interpreter=/lib64/ld-linux-x86-64.so.2
Chế độ: PIE=no (tắt)  RELRO=yes (bật)  STACK=non-exec (Bảo vệ cấm thực thi bộ nhớ NX: bật)
Từ khóa phát hiện: admin
```

Điểm sáng chói loá nhất trong kết quả phân tích là chế độ `no PIE` (Position Independent Executable bị tắt): Biến quản lý phân quyền được ghim chết tại một địa chỉ bất di bất dịch. Nghĩa là, muốn hạ gục hệ thống thông qua lỗi Format String (chuỗi định dạng), ta chỉ cần tung ra đúng một đòn ghi bộ nhớ (write) là xong - dẹp luôn khỏi cần mưu hèn kế bẩn đi rò rỉ (leak) bộ nhớ hay vọc vạch kỹ thuật nhảy ROP.

Phẫu thuật 3 khối hàm chủ lực:

```c
Hàm main:      Lấy đầu vào fgets(16) -> biến qua atoi;  Gõ số 1 -> Đẩy vào hàm feedback(), Gõ số 2 -> Đẩy vào hàm view_manifest(), Gõ thứ khác -> Return.
Hàm feedback:  Tạo khoảng trống char buf[] tại toạ độ rbp-0xd0; Gọi lệnh xoá memset; Nuốt dữ liệu read(0, buf, 0xc7);
               In ra màn hình printf("You said: ");  Tiếp tục gọi printf(buf);      <-- Điểm huyệt (lỗ hổng Format String) rành rành nằm ở đây.
Hàm view_manifest:
               Lệnh kiểm duyệt if (!is_admin) in ra puts("[!] admin clearance required.");
               Ngược lại (nếu qua ải) thì gọi fopen(flag_file,"r"); Lấy fgets(128); Khoe cờ printf("[manifest] clearance code: %s", buf);
```

Mục tiêu săn đuổi: Biến cờ `is_admin` mang kiểu dữ liệu `DWORD`, đóng đô tại địa chỉ `0x40407c` (phân đoạn bộ nhớ `.bss`).

Gỡ băng cấu trúc không gian ngăn xếp (layout): Khi hàm `feedback` kích hoạt, nó triển khai thủ tục mở bài: `push rbp; mov rbp,rsp; sub rsp,0xd0`. Hành động này dán dính cái bộ đệm `buf` vào đúng vị trí của thanh ghi đỉnh stack `rsp`. 
Đến đoạn hệ thống thi hành lệnh `call printf`, theo chuẩn quy tắc, 6 đối số (parameter) đầu tiên sẽ được tuồn qua cửa thanh ghi (Trong đó, `rdi` vác format string; còn `rsi/rdx/rcx/r8/r9` hốt trọn đám vararg từ 1 đến 5). Từ đối số vararg thứ 6 trở đi, dữ liệu buộc phải được moi lên từ stack (nằm vắt vẻo ngay phía trên địa chỉ trả về return address) - tức là trúng phóc cái địa chỉ `buf+0`.

Từ đó ta chốt được 2 toạ độ bắn phá (offset):
- Vị trí `buf+0` chính là đối số định dạng thứ 6 (Mã kích hoạt: `%6$`)
- Vị trí `buf+8` chính là đối số định dạng thứ 7 (Mã kích hoạt: `%7$`)

## Chuỗi khai thác

**Bước 1 - Nã đạn dò đường (Leak) để chốt toạ độ buffer.** 
Quăng chuỗi đạn thử `MARKER-%6$p-%7$p-...` vào hệ thống:

```text
Hệ thống nôn ra: You said: MARKER-0x252d52454b52414d-0x702437252d702436-...
```

Quay ngược khối mã hex `0x252d52454b52414d` theo quy tắc little-endian, nó hiện hình thành 8 ký tự `"MARKER-%"`. Chứng cứ này xác nhận đanh thép giả thuyết ban đầu: toạ độ `buf+0` quả nhiên ăn khớp với tham số offset thứ 6. Chiêu dò đường rẻ tiền này vứt bỏ mọi sự rủi ro của trò đoán mò offset.

**Bước 2 - Lên nòng: Ghìm địa chỉ mục tiêu vào `buf+8` và kích nổ bằng `%7$n`.**

Chế tạo viên đạn payload vỏn vẹn 16 byte:

```text
Khối độn ("CCCC")  +  Khối kích nổ ("%7$n")  +  Đầu đạn p64(0x40407c)
Khoảng: 0..3             Khoảng: 4..7                Khoảng: 8..15
```

**Bước 3 - Vấp cỏ: Hàm `%n` lại đi ghi số 0.** 
Trong phát bắn nháp đầu tiên, ta đặt khối kích nổ `%7$n` chặn ngay lối vào của buffer (Dạng: `"%7$n" + b"AA" + địa_chỉ`). Quả đạn không xịt (không crash), nhưng biến `is_admin` thì vẫn trơ gan nằm ở số 0, và bộ manifest vẫn lạnh lùng từ chối. 
Căn nguyên của cú vấp này là do 2 yếu tố chết người:

- Bản chất của hàm định dạng `%n` là ghi lại TỔNG SỐ KÝ TỰ đã được lệnh in khạc ra màn hình tính tới thời điểm nó được gọi. Bố trí nó chễm chệ ngay đầu dòng thì số lượng ký tự đếm được chỉ là con số 0.
- Tai hại hơn, phần đệm `b"AA"` (dài 2 byte) đã xô đẩy cái đầu đạn địa chỉ trượt sang offset số 6 thay vì số 8, làm nó chệch hoàn toàn khỏi toạ độ `buf+8`.

Phương án sửa sai: Lộn ngược thứ tự cấu trúc. Ta ném 4 ký tự mồi (chữ in được, ở đây dùng `CCCC`) lên tuyến đầu; dồn khối kích nổ `%7$n` tụt về offset 4-7. Cách dàn trận này ép đầu đạn địa chỉ rơi chuẩn không cần chỉnh vào toạ độ `buf+8`. Khi quả nổ `%n` được kích, nó sẽ gom nhặt 4 ký tự mồi phía trước để nén vào bộ nhớ giá trị là 4 - một con số lớn hơn 0, dư sức qua ải lệnh kiểm duyệt `test eax,eax`.

**Bước 4 - Bẻ khoá và Đọc Manifest.** 
Chỉ việc nhẹ nhàng chọn nhánh menu số `2`:

```text
[manifest] clearance code: H7CTF{a2b24085-c670-4a87-93cb-293cfec6196c}
```

## Flag
```bash
python exploit.py pwn.h7tex.com 42506
```

Nhật ký chiến trường:
```text
[*] Máy chủ thả mồi: Leave feedback for the terminal operators:
[*] Bắn vọng lại: b'You said: CCCC|@@\n\n1) leave feedback\n...'
[*] Trích xuất manifest: [manifest] clearance code: H7CTF{a2b24085-c670-4a87-93cb-293cfec6196c}
[+] FLAG: H7CTF{a2b24085-c670-4a87-93cb-293cfec6196c}
```
