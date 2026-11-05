---
title: "Operation BLACKHOLE 2"
category: "Forensics"
tags: ["pcapng", "tshark", "ddos", "http-flood", "tcp-flags", "network-forensics"]
solve_date: "2026-10-07T09:32:00+07:00"
language: "vi"
points: 5
---

# Operation BLACKHOLE 2 — xác định host bị flood từ đích đến của SYN

**Đáp án:** `192.168.43.1` · **File:** `CTF1.pcapng` dùng chung, 3 137 400 byte, SHA-256 `acc7bcb50585244b7f374e3402d157b605e9e5ef22f10ba223fce7e98536319b`

## Đề bài

Tiếp tục dùng capture `CTF1.pcapng` của sự cố DDoS tại Acme Corp. Câu 2 yêu cầu tìm địa chỉ IP của mục tiêu. Phần triage đầy đủ nằm trong [Operation BLACKHOLE 1](BLACKHOLE1.md); write-up này tập trung xác định phía nhận kết nối.

## Phân tích

Bảng endpoint chỉ còn hai ứng viên, và chiều dữ liệu cho biết phía nào đang phản hồi:

```text
                       | Packets | |  Bytes  | | Tx Packets | | Tx Bytes | | Rx Packets | | Rx Bytes |
192.168.43.1                 7463   2857 kB          3450      2427 kB           4013      429 kB
192.168.43.128               7394   2841 kB          4032      431 kB            3362      2410 kB
```

`192.168.43.1` gửi 2 427 kB nhưng chỉ nhận 429 kB. Một host trả về lượng dữ liệu lớn gấp khoảng 5,6 lần lượng nó nhận là host đang phục vụ nội dung, chứ không phải đang gửi request.

## Các hướng đã thử

1. **`192.168.43.128` là mục tiêu vì xuất hiện trong mọi cuộc hội thoại:** nhầm vai trò. Host này gửi 668 gói SYN và nhận phản hồi, tức là máy tấn công (xem câu 1).
2. **`192.168.43.254` là gateway/mục tiêu:** chỉ có 5 packet, gồm lưu lượng DHCP/ARP broadcast. Không có kết nối TCP nào gửi tới địa chỉ này.
3. **Địa chỉ broadcast/multicast `.255`, `224.0.0.x`, `239.255.255.250`:** đây là SSDP, mDNS, IGMP và DHCP broadcast thường thấy trong mạng gia đình; chúng không nhận kết nối unicast.

## Lời giải

**Bước 1 — Đọc địa chỉ đích của các gói mở kết nối.** Gói SYN không có ACK cho biết phía được gọi:

```bash
tshark -r CTF1.pcapng \
  -Y 'tcp.flags.syn==1 && tcp.flags.ack==0 && tcp.dstport==8000' \
  -T fields -e ip.dst | sort | uniq -c
```
```text
    668 192.168.43.1
```

Cả 668 lần thử kết nối đều nhắm tới cùng một địa chỉ.

**Bước 2 — Xác nhận vai trò dịch vụ qua phía phản hồi.** Nếu `192.168.43.1` là mục tiêu thì đây phải là phía phát các phản hồi HTTP:

```bash
tshark -r CTF1.pcapng -Y 'http.response' \
  -T fields -e ip.src -e http.response.code | sort | uniq -c
```
```text
    667 192.168.43.1 200
      1 192.168.43.1 404
```

Cả 668 phản hồi HTTP trong capture đều xuất phát từ địa chỉ này, trùng khớp với số kết nối ở Bước 1.

**Bước 3 — Đối chiếu.** Hai phép đo độc lập (TCP flags gửi đi và HTTP status code nhận về) cùng đưa ra một địa chỉ và tổng số 668, xác nhận vai trò client/server trong capture này.

## Kết quả

```text
192.168.43.1
```

## Tái hiện

```bash
cd "operation-blackhole-2"
tshark -r CTF1.pcapng \
  -Y 'tcp.flags.syn==1 && tcp.flags.ack==0 && tcp.dstport==8000' -T fields -e ip.dst | sort | uniq -c
tshark -r CTF1.pcapng -Y 'http.response' \
  -T fields -e ip.src -e http.response.code | sort | uniq -c
```
