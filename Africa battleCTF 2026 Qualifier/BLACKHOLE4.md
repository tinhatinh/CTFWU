---
title: "Operation BLACKHOLE 4"
category: "Forensics"
tags: ["pcapng", "tshark", "http-method", "get-flood", "http-flood", "network-forensics"]
solve_date: "2026-10-07T09:34:00+07:00"
language: "vi"
points: 10
---

# Operation BLACKHOLE 4 — phương thức GET trong các request flood

**Đáp án:** `GET` · **File:** `CTF1.pcapng` dùng chung, 3 137 400 byte, SHA-256 `acc7bcb50585244b7f374e3402d157b605e9e5ef22f10ba223fce7e98536319b`

## Đề bài

Câu 4 của loạt bài hỏi HTTP method nào được dùng để flood. Phần triage tổng quát nằm trong [Operation BLACKHOLE 1](BLACKHOLE1.md).

## Phân tích

Capture có 668 kết nối TCP tới `192.168.43.1:8000`, mỗi kết nối mang một HTTP request. Có 667 phản hồi `200 OK` và một `404`. Đếm `http.request.method` trong các kết nối này để xác định method.

## Các hướng đã thử

1. **`POST`:** không xuất hiện trong thống kê method của TCP request tới port 8000.
2. **`M-SEARCH`:** xuất hiện 45 lần nhưng là SSDP chạy trên UDP/1900, không thuộc TCP flood (xem [Operation BLACKHOLE 3](BLACKHOLE3.md)).
3. **`HEAD`:** không có trong các request đã lọc. Kết luận dựa trên method field, không phải kích thước response body.

## Lời giải

**Bước 1 — Đếm HTTP method trên toàn capture.**

```bash
tshark -r CTF1.pcapng -Y 'http.request' \
  -T fields -e http.request.method | sort | uniq -c | sort -rn
```
```text
    668 GET
     45 M-SEARCH
```

**Bước 2 — Lọc riêng flood (TCP, port 8000).**

```bash
tshark -r CTF1.pcapng -Y 'http.request && tcp.dstport==8000' \
  -T fields -e http.request.method | sort | uniq -c
```
```text
    668 GET
```

Cả 668 request flood đều là `GET`; không có method thứ hai.

**Bước 3 — Đối chiếu với request mẫu thực tế.** Đọc request line của một vài kết nối đầu (dùng `http.request.method` và `http.request.uri`; lưu ý `http.request.line` chứa header chứ không phải request line):

```bash
tshark -r CTF1.pcapng -Y 'http.request && tcp.dstport==8000' \
  -T fields -e frame.number -e http.request.method -e http.request.uri -e http.request.version | head -3
```
```text
4       GET     /       HTTP/1.1
15      GET     /       HTTP/1.1
26      GET     /       HTTP/1.1
```

Phân bố URI cho thấy 617 request là `GET /`, 50 là `GET /?debug=N` và một là `GET /fichier-inexistant`; tất cả vẫn dùng method `GET`.

## Kết quả

```text
GET
```

## Tái hiện

```bash
cd "operation-blackhole-4"
tshark -r CTF1.pcapng -Y 'http.request' -T fields -e http.request.method | sort | uniq -c | sort -rn
tshark -r CTF1.pcapng -Y 'http.request && tcp.dstport==8000' -T fields -e frame.number -e http.request.method -e http.request.uri | head -3
```
