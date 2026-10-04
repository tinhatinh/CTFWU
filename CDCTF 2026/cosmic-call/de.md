# Đề bài - cosmic-call

## Nguyên văn đề

```text
Cosmic Call
797
Scanning NTA Crypto
b0b, adlee7

ping... ping... ping... there's something out there. Can you figure out what's
communicating on the network and what they're saying? I sure hope Command didn't
reuse the CTR Nonce...

The flag format is cdctf{FL@g!_g03s_h3r3}

Start an instance to get a terminal on the relay.

Your instance is running

https://wigjupsh.i.cdctf.net
```

## Metadata đã xác minh

- Không có file đính kèm. Artifact duy nhất là **terminal trên máy relay** (ttyd trong trình duyệt).
- Instance chạy `ttyd -p 7681 -t titleFixed COSMIC-1 relay`, shell prompt `player@router`, uid 1000 `player`.
- Có sẵn: `tcpdump`, `python3`, `xxd`. **Không có:** `tshark`, `capinfos`, `strings`.
- Instance đầu tiên (`wigjupsh`) kèm sẵn `/tmp/all.pcap` (~3 MB, 1457 gói), `/tmp/pass.pcap` (~88 KB,
  483 gói), `/home/player/OPS-NOTE.txt` và `~/.bash_history` của operator (mode 600, đọc được).
- Instance sau (`zmvopuqy`, `njpwkhrj`...) **không có** các file đó: `/tmp` trống, không có `.bash_history`.
  Toàn bộ giao thức phải tự dẫn lại từ traffic sống.
- Định dạng cờ `cdctf{FL@g!_g03s_h3r3}` ⇒ bảng ký tự gồm chữ hoa/thường, số, `_`, `@`, `!`, `?`.
