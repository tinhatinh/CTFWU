# Dog Whistle — Hardware (Insane)

**Flag:** `H7CTF{3c48f268-6761-422b-9df0-e652f6b2c4d0}`
**Dịch vụ mạng:** `nc pwn.h7tex.com 40918`
**Files cung cấp:** `dog_whistle.zip` (chứa firmware `aria` phiên bản r7.2).

## Đề bài

Hệ thống xoay quanh một chiếc loa thông minh tiếp nhận mệnh lệnh thông qua sóng âm thanh, chạy firmware `aria` r7.2. Tác giả tiết lộ: chướng ngại vật duy nhất cản bước ta kích hoạt bộ lệnh kỹ thuật ẩn (engineering commands) là một "bộ quét phổ âm thanh" hoạt động trong dải tần hẹp 300 - 3400 Hz. Nhiệm vụ của ta là phá vỡ bức tường này và đoạt lấy lá cờ đang bị firmware giam giữ.

## Phân tích ban đầu

Điểm bất ngờ nhất: hệ thống phòng vệ (Guard) không phải là một bộ lọc âm (filter) ngăn chặn tín hiệu. Nó thực chất là một bộ giải mã độc lập thứ hai, chuyên mổ xẻ tín hiệu *trước* khi chúng đi qua khâu khuyếch đại phi tuyến (non-linear amplifier). Trong khi đó, bộ giải mã *thật sự* của loa lại chỉ ăn tín hiệu *sau* khâu phi tuyến. 
Chiến thuật lóe lên: Nếu ta truyền lệnh thông qua tín hiệu phái sinh (tone hiệu) tạo ra từ hai sóng mang tần số cao 4 - 6 kHz, thì ở giai đoạn tín hiệu gốc, không hề có bất kỳ dải âm điều khiển nào lọt vào tần số thấp (khiến bộ Guard nhai phải rác và cho qua). Nhưng khi đi qua khâu phi tuyến, hiện tượng méo tín hiệu sẽ tự động nặn ra khung lệnh ở tần số thấp để bộ giải mã thật nuốt trọn. Hiện tượng này đúng chuẩn với câu nói "chó nghe được, người không" (dog whistle).

| File đính kèm | Vai trò |
|---|---|
| `aria` | Tệp nhị phân ELF x86-64, biên dịch PIE, stripped, nhẹ 18 KB, liên kết động. |
| `SPEC.md` | Tài liệu đặc tả kỹ thuật truyền tải, mô đun mạng (modem) và cấu trúc gói tin TLV. |
| `eq.cfg` | Tệp cấu hình bộ cân bằng âm thanh 8 dải (8 band), tất cả đều phẳng lì 0 dB (flat). |
| `reference_ping.wav` | Tệp âm thanh mẫu (24-bit/96 kHz mono), dài 15.168 khung mẫu, dịch ngược ra chuỗi lệnh `A5 5A 02 10 00 12`. |

Quy trình xử lý một đoạn ghi âm (được mổ ngược từ `analysis/aria.asm`, đối chiếu với tài liệu `frontend_notes.md`):

```text
Chuỗi dữ liệu base64 → Dịch file WAV → 0x1940 Chạy qua EQ → 0x2550 Chạy qua GUARD → 0x1f70 Chạy qua bộ khuyếch đại P(x)
       → 0x1e30 Chạy qua LPF (lọc thông thấp) 7 kHz + ép hạ mẫu /6 → 0x2070 Bộ phân tích Goertzel → 0x2790 Gọi hàm xử lý lệnh (dispatch)
```

Tại offset `0x1f70`, bộ khuyếch đại mô phỏng phản ứng vật lý của màng loa, với công thức phi tuyến:
```text
Đặt u = 4x;   Đầu ra y = 0.98u + 0.05u² + 0.005u³        (Thu gọn ≈ 3.92x + 0.80x² + 0.32x³)
```

Tại `0x2070`, thuật toán Goertzel phân tách 200 mẫu (sample) âm thanh ở tần số 16 kHz - đây chính xác là một phép biến đổi DFT 200 điểm. Khoảng cách giữa các dải tần (bin) là 80 Hz, và 16 tần số điều khiển (nằm ở phổ `800+80k` Hz) rơi chuẩn xác vào các bin từ 10 đến 25.

### Bất ngờ từ bộ Guard: Mù phổ âm, chỉ soi lệnh (Opcode)

