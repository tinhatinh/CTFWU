---
title: "Operation BLACKHOLE 6"
category: "Forensics"
tags: ["pcap", "tshark", "ddos", "conversations", "icmp", "http-flood"]
solve_date: "2026-10-07T09:37:00+07:00"
language: "vi"
points: 15
---

# Operation BLACKHOLE 6 — đo thời lượng DDoS từ bảng conversations

**Đáp án:** `83` · **File:** `CTF1.pcapng` dùng chung, 3 137 400 byte, SHA-256 `acc7bcb50585244b7f374e3402d157b605e9e5ef22f10ba223fce7e98536319b`

## Đề bài

Câu 6 của loạt bài yêu cầu thời lượng tấn công tính bằng giây. Phần triage chung nằm trong `operation-blackhole-1`.

## Phân tích

Capture dài 1060,814 giây, nhưng phần lớn là traffic nền (SSDP, mDNS, NTP, ARP). Traffic tấn công tập trung giữa một cặp địa chỉ và kết thúc sớm:

```text
192.168.43.128  <-> 192.168.43.1   3344 2407 kB   4012 429 kB   7356 2836 kB   0.000000000   83.2457
```

`Relative Start = 0` đánh dấu packet đầu tiên của cặp địa chỉ này trong capture, không nhất thiết là lúc sự cố bắt đầu. `Duration = 83.2457 s` là khoảng thời gian giữa packet đầu và packet cuối của cặp.

## Các hướng đã thử

1. **`Capture duration` = 1060,814 giây:** đây là độ dài toàn file, bao gồm khoảng 16 phút traffic nền sau khi đợt tấn công dừng.
2. **Chỉ lấy khoảng thời gian HTTP flood:** packet cuối trên `tcp.port==8000` nằm tại `t = 79.154051`, packet đầu tại `t = 0`, nên được 79,154 giây. Cách đo này mô tả riêng flood chính xác hơn nhưng **không phải đáp án được tác giả chấp nhận**; nó bỏ qua 5 packet ICMP từ cùng máy tấn công ngay sau đó. Loại cách đo này vì không khớp bảng thống kê của Wireshark.
3. **Cộng thời lượng các đợt flood:** traffic xuất hiện thành hai đợt (`0 → 4.030` và `69.909 → 79.154`), giữa hai đợt im lặng 65,88 giây; tổng “thời gian có packet tấn công” chỉ khoảng 13 giây. Đề bài không yêu cầu tính theo cách này.

## Lời giải

**Bước 1 — Dùng bảng conversations làm mốc.** `Duration` của cặp `.128 <-> .1` trong Statistics → Conversations (cùng dữ liệu được `tshark` in ra):

```bash
tshark -r CTF1.pcapng -q -z conv,ip | sed -n '6p'
```
```text
192.168.43.128       <-> 192.168.43.1            3344 2407 kB      4012 429 kB       7356 2836 kB       0.000000000        83.2457
```

**Bước 2 — Xem traffic nào nằm trong khoảng 79,154 → 83,2457.** Đây là yếu tố giúp phân biệt đáp án 79 hay 83:

```bash
tshark -r CTF1.pcapng -Y 'ip.src==192.168.43.128 && icmp' \
  -T fields -e frame.time_relative -e icmp.type -e icmp.ident -e icmp.seq
```
```text
79.156784851        8       60542   1
80.173473554        8       60542   2
81.197433216        8       60542   3
82.221454444        8       60542   4
83.245389592        8       60542   5
```

Có 5 gói ICMP echo (type 8), cùng `ident`, cách nhau khoảng 1,02 giây, được gửi từ máy tấn công tới mục tiêu ngay sau khi flood kết thúc. `83.245389592 - 0 = 83.2454` gần với giá trị `Duration` ở Bước 1.

**Bước 3 — Lấy thời lượng nguyên.** Khoảng thời gian của cặp địa chỉ bao gồm HTTP và các packet ICMP đến sau, tổng cộng khoảng 83,25 giây. Đáp án `83` được chấp nhận. Chỉ đo TCP/8000 thì được 79,154 giây; hai số này tương ứng với hai phạm vi khác nhau.

## Kết quả

```text
83
```

Đã nộp trên ctf.bugpwn.com và được chấp nhận. Phép đo `79.154` giây (chỉ HTTP flood) đúng về mặt kỹ thuật nhưng không phải cách tác giả chấm; xem ghi chú trong `README.md` của sự kiện.

## Tái hiện

```bash
cd "operation-blackhole-6"
tshark -r CTF1.pcapng -q -z conv,ip | sed -n '6p'
tshark -r CTF1.pcapng -Y 'ip.src==192.168.43.128 && icmp' -T fields -e frame.time_relative -e icmp.type -e icmp.ident -e icmp.seq
tshark -r CTF1.pcapng -Y 'tcp.port==8000' -T fields -e frame.time_relative | sed -n '1p;$p'
```
