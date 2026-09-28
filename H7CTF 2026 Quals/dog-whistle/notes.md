# Dog Whistle — decision log

Đích: `nc pwn.h7tex.com 40918`. Cờ dạng `H7CTF{}` (đọc từ thẻ đề, không suy ra).
Artefact: `files/dog_whistle.zip` → `aria` (ELF PIE, stripped), `SPEC.md`, `eq.cfg`,
`reference_ping.wav`.

## Kiến trúc đã đảo ngược (xem `analysis/frontend_notes.md`)

`main @ 0x1180`: `setvbuf(stdout, NULL, _IONBF)` → `init_cal @ 0x2700` → in banner
(budget 12) → vòng `getdelim`, mỗi dòng base64 → `capture @ 0x13e0`.

Chuỗi xử lý một capture:

```
0x1600 base64 (bảng chuẩn A-Za-z0-9+/=)
0x1710 parse RIFF/WAVE, 1 kênh / 24 bit / 96000 Hz, 128 chunk worst-case
0x1940 EQ biquad (RBJ, max 8 band, Direct Form II)   <- eq.cfg / $EQ_CFG
0x2550 GUARD: tự chạy 0x1e30+0x2070 rồi đi hết 240 byte ra lệnh đã decode,
             return 1 nếu thấy TLV type 0x01 hoặc 0x02  (KHÔNG phải dò phổ)
0x1f70 x = P(x), u=4x, y = 0.98u + 0.05u^2 + 0.005u^3   <- CHẠY SAU GUARD
0x1e30 Butterworth bậc 6 fc=7000 Hz @96k rồi hạ mẫu /6 -> 16 kHz
0x2070 Goertzel 200 sample/cửa sổ = DFT 200 điểm, spacing 80 Hz,
       tone(k)=800+80k = bin 10..25, argmax không có ngưỡng năng lượng
0x2790 dispatch TLV: 0x10 PONG, 0x01 SELECT_PROFILE, 0x02 SET_CAL_VECTOR
0x2970 sau MỌI capture: if (g_cal_desc.fn == &inc32) g_hits += 2
                        else { rdi = &g_hits; jmp g_cal_desc.fn }
```

Heap: `g_cal = malloc(0x20)` (32 byte), chunk kế tiếp `g_cal_desc` (0x30).
`g_cal+0x28` = size chunk desc (0x41), `g_cal+0x30` = `desc.fn`.

## Branch đã xác nhận

- **GUARD chỉ nhìn opcode, không nhìn phổ.** Bằng chứng sống: gửi `01 01 0E` điều
  chế ở band thường → `SAFETY LOCKOUT`; gửi ĐÚNG byte đó nhưng carrier đặt ở
  4080/4880 Hz → `PROFILE SELECTED`. → SPEC nói "quét 300–3400 Hz tìm tone signature"
  là đánh lạc hướng; muốn vượt chỉ cần làm guard decode ra thứ khác với bộ giải mã thật.
- **Hai bộ giải mã ăn hai tín hiệu khác nhau.** Guard chạy trên `x`, bộ thật chạy trên
  `P(x)`. `P` có hạng tử bậc 2 ⇒ sinh tone tổng/hiệu. Chọn 2 carrier ở bin `p,q ≥ 26`
  với `p−q = bin cần`: bin 10..25 của `x` RỖNG tuyệt đối (mọi thành phần là bội số
  80 Hz, trực giao DFT), còn `P(x)` có đúng một tone ở bin đó.
  Kiểm chứng: `DEBUG_PING` carrier-hiệu → `PONG` ngay lần đầu.
- `reference_ping.wav` **đã là tín hiệu tiền xử lý**: burst đúng `14400 = 12·1200`
  sample, grid base 64, biên độ 0.250000 FS bằng nhau mọi symbol, im lặng tuyệt đối.
  Decode ra `A5 5A 02 10 00 12` (CKSUM `0x12`, không phải `0x02` như đoán ban đầu).
- Không có nội dung nào giấu trên 7 kHz trong file mẫu (phép thử subtract-one-sine:
  phần dư >7 kHz = −163.6 dBFS). Nên "micro băng thông rộng" chỉ là dẫn dắt.

## Dead branch (và lý do)

- **Ý định dùng `getenv("EQ_CFG")` để notch băng guard**: vô dụng, vì guard không phải
  bộ lọc dải; và env đó thuộc phía server, ta không đặt được.
- **Tone bậc 3 (`3f0`)**: `f0 = (800+80k)/3` chỉ là bội số 80 Hz với 5/16 tone
  (bin 10,13,16,19,22 → nibble 2,5,8,b,e) ⇒ không đủ bảng chữ hex. Bỏ.
- **Carrier bin thấp (≤9) lấy tổng 2 tone**: chỉ với được bin 10..18 ⇒ nibble 0..8,
  thiếu nửa trên. Bỏ; dùng hiệu ở bin cao.
- **Nghi ngờ "state không đổi giữa các kết nối"**: sai, mỗi kết nối là tiến trình mới —
  `CAL ECHO` ra trị khác nhau mỗi phiên, và `count` tăng dần vẫn chạy đúng.
- **Đoán offset hàm theo bản trong zip**: `inc32`/`show_flag` zip là `0x2690`/`0x26a0`,
  nhưng bản deploy là `0x2570`/`0x2580` (lệch 0x120). Viết `0xa0,0x26` vào `desc.fn`
  → nhảy tới `base+0x26a0` → chết lặng, không in gì. Đây là chỗ mất thời gian nhất.

## Chốt

`CAL ECHO` in 16 byte đầu của `g_cal`; 8 byte đầu **chính là địa chỉ `show_flag`**
(`base+0x2580`, low-12-bit luôn `0x580` ⇒ base thẳng hàng trang, xác nhận qua 6 phiên).
Nên không cần biết base: đọc nó ra rồi ghi nguyên 8 byte vào `desc.fn` (`g_cal+0x48`).
`0x2970` thấy `fn != inc32` → `jmp fn` → in `FACTORY DIAG UNLOCKED` / `FLAG: ...`.

Cần `2*count ≥ 56` ⇒ `count = 28`, payload = `01 01 0E` + `02 39 1C …` (LEN 62,
132 symbol, 1.65 s < 2 s). Giữ `g_cal+0x40 = 0x41` để không hỏng metadata (bài học:
viết 50 byte toàn 0 mà không giữ size cũng làm sập phiên trước khi in gì).

Kết quả: `H7CTF{3c48f268-6761-422b-9df0-e652f6b2c4d0}`, phiên **không** sập
(có `----` sau cờ) ⇒ hàm in cờ return sạch về `process_capture`.