Khám nghiệm sâu đoạn mã `0x2550`, ta thấy nó không thèm kiểm tra bất kỳ một dải tần nào, không hề có cửa sổ giới hạn 300 - 3400 Hz nào, cũng chẳng có ngưỡng âm thanh giới hạn nào. Trái lại, nó hồn nhiên tái sử dụng nguyên xi cụm giải mã `0x1e30` + `0x2070`, quét hết chuỗi TLV đã phân giải được. Trát tử hình sẽ được ban ra (lockout) nếu nó đọc được bản ghi thuộc loại `0x01` hoặc `0x02`.

Kết quả thử lửa trên môi trường live:
```text
Đẩy payload 01 01 0E bằng âm tần thông thường -> Máy chủ bật SAFETY LOCKOUT: phát hiện âm thanh kỹ thuật...
Đẩy payload 01 01 0E bằng sóng mang phái sinh -> Máy chủ nhả PROFILE SELECTED: vùng 0x0e
```

Chốt lại, bài toán trở nên vô cùng đơn giản: Làm thế nào để bộ Guard điếc đặc với âm thanh, nhưng bộ giải mã thật lại nghe rõ mồn một.

## Chuỗi khai thác

**Bước 1 - Lách luật bằng sóng mang phái sinh (Tone hiệu).** 
Bộ Guard đọc nguyên bản tín hiệu `x`, còn bộ giải mã thật thì đọc tín hiệu méo `P(x)`. Trong công thức méo, nhân tố `0.05u²` vô tình đẻ ra sóng tần số hiệu `cos(2π(f_p−f_q)t)`. 
Kế hoạch: Trộn hai sóng mang (carrier) nằm tít ở bin `p = 51+B` và `q = 51` (tương đương 4.080 Hz và `(51+B)*80` Hz). Khi chúng giao thoa, hiệu số `p−q = B` sẽ tạo ra chính cái bin tần số điều khiển mà ta cần. Với điều kiện `B ∈ [10..25]`:

- Tín hiệu `x` truyền vào chỉ dồn toàn bộ năng lượng ở các bin từ 26 trở lên. Đã vậy, nó còn là bội số hoàn hảo của 80 Hz nên vuông góc (trực giao) hoàn toàn với mọi bin từ 10 đến 25. Hậu quả: Guard đo đạc bin điều khiển và nhận về con số 0 tròn trĩnh. Hàm argmax của Guard không được cài đặt ngưỡng âm giới hạn nên nó lấy luôn giá trị rác 0 -> nhả ra một chuỗi toàn `00` -> Mất định dạng chữ ký `A5 5A` -> Giải mã thất bại -> Guard cất còi, không thèm khoá hệ thống.
- Khi tín hiệu đi qua `P(x)`, nó đẻ ra duy nhất một dải tần lọt khe vào bin điều khiển 10..25: đó chính là hiệu số `p−q`. Các dải tần tạp âm khác đều văng ra ngoài không thương tiếc: `2q−p = 51−B ∈ [26,41]`, `p+q >= 28`, `3p`, `3q` vượt xa ngoài dải (và bị lưới lọc LPF 7 kHz vớt sạch). Vì mỗi tần số đều chiếm một số nguyên lần chu kỳ của 200 mẫu âm, nên sự phân tách diễn ra hoàn hảo không lẫn một hạt sạn.
- Lý do ghim cố định `q = 51` (chứ không chọn số thấp hơn) là để dải tạp âm `51−B >= 26` (với mọi `B <= 25`), tránh va chạm ngược vào vùng điều khiển.

Dàn sóng mang được nhào nặn trực tiếp ở độ phân giải 96 kHz với nhịp `1200 mẫu/ký_hiệu`, tương đương một số nguyên vòng chu kỳ, bảo toàn triệt để tính trực giao sau khi bị ép hạ mẫu.

Kiểm tra:
```text
Bắn DEBUG_PING bằng sóng mang phái sinh -> Máy chủ vọng PONG (Thành công lần đầu)
Bắn SELECT_PROFILE(0x0E) bằng sóng mang  -> Máy chủ nôn PROFILE SELECTED + CAL ECHO
```

**Bước 2 - Khoét lỗ hổng tràn Heap trong `SET_CAL_VECTOR`.**

Khám nghiệm mã nguồn giả định:
```c
g_cal       = malloc(0x20);   /* Cấp phát 32 byte */
g_cal_desc  = malloc(0x30);   /* Chunk nối đuôi ngay sát vách */
/* Tại hàm 0x2790, nhánh 2 */
memcpy(g_cal, value + 1, 2 * value[0]);   /* value[0] do người dùng thao túng, giới hạn duy nhất là độ dài gói tin */
```

