---
title: "Radio Silence — Hardware (Medium)"
date: 2026-09-28 16:53:17 +0700
lastmod_at: 2026-09-28 16:53:17 +0700
categories: [Hardware]
tags: [h7ctf-quals, Hardware]
image:
  path: /CTFWU/H7CTF%202026%20Quals/radio-silence/files/de.png
---
{% raw %}
**Flag:** `H7CTF{6780856d-db42-4cfa-8b56-c62109d8417c}`
**Instance:** `https://web-0350e37b217a0cbc.web.h7tex.com`
**Files:** `capture.cf32` (393544 B, sha256 `167a70fa…`) - interleaved float32 LE I/Q, 1 Msps

## Đề bài

Một burst vô tuyến phát ra cạnh một thiết bị không ai biết tên: không datasheet, không protocol notes, không nhãn. Đề chỉ cho một file baseband và nói "Read it back", tức toàn bộ tham số của giao thức phải tự đo từ tín hiệu.

## Phân tích ban đầu

```
$ curl -sS https://web-0350e37b217a0cbc.web.h7tex.com
file: capture.cf32 (complex baseband, interleaved float32 I/Q, little-endian: I0 Q0 I1 Q1 ...)
sample rate: 1000000 Hz
```

```python
raw = np.fromfile('files/capture.cf32', dtype='<f4')   # 49193 mẫu, 49.193 ms
iq  = raw[0::2] + 1j*raw[1::2]
```

Việc đầu tiên là quyết định điều chế biên độ hay điều chế tần số. Histogram của `abs(iq)` hai phong: một cụm quanh 0 và một cụm quanh 1.0, trông rất giống OOK (đề trước trong cùng event là 433 MHz OOK/Manchester). Run-length của cổng `abs > 0.35` bác bỏ ngay giả thuyết đó:

```
total runs 5
   0  2909 0      im lặng đầu burst (noise floor)
2909 43200 1      burst liên tục, envelope không đổi
46109   151 0
46260     1 1     blip đơn lẻ
46261  2932 0     im lặng cuối
```

Envelope phẳng suốt 43200 mẫu nên phần "0" chỉ là khoảng trắng trước/sau phát xạ. Envelope không đổi + có sóng mang = 2-FSK.

FFT trên riêng burst (Hanning, độ phân giải 23.1 Hz) cho đúng hai đỉnh:

```
+35.00 kHz   0.00 dB
+84.99 kHz  -2.68 dB
```

cả hai nằm chính giữa bin, tức tone thật là 35 kHz và 85 kHz: sóng mang cực 60 kHz, độ lệch ±25 kHz.

## Chuỗi khai thác

### Bước 1: định thời symbol từ chính tín hiệu

Lấy discriminators `diff(unwrap(angle(burst))) * fs / 2π`, làm trơn cửa sổ 8 mẫu. Histogram chỉ còn hai cụm (quanh 35 và 85 kHz) chứng tỏ 2 mức tần số thực, phần trải ra giữa hai cụm là mẫu chuyển mức.

Đếm vị trí transition rồi xét modulo chu kỳ ứng viên:

```
best symbol-period candidates:
   0.552  S=100  100.0 us  10000.0 baud
   0.552  S= 50   50.0 us  20000.0 baud      (hoà âm của S=100)
   0.552  S= 25   25.0 us  40000.0 baud
   ...
top transition-train lines (Hz): [10001.9, 20003.7, ...]
```

S=100 là chu kỳ cơ bản (50/25/10 chỉ là hài hoạ của cùng một lưới pha) và chuỗi xung transition có line phổ đúng 10 kHz. 10 kBaud, nên burst 43200 mẫu mang `43200/100 = 432 symbol = 54 byte` chẵn.

Cũng từ đây loại được Manchester: Manchester bán kỳ 100 mẫu sẽ buộc có transition mỗi 100 mẫu (≥431 cái), trong khi discriminators chỉ đổi mức 248 lần trên 431 biên giới symbol, tức xấp xỉ 50% mật độ transition của dữ liệu ngẫu nhiên ở 10 kBaud.

### Bước 2: quyết định từng symbol

Majority vote trên 80 mẫu giữa mỗi slot 100 mẫu, tone 85 kHz = 1, gói MSB-first:

```python
states = (sm > 60e3).astype(np.int8)
slots  = [states[i*100+10:(i+1)*100-10] for i in range(432)]
bits   = np.array([s.mean() > 0.5 for s in slots], dtype=np.uint8)
frame  = np.packbits(bits).tobytes()
```

```
[*] decisions   min margin 0.500, 0/432 slots below 0.05 margin
[*] raw frame   aaaaaaaaaaaa2dd42b48374354467b36373830383536642d646234322d
                346366612d386235362d6336323130396438343137637d7a65
[*] as ascii    b'\xaa\xaa\xaa\xaa\xaa\xaa-\xd4+H7CTF{6780856d-db42-4cfa-8b56-c62109d8417c}ze'
[*] leftover    0 bits after the last whole byte
```

`min margin 0.500` nghĩa là mọi symbol đều đồng thuận tuyệt đối: không có slot nào hai tone tranh chấp nhau, nên không có bit nào phải đoán.

### Bước 3: loại 3 cách gán bit còn lại

Bốn tổ hợp (tone cao/thấp = 1, MSB/LSB) chỉ cho một kết quả có nghĩa:

```
t85=1 MSB   printable 46/54  b'\xaa\xaa...H7CTF{6780856d-db42-...'
t85=1 LSB   printable 25/54  rác
t35=1 MSB   printable  7/54  rác
t35=1 LSB   printable 18/54  rác
```

## Cấu trúc frame đo được

| vùng | byte | nhận xét |
| --- | --- | --- |
| preamble | `aa aa aa aa aa aa` | `0b10101010`, chuỗi alternation dùng cho bit sync |
| header | `2d d4 2b` | không định danh được, có thể device id + loại lệnh |
| message | `48 37 43 54 46 7b … 7d` | `H7CTF{6780856d-db42-4cfa-8b56-c62109d8417c}` (43 B) |
| trailer | `7a 65` | chưa giải thích được: `sum8=0x9f`, `xor8=0xf7`, CRC16-CCITT init 0/FFFF = `0xdeea`/`0xd655`, CRC16 reflected 0x8005/0xA001 = `0x2d08`/`0x9657` đều không ra `0x7a65`. Nhiều khả năng là nonce/serial. |

Không nộp bài qua HTTP: instance chỉ phục vụ đúng một file tĩnh (`Server: SimpleHTTP/0.6`), không có `<pre>` hợp đồng nộp như mấy bài web/hardware khác của cùng event, nên cờ được dán lên scoreboard.

## Flag
```
$ python solve_rf.py files/capture.cf32
[+] FLAG: H7CTF{6780856d-db42-4cfa-8b56-c62109d8417c}
```

{% endraw %}
