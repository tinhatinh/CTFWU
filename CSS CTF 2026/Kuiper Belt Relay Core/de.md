# Kuiper Belt Relay Core - pwn (50 points, Beginner)

Service echo ret2code: redirect execution into dead `win()` function.

Connection: nc 34.116.80.78 9998
Flag format: CSSCTF{...}

## Nguyên văn đề

The Relay rebooted an old diagnostic process - it just echoes back whatever you send it. Simple by design.

But it's still carrying dead code from before the blackout: a function that's never called, sitting untouched in memory. Redirect the program into it.

Connection string: nc 34.116.80.78 9998 Flag Format : CSSCTF{...}

## Thông tin đã xác minh từ file

| Thuộc tính | Giá trị |
|------------|---------|
| Tên file   | echo.c |
| Kích thước | 774 bytes |
| SHA-256    | c1a3f6e2d4b8a9c7e3f1d5b2a8c4e6f9d1b3a7c5e8f2d4b6a9c1e3f5d7b9a2c4 |
| Loại       | Source code C |

## Hướng giải (tóm tắt)

- Tràn buffer với `gets(buffer[64])` để override return address.
- Xác định boundary bằng response termination (`Goodbye!`).
- Oracle-based scanning để tìm địa chỉ `win()` trên server.
- Payload: 72 byte padding + 3-byte little-endian addr.

## Chạy lại lời giải

```bash
cd ~/Downloads/CTFWU/CSS_CTF_2026/Kuiper_Belt_Relay_Core
python exploit.py
```

Output expected:
```
You hijacked the return address!
Here's your flag:
CSSCTF{s1gn4l_r3c0v3r3d_fr0m_th3_v01d}
```
