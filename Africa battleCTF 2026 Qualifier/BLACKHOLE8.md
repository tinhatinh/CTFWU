---
title: "Operation BLACKHOLE 8"
category: "Forensics"
tags: ["pcap", "tshark", "ddos", "http-headers", "referer", "packet-analysis"]
solve_date: "2026-10-07T09:40:00+07:00"
language: "vi"
points: 30
---

# Operation BLACKHOLE 8 — flag nằm trong header Referer

**Flag:** `CTF{UF0N3t_DD0S_4n4lys1s_2026}` · **File:** `CTF1.pcapng` dùng chung, 3 137 400 byte, SHA-256 `acc7bcb50585244b7f374e3402d157b605e9e5ef22f10ba223fce7e98536319b`

## Đề bài

Câu cuối của loạt bài yêu cầu khôi phục flag được giấu trong một HTTP header. Khác với sáu câu trước, đáp án có wrapper và tiền tố là `CTF{`, không phải `battleCTF{`.

## Phân tích

Trong 52 request dùng `curl/8.21.0`, có 50 request tới `/?debug=N` và chứa header liên quan. Chỉ dựa vào URI và UA thì chưa thể biết các request này được gửi thủ công hay bằng script.

## Các hướng đã thử

1. **Grep các chuỗi gợi ý:** `frame contains "battle"`, `"flag"`, `"Flag"`, `"FLAG"` đều trả về **0** packet. Flag không dùng prefix của sự kiện và cũng không xuất hiện nguyên văn từ “flag”, nên grep trực tiếp không hiệu quả.
2. **Một header tùy chỉnh `X-...`:** `frame contains "X-"` khớp đúng một frame (6192), nhưng hex dump cho thấy `58 2d` ở offset packet 0x12–0x13, tức trường **IP checksum**, không phải HTTP payload: `45 00 00 3c 0a bd 40 00 40 06 58 2d c0 a8 2b 80`.
3. **Flag trong response body:** `http.response` chỉ có 667 phản hồi `200` với `Content-Length: 3114` giống nhau và một phản hồi `404`; không response nào chứa `CTF`.
4. **Flag trong URI:** các URI chỉ gồm `/`, `/?debug=1..50` và `/fichier-inexistant`.

## Lời giải

**Bước 1 — Tìm prefix thực của flag.** Chuỗi `CTF` xuất hiện trong 50 frame:

```bash
tshark -r CTF1.pcapng -Y 'frame contains "CTF"' \
  -T fields -e frame.number | wc -l
```
```text
50
```

**Bước 2 — Kiểm tra 50 frame đó.**

```bash
tshark -r CTF1.pcapng -Y 'http.request && http.referer != ""' \
  -T fields -e frame.number -e http.request.uri -e http.user_agent -e http.referer | head -3
```
```text
6757    /?debug=1       curl/8.21.0   http://ctf.local/CTF{UF0N3t_DD0S_4n4lys1s_2026}
6768    /?debug=2       curl/8.21.0   http://ctf.local/CTF{UF0N3t_DD0S_4n4lys1s_2026}
6779    /?debug=3       curl/8.21.0   http://ctf.local/CTF{UF0N3t_DD0S_4n4lys1s_2026}
```

Header chứa flag là `Referer`, một header gửi từ client lên server — máy tấn công tự gắn flag vào request của mình; dịch vụ không làm lộ flag.

**Bước 3 — Kiểm tra tính duy nhất.**

```bash
tshark -r CTF1.pcapng -Y 'http.request && http.referer != ""' \
  -T fields -e http.referer | sort -u
```
```text
http://ctf.local/CTF{UF0N3t_DD0S_4n4lys1s_2026}
```

Trong toàn bộ capture chỉ có một giá trị `Referer` không rỗng; nó được lặp lại giống hệt 50 lần. Chính 50 frame đó khớp với `"CTF"` ở Bước 1. Giữ nguyên chuỗi `UF0N3t_DD0S_4n4lys1s_2026` đúng như trong header.

## Kết quả

```text
CTF{UF0N3t_DD0S_4n4lys1s_2026}
```

Trạng thái xác nhận: trích xuất trực tiếp từ packet; flag đã được nộp và chấp nhận.

## Tái hiện

```bash
cd "operation-blackhole-8"
tshark -r CTF1.pcapng -Y 'http.request && http.referer != ""' -T fields -e http.referer | sort -u
tshark -r CTF1.pcapng -Y 'frame contains "CTF"' -T fields -e frame.number | wc -l
```
