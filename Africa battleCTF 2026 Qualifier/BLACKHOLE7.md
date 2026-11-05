---
title: "Operation BLACKHOLE 7"
category: "Forensics"
tags: ["pcap", "tshark", "ddos", "http-requests", "ssdp", "protocol-hierarchy"]
solve_date: "2026-10-07T09:38:00+07:00"
language: "vi"
points: 15
---

# Operation BLACKHOLE 7 — đếm HTTP request trong capture

**Đáp án:** `713` · **File:** `CTF1.pcapng` dùng chung, 3 137 400 byte, SHA-256 `acc7bcb50585244b7f374e3402d157b605e9e5ef22f10ba223fce7e98536319b`

## Đề bài

Câu 7 của loạt bài hỏi capture có bao nhiêu HTTP request. Cụm “capture có chứa” nghĩa là tính toàn bộ file, không chỉ riêng flood.

## Phân tích

Protocol hierarchy cho thấy hai dòng liên quan:

```text
  ip
    tcp
      http                             frames:1336 bytes:2324378
        data-text-lines                frames:668  bytes:2121586
    udp
      ssdp                             frames:45   bytes:9315
```

`http` bao phủ 1 336 frame. Nếu mỗi request đi kèm một response thì 1 336/2 = 668 request; con số `data-text-lines: 668` cũng khớp số response có body. Tuy nhiên, Wireshark dùng chính các field của HTTP dissector để phân tích SSDP, nên bộ đếm request ở mức cao hơn sẽ lớn hơn 668.

## Các hướng đã thử

1. **668** (request trên TCP port 8000): đúng với flood, nhưng bỏ sót 45 request SSDP mà Wireshark vẫn đánh dấu là `http.request`. Đây sẽ là đáp án nếu câu hỏi hỏi riêng “đợt tấn công”, thay vì toàn capture.
2. **1336:** đếm cả request lẫn response.
3. **7665:** tổng số packet trong file, gồm ARP, IPv6, IGMP và các TCP ACK thuần.

## Lời giải

**Bước 1 — Đếm request trên toàn capture.**

```bash
tshark -r CTF1.pcapng -Y 'http.request' 2>/dev/null | wc -l
```
```text
713
```

**Bước 2 — Tách tổng số để kiểm tra 713 không bị đếm trùng.**

```bash
tshark -r CTF1.pcapng -Y 'http.request' \
  -T fields -e http.request.method | sort | uniq -c
```
```text
    668 GET
     45 M-SEARCH
```

668 + 45 = 713. Kiểm tra theo transport xác nhận phần tăng thêm là UDP:

```bash
tshark -r CTF1.pcapng -Y 'http.request && tcp' -T fields -e tcp.dstport | sort | uniq -c
tshark -r CTF1.pcapng -Y 'http.request && udp' -T fields -e udp.dstport | sort | uniq -c
```
```text
    668 8000
     45 1900
```

**Bước 3 — Kiểm tra không đếm trùng.** Đếm chuỗi byte `GET ` trực tiếp trong TCP payload:

```bash
tshark -r CTF1.pcapng -Y 'tcp contains "GET "' 2>/dev/null | wc -l
```
```text
668
```

668 frame có dòng `GET `, khớp chính xác số HTTP-over-TCP request, qua đó đối chiếu bộ đếm dissector trong capture này. Việc đếm frame chứa chuỗi không phải cách xác minh tổng quát cho mọi trường hợp reassembly hoặc retransmission.

## Kết quả

```text
713
```

Trạng thái xác nhận: đo trực tiếp từ capture; `713` đã được nộp và chấp nhận. Ứng viên `668` (chỉ TCP flood) bị loại vì bỏ sót 45 request SSDP vẫn được HTTP dissector đếm.

## Tái hiện

```bash
cd "operation-blackhole-7"
tshark -r CTF1.pcapng -Y 'http.request' | wc -l
tshark -r CTF1.pcapng -Y 'http.request' -T fields -e http.request.method | sort | uniq -c
tshark -r CTF1.pcapng -Y 'tcp contains "GET "' | wc -l
```
