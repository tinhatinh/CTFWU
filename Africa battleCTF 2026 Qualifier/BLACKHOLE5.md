---
title: "Operation BLACKHOLE 5"
category: "Forensics"
tags: ["pcapng", "tshark", "user-agent", "curl", "http-flood", "network-forensics"]
solve_date: "2026-10-07T09:36:00+07:00"
language: "vi"
points: 10
---

# Operation BLACKHOLE 5 — User-Agent curl trong các request đáng ngờ

**Đáp án:** `curl/8.21.0` · **File:** `CTF1.pcapng` dùng chung, 3 137 400 byte, SHA-256 `acc7bcb50585244b7f374e3402d157b605e9e5ef22f10ba223fce7e98536319b`

## Đề bài

Câu 5 của loạt bài yêu cầu tìm User-Agent gắn với các request độc hại. Phần triage chung nằm trong [Operation BLACKHOLE 1](BLACKHOLE1.md).

## Phân tích

668 request flood sử dụng **108 User-Agent khác nhau**, tức các request dùng nhiều chuỗi UA. Chỉ số này chưa cho biết chúng được tạo ra bằng cách nào. Tần suất phân bố khá đồng đều: UA trình duyệt xuất hiện nhiều nhất chỉ có 12 lần; phần lớn chuỗi còn lại xuất hiện 2–10 lần. Vì vậy, chỉ chọn “UA xuất hiện nhiều nhất” trong nhóm `Mozilla/5.0...` không phải cách phân biệt đáng tin cậy.

Điểm khác thường thực sự nằm ở định dạng chuỗi: chỉ có một UA không giống UA của trình duyệt.

## Các hướng đã thử

1. **Chọn UA `Mozilla/5.0` phổ biến nhất:** mức cao nhất chỉ là 12/668 (1,8%), tiếp theo là 10, 10, 10, 9… Không có khoảng cách thống kê rõ ràng; chọn bất kỳ chuỗi nào trong nhóm này đều tùy ý.
2. **`Chromium/146.0.7680.179 Windows` và `Chromium/128.0.6613.138 Windows`** (mỗi chuỗi 20 lần): đây là UA sai định dạng, nhưng mỗi chuỗi chỉ chiếm 3% traffic và vẫn thuộc pool ngẫu nhiên của flood, không có hành vi đáng ngờ riêng.
3. **`Downloader`:** đây là User-Agent của binary `0byte.exe` trong bài reverse của cùng sự kiện; nó không xuất hiện trong capture này.

## Lời giải

**Bước 1 — Đếm User-Agent trong nhóm flood.**

```bash
tshark -r CTF1.pcapng -Y 'http.request && tcp.dstport==8000' \
  -T fields -e http.user_agent | sort | uniq -c | sort -rn | head -8
```
```text
     52 curl/8.21.0
     12 Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1
     10 Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Vivaldi/7.0.3495.18 Chrome/134.0.0.0 Safari/537.36
     10 Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36
     10 Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36
     10 Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36
```

`curl/8.21.0` đứng đầu với 52 lần, nhiều hơn các chuỗi Chromium xuất hiện 20 lần, và cho thấy đây là client dòng lệnh.

**Bước 2 — Liên hệ UA với hành vi.** UA này gửi request tới đâu?

```bash
tshark -r CTF1.pcapng -Y 'http.request && http.user_agent=="curl/8.21.0"' \
  -T fields -e http.request.uri | sed 's/=[0-9][0-9]*$/=N/' | sort | uniq -c
```
```text
      1 /
     50 /?debug=N
      1 /fichier-inexistant
```

50 request là chuỗi `GET /?debug=1..50`; mỗi request có header `Referer: http://ctf.local/CTF{UF0N3t_DD0S_4n4lys1s_2026}` — flag của câu 8. Request tới `/fichier-inexistant` nhận `404`, là request duy nhất thất bại trong toàn bộ capture.

**Bước 3 — Đối chiếu.** `curl/8.21.0` xuất hiện trong 52 trên 668 request và đi kèm 50 request `/?debug=N` có flag trong header. Mối liên hệ này hỗ trợ đáp án; chỉ riêng tần suất không chứng minh mọi request đều có cùng mục đích.

## Kết quả

```text
curl/8.21.0
```

## Tái hiện

```bash
cd "operation-blackhole-5"
tshark -r CTF1.pcapng -Y 'http.request && tcp.dstport==8000' -T fields -e http.user_agent | sort | uniq -c | sort -rn | head
tshark -r CTF1.pcapng -Y 'http.request && http.user_agent=="curl/8.21.0"' -T fields -e http.request.uri | sort | uniq -c
```
