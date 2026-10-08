# Dog Whistle - Hardware (Insane)

**Flag:** `H7CTF{3c48f268-6761-422b-9df0-e652f6b2c4d0}`
**Dịch vụ mạng:** `nc pwn.h7tex.com 40918`
**Files cung cấp:** `dog_whistle.zip` (chứa firmware `aria` phiên bản r7.2).

## Đề bài

Hệ thống điều khiển một loa thông minh nhận lệnh qua sóng âm thanh, sử dụng firmware `aria` r7.2. Để kích hoạt các lệnh kỹ thuật ẩn (engineering commands), cần vượt qua "bộ quét phổ âm thanh" hoạt động trong dải tần hẹp 300 - 3400 Hz. Yêu cầu của thử thách là vượt qua cơ chế bảo vệ này và trích xuất cờ từ hệ thống.

## Phân tích

Hệ thống phòng vệ (Guard) không đơn thuần là một bộ lọc âm (filter). Nó là một bộ giải mã độc lập, phân tích tín hiệu *trước* khi tín hiệu đi qua bộ khuyếch đại phi tuyến (non-linear amplifier). Trong khi đó, bộ giải mã chính của hệ thống lại xử lý tín hiệu *sau* khâu phi tuyến.
Phương pháp khai thác: Truyền lệnh bằng tín hiệu phái sinh (tone hiệu) tạo từ hai sóng mang tần số cao 4 - 6 kHz. Ở giai đoạn gốc, tín hiệu không nằm trong dải tần số thấp nên vượt qua được Guard. Khi qua khâu phi tuyến, hiện tượng méo tín hiệu sẽ tạo ra các khung lệnh ở tần số thấp để bộ giải mã chính xử lý. Cơ chế này hoạt động tương tự hiện tượng "dog whistle" (âm thanh chỉ chó nghe được).

| File đính kèm | Vai trò |
|---|---|
| `aria` | Binary ELF x86-64, biên dịch PIE, stripped, kích thước 18 KB, liên kết động. |
| `SPEC.md` | Tài liệu đặc tả kỹ thuật truyền tải, mô đun mạng (modem) và cấu trúc gói tin TLV. |
| `eq.cfg` | File cấu hình bộ cân bằng âm thanh 8 dải (8 band), với mức tăng 0 dB (flat). |
| `reference_ping.wav` | File âm thanh mẫu (24-bit/96 kHz mono), dài 15.168 mẫu, giải mã ra chuỗi `A5 5A 02 10 00 12`. |

Quy trình xử lý âm thanh (phân tích từ `analysis/aria.asm` và tài liệu `frontend_notes.md`):

```text
Chuỗi dữ liệu base64 → Đọc file WAV → 0x1940 Xử lý EQ → 0x2550 Xử lý GUARD → 0x1f70 Xử lý khuyếch đại P(x)
       → 0x1e30 Lọc thông thấp (LPF) 7 kHz + hạ mẫu /6 → 0x2070 Phân tích Goertzel → 0x2790 Xử lý lệnh (dispatch)
```

Tại offset `0x1f70`, bộ khuyếch đại áp dụng công thức phi tuyến:
```text
Đặt u = 4x;   Đầu ra y = 0.98u + 0.05u² + 0.005u³        (Thu gọn ≈ 3.92x + 0.80x² + 0.32x³)
```

Tại `0x2070`, thuật toán Goertzel phân tích 200 mẫu (sample) ở tần số 16 kHz - tương đương một phép biến đổi DFT 200 điểm. Khoảng cách dải tần (bin) là 80 Hz, và 16 tần số điều khiển (phổ `800+80k` Hz) rơi vào các bin từ 10 đến 25.

### Phân tích bộ Guard

Tại đoạn mã `0x2550`, bộ Guard không kiểm tra dải tần giới hạn 300 - 3400 Hz hoặc ngưỡng âm lượng. Thay vào đó, nó tái sử dụng quy trình giải mã `0x1e30` + `0x2070` để phân tích chuỗi TLV. Hệ thống sẽ bị khóa (lockout) nếu phát hiện bản ghi loại `0x01` hoặc `0x02`.

Kiểm thử trên môi trường live:
```text
Truyền payload 01 01 0E bằng âm tần chuẩn -> Hệ thống kích hoạt SAFETY LOCKOUT.
Truyền payload 01 01 0E bằng sóng mang phái sinh -> Hệ thống phản hồi PROFILE SELECTED: vùng 0x0e.
```

## Lời giải

**Bước 1 - Sử dụng sóng mang phái sinh.**
Bộ Guard phân tích tín hiệu gốc `x`, trong khi bộ giải mã chính phân tích tín hiệu méo `P(x)`. Trong công thức méo, thành phần `0.05u²` tạo ra sóng tần số hiệu `cos(2π(f_p−f_q)t)`.
Kỹ thuật: Kết hợp hai sóng mang ở bin `p = 51+B` và `q = 51` (tương đương 4.080 Hz và `(51+B)*80` Hz). Giao thoa tạo ra hiệu số `p−q = B`, rơi vào bin tần số điều khiển. Yêu cầu `B ∈ [10..25]`:

