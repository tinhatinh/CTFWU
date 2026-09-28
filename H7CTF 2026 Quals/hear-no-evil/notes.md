# Notes — Hear No Evil

## Cấu trúc capture

50 packet, chia làm hai loại:

1. **4 packet ADV thật** (bắt đầu bằng access address `D6BE898E`): quảng cáo của `Mi Smart Band 6`, `JBUL TUNE 230NC`, `NoiseGate Buds`, `Galaxy Fit3`. Ba cái đầu là thiết bị nhiễu đúng như đề ("they are not the only ones chattering on the air").
2. **46 packet giả lập**, mỗi packet mở đầu bằng `C3 B2 A1 50` rồi `02`, 6 byte header, payload, 3 byte CRC cuối. Đây không phải khung LL chuẩn; tác giả tự đóng gói ATT-like transport vào pcap có DLT ghi là 251.

Vì không có `tshark`/`btlejack`/`capinfos` trên host (và file cũng không phải btle chuẩn), tự parse bằng `struct` là nhanh nhất: payload = `packet[11:-3]`.

## Ba dạng payload đã quan sát

| Độ dài | Ý nghĩa | Ví dụ |
| --- | --- | --- |
| 2 | chọn handle, offset 0 | `21 00` |
| 4 | handle (LE) + offset (LE) | `21 00 14 00` |
| 20 / n | data cho request đang chờ | 20 byte một chunk |
| >= 11 | notify tự chứa: handle + data | `31 00` + 16 byte |

Điểm dễ ghép sai: packet 2 byte vừa có thể là "chọn handle" vừa có thể là data nối tiếp (`31 0a` là 2 byte cuối của blob 0x0041). Phân biệt bằng ngữ cảnh: chỉ là request nếu packet **kế tiếp** dài đúng 20 byte.

## Đặc tả tự nằm trong capture (handle 0x0041, 322 byte)

```
NoiseGate fw1.4.2 [dbg]
provkey = adv mfg data (company 0x0f39) after the 0x01 type byte, 16 bytes
config@0x0021: plaintext = value XOR provkey (provkey repeated cyclically)
vault@0x0033: released after auth; plaintext = ct XOR ks, ks = sha256(provkey || nonce || byte(i)) for i=0,1,.. concatenated; nonce = notify@0x0031
```

Đây là lý do bài không cần破解 pairing thật: "auth" chỉ là XOR với khoá suy từ provkey + nonce, và cả hai đều có trong không khí.

## Khoá và dữ liệu

| Mục | Giá trị |
| --- | --- |
| provkey (16 B, sau `FF 39 0F 01` trong AD của quảng cáo NoiseGate) | `cb0bba6665a4fc08131cd624f22869ca` |
| nonce @0x0031 (16 B) | `ca2458f360ade373f6d055aeb0304501` |
| ct @0x0021 (43 B) | `833cf93223dfcf30712cb313c34b44fcfa398c4b519d9a3f3e24e01dc0055aacfb69dc5007c2cf39712cab` |
| ct @0x0033 (43 B) | `cc34ba6fa4a592a7f46c83edbc7fdb60fb91d6c01523a34302a8c1501cc5fe1099ba32f026702e592a7ea9` |

`ks = sha256(provkey||nonce||00) || sha256(...||01) || ...` (43 byte cần 3 block 32 byte, sinh 8 block cho đủ).

## Kết quả

```
v1 = H7CTF{38b0e71c-6126-49f7-8692-3f0bf6bf31b0}   (config@0x0021)
v2 = H7CTF{11945790-f241-4644-9e45-e19819bdc996}   (vault@0x0033)
```

Cả hai đều 43 byte và khớp mẫu `H7CTF{uuid}`. Blob 0x0041 ghép lại đúng 322 byte ASCII thuần là bằng chứng bộ reassemble đã ghép đúng offset.

## Nhánh đã loại / đã sửa

- Tìm LL Encryption Request / Start Encryption để lấy LTK rồi decrypt: **DEAD** — capture không có PDU pairing hay encryption nào, toàn bộ "mã hoá" là XOR theo đặc tả ở 0x0041.
- Bản reassemble đầu tiên phân loại nhầm chunk 20 byte thành "handle + data" (điều kiện `len>=11` đặt trước), làm handle 0x0021 chỉ còn 3 byte và sinh ra các handle rác `0x6F4E`, `0x9D51`... Sửa bằng thứ tự: data-nối-trước, request, rồi notify.
