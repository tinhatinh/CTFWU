# Dog Whistle — Hardware (Insane)

**Flag:** `H7CTF{3c48f268-6761-422b-9df0-e652f6b2c4d0}` · **Dịch vụ:** `nc pwn.h7tex.com 40918` · **Files:** `dog_whistle.zip` (firmware `aria` r7.2)

## Đề bài

Loa thông minh nhận lệnh bằng âm thanh, firmware `aria` r7.2. Đề nói cái duy nhất đứng giữa
ta và nhóm lệnh engineering là một "bộ quét phổ" trong dải 300 - 3400 Hz. Mục tiêu: lấy cờ
mà firmware đang giữ.

## Phân tích ban đầu

Hàng phòng vệ không phải bộ lọc. Nó là một bộ giải mã thứ hai, chạy trên tín hiệu *trước*
khâu khuyếch đại phi tuyến, trong khi bộ giải mã *thật* chạy trên tín hiệu *sau*. Đưa lệnh
vào bằng tone hiệu của hai sóng mang 4 - 6 kHz thì tín hiệu gốc không chứa gì trong dải điều
khiển nên guard giải mã ra rác, còn sau khâu phi tuyến thì khung lệnh xuất hiện. Đúng nghĩa
"chó nghe được, người không".

| File | Nội dung |
|---|---|
| `aria` | ELF x86-64, PIE, stripped, 18 KB, động |
| `SPEC.md` | mô tả transport + modem + TLV |
| `eq.cfg` | 8 band, all 0 dB (flat) |
| `reference_ping.wav` | 24-bit/96 kHz mono, 15168 frame, đã decode ra `A5 5A 02 10 00 12` |

Chuỗi xử lý một capture (đảo ngược từ `analysis/aria.asm`, đối chiếu `frontend_notes.md`):

```
base64 → parse WAV → 0x1940 EQ → 0x2550 GUARD → 0x1f70 P(x)
       → 0x1e30 LPF 7 kHz + hạ mẫu /6 → 0x2070 Goertzel → 0x2790 dispatch
```

`0x1f70` là bộ khuyếch đại + đáp ứng transducer, không nhớ:

```
u = 4x;   y = 0.98u + 0.05u² + 0.005u³        (≈ 3.92x + 0.80x² + 0.32x³)
```

`0x2070` phân tích bằng Goertzel 200 sample tại 16 kHz - tức đúng một DFT 200 điểm, các bin
cách nhau 80 Hz, và 16 tone điều khiển `800+80k` chính là bin 10…25.

### Guard không nhìn phổ, chỉ nhìn opcode

`0x2550` không có bin nào, không có cửa sổ 300 - 3400 Hz, không có ngưỡng nào. Nó gọi lại
`0x1e30` + `0x2070`, rồi đi hết chuỗi TLV đã giải mã được và trả 1 nếu thấy bản ghi type
`0x01` hoặc `0x02`.

Kiểm chứng sống:

```
payload 01 01 0E, điều chế tone thường   -> SAFETY LOCKOUT: engineering tone signature...
payload 01 01 0E, điều chế carrier-hiệu  -> PROFILE SELECTED: region 0x0e
```

Vấn đề quy về một câu: làm cho guard giải ra khác bộ giải mã thật.

## Các hướng đã loại

Trước khi chốt đã kiểm tra và loại các kênh sau (log đầy đủ ở `notes.md`):

1. Hàng phòng vệ là bộ lọc phổ 300 - 3400 Hz như đề gợi. `0x2550` không chứa bin, cửa sổ
   hay ngưỡng nào; nó chỉ gọi lại `0x1e30` + `0x2070`, đi hết chuỗi TLV và trả 1 khi gặp bản
   ghi type `0x01`/`0x02` (kiểm chứng sống ở mục trên).
2. Phải tính `base` rồi tự cộng offset để có địa chỉ `show_flag`. 12 bit thấp luôn
   `0x580` ở cả 6 phiên, `base` thẳng hàng trang, nhưng không cần dùng tới con đường đó: đọc
   nguyên giá trị 8 byte từ `CAL ECHO` và ghi thẳng vào `desc.fn`.
3. Partial overwrite byte thấp theo bản zip (`0xa0,0x26`). Bản deploy lệch `0x120` so với
   bản trong zip (`inc32` 0x2690→0x2570, `show_flag` 0x26a0→0x2580), nên giả thuyết này nhảy
   tới `base+0x26a0` và chết lặng. Tôi giữ nó ba phiên, chỉ loại khi lấy con số trực tiếp từ
   leak.

## Chuỗi khai thác

**Bước 1 - Tone hiệu.** Guard đọc `x`; bộ thật đọc `P(x)`. Hạng tử `0.05u²` sinh
`cos(2π(f_p−f_q)t)`. Chọn mỗi symbol hai sóng mang ở bin `p = 51+B` và `q = 51` (4080 Hz và
`(51+B)·80` Hz), khi đó `p−q = B` là bin điều khiển cần mô phỏng. Với `B ∈ 10..25`:

- `x` chỉ có năng lượng ở bin ≥ 26, lại đúng bội số của 80 Hz nên trực giao với mọi bin
  10…25 → guard đo được số 0 tuyệt đối, argmax của nó không có ngưỡng năng lượng nên luôn trả
  nibble 0 → chuỗi byte toàn `00` → không có `A5 5A` → decode fail → guard trả 0, không
  lockout.
- `P(x)` có đúng một thành phần trong bin 10…25: hiệu `p−q`. Các tích khác đều rơi ra ngoài:
  `2q−p = 51−B ∈ [26,41]`, `p+q ≥ 28`, `3p`, `3q` ngoài dải (và bị LPF 7 kHz chặn bớt). Vì mỗi
  tần số là số nguyên lần chu kỳ trong cửa sổ 200 sample nên cửa sổ phân tách sạch hoàn toàn.
- Chọn `q = 51` (không phải thấp hơn) là để `51−B ≥ 26` với mọi `B ≤ 25`.

Sóng mang được sinh trực tiếp ở 96 kHz với `1200 sample/symbol`, tức đúng `m` chu kỳ mỗi
symbol, nên sau khi hạ mẫu vẫn còn nguyên tắc trực giao.

```
DEBUG_PING đặt trên carrier-hiệu  -> PONG     (lần đầu tiên)
SELECT_PROFILE(0x0E) trên carrier -> PROFILE SELECTED + CAL ECHO
```

**Bước 2 - Tràn heap trong `SET_CAL_VECTOR`.**

```c
g_cal       = malloc(0x20);   /* 32 byte */
g_cal_desc  = malloc(0x30);   /* chunk ngay sau */
/* 0x2790, case 2 */
memcpy(g_cal, value + 1, 2 * value[0]);   /* value[0] do ta chọn, chỉ bị chặn bởi độ dài frame */
```

`count` là một byte ⇒ ghi được tới ~70 byte lên một vùng 32 byte. Chunk kế tiếp nằm ở
`g_cal+0x20` (prev_size), `g_cal+0x28` (size, `0x41`), `g_cal+0x30` (`desc.fn`).

`0x2970` chạy sau mọi capture được chấp nhận:

```c
if (g_cal_desc->fn == &inc32) g_hits += 2;
else { rdi = &g_hits; jmp g_cal_desc->fn; }     /* nhảy, không gọi */
```

Chỉ cần sửa `desc.fn` là lấy được một lời gọi hàm với đối số ta không cần quan tâm.

**Bước 3 - `CAL ECHO` tự lộ địa chỉ hàm.** `SELECT_PROFILE(0x0E)` in 16 byte đầu của `g_cal`.
8 byte đầu chính là địa chỉ con trỏ hàm show_flag:

```
CAL ECHO: 80 25 53 df bc 55 00 00 | d0 62 53 df bc 55 00 00
           ^ base+0x2580            ^ base+0x62d0 = g_cal+0x30 (chính là desc)
```

**Bước 4 - ba phát trên socket.** `exploit.py` (chỉ stdlib + `analysis/enc.py`):

1. kết nối, gửi `SELECT_PROFILE(0x0E)` điều chế carrier-hiệu, parse `CAL ECHO` → `fn`;
2. gửi `SET_CAL_VECTOR(count=28)` - payload 56 byte: `0..39 = 0`,
   `g_cal+0x28 = 0x41` (giữ size để không hỏng heap), `g_cal+0x30 = fn`;
3. `0x2970` nhảy vào `show_flag`, in cờ; đọc socket kiểu chịu EOF/RST.

**Bước 5 - Kiểm chứng độ dài khung.** Tổng độ dài khung
`A5 5A 3E 01 01 0E 02 39 1C … CK` = 66 byte = 132 symbol = 1.65 s, vừa trần 2 giây của WAV.

## Flag
```bash
python -u exploit.py
```

```
$ python -u exploit.py
[1] ===
[*] leak show_flag = 0x5619a36fa580
[*] 106 byte cuoi: CAL VECTOR WRITTEN: count=28 | FACTORY DIAG UNLOCKED |
    FLAG: H7CTF{3c48f268-6761-422b-9df0-e652f6b2c4d0} | ---- |
[+] FLAG: H7CTF{3c48f268-6761-422b-9df0-e652f6b2c4d0}
```

## Files

```
de.md  notes.md  writeup.md  flag.txt  exploit.py
analysis/
  unpacked/            dog_whistle.zip giải ra: aria, SPEC.md, eq.cfg, reference_ping.wav
  aria.asm             objdump -D -M intel .text
  frontend_notes.md    0x1940 / 0x1e30 / 0x1f70 / 0x2550 viết lại thành công thức
  enc.py               khung MFSK + generator carrier-hiệu (96 kHz, 1200 sample/symbol)
  client.py            socket event-driven, đọc tới dấu '----'
  exploit.py           3 bước ở trên, in cờ hoặc exit khác 0
  wav_ref.py           decode + kiểm chứng reference_ping.wav
  probe1-3.py sweep.py dẫn dò layout heap; tries/ phản hồi đầy đủ từng biến thể
  live1-8.txt          nhật ký phiên đích
files/dog_whistle.zip
```
