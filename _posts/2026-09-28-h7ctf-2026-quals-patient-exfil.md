---
title: "Patient Exfil — Forensics (Medium)"
date: 2026-09-28 16:53:17 +0700
lastmod_at: 2026-09-28 16:53:17 +0700
categories: [Forensics]
tags: [h7ctf-quals, Forensics]
image:
  path: /CTFWU/H7CTF%202026%20Quals/patient-exfil/files/de.png
---
{% raw %}
**Flag:** `H7CTF{6787b86cc777f426b9c0}` · Files: `capture (2).pcap`, 108.604 byte, sha256 `3ab17689659f80efadceea1adc2eea5e9bddfcc3254ad85e89c4c75ee20bbb76`

## Đề bài

Một máy trong lab đã "nói chuyện với bên ngoài" theo lịch rất chậm, trong sáu tuần không gây ra cảnh báo nào.
Đề cho duy nhất một bản thu mạng (`capture.pcap`) và yêu cầu tìm thông điệp bí mật mà kẻ tấn công đã gửi ra ngoài.
Format cờ của giải là `H7CTF{...}`.

## Phân tích ban đầu

Triage bằng `node ~/.qoder/skills/ctf-solve/scripts/triage.cjs`:

- `magic = libpcap capture (little-endian)`, `entropy = 5.084/8`, chỉ 87 chuỗi ký tự in được, `flag-pattern hits = 0`.
  Kết luận ngay: không có cờ nằm rõ trong file, thông tin chắc chắn bị encode hoặc rải nhiều nơi.
- `survey.py` (scapy): 1260 gói trong 148,31 giây, toàn bộ là loopback `127.0.0.1`;
  1080 gói TCP + 180 gói DNS. Không có ICMP, không có giao thức lạ.
- Cổng đích: `8080` (534 gói), `8443` (114 gói), còn lại là cổng ephemeral phía server, mỗi cổng 4 gói.
- HTTP: trên 8080 chỉ 5 kiểu request lặp lại (`/assets/app.js` x28, `/api/health` x22, `/index` x20, `/` x19);
  trên 8443 là 19 lần `GET /api/v2/checkin` với `User-Agent: telemetry-agent/1.4` - đây chính là C2 heartbeat
  mà đề gợi ý ("very patient schedule"), nhưng nó đồng nhất 100%: mọi response đều `ok`, độ dài 66 byte.
- DNS: 10 qname unique, trong đó 7 tên vô hại (`pool.ntp.org`, `updates.ubuntu.com`, `mirror.lab.local`,
  `grafana.internal.lab`, `logging.googleapis.com`, `api.weather.example`, `cdn.jsdelivr.net`)
  và 3 tên kỳ lạ cùng một cha:

  ```
  00ja3ugvcgpm3doobx.sync.cdn-telemetry-lab.net.
  01mi4dmy3dg43tozru.sync.cdn-telemetry-lab.net.
  02gi3geoldgb6q.sync.cdn-telemetry-lab.net.
  ```

Hướng nghi vấn: DNS tunneling. Domain `cdn-telemetry-lab.net` giả danh dịch vụ telemetry, prefix `00/01/02`
là chỉ mục mẩu tin, và đây là cách kinh điển để lọt qua dashboard vì mỗi truy vấn chỉ là một DNS lookup.

## Các hướng đã loại

Trước khi chốt, đã kiểm tra và loại ba kênh khác (chi tiết trong `notes.md`):

1. Response DNS giấu dữ liệu: query exfil có `ancount=0, nscount=0, arcount=0`. 84 answer record trong file
   thuộc về các tên vô hại và chỉ là A record ngẫu nhiên để gây nhiễu.
2. HTTP header/body: không có tiêu đề biến thể, không có body nào khác `ok`, không có endpoint hiếm.
3. Kênh độ dài gói / giãn cách thời gian: payload chỉ nhận 6 giá trị rời rạc `{40,45,50,53,66,87}`,
   19 request checkin đều dài 87 byte như nhau.

## Chuỗi khai thác

**Bước 1 - Đếm query theo domain cha.** Lọc mọi DNS query có `qname` kết thúc bằng `.sync.cdn-telemetry-lab.net.`.
Có 12 packet, nhưng chỉ 3 label unique: mỗi label được gửi thành từng cặp (retry), lặp qua 2 vòng,
trải từ giây 5,60 đến giây 47,02 của phiên capture. Đây chính là "low and slow": 12 query trong 148 giây,
không đủ dày để kích hoạt bất kỳ threshold nào.

**Bước 2 - Tách chỉ mục khỏi payload.** Regex `^(\d{2})([a-z2-7]+)\.sync\.cdn-telemetry-lab\.net$`.
Phần payload chỉ chứa ký tự trong bảng `[a-z2-7]`, tức tập chữ cái của base32 (không có `0`,`1`,`8`,`9`).
Điều này buộc ta phải hiểu `00/01/02` là chỉ mục chứ không phải dữ liệu: nếu gộp cả prefix vào thì không decode được.

**Bước 3 - Ghép theo thứ tự chỉ mục và base32-decode.**

```python
blob = "".join(chunks[k] for k in sorted(chunks))     # 00,01,02
pad  = blob.upper() + "=" * ((8 - len(blob) % 8) % 8)
data = base64.b32decode(pad)
```

```
blob (44 ký tự): ja3ugvcgpm3doobxmi4dmy3dg43tozrugi3geoldgb6q
decoded (27 byte): H7CTF{6787b86cc777f426b9c0}
```

**Bước 4 - Kiểm chứng tính đầy đủ.** 44 % 8 = 4 nên chunk cuối ngắn hơn (12 ký tự so với 16), đúng dấu hiệu
của mẩu tin cuối trong một dòng dữ liệu bị cắt; kết quả kết thúc chính xác bằng `}` và mở đầu bằng `H7CTF{`.
Nếu thứ tự chunk sai, hoặc nếu còn chunk bị thiếu, đầu ra sẽ là rác và không thể thẳng hàng ngoặc như vậy.
Đó là bằng chứng cấu trúc ghép đã đúng, không phải suy đoán.

## Flag
Chạy lại được bằng:

```bash
python _ctf/patient-exfil/exploit.py "C:/Users/Administrator/Downloads/capture (2).pcap"
```

```
[+] 3 chunks: ['00', '01', '02']
[+] base32 blob (44 chars): ja3ugvcgpm3doobxmi4dmy3dg43tozrugi3geoldgb6q
[+] decoded 27 bytes -> b'H7CTF{6787b86cc777f426b9c0}'
[+] flag: H7CTF{6787b86cc777f426b9c0}
```

{% endraw %}
