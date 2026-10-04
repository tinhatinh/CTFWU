# Epic Rat Encoding - Reverse (498 points)

**Flag:** `cdctf{Tom_Bevill_Building_at_noon_next_week_Thursday}`
**Files:** `files/message_encoder.c`, 360 byte, sha256 `738e4cbaa71cc9a48260ed6130718c04f66d910582a10d4760fc27466deb2734` · `files/nums.txt`, 160 byte, sha256 `188ff63f2326345e495fffc6b2199384b87c021d92489a027354fe4d4f9085b5`
**Event:** CDCTF 2026 (Crimson Defense CTF) · **Tác giả:** alex

## Đề bài

Đề cho một file `message_encoder.c` và 8 số nguyên kèm theo, nói rằng 8 số đó chứa thông tin
về một buổi gặp bí mật (ở đâu và lúc nào). Trong file C, dòng khởi tạo chuỗi đã bị rút đi
(`char* message = ""; // I think that Ratón deleted this part.`), nên chỉ còn lại hàm mã hoá và
đầu vào là 8 số. Định dạng cờ: `cdctf{Place_Place_Place_at_time_time_time_Time}`.

## Phân tích ban đầu

- `nums[j] += message[i + 8 * j]` chạy 8 lần cho mỗi `j`, và `nums[j] = nums[j] << 8` chỉ chạy khi
  `i != 7`. Không có shift sau byte cuối, do đó byte đầu tiên của chunk được đẩy lên 8 bit cao:
  `nums[j]` là 8 byte `message[8j..8j+7]` đóng gói big-endian trong một `uint64_t`.
- 8 chunk × 8 byte = 64 byte. Định dạng cờ cần `Place_Place_Place` + `at` + 4 token thời gian,
  tức khoảng 47-64 byte, nên đúng 8 số là đủ chứa toàn bộ thông điệp, không thiếu dữ liệu.
- `uint64_t nums[8];` chưa được khởi tạo, nên source C có undefined behavior. Lời giải diễn giải tám số đã cho thành byte big-endian; khi dựng encoder để đối chiếu cần khởi tạo mảng bằng 0.

## Các hướng đã loại

1. **`+=` là phép cộng số học thuần tuý** (mỗi `nums[j]` chỉ là tổng 8 byte, thông tin bị mất):
   nếu đúng thì 8 số chỉ mang khoảng 8 bit mỗi số, không thể dựng lại 61 ký tự. Cách hiểu đóng
   gói byte cho ra ASCII trọn nghĩa ngay lần giải đầu tiên, nên loại.
2. **Đoạn encoder tự dựng để đối chứng in ra số sai**: bản chạy trên Windows dùng `printf("%lu")`
   cho `uint64_t` chỉ in ra 32 bit thấp (LLP64, `long` 4 byte), biểu hiện là 8 token 10 chữ số và
   giải mã ra toàn dấu chấm xen kẽ chữ. Thêm `-D__USE_MINGW_ANSI_STDIO=1` và in bằng `%llu` thì
   số quay lại đúng 19-20 chữ số như đề. Đây là bẫy của môi trường dựng, không phải của bài.

## Chuỗi khai thác

**Bước 1 - Đổi mỗi số về 8 byte big-endian và nối lại.** Không có khoá, không có phép biến đổi
nào ngoài đúng một phép đóng gói.

```python
nums = [int(t) for t in open("files/nums.txt").read().split()]
raw = b"".join(n.to_bytes(8, "big") for n in nums)
print("".join(chr(b) if 32 <= b < 127 else "." for b in raw))
```

```text
[*] 8 so -> 64 byte
[*] hex      : 4d656574206d652061742074686520546f6d20426576696c6c204275696c64696e67206174206e6f6f6e206e657874207765656b20546875727364617900256c
[*] printable: Meet me at the Tom Bevill Building at noon next week Thursday.%l
[*] byte sau NUL: 256c = %l (duoi cua chuoi format "%lu " trong binary)
[+] message (61 ky tu): Meet me at the Tom Bevill Building at noon next week Thursday
[+] flag      : cdctf{Tom_Bevill_Building_at_noon_next_week_Thursday}
[+] round-trip: re-encode bang vong lap C khop ca 8 so
```

**Bước 2 - Ghép cờ theo đúng khuôn.** `Meet me at the ` là phần mở đầu thông điệp, không thuộc giá trị cần nộp; `Place_Place_Place` tương ứng
`Tom_Bevill_Building`, `at` giữ nguyên, bốn token cuối `time_time_time_Time` tương ứng
`noon_next_week_Thursday` (token cuối in hoa, khớp `Thursday`).

**Bước 3 - Kiểm chứng bằng cách chạy lại encoder.** Điền chuỗi tìm được vào đúng vòng lặp C rồi
biên dịch; đầu ra phải khớp cả 8 số của đề, không chỉ khớp từng ký tự đọc được.

```bash
gcc -O0 -D__USE_MINGW_ANSI_STDIO=1 -o analysis/encoder_reconstructed.exe analysis/encoder_reconstructed.c
./analysis/encoder_reconstructed.exe
```

```text
5576975263002879264 7022273403317198932 8029109180213651820 7791300427398276201 7955362869705469551 8029390844169057312 8603394173939509365 8247045712450168172
nums.txt          : [5576975263002879264, 7022273403317198932, 8029109180213651820, 7791300427398276201, 7955362869705469551, 8029390844169057312, 8603394173939509365, 8247045712450168172]
re-encode         : [5576975263002879264, 7022273403317198932, 8029109180213651820, 7791300427398276201, 7955362869705469551, 8029390844169057312, 8603394173939509365, 8247045712450168172]
identical         : True
```

Hai byte cuối giải mã thành `0x25 0x6c` = `%l`, giống đầu chuỗi format `"%lu "`. Vòng lặp đọc 64 byte trong khi thông điệp có 61 ký tự và NUL, nên có thể đọc vượt chuỗi. Không thể xác định vị trí các byte này trong bộ nhớ chỉ từ source và tám số đã cho.

## Flag

```text
cdctf{Tom_Bevill_Building_at_noon_next_week_Thursday}
```

## Reproduce

```bash
python exploit.py files/nums.txt
```

Đối chứng lại bằng chính encoder:

```bash
gcc -O0 -D__USE_MINGW_ANSI_STDIO=1 -o analysis/encoder_reconstructed.exe analysis/encoder_reconstructed.c
./analysis/encoder_reconstructed.exe
```

Không có key riêng tư hay thông tin instance trong script.
