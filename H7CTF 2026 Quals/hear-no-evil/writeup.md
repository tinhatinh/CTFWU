# Hear No Evil — Hardware (Medium)

**Flag:** 2/2
`v1 = H7CTF{38b0e71c-6126-49f7-8692-3f0bf6bf31b0}` · `v2 = H7CTF{11945790-f241-4644-9e45-e19819bdc996}`
**Target:** `https://web-2c53753bcbf2c207.web.h7tex.com` · Artifact: `/capture.pcap` (2220 B, 50 packet)

## Đề bài

Một cặp tai nghe NoiseGate nói chuyện với app qua BLE, và bản ghi không chỉ có chúng. Hai bí mật nằm
trong capture: một cái tai nghe tự lộ trong một lần đọc cấu hình, một cái chỉ được đưa ra sau khi app
xác thực. Lấy cả hai.

## Phân tích ban đầu

Trang chủ chỉ trỏ tới một file:

```
capture.pcap (open in Wireshark: it dissects btle / btatt natively)
There is more than one device in the air. Two secrets are in here: one the earbuds
leak in a config read, and one they only hand over after the app authenticates.
```

Host không có `tshark`, `capinfos`, `btlejack`. Dump tay từng packet thì capture không phải btle chuẩn:

- 4 packet mở đầu bằng access address `D6BE898E` là quảng cáo BLE thật, của `Mi Smart Band 6`,
  `JBUL TUNE 230NC`, `Galaxy Fit3` và `NoiseGate Buds`. Ba cái đầu là thiết bị nhiễu.
- 46 packet còn lại mở đầu bằng `C3 B2 A1 50`, theo sau là 6 byte header, payload và 3 byte CRC.
  DLT trong pcap header ghi 251 nhưng nội dung là transport ATT kiểu tự chế.

Nên parse tay: `payload = packet[11:-3]`.

## Các hướng đã loại

1. Phải phá pairing BLE rồi decrypt. Trong capture không có PDU pairing hay Start Encryption nào,
   nên không có LTK để mà decrypt. Khoá của cả hai đặc tính dẫn xuất từ dữ liệu đã bay trên không khí.
   Loại hướng tấn công crypto thật; bài còn lại là bài reassemble.
2. Dissect bằng tool có sẵn như capture btle thường. Host không có `tshark`/`btlejack`/`capinfos`,
   và 46/50 packet không theo khung LL nào: DLT ghi 251 nhưng payload là ATT tự chế.
3. Cứ payload 2 byte là một request chọn handle. `31 0a` đọc được thành handle `0x0031`, nhưng nó
   cũng là 2 byte cuối của blob đang đọc dở. Lần reassemble đầu tôi đặt điều kiện `len >= 11` trước
   điều kiện handle nên nhận nhầm chunk 20 byte thành "handle + data". Chốt lại bằng kiểm tra ngữ cảnh:
   một payload 2 byte chỉ là request nếu packet kế tiếp dài đúng 20 byte.

## Chuỗi khai thác

**Bước 1 - Định dạng lại transport.** Ba dạng payload phân biệt được bằng độ dài và ngữ cảnh:

| Dạng | Ví dụ | Nghĩa |
| --- | --- | --- |
| 2 byte | `21 00` | chọn handle, offset 0 |
| 4 byte | `21 00 14 00` | handle + offset |
| 20 byte (hoặc phần dư) | `83 3c f9 ...` | data cho request đang chờ |
| >= 11 byte | `31 00 <16 byte>` | notify tự chứa |

**Bước 2 - Đọc đặc tả từ chính capture.** Ghép các chunk của handle `0x0041` được 322 byte ASCII thuần:

```
NoiseGate fw1.4.2 [dbg]
provkey = adv mfg data (company 0x0f39) after the 0x01 type byte, 16 bytes
config@0x0021: plaintext = value XOR provkey (provkey repeated cyclically)
vault@0x0033: released after auth; plaintext = ct XOR ks,
  ks = sha256(provkey || nonce || byte(i)) for i=0,1,.. concatenated;
  nonce = notify@0x0031
```

Thiết bị tự ghi lại scheme khoá của nó. `config` là value XOR provkey. `vault` là ct XOR ks, với ks
dựng từ provkey và nonce của notify - không có bước xác thực nào ngoài việc hai giá trị đó phải đúng.

**Bước 3 - Lấy khoá.** Trong packet quảng cáo của NoiseGate, AD structure `14 FF 39 0F 01 ...` là
Manufacturer Specific Data, company `0x0F39`, byte con-type `0x01`, rồi đúng 16 byte:

```
provkey = cb0bba6665a4fc08131cd624f22869ca
nonce   = ca2458f360ade373f6d055aeb0304501     (notify @ 0x0031)
```

**Bước 4 - Giải hai đặc tính.**

```python
v1 = bytes(c ^ provkey[i % 16] for i, c in enumerate(ct_0x21))

ks = b"".join(hashlib.sha256(provkey + nonce + bytes([i])).digest() for i in range(8))
v2 = bytes(c ^ ks[i] for i, c in enumerate(ct_0x33))
```

Cả hai ciphertext dài 43 byte, và 43 byte đó chính là độ dài chuỗi flag.

**Bước 5 - Kiểm chứng tính đúng.** 322 byte của blob `0x0041` ghép lại là ASCII liền mạch từ đầu tới
cuối. Một bộ reassemble đặt sai offset, hoặc nhầm request với data nối tiếp, không cho ra chuỗi như
vậy; nên thứ tự chunk và các offset là đúng, không phải giải trùng hợp.

## Flag
```
python solve.py analysis/capture.pcap

[*] provkey          : cb0bba6665a4fc08131cd624f22869ca
[*] 0x0041 (322 byte) b'NoiseGate fw1.4.2 [dbg]\nprovkey = adv mfg data (company 0x0f'
[*] config@0x0021 -> b'H7CTF{38b0e71c-6126-49f7-8692-3f0bf6bf31b0}'
[*] vault @0x0033 -> b'H7CTF{11945790-f241-4644-9e45-e19819bdc996}'
```

```
v1: H7CTF{38b0e71c-6126-49f7-8692-3f0bf6bf31b0}
v2: H7CTF{11945790-f241-4644-9e45-e19819bdc996}
```
