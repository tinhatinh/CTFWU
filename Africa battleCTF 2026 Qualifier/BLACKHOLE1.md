---
title: "Operation BLACKHOLE 1"
category: "Forensics"
tags: ["pcapng", "tshark", "ddos", "http-flood", "tcp-flags", "network-forensics"]
solve_date: "2026-10-07T09:30:00+07:00"
language: "vi"
points: 5
---

# Operation BLACKHOLE 1 — lần theo nguồn flood dựa trên chiều lưu lượng

**Đáp án:** `192.168.43.128` · **File:** `CTF1.pcapng`, 3 137 400 byte, SHA-256 `acc7bcb50585244b7f374e3402d157b605e9e5ef22f10ba223fce7e98536319b`

## Đề bài

Acme Corp bị tấn công DDoS; đội SOC đã ghi lại toàn bộ lưu lượng trong sự cố vào file `CTF1.pcapng`. Câu 1 yêu cầu tìm địa chỉ IP của máy tấn công. Cả 8 câu trong loạt bài này dùng chung file capture, vì vậy phần triage dưới đây cũng được dùng lại trong các write-up sau.

## Phân tích

```text
Number of packets:   7665
Capture duration:    1060.814057483 seconds
Earliest packet time: 2026-09-17 17:40:33.888190960
```

Bảng endpoint cho thấy gần như toàn bộ lưu lượng xoay quanh hai địa chỉ:

```text
                       | Packets | |  Bytes  | | Tx Packets | | Tx Bytes | | Rx Packets | | Rx Bytes |
192.168.43.1                 7463   2857 kB          3450      2427 kB           4013      429 kB
192.168.43.128               7394   2841 kB          4032      431 kB            3362      2410 kB
239.255.255.250                53    14 kB             0        0 bytes            53       14 kB
84.77.195.114                  30  2700 bytes         15     1350 bytes           15     1350 bytes
```

Cả hai ứng viên đều có khoảng 7,4 nghìn packet, nên chỉ đếm packet thì chưa phân biệt được. Điểm khác biệt nằm ở **chiều lưu lượng**: `192.168.43.1` gửi 2 427 kB nhưng chỉ nhận 429 kB, đây là phía phản hồi; `192.168.43.128` gửi 431 kB và nhận 2 410 kB, nên đây là phía khởi tạo và nhận phần lớn dữ liệu trả về. Mẫu “một phía gửi request nhỏ, phía kia trả về lượng dữ liệu lớn” phù hợp với một đợt flood nhắm vào dịch vụ.

## Các hướng đã thử

1. **`84.77.195.114` là máy tấn công từ ngoài mạng:** chỉ có 30 packet, đều là NTP theo cả hai chiều (gửi 15, nhận 15), rải đều trong 521 giây. Không có dấu hiệu flood.
2. **`192.168.43.1` là máy tấn công vì có nhiều packet nhất:** sai chiều. Endpoint này nhận 668 kết nối TCP và phát 667 phản hồi HTTP `200 OK`, tức nó đang đóng vai trò máy chủ bị tấn công.
3. **Các địa chỉ multicast (`239.255.255.250`, `224.0.0.22/251/252`):** đây là thông báo SSDP/IGMP thường thấy trong mạng gia đình, không phải nguồn unicast.

## Lời giải

**Bước 1 — Gộp các cuộc hội thoại để tìm cặp chiếm ưu thế.** Bảng IPv4 conversations cho thấy cặp có số packet lớn nhất:

```bash
tshark -r CTF1.pcapng -q -z conv,ip | head -8
```
```text
192.168.43.128  <-> 192.168.43.1   3344 2407 kB   4012 429 kB   7356 2836 kB   0.000000000   83.2457
192.168.43.1    <-> 239.255.255.250   0  0 bytes     52  14 kB     52   14 kB   6.362195476  534.8808
```

7 356 trên tổng số 7 665 packet thuộc về cặp này; lưu lượng giữa chúng bắt đầu đúng tại `t = 0` của capture.

**Bước 2 — Xác định chiều kết nối bằng TCP flags.** Gói SYN không có ACK mở một kết nối và chỉ do phía chủ động gửi:

```bash
tshark -r CTF1.pcapng -Y 'tcp.flags.syn==1 && tcp.flags.ack==0 && tcp.dstport==8000' \
  -T fields -e ip.src | sort | uniq -c
```
```text
    668 192.168.43.128
```

Cả 668 lần mở kết nối tới port 8000 đều do `192.168.43.128` khởi tạo; `192.168.43.1` chỉ xuất hiện với SYN-ACK. Kết hợp với chiều dữ liệu ở phần Phân tích, nguồn tấn công là `192.168.43.128`.

**Bước 3 — Đối chiếu.** Các phép đo cùng xác nhận một địa chỉ: (a) máy này gửi ít byte hơn nhưng tạo cả 668 kết nối; (b) nó nhận 2 410 kB dữ liệu phản hồi; (c) các gói ICMP echo sau đợt flood cũng xuất phát từ nó, cho thấy cùng một host thực hiện cả hai hoạt động.

## Kết quả

```text
192.168.43.128
```

Đã nộp lên ctf.bugpwn.com và được chấp nhận.

## Tái hiện

```bash
cd "operation-blackhole-1"
bash triage.sh CTF1.pcapng          # toan bo so lieu dung cho 8 cau
```

Cần Wireshark ≥ 4.x, hoặc có `tshark`/`capinfos` trong `PATH`.
