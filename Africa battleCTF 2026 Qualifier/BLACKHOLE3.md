---
title: "Operation BLACKHOLE 3"
category: "Forensics"
tags: ["pcapng", "tshark", "http-flood", "tcp", "port-identification", "ssdp"]
solve_date: "2026-10-07T09:33:00+07:00"
language: "vi"
points: 10
---

# Operation BLACKHOLE 3 — port không chuẩn được dùng cho HTTP flood

**Đáp án:** `8000` · **File:** `CTF1.pcapng` dùng chung, 3 137 400 byte, SHA-256 `acc7bcb50585244b7f374e3402d157b605e9e5ef22f10ba223fce7e98536319b`

## Đề bài

Câu 3 của loạt bài yêu cầu xác định TCP port bị HTTP attack nhắm tới. Phần triage tổng quát nằm trong [Operation BLACKHOLE 1](BLACKHOLE1.md).

## Phân tích

Toàn bộ HTTP traffic trong capture đi giữa đúng hai địa chỉ `192.168.43.128 <-> 192.168.43.1` (7 356 trên tổng số 7 665 packet). Không có traffic trên port 80 hoặc 443, nên dịch vụ bị flood chạy trên một port không chuẩn. Bảng `conv,tcp` liệt kê 668 cuộc hội thoại, tất cả đều có dạng `192.168.43.128:<random source port> <-> 192.168.43.1:8000`.

## Các hướng đã thử

1. **Port 80:** capture không có packet HTTP nào trên port này.
2. **Port 1900 (SSDP):** `http.request` cũng khớp 45 packet `M-SEARCH` tại port đó, nhưng chúng chạy trên **UDP** và là broadcast service discovery bình thường trong mạng gia đình, không phải TCP flood. Loại khỏi phạm vi “TCP port”.
3. **Source port 42302, 42304, …:** các port này thay đổi theo từng kết nối (668 giá trị khác nhau), đặc trưng cho phía client chứ không phải dịch vụ được gọi.

## Lời giải

**Bước 1 — Đếm destination port của HTTP request chạy trên TCP.**

```bash
tshark -r CTF1.pcapng -Y 'http.request && tcp' \
  -T fields -e tcp.dstport | sort | uniq -c
```
```text
    668 8000
```

Chỉ có một port xuất hiện, không có giá trị thứ hai.

**Bước 2 — Tách phần UDP để tránh nhầm với SSDP.**

```bash
tshark -r CTF1.pcapng -Y 'http.request && udp' \
  -T fields -e udp.dstport | sort | uniq -c
```
```text
     45 1900
```

45 request còn lại (cộng với 668 thành 713) chạy trên UDP/1900 như đã loại trừ ở trên.

**Bước 3 — Xác minh từ phía phản hồi.** `http.response` cho kết quả 667 phản hồi `200` và một phản hồi `404`; tất cả đều có `tcp.srcport == 8000` và `ip.src == 192.168.43.1`. Số response khớp với số kết nối SYN tới cùng port này.

## Kết quả

```text
8000
```

## Tái hiện

```bash
cd "operation-blackhole-3"
tshark -r CTF1.pcapng -Y 'http.request && tcp' -T fields -e tcp.dstport | sort | uniq -c
tshark -r CTF1.pcapng -Y 'http.request && udp' -T fields -e udp.dstport | sort | uniq -c
```