Biến `count` (tương ứng `value[0]`) là một số nguyên 8-bit, cho phép ta nhồi tới ~70 byte đè thẳng lên vùng nhớ chỉ dài 32 byte. Nạn nhân trực tiếp là đoạn meta của chunk kế tiếp: `g_cal+0x20` (prev_size), `g_cal+0x28` (size, mang trị số `0x41`), và đau đớn nhất là `g_cal+0x30` chứa con trỏ hàm (`desc.fn`).

Đoạn mã `0x2970` chạy dọn dẹp sau mỗi bản thu âm:
```c
if (g_cal_desc->fn == &inc32) g_hits += 2;
else { rdi = &g_hits; jmp g_cal_desc->fn; }     /* Nhảy thẳng vào con trỏ hàm bị đè */
```
Chỉ cần đè trúng địa chỉ mong muốn vào `desc.fn`, ta sẽ chiếm trọn một quyền thực thi hàm tuỳ ý.

**Bước 3 - Cạm bẫy `CAL ECHO` nôn địa chỉ hàm.** 
Lệnh `SELECT_PROFILE(0x0E)` có chức năng in ra 16 byte đầu tiên của mảng `g_cal`. Thật tuyệt vời, 8 byte trong số đó lại chính là địa chỉ thực của con trỏ hàm `show_flag`:

```text
CAL ECHO in ra: 80 25 53 df bc 55 00 00 | d0 62 53 df bc 55 00 00
                 ^ Ứng với base+0x2580    ^ Ứng với base+0x62d0 = g_cal+0x30 (Chính là con trỏ fn cần tìm)
```

**Bước 4 - Liên hoàn ba phát súng trên Socket.** 
Chương trình `exploit.py` (chỉ dùng thư viện chuẩn stdlib + công cụ tạo sóng `analysis/enc.py`):

1. Kết nối, bắn lệnh `SELECT_PROFILE(0x0E)` bọc trong sóng mang phái sinh, bóc tách chuỗi `CAL ECHO` để chộp lấy địa chỉ `fn`.
2. Bắn tiếp `SET_CAL_VECTOR(count=28)` - mang payload chết chóc dài 56 byte: đoạn `0..39` nhét toàn số `0`, chèn `g_cal+0x28 = 0x41` (để giữ nguyên size, tránh làm sập bộ quản lý heap), chèn `g_cal+0x30 = fn` (hướng thẳng vào hàm `show_flag`).
3. Luồng `0x2970` bị bẻ lái đâm sầm vào `show_flag`, nhả cờ. Đọc dữ liệu thô từ socket cho đến khi cạn kiệt.

**Bước 5 - Chốt hạ thời lượng khung tin.** 
Tổng độ dài của gói tin `A5 5A 3E 01 01 0E 02 39 1C … CK` là 66 byte (bằng 132 ký hiệu âm thanh), tốn khoảng 1.65 giây phát sóng. Hoàn toàn nằm gọn gàng trong giới hạn 2 giây mà hệ thống cho phép.

## Flag
```bash
python -u exploit.py
```

Nhật ký chạy thật:
```text
$ python -u exploit.py
[1] ===
[*] Bóc được show_flag = 0x5619a36fa580
[*] 106 byte cuoi: CAL VECTOR WRITTEN: count=28 | FACTORY DIAG UNLOCKED |
    FLAG: H7CTF{3c48f268-6761-422b-9df0-e652f6b2c4d0} | ---- |
[+] FLAG: H7CTF{3c48f268-6761-422b-9df0-e652f6b2c4d0}
```

## Hệ sinh thái file

```text
de.md  notes.md  writeup.md  flag.txt  exploit.py
analysis/
  unpacked/            Dữ liệu bung ra từ dog_whistle.zip: aria, SPEC.md, eq.cfg, reference_ping.wav
  aria.asm             Lệnh mã máy thô từ objdump -D -M intel .text
  frontend_notes.md    Phục dựng các thuật toán 0x1940 / 0x1e30 / 0x1f70 / 0x2550 thành công thức toán học
  enc.py               Động cơ tạo khung MFSK + Nhào nặn sóng mang phái sinh (96 kHz, 1200 mẫu/ký hiệu)
  client.py            Trình giao tiếp mạng event-driven, bám đuôi cờ '----'
  exploit.py           Thực thi 3 phát súng lấy cờ
  wav_ref.py           Giải mã + đối chiếu với mẫu reference_ping.wav
  probe1-3.py sweep.py Đạn dò đường để dựng bản đồ bộ nhớ heap; thư mục tries/ giữ log của các phát đạn
  live1-8.txt          Nhật ký lưu trữ các phiên đánh sập thật
files/dog_whistle.zip
```
