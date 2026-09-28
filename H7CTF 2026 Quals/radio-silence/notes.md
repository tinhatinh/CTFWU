# notes.md — Radio Silence (hardware / RF)

## H1 — định dạng file
target: `capture.cf32` 393544 B
evidence: `393544 / 8 = 49193` mẫu I/Q chẵn, đúng như index page mô tả (interleaved float32 LE, 1 Msps) -> 49.193 ms
did: `np.fromfile(dtype='<f4')`, `iq = raw[0::2] + 1j*raw[1::2]`
result: CONFIRMED, mọi giá trị hữu hạn, biên độ trong [-1.34, 1.26]

## H2 — OOK hay FSK?
target: histogram `abs(iq)` và run-length của `abs>0.35`
evidence: chỉ có **5 run**: off 2909 | **on 43200** | off 151 | on 1 | off 2932. Phần "off" đầu/cuối chỉ là noise floor trước và sau burst (1 run 43200 mẫu liên tục)
result: DEAD cho OOK (giả thuyết ban đầu vì đề trước trong cùng event là OOK/Manchester) -> envelope không đổi trong burst = **2-FSK**

## H3 — tìm tone
target: FFT burst 43200 mẫu, cửa sổ Hanning, độ phân giải 23.1 Hz
evidence: hai đỉnh +35.00 kHz (0.00 dB) và +84.99 kHz (-2.68 dB), đỉnh chẵn giữa bin -> tone đúng 35 kHz và 85 kHz
result: CONFIRMED — tâm 60 kHz, deviation ±25 kHz. Phổ rộng 130 kHz là do keying, không phải nhiễu.

## H4 — symbol rate
target: phase discriminator `diff(unwrap(angle))/2pi * fs`
evidence: histogram discriminators (smooth 8) chỉ có 2 cụm quanh 35 và 85 kHz; xung transition của discriminators tập trung theo chu kỳ 100 mẫu (137/248 tại một lớp mod-100, các lớp 50/25/20/10 cùng pha -> 100 là cơ bản); FFT của chuỗi transition có line tại 10001.9 Hz
did: `S=100` mẫu/symbol = **10 kBaud**, `43200/100 = 432 symbol = 54 byte` chẵn
result: CONFIRMED — và là bằng chứng mạnh nhất: với S=100 thì **432/432 slot đồng thuận tuyệt đối** (mỗi slot 80 mẫu giữa cửa sổ chỉ ra đúng 1 tone, min margin = 0.500), frame đúng 54 byte không thừa bit nào

## H5 — gán bit
did: tone cao (85 kHz) = 1, MSB-first
result: `aa aa aa aa aa aa 2d d4 2b 48 37 43 54 46 7b …` -> "H7CTF{" xuất hiện ngay
polarity khác (thử cả 4 tổ hợp tone/bit-order) cho 7-25/53 byte in được, không tạo thành UUID hợp lệ -> loại

## H6 — kiểm chứng độc lập
- Chuỗi trong slot cuối: `…36313039643834313763 7d` -> `62109d8417c}`; khớp đúng khuôn UUID 8-4-4-4-12 mà `H7CTF{}` mở -> không thể là giải mã lệch pha.
- 432 symbol chẵn 54 byte, 0 bit thừa; nếu S lệch 1 mẫu thì đuôi frame sẽ thành rác vô nghĩa.
- Preamble `AA` (0b10101010) đúng là chuỗi alternation dùng cho clock recovery -> cấu trúc frame tự chứng minh.

## Cấu trúc frame suy ra được
```
aa aa aa aa aa aa   preamble / bit sync (6 B)
2d d4 2b            header (3 B) - không rõ, có thể device id + type
48 .. 7d            "H7CTF{6780856d-db42-4cfa-8b56-c62109d8417c}" (43 B)
7a 65               trailer (2 B) - KHÔNG giải thích được: thử sum8=0x9f, xor8=0xf7,
                    CRC16-CCITT(0/FFFF)=0xdeea/0xd655, CRC16-IBM(0x8005/0xA001 reflected)=0x2d08/0x9657
                    đều không khớp 0x7a65 (hay 0x657a). Có thể là nonce/serial ngẫu nhiên.
```

## Primitive cuối cùng
Không cần biết thiết bị, không cần datasheet: đo envelope -> loại ASK -> tìm 2 tone -> clock từ chính transition -> majority vote mỗi slot.
Script: `solve_rf.py files/capture.cf32` (in ra frame hex + ASCII + `flag.txt`)
Flag: `H7CTF{6780856d-db42-4cfa-8b56-c62109d8417c}`
