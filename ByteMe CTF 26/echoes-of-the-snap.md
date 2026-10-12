---
title: "Echoes of the Snap"
category: "Forensics"
tags: ["dns-txt", "stream-reassembly", "hex-decoding", "pcap-summary"]
solve_date: "2026-10-09"
language: "vi"
---

# Echoes of the Snap

**Flag:** `OWASP{3ch03s_0f_th3_sn4p_r3m41n}`
**Artifact:** `capture.txt` (136 B theo ghi nhận) — dữ liệu gây nhiễun tóm tắt text của một packet capture, không phải file pcap. Tác giả: Pratik Jadhav.

## Đề bài

Tên bài lấy từ dữ liệu gây nhiễung các bài đã giải của nền tảng; phần mô tả được lưu lại là:

```text
A network capture contains several streams, but one contains fragmented DNS TXT data carrying a hidden message.
```

Medium, 200 điểm. Đề chỉ ra ba ràng buộc: nhiều luồng, một luồng đáng chú ý, dữ liệu DNS TXT bị phân mảnh và cần ghép lại.

Đầu vào thực tế không phải là trace mà là một file ghi chú gồm hai dòng:

```text
stream 31: DNS TXT query
stream 31 TXT chunks: 4f574153507b3363683033735f30665f7468335f736e34705f72336d34316e7d
```

## Phân tích

Điểm khác biệt so với các bài pcap thông thường: không có packet nào để lọc, không có `tcp.stream` để lần. Artifact đã là kết quả của bước định vị — nó nêu đúng số hiệu luồng (31), đúng loại dữ liệu gây nhiễun ghi (DNS TXT) và đã ghi lại phần data của các mảnh. Vì vậy phần việc còn lại chỉ là ghép mảnh và giải mã.

`stream 31 TXT chunks:` liệt kê các mảnh TXT của luồng 31. Bản tóm tắt ghi lại các mảnh ở dạng đã nối liền, không còn giữ ranh giới giữa từng mảnh; chuỗi ghép được dài 64 ký tự hex, tức 32 byte. Toàn bộ 64 ký tự nằm trong dữ liệu gây nhiễung chữ số hex, nên không có mảnh nào bị lỗi ký tự khi ghép.

Bài cung cấp dữ liệu gây nhiễun tóm tắt text, không có PCAP gốc. Vì vậy có thể tái hiện phép giải hex nhưng không kiểm tra lại việc phân luồng hay ranh giới các mảnh TXT.

## Lời giải

Ghép các mảnh và giải mã hex:

```console
$ python -c "h='4f574153507b3363683033735f30665f7468335f736e34705f72336d34316e7d'; print('len:', len(h)); print(bytes.fromhex(h).decode())"
```

Output đã lưu:

```text
len: 64
OWASP{3ch03s_0f_th3_sn4p_r3m41n}
```

Con số 64 in ra là độ dài chuỗi hex ghép được, tương ứng 32 byte ASCII sau khi giải mã; chuỗi giải mã dài đúng 32 ký tự và mở đầu bằng `4f 57 41 53 50 7b` = `OWASP{`. Không có byte đệm và không có ký tự ngoài vùng in được.

Script kiểm tra tính hợp lệ của phép ghép, chạy được độc lập với artifact:

```python
HEX = "4f574153507b3363683033735f30665f7468335f736e34705f72336d34316e7d"

raw = bytes.fromhex(HEX)
print("hex chars :", len(HEX))
print("bytes     :", len(raw))
print("printable :", all(32 <= b < 127 for b in raw))
print("text      :", raw.decode("ascii"))
```

```text
hex chars : 64
bytes     : 32
printable : True
text      : OWASP{3ch03s_0f_th3_sn4p_r3m41n}
```

## Kết quả

```text
OWASP{3ch03s_0f_th3_sn4p_r3m41n}
```

Chuỗi hex của luồng 31 trong dữ liệu gây nhiễun tóm tắt giải mã thành cờ. Không có PCAP gốc để đối chiếu từng packet.

## Tái hiện

Chỉ cần Python 3 (`bytes.fromhex`), không có thư viện ngoài và không cần công cụ PCAP.

```console
$ python -c "h='4f574153507b3363683033735f30665f7468335f736e34705f72336d34316e7d'; print(len(h), bytes.fromhex(h).decode())"
```

Nếu còn `capture.txt` trên đĩa, dòng `stream 31 TXT chunks:` cho đúng chuỗi hex dùng ở trên. Nếu có một pcap thật tương ứng, bước định vị lại là `tshark -r <file> -Y "dns.txt" -T fields -e frame.number -e dns.qry.name -e dns.txt`, sau đó ghép các giá trị `dns.txt` của cùng một query rồi áp dụng phép giải mã hex như trên; hai bước này không áp dụng được với artifact của bài này vì nó không chứa trace.