- Tín hiệu `x` truyền vào chỉ chứa năng lượng ở các bin từ 26 trở lên, vuông góc (trực giao) với bin 10 đến 25. Guard phân tích bin điều khiển nhận giá trị 0, dẫn đến giải mã lỗi và không kích hoạt khóa hệ thống.
- Khi qua `P(x)`, tín hiệu tạo ra dải tần điều khiển `p−q` trong khoảng 10..25. Các tần số nhiễu khác đều nằm ngoài dải và bị loại bỏ bởi LPF 7 kHz.
- Việc đặt `q = 51` đảm bảo dải tạp âm `51−B >= 26` (với mọi `B <= 25`), không gây nhiễu dải điều khiển.

Dàn sóng mang được khởi tạo ở 96 kHz với chu kỳ `1200 mẫu/ký_hiệu`, bảo toàn tính trực giao sau khi hạ mẫu.

Kiểm tra:
```text
Lệnh DEBUG_PING qua sóng mang phái sinh -> Máy chủ phản hồi PONG.
Lệnh SELECT_PROFILE(0x0E) qua sóng mang -> Máy chủ phản hồi PROFILE SELECTED + CAL ECHO.
```

**Bước 2 - Khai thác lỗi tràn Heap trong `SET_CAL_VECTOR`.**

Phân tích mã nguồn bộ nhớ:
```c
g_cal       = malloc(0x20);   /* Cấp phát 32 byte */
g_cal_desc  = malloc(0x30);   /* Chunk nối tiếp */
/* Tại hàm 0x2790, nhánh 2 */
memcpy(g_cal, value + 1, 2 * value[0]);   /* value[0] được kiểm soát bởi dữ liệu đầu vào */
```

Tham số `count` (`value[0]`) là số nguyên 8-bit, cho phép ghi đè tối đa ~70 byte lên vùng nhớ 32 byte. Việc ghi đè sẽ ảnh hưởng đoạn meta của chunk kế tiếp: `g_cal+0x20` (prev_size), `g_cal+0x28` (size, giá trị `0x41`), và `g_cal+0x30` chứa con trỏ hàm (`desc.fn`).

Đoạn mã `0x2970` thực thi sau bản thu:
```c
if (g_cal_desc->fn == &inc32) g_hits += 2;
else { rdi = &g_hits; jmp g_cal_desc->fn; }     /* Thực thi qua con trỏ hàm */
```
Việc kiểm soát địa chỉ `desc.fn` cho phép thực thi mã tùy ý.

**Bước 3 - Rò rỉ địa chỉ hàm qua `CAL ECHO`.**
Lệnh `SELECT_PROFILE(0x0E)` in ra 16 byte đầu của mảng `g_cal`, chứa địa chỉ của con trỏ hàm `show_flag`:

```text
CAL ECHO xuất ra: 80 25 53 df bc 55 00 00 | d0 62 53 df bc 55 00 00
                 ^ Tương ứng base+0x2580    ^ Tương ứng base+0x62d0 = g_cal+0x30 (Con trỏ fn)
```

**Bước 4 - Thực thi chuỗi lệnh khai thác.**
Quá trình tự động (`exploit.py`):

1. Gửi lệnh `SELECT_PROFILE(0x0E)` qua sóng phái sinh, lấy địa chỉ `fn` từ chuỗi `CAL ECHO`.
2. Gửi lệnh `SET_CAL_VECTOR(count=28)` với payload 56 byte: đoạn `0..39` gán giá trị `0`, cấu hình `g_cal+0x28 = 0x41` (duy trì tính nguyên vẹn của heap), và `g_cal+0x30 = fn` (trỏ tới `show_flag`).
3. Luồng `0x2970` thực thi hàm `show_flag` và trả về cờ.

**Bước 5 - Tối ưu thời lượng khung tin.**
Gói tin `A5 5A 3E 01 01 0E 02 39 1C … CK` có kích thước 66 byte (132 ký hiệu âm thanh), yêu cầu ~1.65 giây truyền tải, nằm trong giới hạn 2 giây của hệ thống.

## Kết quả
```bash
python -u exploit.py
```

Nhật ký thực thi:
```text
$ python -u exploit.py
[1] ===
[*] Bóc được show_flag = 0x5619a36fa580
[*] 106 byte cuoi: CAL VECTOR WRITTEN: count=28 | FACTORY DIAG UNLOCKED |
    FLAG: H7CTF{3c48f268-6761-422b-9df0-e652f6b2c4d0} | ---- |
[+] FLAG: H7CTF{3c48f268-6761-422b-9df0-e652f6b2c4d0}
```

## Các file liên quan

```text
de.md  notes.md  writeup.md  flag.txt  exploit.py
analysis/
  unpacked/            Dữ liệu từ dog_whistle.zip: aria, SPEC.md, eq.cfg, reference_ping.wav
  aria.asm             Mã máy dịch ngược (objdump -D -M intel .text)
  frontend_notes.md    Phân tích thuật toán 0x1940 / 0x1e30 / 0x1f70 / 0x2550
  enc.py               Công cụ tạo khung MFSK và sóng mang phái sinh (96 kHz, 1200 mẫu/ký hiệu)
  client.py            Trình quản lý giao tiếp mạng
  exploit.py           Thực thi chuỗi khai thác
  wav_ref.py           Giải mã tệp tham chiếu reference_ping.wav
  probe1-3.py sweep.py Công cụ lập bản đồ bộ nhớ heap
  live1-8.txt          Nhật ký hệ thống
files/dog_whistle.zip
```
